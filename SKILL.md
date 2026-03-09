---
name: embody-skill
description: Simple client skill for getting a time-limited Embody avatar session (up to 24h), auto-allocating the nearest available orchestrator, and using the current public session API safely.
---

# Embody Skill

This skill has one goal: let an agent get an avatar session fast, use the public session API correctly, and release it cleanly.

Current access model:
- Initial consumer access is expected to be gated by an admin-issued one-time session code.
- After `start`, the session remains bound to your calling IP and `session_id`.
- Control stays on the public session API; do not switch to direct orchestrator access.

Base URL:
- `https://api.embody.zone`

Operator-only domain:
- `https://ops.embody.zone`
- Do not use this from client/consumer flows. It is reserved for private operator actions and is not part of the session UX.

## 1) What You Get
- A session bound to your calling IP.
- Duration: up to 24 hours (`1 day` or less).
- Orchestrator selection is automatic.
- Current rollout is canary-only: the public allocator is intentionally constrained to the single working public path.
- Initial user access may require a one-time session code from the operator/admin.
- You do not provide an orchestrator id.
- Control is API-routed: you do not send TCP directly to orchestrator or edge IPs.
- The consumer flow is tokenless: your session is bound to your calling IP and `session_id`.
- Important: use the returned `webrtc_url` exactly as provided, even if it is `http://...` with query parameters.

## 2) Hard Rules
- Use only the session API. Do not call orchestrators directly.
- Start from `https://api.embody.zone` only.
- Treat `webrtc_url` as the scene entrypoint and `control_url` as the command entrypoint.
- Never print or store secrets (provider keys, internal operator credentials).
- Do not print or reuse `edge.matchmaker_host`, `turn_external_ip`, or other edge diagnostics outside local debugging.
- Use stable-build commands only.
- Keep command pacing sane (one command at a time for validation-critical actions).

## 3) Session Flow (Deterministic)

### Step A: Start
`POST https://api.embody.zone/api/sessions/start`

Optional request body:
- `{}` is valid.
- `{ "requested_duration_seconds": <seconds> }`
- `{ "invite_code": "<ONE_TIME_CODE>" }`
- `{ "requested_duration_seconds": <seconds>, "invite_code": "<ONE_TIME_CODE>" }`
- Range: `60` to `86400` (server also enforces max lease policy).
- `wallet_address` is not required for the client session flow.
- When the control plane enables invite gating, `invite_code` is required for the initial session on a new client IP.

Expected response fields:
- `session_id`
- `expires_at`
- `lease_seconds`
- `webrtc_url`
- `control_url`
- `edge` (diagnostic assignment data only; not for direct client TCP use)

Current behavior to expect:
- Repeated `start` calls from the same public IP can return the same active session instead of creating a second parallel session.
- Once your IP already has an active or pinned session, the control plane can reuse it without consuming another one-time code.
- A returned `webrtc_url` can still be wrong if the control plane points at a signaling-only host instead of a real UI/gateway URL. That is an edge/public-base-url configuration issue, not an invite-code issue.
- The public front door is currently behind bot filtering. Default `curl` / `urllib` fingerprints can trigger Cloudflare `403` with `error code: 1010`. For public API use, send a normal browser-like `User-Agent` and standard browser headers (`Accept`, `Origin`, `Referer`).

### Step B: Inspect assignment
`GET https://api.embody.zone/api/sessions/me`

Check:
- session exists and `ended_at` is `null`
- `webrtc_url` is present
- `control_url` is present

Interpretation:
- The public canary path currently uses a direct runner-backed command path, so `edge.tcp_relay_url` may be `null` while control still works.
- If `webrtc_url` times out, treat it as an edge health issue, not as a command-format issue.

### Step C: Control
`POST https://api.embody.zone/api/sessions/tcp`

Important:
- Send TCP commands to `control_url` (or `https://api.embody.zone/api/sessions/tcp`) only.
- Do not send TCP commands directly to any orchestrator or edge IP.
- Routing to your assigned edge/orchestrator is handled server-side.
- The public flow is IP-bound. Use `session_id` in the JSON body for explicitness; no bearer token is required.
- The current canary path accepts safe commands without a consumer token.

### Step D: Keep alive (optional for long runs)
`POST https://api.embody.zone/api/sessions/heartbeat`

### Step E: End cleanly
`POST https://api.embody.zone/api/sessions/end`

## 4) Quickstart Commands (Minimal, High Signal)
Use these first after Step B confirms you have an active session. They are low-risk commands for proving control on the current public canary.

- `EMOTE_Wave`
- `CAMSHOT.Medium`
- `PRS.Fem` or `PRS.Masc`

If these work, your session and control path are healthy for that assignment.

## 5) Control Patterns

### A) Character and style
- Preset: `PRS.Fem`, `PRS.Masc`, `PRS.Fem1`, `PRS.Masc1`
- Name/save/load:
  - `NAME.<AgentName>`
  - `BTN.Save`
  - `Load.<AgentName>`

### B) Look customization
- Outfit: `OF_Head_Torso_Legs_Feet_Back`
- Hair: `HS.Default`, `HS.Buzz`, `HS.Crop`
- Skin: `SKC.<float>`
- Eyes: `EC.<float>`, `ES.<float>`

