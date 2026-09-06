# MoVoKaL

A standalone, warm and witty voice companion built around **MoStar Grid**.

## Run

Requires Node.js 22+, a running Grid API and MoStar Voice API. No npm dependencies.

```sh
cp .env.example .env
npm start
```

Open http://localhost:4317. Defaults connect to Grid on port 41010 and Voice on 41071.
Use **Hear this voice** to audition the actual backend audio. Lessac is selected by default; other installed voices remain available.
Tap the microphone, talk at your own pace, then press **Send**. Text input works without microphone support.
**Interrupt & speak** cancels pending requests and stops playback. **Stop & reset** clears local conversation context.

This implementation does not pretend Piper is a human voice, use browser text-to-speech, or substitute OpenAI for MoStar.
Browser speech recognition is an input adapter: availability varies and the browser provider may process audio remotely.
Turn submission is explicit, not semantic voice activity detection. Hands-free duplex speech and local transcription are not implemented.

## Actual integration

1. Speech recognition or typed text → MoVoKaL.
2. `POST /api/semantic/interpret` with `persist:false` supplies Grid emotion, warmth, humour and risk cues.
3. `POST /api/think` generates the answer through Grid's existing governed mind.
4. `POST /speak` renders the answer through MoStar Voice with `codex:false`, returning WAV.
5. Captions and audio are displayed together. No canned reply is substituted when Grid is unavailable.

A failed or unavailable semantic interpretation is disclosed in captions. A closed mind or failed truth gate stops the reply;
MoVoKaL never bypasses Grid's Mind Conduit by calling Ollama directly.
Grid's `/api/think` may retain its normal memory/telemetry; `persist:false` applies to semantic interpretation only.
The voice service caches synthesized WAVs. MoVoKaL itself keeps its last 12 messages only in browser memory.

## Improving the existing voice

The source Grid voice API was found at:
`back/services/voice/voice_api.py`.

An attributed copy is included under `services/voice/voice_api.py`, with an opt-in
`conversational` mood. Unlike the original breath processor, this mood preserves question and exclamation
intonation, removes ceremonial suffixes by default, and shortens inter-sentence silence.
Existing moods remain compatible. Piper remains the synthesizer; these changes improve pacing, not its fundamental vocal range.

Run the enhanced service separately, with your existing Piper binary and models:

```sh
python -m venv .venv
.venv/bin/pip install -r services/voice/requirements.txt
PORT=4318 .venv/bin/python services/voice/voice_api.py
```

It defaults to `~/MoStar/voice` for Piper and models. Set `VOICE_ROOT`, `PIPER_BIN` and `VOICE_MODEL_DIR` if needed.
Then set `VOICE_API_URL=http://127.0.0.1:4318` and `VOICE_MOOD=conversational` in MoVoKaL's .env and restart.
Do not expose this inherited voice service directly to the public internet.

## Deployment and credentials

The web server binds to loopback by default. If you change HOST, you must set VOKAL_ACCESS_KEY.
Use HTTPS and a trusted reverse proxy for remote microphone access. The access key is sent to the same-origin
MoVoKaL server and kept only in page memory. Grid credentials never enter the browser.
This is a single-operator prototype, not a multi-tenant hosted service. Rate limits are per-process and per socket IP.
Do not commit .env, audio, model weights or runtime secrets.

## Verify

```sh
npm run check
npm test
```

Tests cover the Grid contracts, truth-gate rejection, authentication, origin validation, input limits,
provider failures, and secret-safe response handling. Real voice quality still requires a listening test
with the chosen model and microphone.

## Provenance

MoStar Grid code retains its African Sovereignty License; see LICENSE.
The copied voice API is attributed in services/voice/UPSTREAM.md. No Grid credentials, database,
runtime state or unrelated CrypSide code is included.

## Natural speech defaults

Lessac high (`mostar-clear-v1`) is the default. `VOICE_DEFAULT` can select another registered voice; `VOICE_MOOD` defaults to `conversational`. Complete replies retain punctuation and are sent as one Piper utterance, including multiline replies. Audio is published only after the entire WAV is written. Over-limit replies are rejected explicitly instead of cut mid-word. Ordinary speech has no Codex decorations or canned replies; existing explicit Codex wording remains opt-in. Preview reads your composed text, or asks Grid for a fresh introduction. Pronunciation quality still depends on the model and needs listening checks, particularly for names and languages outside English.
