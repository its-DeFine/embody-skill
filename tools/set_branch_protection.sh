#!/usr/bin/env bash
set -euo pipefail

BRANCH="${1:-main}"
REQUIRED_CHECK="${2:-CI}"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required. Install from https://cli.github.com/" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "gh is not authenticated. Run: gh auth login" >&2
  exit 1
fi

REPO_SLUG="${GITHUB_REPOSITORY:-}"
if [[ -z "$REPO_SLUG" ]]; then
  ORIGIN_URL="$(git config --get remote.origin.url || true)"
  if [[ -z "$ORIGIN_URL" ]]; then
    echo "Unable to detect repository slug. Set GITHUB_REPOSITORY=owner/repo." >&2
    exit 1
  fi

  REPO_SLUG="$(printf '%s' "$ORIGIN_URL" | sed -E 's#^git@github.com:##; s#^https://github.com/##; s#\.git$##')"
fi

if [[ ! "$REPO_SLUG" =~ ^[^/]+/[^/]+$ ]]; then
  echo "Invalid repository slug: $REPO_SLUG (expected owner/repo)" >&2
  exit 1
fi

PAYLOAD_FILE="$(mktemp)"
cat > "$PAYLOAD_FILE" <<JSON
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["${REQUIRED_CHECK}"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null
}
JSON

trap 'rm -f "$PAYLOAD_FILE"' EXIT

gh api \
  --method PUT \
  --header "Accept: application/vnd.github+json" \
  "repos/${REPO_SLUG}/branches/${BRANCH}/protection" \
  --input "$PAYLOAD_FILE" >/dev/null

echo "Branch protection updated for ${REPO_SLUG}:${BRANCH}. Required check: ${REQUIRED_CHECK}"
