---
name: embody-skill
description: Simple client skill for getting a time-limited Embody avatar session (up to 24h), auto-allocating the nearest available orchestrator, and using the current public session API safely.
---

# Embody Skill

This skill has one goal: let an agent get an avatar session fast, use the public session API correctly, and release it cleanly.

Base URL:
- `https://api.embody.zone`

Operator-only domain:
- Do not use this from client/consumer flows. It is reserved for private operator actions and is not part of the session UX.

## 1) What You Get
- A session bound to your calling IP.
- Duration: up to 24 hours (`1 day` or less).
- Orchestrator selection is automatic (nearest available, first-come-first-served).
- You do not provide an orchestrator id.
- Control is API-routed: you do not send TCP directly to orchestrator or edge IPs.
- Important: public session allocation is verified. Public TCP relay is only usable when your assigned edge exposes a relay path. If the API returns `503 Edge TCP relay not configured for this orchestrator`, the problem is infrastructure state, not your command syntax.

## 2) Hard Rules
- Use only the session API. Do not call orchestrators directly.
- Start from `https://api.embody.zone` only.
- Treat `webrtc_url` as the scene entrypoint and `control_url` as the command entrypoint.
- Never print or store secrets (tokens, auth headers, provider keys).
- Do not print or reuse `edge.matchmaker_host`, `turn_external_ip`, or other edge diagnostics outside local debugging.
- Use stable-build commands only.
- Keep command pacing sane (one command at a time for validation-critical actions).

## 3) Session Flow (Deterministic)

### Step A: Start
`POST https://api.embody.zone/api/sessions/start`

Optional request body:
- `{}` is valid.
- `{ "requested_duration_seconds": <seconds> }`
- Range: `60` to `86400` (server also enforces max lease policy).
- `wallet_address` is not currently required for the public flow.

Expected response fields:
- `session_id`
- `token`
- `expires_at`
- `webrtc_url`
- `control_url`
- `edge` (diagnostic assignment data only; not for direct client TCP use)

Current behavior to expect:
- Repeated `start` calls from the same public IP can return the same active session instead of creating a second parallel session.

### Step B: Inspect assignment
`GET https://api.embody.zone/api/sessions/me`

Check:
- session exists and `ended_at` is `null`
- `webrtc_url` is present
- `control_url` is present
- `edge.tcp_relay_url`

Interpretation:
- If `edge.tcp_relay_url` is `null`, do not keep retrying avatar commands. Session lifecycle is available, but public command relay is not wired for that assigned orchestrator yet.
- If `webrtc_url` times out, treat it as an edge health issue, not as a command-format issue.

### Step C: Control (only when relay is available)
`POST https://api.embody.zone/api/sessions/tcp` with `Authorization: Bearer <token>`

Important:
- Send TCP commands to `control_url` (or `https://api.embody.zone/api/sessions/tcp`) only.
- Do not send TCP commands directly to any orchestrator or edge IP.
- Routing to your assigned edge/orchestrator is handled server-side.
- If the response is `503` with `Edge TCP relay not configured for this orchestrator`, stop and escalate. The relay is not ready on that assignment.

### Step D: Keep alive (optional for long runs)
`POST https://api.embody.zone/api/sessions/heartbeat`

### Step E: End cleanly
`POST https://api.embody.zone/api/sessions/end`

## 4) Quickstart Commands (Minimal, High Signal)
Use these first only after Step B confirms relay availability. They are low-risk commands, not proof that the public relay is always configured.

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
- Never send real provider keys in logs or docs.

## 6) Full Command Reference
For complete stable-build command coverage, use:
- `TCP_CONTROLLER_STABLE_REFERENCE.md`

Use this only after the quickstart commands pass.

## 7) Curl Template
```bash
BASE="https://api.embody.zone"

START="$(curl -s -X POST "${BASE}/api/sessions/start" \
  -H "Content-Type: application/json" \
  -d '{}')"

TOKEN="$(echo "${START}" | jq -r '.token')"
WEBRTC_URL="$(echo "${START}" | jq -r '.webrtc_url')"
CONTROL_URL="$(echo "${START}" | jq -r '.control_url')"
TCP_RELAY_URL="$(echo "${START}" | jq -r '.edge.tcp_relay_url // empty')"

# Local debug only. Do not paste assigned edge diagnostics into public logs.
echo "Assigned WebRTC URL: ${WEBRTC_URL}"

curl -s "${BASE}/api/sessions/me" \
  -H "Authorization: Bearer ${TOKEN}"

if [ -n "${TCP_RELAY_URL}" ]; then
  curl -s -X POST "${CONTROL_URL}" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"command":"EMOTE_Wave"}'

  curl -s -X POST "${CONTROL_URL}" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"command":"CAMSHOT.Medium"}'
else
  echo "Public TCP relay is not configured for this assignment yet."
fi

curl -s -X POST "${BASE}/api/sessions/heartbeat" \
  -H "Authorization: Bearer ${TOKEN}"

curl -s -X POST "${BASE}/api/sessions/end" \
  -H "Authorization: Bearer ${TOKEN}"
```

## 8) Failure Handling
- If `start` returns an already-active session from your IP: reuse that session instead of trying to force a second one.
- If `start` fails: retry once, then inspect API health/logs.
- If `tcp` returns `503 Edge TCP relay not configured for this orchestrator`: session allocation worked, but the public relay is not available on that assignment.
- If `webrtc_url` does not load: treat it as an edge availability problem.
- If commands are ignored and relay is present: send one known-safe command (`EMOTE_Wave`) and re-check `/api/sessions/me`.
- If session expires: create a new session; do not reuse old token.
- If output quality is uncertain: validate with non-TTS visible commands before any complex sequence.
