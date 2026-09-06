# MoVoKaL: complete Grid handoff

## What is included

- `MoVoKaL.html`: complete interface with embedded CSS and JavaScript for integration into Grid.
- `public/index.html`, `public/app.js`, `public/style.css`: the same interface as separate files, served by the included Node server.
- `server.mjs` and `lib/grid.mjs`: same-origin backend adapters for conversation, status, and WAV audio.
- `services/voice/voice_api.py`: attributed Piper service with a conversational pacing mode.
- `.env.example`, tests, and the original Grid license.

## Voices

| Voice ID | Model |
| --- | --- |
| `mostar-sovereign-v1` | Cori, British English, high quality |
| `mostar-clear-v1` | Lessac, American English, high quality |
| `mostar-libritts-v1` | LibriTTS, American English, high quality |

The dropdown loads all available voices from the configured voice service's `/voices` registry. Any additional available voices it advertises appear automatically. ONNX model weights and the Piper executable are not included; reuse the models already installed on Grid or install them according to the voice service's deployment instructions. These are Piper voices, not custom voice clones.

## Run the complete app

Use Node.js 22 or later. Copy `.env.example` to `.env`, set `GRID_API_URL` and `VOICE_API_URL` to your verified services, then run `npm start`. Open `http://localhost:4317`. No Node package installation is required.

To use the included enhanced voice service, follow README.md, point `VOICE_API_URL` to that service, and set `VOICE_MOOD=conversational`. Both bundled and active Grid voice services support conversational pacing, the default.

## Embed the single HTML into Grid

The single HTML contains the whole frontend, but still needs these same-origin routes from the included server (or equivalent Grid handlers):

| Method | Route | Contract |
| --- | --- | --- |
| GET | `/api/config` | `{ locked: boolean }` |
| GET | `/api/status` | `{ voiceReady, gridReachable, voices: [{ id, label }] }` |
| POST | `/api/turn` | Accept `{ text, history, sessionId }`; return `{ text, semanticAvailable, semanticSource }` |
| POST | `/api/speak` | Accept `{ text, voice }`; return WAV audio |

Grid already has its own `/api/status`, with a different shape. Do not replace it with MoVoKaL's route: host MoVoKaL on a separate origin, or namespace its four frontend API paths and mount the adapter routes under that namespace. The included Node server handles this by running separately.

Do not open the HTML through `file://` and expect backend calls or microphone permissions to work. Serve it from localhost or HTTPS. If Grid enforces a Content Security Policy, use the separate JS/CSS files or approved CSP hashes/nonces for the embedded scripts/styles. Do not weaken Grid's CSP with `unsafe-inline`.

## Backend dependencies and limits

Responses use Grid's `/api/semantic/interpret` and governed `/api/think`; synthesized speech uses the voice service's `/speak`. Grid's Mind Conduit must authorize inference for replies to work. This bundle does not grant that authorization or include a human attestation.

Microphone input uses browser speech recognition where supported, with explicit Send and a text-input fallback. Hands-free semantic turn detection is not implemented. Voice preview and actual conversation depend on live backend services. VPS URLs and credentials are not preconfigured, and a direct MCP transport client is not included: the integration currently uses Grid's HTTP API.

Keep service credentials in server environment variables. Never insert them into the HTML. No secrets, conversation recordings, or model weights are in this handoff.

## Natural speech defaults

Lessac high (`mostar-clear-v1`) is the default. `VOICE_DEFAULT` can select another registered voice; `VOICE_MOOD` defaults to `conversational`. Complete replies retain punctuation and are sent as one Piper utterance, including multiline replies. Audio is published only after the entire WAV is written. Over-limit replies are rejected explicitly instead of cut mid-word. Ordinary speech has no Codex decorations or canned replies; existing explicit Codex wording remains opt-in. Preview reads your composed text, or asks Grid for a fresh introduction. Pronunciation quality still depends on the model and needs listening checks, particularly for names and languages outside English.
