---
name: embody-skill
description: Bootstrap a live Embody avatar session, fetch the current hosted contract, and control the avatar through the Pixel Streaming DataChannel.
---

# Embody Skill

This skill is a bootstrap, not the full protocol.

Use it to:
- fetch the current public contract
- start a guest session
- attach to the returned Pixel Streaming URL
- send real-time avatar commands over the live WebRTC DataChannel
- end the session cleanly

## 1) Current Model

Current alpha access model:
- no invite code
- no login
- guest session on first use
- one installation identity per runtime
- one active session per installation identity
- hard public capacity bound to healthy orchestrators

Current public base URL:
- `https://api.embody.zone`

Current hosted bootstrap contract:
- `https://api.embody.zone/api/bootstrap/skillmd`

Operator-only domain:
- do not use this from client/consumer flows

## 2) Hard Rules

- Start from the hosted bootstrap contract, not from stale copied examples.
- Treat the returned `webrtc_url` as the session entrypoint.
- Real-time control should use the Pixel Streaming DataChannel.
- Primary command transport is `emitCommand({ command: "..." })`.
- Do not use `/api/sessions/tcp` as the normal embodiment path.
- Keep `/api/sessions/tcp` only as fallback/admin/debug.
- Never print or store secrets or internal diagnostics.
- Do not send commands directly to orchestrator or edge TCP ports.

## 3) Deterministic Flow

### Step A: Fetch the current contract

`GET https://api.embody.zone/api/bootstrap/skillmd`

Read at minimum:
- `base_url`
- `version`
- `transport.primary`
- `webrtc.command_method`
- `limits.max_concurrent_sessions`

Expected alpha transport:
- `transport.primary = pixelstreaming_datachannel_emitcommand`
- `webrtc.command_method = emitCommand`

### Step B: Create or load installation identity

Persist one local installation identity per runtime.

Minimum fields:
- `installation_id`
- `installation_public_fingerprint`

Recommended generation:
- `installation_id = uuid4().hex`
- `installation_public_fingerprint = sha256(installation_id)`

Do not rotate this every call. Reuse it so the control plane can enforce sane guest limits.

### Step C: Start the session

`POST https://api.embody.zone/api/sessions/start`

Recommended body:

```json
{
  "requested_duration_seconds": 600,
  "installation_id": "<INSTALLATION_ID>",
  "installation_public_fingerprint": "<SHA256_FINGERPRINT>",
  "client_name": "your-client-name",
  "client_version": "0.1.0",
  "bootstrap_manifest_version": "v1"
}
```

Important response fields:
- `session_id`
- `expires_at`
- `lease_seconds`
- `mode`
- `webrtc_url`
- `command_mode`
- `command_method`
- `capacity_hint`

Expected alpha response:
- `mode = guest`
- `command_mode = datachannel`
- `command_method = emitCommand`

### Step D: Attach to the live session

Open the returned `webrtc_url` exactly as provided.

Do not rewrite:
- scheme
- query string
- websocket target

### Step E: Send commands over DataChannel

Primary real-time command path:

```js
window.pixelStreaming.emitCommand({ command: "CAMSHOT.ExtremeClose" })
window.pixelStreaming.emitCommand({ command: "TTS_Kokoro_Bella_Happy_0.7_Hello from Kokoro" })
```

If you are building a wrapper client, the wrapper should expose something like:

```ts
await client.connect(webrtcUrl)
await client.sendCommand("CAMSHOT.ExtremeClose")
await client.sendCommand("TTS_Kokoro_Bella_Happy_0.7_Hello from Kokoro")
await client.disconnect()
```

But internally it should still use:
- Pixel Streaming client
- WebRTC DataChannel
- `emitCommand({ command: ... })`

### Step F: End cleanly

`POST https://api.embody.zone/api/sessions/end`

Body:

```json
{ "session_id": "<SESSION_ID>" }
```

## 4) Minimal Proof Commands

Use these first:
- `CAMSHOT.Medium`
- `CAMSHOT.ExtremeClose`
- `EMOTE_Wave`

Then validate Kokoro:
- `TTS_Kokoro_Bella_Happy_0.7_Hello from Kokoro`

Operational rule:
- for Kokoro, send one line at a time unless you have timing-aware queueing

## 5) Command Contract

Stable command families remain documented in:
- `TCP_CONTROLLER_STABLE_REFERENCE.md`

Important distinction:
- the command *strings* are still the same stable avatar commands
- the preferred transport is now DataChannel, not the public TCP relay API

## 6) HTTP Templates

### Bootstrap

```bash
curl -s https://api.embody.zone/api/bootstrap/skillmd
```

### Start

```bash
BASE="https://api.embody.zone"
INSTALLATION_ID="$(python3 - <<'PY'
import uuid
print(uuid.uuid4().hex)
PY
)"
export INSTALLATION_ID
FINGERPRINT="$(python3 - <<'PY'
import hashlib, os
installation_id = os.environ["INSTALLATION_ID"]
print(hashlib.sha256(installation_id.encode("utf-8")).hexdigest())
PY
)"

curl -s -X POST "${BASE}/api/sessions/start" \
  -H "Content-Type: application/json" \
  -d "{
    \"requested_duration_seconds\": 600,
    \"installation_id\": \"${INSTALLATION_ID}\",
    \"installation_public_fingerprint\": \"${FINGERPRINT}\",
    \"client_name\": \"skillmd-client\",
    \"client_version\": \"0.1.0\",
    \"bootstrap_manifest_version\": \"v1\"
  }"
```

### End

```bash
curl -s -X POST "https://api.embody.zone/api/sessions/end" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"${SESSION_ID}\"}"
```

## 7) Failure Handling

- If bootstrap fetch fails: treat it as control-plane outage.
- If `start` fails with capacity exhaustion: wait and retry; do not spin.
- If browser attach fails: treat it as edge/session problem, not command-format problem.
- If DataChannel commands appear ignored:
  - first verify you used `emitCommand({ command: ... })`
  - do not assume `emitConsoleCommand(...)` is valid
- If camera works but Kokoro does not:
  - treat it as TTS/runtime behavior, not transport failure
- If you have no browser/DataChannel client available:
  - `/api/sessions/tcp` may still exist as fallback/admin
  - but it is not the preferred embodiment path

## 8) Product Direction

This skill intentionally stays short and stable.

The hosted bootstrap contract is the source of truth.

Future updates should prefer:
- updating the hosted contract
- updating the client wrapper
- not constantly rewriting this skill
