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

## 1) Check For Updates First

Before using this skill, and especially before debugging failures, check for updates.

Minimum rule:
- fetch the current hosted bootstrap contract:
  - `https://api.embody.zone/api/bootstrap/skillmd`

If behavior looks wrong, stale, or broken:
- re-read this `SKILL.md`
- re-fetch the hosted bootstrap contract
- re-check the command reference in:
  - `TCP_CONTROLLER_STABLE_REFERENCE.md`

Operational assumption:
- the hosted bootstrap contract is the current source of truth
- this skill file should also be re-checked before assuming the product behavior has not changed

## 2) Current Model

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

## 3) Hard Rules

- Start from the hosted bootstrap contract, not from stale copied examples.
- If anything behaves unexpectedly, re-check both this `SKILL.md` and the hosted bootstrap contract before debugging deeper.
- Treat the returned `webrtc_url` as the session entrypoint.
- Real-time control should use the Pixel Streaming DataChannel.
- Primary command transport is `client.sendCommand("...")`  via the EmbodyDataChannelClient wrapper.
- Do not use `/api/sessions/tcp` as the normal embodiment path.
- Keep `/api/sessions/tcp` only as fallback/admin/debug.
- Never print or store secrets or internal diagnostics.
- Do not send commands directly to orchestrator or edge TCP ports.

## 4) What An Agent Can Do

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
- `SPWND`
- `LIGHT_Key_0_0_200`
- `SPWN_Table01_...`

Important reset command:
- `SPWND`
  - clears all spawned objects
  - use this when the environment becomes cluttered, broken, or visually deformed
  - use this before loading a new spawned environment pack

The command surface is broad enough to support use cases like:
- real-time assistant
- news presenter
- meeting participant
- character performer
- product guide

## 5) Where To Find Commands

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

## 6) Deterministic Flow

### Step A: Fetch the current contract

`GET https://api.embody.zone/api/bootstrap/skillmd`

Read at minimum:
- `base_url`
- `version`
- `transport.primary`
- `webrtc.command_method`
- `limits.max_concurrent_sessions`

Expected alpha transport:
- `transport.primary = pixelstreaming_datachannel_sendcommand`
- `webrtc.command_method = sendCommand`

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

Required body:

```json
{
  "installation_id": "<INSTALLATION_ID>",
  "token": "<OTP_TOKEN>",
  "requested_duration_seconds": 600
}
```

The `token` is an OTP token in format `hmac_hex.expires_at_unix`. Obtain one via the token minting API (requires admin authorization). Expired or invalid tokens are rejected.

Token lifecycle:
- Tokens are bound to `installation_id` — a token minted for one identity cannot be used with another
- Same token + same `installation_id` returns the existing active session (session resume)
- Session lease (`expires_at`) is independent of token expiry
- Tokens are not consumed on use — they remain valid until their expiry timestamp

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
- `command_method = sendCommand`

### Step D: Attach to the live session

Open the returned `webrtc_url` exactly as provided.

Do not rewrite:
- scheme
- query string
- websocket target

### Step E: Send commands over DataChannel

Use the EmbodyDataChannelClient wrapper (from `browser/embody_datachannel_client.js`):

```js
const client = await EmbodyDataChannelClient.waitForPixelStreaming();
await client.waitForPlayableVideo();
client.sendCommand("CAMSHOT.ExtremeClose");
client.sendCommand("TTS_Kokoro_Bella_Happy_0.7_Hello from Kokoro");
```

The wrapper API:
- `sendCommand(commandString)` — send a single command
- `sendCommands(commandArray, { delayMs })` — send multiple commands with optional delay
- `addResponseListener(callback)` — listen for avatar responses
- `getState()` — get current connection state

Internally the wrapper calls `pixelStreaming.emitCommand({ command })` over the WebRTC DataChannel. Agents should use `sendCommand()`, not `emitCommand()` directly.

### Step F: End cleanly

`POST https://api.embody.zone/api/sessions/end`

Body:

```json
{ "session_id": "<SESSION_ID>" }
```

## 7) Minimal Proof Commands

Use these first:
- `CAMSHOT.Medium`
- `CAMSHOT.ExtremeClose`
- `EMOTE_Wave`
- `SPWND`

Then validate Kokoro:
- `TTS_Kokoro_Bella_Happy_0.7_Hello from Kokoro`

Operational rule:
- for Kokoro, send one line at a time unless you have timing-aware queueing

## 8) Minimal Client Shape

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
- use `sendCommand(commandString)` (wraps `emitCommand` internally)

This makes the product usable from:
- a browser
- an embedded iframe client
- an agent runtime with a browser/WebRTC shell

## 9) Command Contract

Stable command families remain documented in:
- `TCP_CONTROLLER_STABLE_REFERENCE.md`

Important distinction:
- the command *strings* are still the same stable avatar commands
- the preferred transport is now DataChannel, not the public TCP relay API

## 10) HTTP Templates

### Bootstrap

```bash
curl -s https://api.embody.zone/api/bootstrap/skillmd
```

### Start

```bash
BASE="https://api.embody.zone"
INSTALLATION_ID="$(python3 -c 'import uuid; print(uuid.uuid4().hex)')"
TOKEN="<OTP_TOKEN>"  # from /api/tokens/mint

curl -s -X POST "${BASE}/api/sessions/start" \
  -H "Content-Type: application/json" \
  -d "{
    \"installation_id\": \"${INSTALLATION_ID}\",
    \"token\": \"${TOKEN}\",
    \"requested_duration_seconds\": 600
  }"
```

### End

```bash
curl -s -X POST "https://api.embody.zone/api/sessions/end" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\":\"${SESSION_ID}\"}"
```

## 11) Failure Handling

- If bootstrap fetch fails: treat it as control-plane outage.
- If behavior diverges from expectation: first re-check this `SKILL.md` and re-fetch the bootstrap contract before assuming a deeper platform bug.
- If `start` fails with capacity exhaustion: wait and retry; do not spin.
- If browser attach fails: treat it as edge/session problem, not command-format problem.
- If DataChannel commands appear ignored:
  - first verify you used `client.sendCommand("...")` via the wrapper
  - do not call `emitCommand` or `emitConsoleCommand` directly
- If camera works but Kokoro does not:
  - treat it as TTS/runtime behavior, not transport failure
- If the avatar state or spawned world becomes messy, cluttered, or visually broken:
  - send `SPWND`
  - treat it as the first reset step for spawned environment state
- If you have no browser/DataChannel client available:
  - `/api/sessions/tcp` may still exist as fallback/admin
  - but it is not the preferred embodiment path

## 12) Product Direction

This skill intentionally stays short and stable.

The hosted bootstrap contract is the source of truth.

Future updates should prefer:
- updating the hosted contract
- updating the client wrapper
- not constantly rewriting this skill
