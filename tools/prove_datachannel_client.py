#!/usr/bin/env python3
import argparse
import hashlib
import json
import time
import uuid
from pathlib import Path

import requests


def browser_headers(origin: str) -> dict:
    return {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": origin,
        "Referer": f"{origin}/",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prove the Embody DataChannel client over a leased public session.")
    parser.add_argument("--base-url", default="https://api.embody.zone")
    parser.add_argument("--origin", default="http://app.embody.zone")
    parser.add_argument("--bootstrap-manifest-url", default=None)
    parser.add_argument("--token", required=True, help="OTP token (hmac_hex.expires_at_unix) from /api/tokens/mint")
    parser.add_argument("--installation-id-file", required=True)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--client-js", required=True)
    parser.add_argument("--command", action="append", required=True, help="Command to send via DataChannel. Repeat for multiple commands.")
    parser.add_argument("--requested-duration-seconds", type=int, default=600)
    parser.add_argument("--command-delay-seconds", type=float, default=3.0)
    parser.add_argument("--video-settle-seconds", type=float, default=5.0)
    return parser.parse_args()


def load_or_create_installation_identity(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    installation_id = uuid.uuid4().hex
    fingerprint = hashlib.sha256(installation_id.encode("utf-8")).hexdigest()
    payload = {
        "installation_id": installation_id,
        "installation_public_fingerprint": fingerprint,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    return payload


def start_session(
    session: requests.Session,
    *,
    base_url: str,
    requested_duration_seconds: int,
    token: str,
    installation_identity: dict,
) -> dict:
    payload = {
        "installation_id": installation_identity["installation_id"],
        "token": token,
        "requested_duration_seconds": requested_duration_seconds,
    }
    response = session.post(
        f"{base_url}/api/sessions/start",
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def end_session(session: requests.Session, base_url: str, session_id: str) -> requests.Response:
    return session.post(
        f"{base_url}/api/sessions/end",
        json={"session_id": session_id},
        timeout=30,
    )


def main() -> None:
    args = parse_args()
    from playwright.sync_api import sync_playwright

    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    client_js = Path(args.client_js).read_text()

    session = requests.Session()
    base_url = args.base_url.rstrip("/")
    origin = args.origin
    manifest = {
        "installation_id_file": args.installation_id_file,
        "base_url": base_url,
        "origin": origin,
        "bootstrap_manifest_url": args.bootstrap_manifest_url,
        "artifact_dir": str(artifact_dir),
        "commands": list(args.command),
    }

    bootstrap_manifest = None
    if args.bootstrap_manifest_url:
        bootstrap_manifest = requests.get(args.bootstrap_manifest_url, timeout=30).json()
        (artifact_dir / "bootstrap-manifest.json").write_text(json.dumps(bootstrap_manifest, indent=2))
        base_url = str(bootstrap_manifest.get("base_url") or base_url).rstrip("/")
        manifest["base_url"] = base_url
        manifest["bootstrap_manifest"] = bootstrap_manifest
    session.headers.update(browser_headers(origin))

    installation_identity = load_or_create_installation_identity(Path(args.installation_id_file))
    manifest["installation_identity"] = installation_identity

    start = start_session(
        session,
        base_url=base_url,
        requested_duration_seconds=args.requested_duration_seconds,
        token=args.token,
        installation_identity=installation_identity,
    )
    manifest["start"] = start
    session_id = start["session_id"]
    webrtc_url = start["webrtc_url"]

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
                client.addResponseListener((...args) => window.__embodyResponses.push(args));
            }"""
        )

        manifest["state_before"] = page.evaluate("() => window.__embodyClient.getState()")
        page.screenshot(path=str(artifact_dir / "before.png"))

        sent = []
        for index, command in enumerate(args.command):
            sent.append(page.evaluate("(command) => window.__embodyClient.sendCommand(command)", command))
            time.sleep(args.command_delay_seconds)
            page.screenshot(path=str(artifact_dir / f"after_{index+1:02d}.png"))
        manifest["sent"] = sent
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

    end = end_session(session, base_url, session_id)
    manifest["end_status"] = end.status_code
    manifest["end_text"] = end.text

    (artifact_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps({"artifact_dir": str(artifact_dir), "webrtc_url": webrtc_url}, indent=2))


if __name__ == "__main__":
    main()
