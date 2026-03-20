#!/usr/bin/env python3
from pathlib import Path
import re
import sys

SKILL_MD = Path(__file__).resolve().parents[1] / "SKILL.md"
TEXT = SKILL_MD.read_text(encoding="utf-8")
LINES = TEXT.splitlines()
LOWER = TEXT.lower()
errors = []

if not LINES or LINES[0].strip() != "---":
    errors.append("Missing YAML frontmatter: first line must be ---")

SECTION_RULES = {
    "Bootstrap": [r"^##+\s+.*bootstrap", r"hosted bootstrap contract", r"/api/bootstrap/skillmd"],
    "Command Protocol": [r"^##+\s+.*command protocol", r"^##+\s+.*command contract", r"sendcommand", r"datachannel"],
    "Session Lifecycle": [r"^##+\s+.*session lifecycle", r"^##+\s+.*deterministic flow", r"/api/sessions/start", r"/api/sessions/end"],
}
for name, patterns in SECTION_RULES.items():
    if not any(re.search(p, TEXT, re.I | re.M) for p in patterns):
        errors.append(f"Missing required section: {name}")

placeholder = re.compile(r"(<[^>\n]+>|\$\{[A-Z0-9_]+\}|[A-Z][A-Z0-9_]*=\"<[^\"\n]+>\")")
filtered = placeholder.sub("", TEXT)
secret_patterns = [
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"\b(?:sk|rk|pk)_(?:live|test)?[A-Za-z0-9]{16,}\b",
    r"\bgh[pousr]_[A-Za-z0-9]{20,}\b",
    r"\bAIza[0-9A-Za-z\-_]{20,}\b",
    r"Bearer\s+[A-Za-z0-9._-]{20,}",
    r"\b[A-F0-9]{32,}\.[0-9]{10,}\b",
]
for pattern in secret_patterns:
    if re.search(pattern, filtered):
        errors.append(f"Potential hardcoded secret matched pattern: {pattern}")

for i, line in enumerate(LINES, 1):
    if "api_key" in line.lower() and "<" not in line and "YOUR_" not in line:
        if re.search(r"[:=]\s*[\"']?[A-Za-z0-9._-]{12,}", line):
            errors.append(f"Potential hardcoded API key on line {i}")

if errors:
    print("\n".join(errors), file=sys.stderr)
    sys.exit(1)

print("SKILL.md is valid")
