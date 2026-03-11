---
name: embody-skill
description: Bootstrap a live Embody avatar session, fetch the current hosted contract, and control the avatar through the Pixel Streaming DataChannel.
---

# Embody Skill

This skill gives an agent a live embodied avatar.

Use it to:
- start a guest avatar session with no code or login
- connect to the live avatar stream
- control the avatar in real time over the WebRTC DataChannel
- speak through Kokoro TTS
- change camera, emotion, appearance, and visual style
- end the session cleanly

This file is a bootstrap and field guide.
It should tell an agent:
- what the product can do
- how to get a session
- how to send commands
- where the full current command surface lives

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

## 2) Hard Rules

- Start from the hosted bootstrap contract, not from stale copied examples.
- Treat the returned `webrtc_url` as the session entrypoint.
- Real-time control should use the Pixel Streaming DataChannel.
- Primary command transport is `emitCommand({ command: "..." })`.
- Do not use `/api/sessions/tcp` as the normal embodiment path.
- Keep `/api/sessions/tcp` only as fallback/admin/debug.
- Never print or store secrets or internal diagnostics.
- Do not send commands directly to orchestrator or edge TCP ports.

## 3) What An Agent Can Do

The stable avatar command strings are the same ones used in the older TCP flow.
What changed is the preferred transport:

- old preferred transport: server-side TCP relay
- current preferred transport: Pixel Streaming DataChannel

So the agent should think:
- same command language
- better real-time transport

Main capability groups:

### Camera And Framing

Use this to control how the avatar is framed on screen.

Examples:
- `CAMSHOT.Medium`
- `CAMSHOT.ExtremeClose`
- `CAMSHOT.WideShot`
- `CAMSHOT.HighAngle`
- `CAMSHOT.LowAngle`

### Speech And Voice

Use this to make the avatar speak.

Current proven path:
- Kokoro TTS commands over DataChannel

Example:
- `TTS_Kokoro_Bella_Happy_0.7_Hello from Kokoro`

### Emotion And Performance

Use this to make the avatar react and perform.

Examples:
- `EMOTE_Wave`
- `EMOTE_Angry`
- `EMOTE_Confused`
- `CONVO_Speaking`
- `CONVO_SadTalk`

### Appearance And Customization

Use this to change the avatar body, clothes, hair, makeup, and styling.

Examples:
- `PRS.Fem`
- `OF_NoHead_LucyBlackDress_LucyShorts1_LucyBoots1_NoBack`
- `HS.Crop`
- `HCR.2.5`
- `MKUPF_Lipstick_1.0`

### Visual Style And Post Processing

Use this to change the mood and rendering feel.

Examples:
- `BloomInt_0.2`
- `EXPOComp_1.0`
- `CHROME_Int_0.1`
- `VIG_0.2`
- `GRAIN_GrainInten_0.0`

### Environment And Worldbuilding

Use this to place the avatar in a different scene or surround it with props and lights.

Examples:
- `LIGHT_Key_0_0_200`
- `SPWN_Table01_...`

The command surface is broad enough to support use cases like:
- real-time assistant
- news presenter
- meeting participant
- character performer
- product guide

## 4) Where To Find Commands

Start with the human-readable stable reference in this repo:
- `TCP_CONTROLLER_STABLE_REFERENCE.md`

That file groups commands by category:
- load/save
- appearance
- camera
- animation
- emotes
- post-processing
- lighting and assets

Use that file as the current command catalog until a hosted command manifest is published.

## 5) Deterministic Flow

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

## 6) Minimal Proof Commands

Use these first:
- `CAMSHOT.Medium`
- `CAMSHOT.ExtremeClose`
- `EMOTE_Wave`

Then validate Kokoro:
- `TTS_Kokoro_Bella_Happy_0.7_Hello from Kokoro`

Operational rule:
- for Kokoro, send one line at a time unless you have timing-aware queueing

## 7) Minimal Client Shape

The intended shape is not “manually implement raw WebRTC.”

The intended shape is a small session client that does:

```ts
await client.connect(webrtcUrl)
await client.sendCommand("CAMSHOT.ExtremeClose")
await client.sendCommand("TTS_Kokoro_Bella_Happy_0.7_Hello from Kokoro")
await client.disconnect()
```

Internally:
- connect to the Pixel Streaming session
- wait for the DataChannel to be ready
- use `emitCommand({ command: ... })`

This makes the product usable from:
- a browser
- an embedded iframe client
- an agent runtime with a browser/WebRTC shell

## 8) Command Contract

Stable command families remain documented in:
- `TCP_CONTROLLER_STABLE_REFERENCE.md`

Important distinction:
- the command *strings* are still the same stable avatar commands
- the preferred transport is now DataChannel, not the public TCP relay API

## 9) HTTP Templates

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

## 10) Product Direction

This skill intentionally stays short and stable.

The hosted bootstrap contract is the source of truth.

Future updates should prefer:
- updating the hosted contract
- updating the client wrapper
- not constantly rewriting this skill
