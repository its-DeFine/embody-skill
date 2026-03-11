#!/usr/bin/env python3
import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests

from prove_datachannel_client import browser_headers, end_session, start_session


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inventory or run a leased-session command suite against the local Embody-Patches corpus."
    )
    parser.add_argument("--catalog-root", required=True, help="Root folder containing StartOfOman/Public command JSON files.")
    parser.add_argument("--artifact-dir", required=True, help="Output directory for suite artifacts.")
    parser.add_argument("--client-js", required=True, help="Path to embody_datachannel_client.js")
    parser.add_argument("--base-url", default="https://api.embody.zone")
    parser.add_argument("--origin", default="http://app.embody.zone")
    parser.add_argument("--invite-code")
    parser.add_argument("--invite-code-file", help="Path to a file containing the invite code.")
    parser.add_argument("--requested-duration-seconds", type=int, default=1200)
    parser.add_argument("--command-delay-seconds", type=float, default=3.0)
    parser.add_argument("--video-settle-seconds", type=float, default=5.0)
    parser.add_argument("--max-commands", type=int, default=0, help="Limit total concrete commands across all files.")
    parser.add_argument(
        "--include-source",
        action="append",
        default=[],
        help="Only include inventory files whose path contains this substring. Repeatable.",
    )
    parser.add_argument(
        "--exclude-source",
        action="append",
        default=[],
        help="Exclude inventory files whose path contains this substring. Repeatable.",
    )
    parser.add_argument(
        "--commands-file",
        help="Optional JSON file containing an explicit array of command strings to run in order.",
    )
    parser.add_argument(
        "--mode",
        choices=("inventory", "run"),
        default="inventory",
        help="inventory: emit command extraction only; run: execute extracted commands in a leased browser session",
    )
    return parser.parse_args()


PLACEHOLDER_RE = re.compile(r"\{[^}]+\}")


def iter_command_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*Commands.json")):
        if path.is_file():
            yield path


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def normalize_command_entry(command: str, source: Path, category: str, note: str = "") -> Dict[str, Any]:
    return {
        "command": command,
        "source_file": str(source),
        "category": category,
        "note": note,
    }


def extract_from_endpoint_item(item: Dict[str, Any], source: Path) -> List[Dict[str, Any]]:
    extracted: List[Dict[str, Any]] = []

    for example in item.get("examples", []) or []:
        if isinstance(example, str):
            extracted.append(normalize_command_entry(example, source, "example"))

    presets = item.get("presets")
    if isinstance(presets, dict):
        for key in presets.keys():
            if isinstance(key, str):
                extracted.append(normalize_command_entry(key, source, "preset"))

    commands = item.get("commands")
    if isinstance(commands, list):
        for command in commands:
            if isinstance(command, str) and not PLACEHOLDER_RE.search(command):
                extracted.append(normalize_command_entry(command, source, "commands_list"))

    command_template = item.get("command")
    if isinstance(command_template, str) and not PLACEHOLDER_RE.search(command_template):
        extracted.append(normalize_command_entry(command_template, source, "command"))

    if not extracted and isinstance(command_template, str):
        extracted.append(
            normalize_command_entry(
                command_template,
                source,
                "template_only",
                note="template contains placeholders; manual expansion required",
            )
        )

    return extracted


def extract_commands_from_spec(path: Path) -> List[Dict[str, Any]]:
    spec = load_json(path)
    extracted: List[Dict[str, Any]] = []
    endpoints = spec.get("endpoints") or {}

    for method in ("POST", "GET"):
        items = endpoints.get(method) or []
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            for entry in extract_from_endpoint_item(item, path):
                entry["method"] = method
                entry["transport"] = spec.get("transport")
                entry["api"] = spec.get("api")
                extracted.append(entry)

    return extracted


def build_inventory(root: Path) -> List[Dict[str, Any]]:
    inventory: List[Dict[str, Any]] = []
    for path in iter_command_files(root):
        commands = extract_commands_from_spec(path)
        inventory.append(
            {
                "source_file": str(path),
                "api": (load_json(path)).get("api"),
                "command_count": len(commands),
                "commands": commands,
            }
        )
    return inventory


