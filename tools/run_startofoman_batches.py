#!/usr/bin/env python3
import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one or more named StartOfOman command batches through the DataChannel suite runner."
    )
    parser.add_argument("--suite-script", required=True, help="Path to startofoman_command_suite.py")
    parser.add_argument("--batches-file", required=True, help="Path to startofoman-batches.json")
    parser.add_argument("--catalog-root", required=True)
    parser.add_argument("--client-js", required=True)
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--base-url", default="https://api.embody.zone")
    parser.add_argument("--origin", default="http://app.embody.zone")
    parser.add_argument("--invite-code")
    parser.add_argument("--invite-code-file")
    parser.add_argument("--requested-duration-seconds", type=int, default=1200)
    parser.add_argument("--command-delay-seconds", type=float, default=3.0)
    parser.add_argument("--video-settle-seconds", type=float, default=5.0)
    parser.add_argument("--max-commands", type=int, default=0)
    parser.add_argument("--mode", choices=("inventory", "run"), default="inventory")
    parser.add_argument("--batch-id", action="append", default=[], help="Only run selected batch ids. Repeatable.")
    return parser.parse_args()


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_batches(path: Path) -> List[Dict[str, Any]]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, list):
        raise SystemExit("batches file must contain a JSON array")
    return payload


def select_batches(batches: List[Dict[str, Any]], requested_ids: List[str]) -> List[Dict[str, Any]]:
    if not requested_ids:
        return batches
    requested = set(requested_ids)
    selected = [batch for batch in batches if batch.get("batch_id") in requested]
    missing = requested.difference({batch.get("batch_id") for batch in selected})
    if missing:
        raise SystemExit(f"unknown batch ids: {sorted(missing)}")
    return selected


def run_batch(args: argparse.Namespace, batch: Dict[str, Any], artifact_root: Path) -> Dict[str, Any]:
    batch_id = batch["batch_id"]
    artifact_dir = artifact_root / f"{batch_id}-{utc_stamp()}"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "python3",
        str(Path(args.suite_script)),
        "--mode",
        args.mode,
        "--catalog-root",
        args.catalog_root,
        "--artifact-dir",
        str(artifact_dir),
        "--client-js",
        args.client_js,
        "--base-url",
        args.base_url,
        "--origin",
        args.origin,
        "--requested-duration-seconds",
        str(args.requested_duration_seconds),
        "--command-delay-seconds",
        str(args.command_delay_seconds),
        "--video-settle-seconds",
        str(args.video_settle_seconds),
    ]

    if args.max_commands > 0:
        cmd.extend(["--max-commands", str(args.max_commands)])

    for token in batch.get("include_source", []):
        cmd.extend(["--include-source", token])

    if args.mode == "run":
        if args.invite_code:
            cmd.extend(["--invite-code", args.invite_code])
        elif args.invite_code_file:
            cmd.extend(["--invite-code-file", args.invite_code_file])
        else:
            raise SystemExit("--invite-code or --invite-code-file is required in run mode")

    completed = subprocess.run(cmd, capture_output=True, text=True)
    result = {
        "batch_id": batch_id,
        "artifact_dir": str(artifact_dir),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "observability": batch.get("observability"),
        "notes": batch.get("notes", []),
    }
    (artifact_dir / "runner-result.json").write_text(json.dumps(result, indent=2))
    return result


def main() -> None:
    args = parse_args()
    batches = select_batches(load_batches(Path(args.batches_file)), args.batch_id)
    artifact_root = Path(args.artifact_root)
    artifact_root.mkdir(parents=True, exist_ok=True)

    summary = {
        "mode": args.mode,
        "artifact_root": str(artifact_root),
        "batches_requested": [batch["batch_id"] for batch in batches],
        "results": [],
    }

    for batch in batches:
        summary["results"].append(run_batch(args, batch, artifact_root))

    summary_path = artifact_root / f"batch-summary-{utc_stamp()}.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(json.dumps({"summary_file": str(summary_path), "batch_count": len(summary["results"])}, indent=2))


if __name__ == "__main__":
    main()
