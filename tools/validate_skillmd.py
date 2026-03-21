#!/usr/bin/env python3
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = {
    "Session Lifecycle": [r"^#+\s+.*session lifecycle", r"^#+\s+.*deterministic flow"],
    "Command Protocol": [r"^#+\s+.*command protocol", r"^#+\s+.*command contract"],
    "Bootstrap": [r"^#+\s+.*bootstrap"],
}

SECRET_PATTERNS = [
    ("OpenAI key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("JWT token", re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9._-]{20,}\.[A-Za-z0-9._-]{10,}\b")),
    ("Private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Bearer token", re.compile(r"\bBearer\s+([A-Za-z0-9._-]{20,})", re.IGNORECASE)),
]

ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|token|secret|password)\b[^:=\n]{0,20}[:=]\s*['\"]?([A-Za-z0-9._/+\-=]{12,})"
)
PLACEHOLDER_RE = re.compile(r"[<>{}$]|\b(YOUR|EXAMPLE|SAMPLE|PLACEHOLDER|OTP)\b", re.IGNORECASE)


def has_required_section(headings, patterns):
    return any(re.search(pattern, line, flags=re.IGNORECASE) for pattern in patterns for line in headings)


def main() -> int:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("SKILL.md")
    if not target.exists():
        print(f"ERROR: file not found: {target}")
        return 1

    text = target.read_text(encoding="utf-8")
    lines = text.splitlines()
    headings = [line.strip() for line in lines if line.lstrip().startswith("#")]
    errors = []

    if not lines or lines[0].strip() != "---":
        errors.append("Missing YAML frontmatter start: first line must be `---`.")

    for section, patterns in REQUIRED_SECTIONS.items():
        if not has_required_section(headings, patterns):
            errors.append(f"Missing required section: {section}.")

    for lineno, line in enumerate(lines, start=1):
        for label, pattern in SECRET_PATTERNS:
            match = pattern.search(line)
            if match and not PLACEHOLDER_RE.search(line):
                snippet = match.group(0)
                errors.append(f"Possible hardcoded secret ({label}) at line {lineno}: {snippet}")
        for match in ASSIGNMENT_RE.finditer(line):
            candidate = match.group(2)
            if PLACEHOLDER_RE.search(line):
                continue
            if candidate.isupper() and "_" in candidate:
                continue
            errors.append(f"Possible hardcoded secret assignment at line {lineno}: {match.group(0)}")

    if errors:
        print(f"{target} validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"{target} is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