def flatten_runnable_commands(inventory: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    runnable: List[Dict[str, Any]] = []
    for item in inventory:
        for command in item.get("commands", []):
            if command.get("category") == "template_only":
                continue
            if not isinstance(command.get("command"), str):
                continue
            runnable.append(command)
    return runnable


def apply_source_filters(
    inventory: List[Dict[str, Any]],
    include_source: List[str],
    exclude_source: List[str],
) -> List[Dict[str, Any]]:
    filtered: List[Dict[str, Any]] = []
    include_source = [item for item in include_source if item]
    exclude_source = [item for item in exclude_source if item]

    for item in inventory:
        source = item.get("source_file", "")
        if include_source and not any(token in source for token in include_source):
            continue
        if exclude_source and any(token in source for token in exclude_source):
            continue
        filtered.append(item)
    return filtered


def load_explicit_commands(commands_file: Optional[str]) -> List[str]:
    if not commands_file:
        return []
    payload = json.loads(Path(commands_file).read_text())
    if not isinstance(payload, list) or not all(isinstance(item, str) for item in payload):
        raise SystemExit("--commands-file must be a JSON array of command strings")
    return payload


def resolve_invite_code(invite_code: Optional[str], invite_code_file: Optional[str]) -> Optional[str]:
    if invite_code:
        return invite_code
    if invite_code_file:
        return Path(invite_code_file).read_text().strip()
    env_code = os.environ.get("EMBODY_INVITE_CODE")
    if env_code:
        return env_code.strip()
    return None


def write_analysis_stub(artifact_dir: Path, manifest: Dict[str, Any]) -> None:
    lines = [
        "# Suite Analysis",
        "",
        "Status: pending review",
        "",
        "## Summary",
        f"- Commands attempted: {len(manifest.get('sent', []))}",
        f"- Response events captured: {manifest.get('state_after', {}).get('response_count', 0)}",
        "",
        "## Review Notes",
        "- Compare `before.png` with per-command `after_XX.png` frames.",
        "- Check `proof.webm` for visible state changes and continuity.",
        "- For TTS commands, compare against Unreal diagnostics/logs in a parallel review pass.",
        "",
        "## Classification Template",
        "- pass: visible or logged effect matches command",
        "- partial: command appears sent but outcome is ambiguous or incomplete",
        "- fail: no visible or logged effect",
        "- untestable_without_manual_review: command requires semantic judgment or missing game-side signal",
    ]
    (artifact_dir / "analysis.md").write_text("\n".join(lines) + "\n")


def run_suite(args: argparse.Namespace, inventory: List[Dict[str, Any]]) -> Dict[str, Any]:
    from playwright.sync_api import sync_playwright

    invite_code = resolve_invite_code(args.invite_code, args.invite_code_file)
    if not invite_code:
        raise SystemExit("--invite-code is required in run mode")

    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    client_js = Path(args.client_js).read_text()
    explicit_commands = load_explicit_commands(args.commands_file)
    if explicit_commands:
        runnable = [
            normalize_command_entry(
                command,
                Path(args.commands_file),
                "explicit_commands_file",
                note="provided via --commands-file",
            )
            for command in explicit_commands
        ]
    else:
        runnable = flatten_runnable_commands(inventory)
    if args.max_commands and args.max_commands > 0:
        runnable = runnable[: args.max_commands]

    session = requests.Session()
    session.headers.update(browser_headers(args.origin))
    start = start_session(session, args.base_url, invite_code, args.requested_duration_seconds)
    session_id = start["session_id"]
    webrtc_url = start["webrtc_url"]

    manifest: Dict[str, Any] = {
        "base_url": args.base_url,
        "origin": args.origin,
        "invite_code_redacted": True,
        "invite_code_file": args.invite_code_file,
        "start": start,
        "webrtc_url": webrtc_url,
        "catalog_root": args.catalog_root,
        "include_source": list(args.include_source),
        "exclude_source": list(args.exclude_source),
        "commands_file": args.commands_file,
        "inventory_file_count": len(inventory),
        "commands_requested": runnable,
        "commands_sent_count": 0,
    }

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--autoplay-policy=no-user-gesture-required"],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(artifact_dir),
            record_video_size={"width": 1280, "height": 720},
        )
        page = context.new_page()
        page.goto(webrtc_url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(args.video_settle_seconds)
        page.add_script_tag(content=client_js)
        page.evaluate(
            """() => {
                window.__embodyResponses = [];
                window.__embodyClient = null;
            }"""
        )
        page.evaluate(
            """async () => {
                const client = await window.EmbodyDataChannelClient.waitForPixelStreaming();
                await client.waitForPlayableVideo();
                window.__embodyClient = client;
                if (typeof client.addResponseListener === "function") {
                  client.addResponseListener((...args) => window.__embodyResponses.push(args));
                }
            }"""
        )

        manifest["state_before"] = page.evaluate("() => window.__embodyClient.getState()")
        page.screenshot(path=str(artifact_dir / "before.png"))

        sent: List[Dict[str, Any]] = []
        for index, command_entry in enumerate(runnable, start=1):
            sent_entry = dict(command_entry)
            sent_entry["send_result"] = page.evaluate(
                "(command) => window.__embodyClient.sendCommand(command)",
                command_entry["command"],
            )
            sent.append(sent_entry)
            page.screenshot(path=str(artifact_dir / f"after_{index:02d}.png"))
            time.sleep(args.command_delay_seconds)

        manifest["sent"] = sent
        manifest["commands_sent_count"] = len(sent)
        manifest["state_after"] = page.evaluate(
            """() => ({
                client: window.__embodyClient.getState(),
                response_count: window.__embodyResponses.length,
                responses: window.__embodyResponses,
            })"""
        )

        video_path = Path(page.video.path())
        context.close()
        browser.close()
        final_video = artifact_dir / "proof.webm"
        video_path.rename(final_video)
        manifest["video_file"] = str(final_video)

    end = end_session(session, args.base_url, session_id)
    manifest["end_status"] = end.status_code
    manifest["end_text"] = end.text

    (artifact_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (artifact_dir / "commands.json").write_text(json.dumps(runnable, indent=2))
    write_analysis_stub(artifact_dir, manifest)
    return manifest


def main() -> None:
    args = parse_args()
    catalog_root = Path(args.catalog_root)
    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    inventory = build_inventory(catalog_root)
    inventory = apply_source_filters(inventory, args.include_source, args.exclude_source)
    inventory_path = artifact_dir / "inventory.json"
    inventory_path.write_text(json.dumps(inventory, indent=2))

    if args.mode == "inventory":
        print(json.dumps({"inventory_file": str(inventory_path), "files": len(inventory)}, indent=2))
        return

    manifest = run_suite(args, inventory)
    print(
        json.dumps(
            {
                "artifact_dir": str(artifact_dir),
                "inventory_file": str(inventory_path),
                "webrtc_url": manifest["webrtc_url"],
                "commands_sent_count": manifest["commands_sent_count"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
