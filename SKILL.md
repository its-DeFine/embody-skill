---
name: embody-skill
description: Simple client skill for getting a time-limited Embody avatar session (up to 24h), auto-allocating the nearest available orchestrator, and controlling the avatar via token-authenticated TCP commands.
---

# Embody Skill

This skill has one goal: let an agent get an avatar session fast, control it reliably, and release it cleanly.

## 1) What You Get
- A session bound to your calling IP.
- Duration: up to 24 hours (`1 day` or less).
- Orchestrator selection is automatic (nearest available, first-come-first-served).
- You do not provide an orchestrator id.

## 2) Hard Rules
- Use only the session API. Do not call orchestrators directly.
- Never print or store secrets (tokens, auth headers, provider keys).
- Use stable-build commands only.
- Keep command pacing sane (one command at a time for validation-critical actions).

## 3) Session Flow (Deterministic)

### Step A: Start
`POST /api/sessions/start`

Expected response fields:
- `session_id`
- `token`
- `expires_at`
- `webrtc_url`
- `control_url`

### Step B: Control
`POST /api/sessions/tcp` with `Authorization: Bearer <token>`

### Step C: Check state
`GET /api/sessions/me`

### Step D: Keep alive (optional for long runs)
`POST /api/sessions/heartbeat`

### Step E: End cleanly
`POST /api/sessions/end`

## 4) Quickstart Commands (Minimal, High Signal)
Use these first to verify control end-to-end without TTS risk.

- `EMOTE_Wave`
- `CAMSHOT.Medium`
- `PRS.Fem` or `PRS.Masc`

If these work, your session and control path are healthy.

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
BASE="${API_BASE}"

START="$(curl -s -X POST "${BASE}/api/sessions/start" \
  -H "Content-Type: application/json" \
  -d '{}')"

TOKEN="$(echo "${START}" | jq -r '.token')"

curl -s -X POST "${BASE}/api/sessions/tcp" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"command":"EMOTE_Wave"}'

curl -s -X POST "${BASE}/api/sessions/tcp" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"command":"CAMSHOT.Medium"}'

curl -s "${BASE}/api/sessions/me" \
  -H "Authorization: Bearer ${TOKEN}"

curl -s -X POST "${BASE}/api/sessions/end" \
  -H "Authorization: Bearer ${TOKEN}"
```

## 8) Failure Handling
- If `start` fails: retry once, then inspect API health/logs.
- If commands are ignored: send one known-safe command (`EMOTE_Wave`) and re-check `/api/sessions/me`.
- If session expires: create a new session; do not reuse old token.
- If output quality is uncertain: validate with non-TTS visible commands before any complex sequence.