### C) Expression and motion
- Emotes: `EMOTE_*`
- Conversation animations: `CONVO_*`
- Camera presets: `CAMSHOT.*`
- Position/rotation: `LOC_X_Y_Z`, `ROT_X_Y_Z`, `CAMLOC_X_Y_Z`

### D) Voice (optional)
- Prefer non-TTS for smoke tests.
- Use TTS only when needed.
- For Kokoro, validate the command path with a visible camera command first, then use the verified format `TTS_Kokoro_Bella_Happy_0.7_<text>`.
- For normal Kokoro use, send one line at a time. Fixed `5s` spacing is only a stress-test pattern; if batching is required, use timing-aware queueing instead of blind delays.
- When runtime logs are available, interpret them carefully: `Received audio buffer with N samples` means synth success, `Kokoro synthesis cancelled after inference` means the line truly failed, and lip-sync or audio buffer overflow can make a successful line feel skipped.
- Never send real provider keys in logs or docs.

## 6) Full Command Reference
For complete stable-build command coverage, use:
- `TCP_CONTROLLER_STABLE_REFERENCE.md`

Use this only after the quickstart commands pass.

## 7) Curl Template
```bash
BASE="https://api.embody.zone"
INVITE_CODE="<ONE_TIME_CODE>"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"

START="$(curl -s -X POST "${BASE}/api/sessions/start" \
  -A "${UA}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json,text/plain,*/*" \
  -H "Origin: https://app.embody.zone" \
  -H "Referer: https://app.embody.zone/" \
  -d "{\"invite_code\":\"${INVITE_CODE}\"}")"

SESSION_ID="$(echo "${START}" | jq -r '.session_id')"
WEBRTC_URL="$(echo "${START}" | jq -r '.webrtc_url')"
CONTROL_URL="$(echo "${START}" | jq -r '.control_url')"
TCP_RELAY_URL="$(echo "${START}" | jq -r '.edge.tcp_relay_url // empty')"

# Local debug only. Do not paste assigned edge diagnostics into public logs.
echo "Assigned WebRTC URL: ${WEBRTC_URL}"

curl -s \
  -A "${UA}" \
  -H "Accept: application/json,text/plain,*/*" \
  -H "Origin: https://app.embody.zone" \
  -H "Referer: https://app.embody.zone/" \
  "${BASE}/api/sessions/me"

curl -s -X POST "${CONTROL_URL}" \
  -A "${UA}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json,text/plain,*/*" \
  -H "Origin: https://app.embody.zone" \
  -H "Referer: https://app.embody.zone/" \
  -d "{\"session_id\":\"${SESSION_ID}\",\"command\":\"EMOTE_Wave\",\"timeout_seconds\":15}"

curl -s -X POST "${CONTROL_URL}" \
  -A "${UA}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json,text/plain,*/*" \
  -H "Origin: https://app.embody.zone" \
  -H "Referer: https://app.embody.zone/" \
  -d "{\"session_id\":\"${SESSION_ID}\",\"command\":\"CAMSHOT.Medium\",\"timeout_seconds\":15}"

curl -s -X POST "${BASE}/api/sessions/heartbeat" \
  -A "${UA}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json,text/plain,*/*" \
  -H "Origin: https://app.embody.zone" \
  -H "Referer: https://app.embody.zone/" \
  -d "{\"session_id\":\"${SESSION_ID}\"}"

curl -s -X POST "${BASE}/api/sessions/end" \
  -A "${UA}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json,text/plain,*/*" \
  -H "Origin: https://app.embody.zone" \
  -H "Referer: https://app.embody.zone/" \
  -d "{\"session_id\":\"${SESSION_ID}\"}"
```

## 8) Failure Handling
- If `start` returns an already-active session from your IP: reuse that session instead of trying to force a second one.
- If `start` returns `401` or `404` around invite handling: check that you were given the correct one-time session code and that it has not expired.
- If `start` returns `409` around invite handling: treat the code as already redeemed/in-progress and ask the operator/admin for a fresh one.
- If `start` returns Cloudflare `403` with `error code: 1010`: retry with browser-like headers before treating it as an invite or backend failure.
- If `start` fails: retry once, then inspect API health/logs.
- If `tcp` returns `503` or `502`: treat it as infrastructure/runtime drift and escalate. It is not a consumer-token problem.
- If `webrtc_url` does not load: treat it as an edge availability problem.
- If `webrtc_url` opens a page that says `Pixel Streaming signaling is running` and `does not serve the Pixel Streaming UI bundle`: treat it as a control-plane edge/public-base-url misconfiguration. Your session may still be valid; verify control with `/api/sessions/tcp` and escalate the returned `webrtc_url`.
- If commands are ignored: send one known-safe command (`EMOTE_Wave`) and re-check `/api/sessions/me`.
- If Kokoro behavior is uncertain: prove the path with `CAMSHOT.Medium` or `CAMSHOT.Close` before debugging TTS format or pacing.
- If commands stopped working after a game-only recreate: the script-runner may need recreation too, because it shares the game network namespace and can drift after partial runtime resets.
- If session expires: create a new session; do not reuse an old `session_id`.
- If output quality is uncertain: validate with non-TTS visible commands before any complex sequence.
