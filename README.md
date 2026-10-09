# Aura AI — text-to-speech prototype

A personal React/Vite frontend and FastAPI backend for text-to-speech synthesis. Despite the repository name `voice-clone`, this code does not implement voice recording, voice-model training or a voice-cloning endpoint. It offers Edge TTS and optional ElevenLabs account voices.

## Local setup

Use Python 3.12 and Node.js 22+. Create a virtual environment, install `backend/requirements.txt`, and copy `backend/.env.example` to `backend/.env`. ElevenLabs is optional; its API key stays on the backend.

Run `python backend/main.py`, then in `frontend` run `npm ci` and `npm run dev`. Copy the frontend environment example if you need a different local API URL. `Launch-Aura.ps1` provides a Windows launcher using its own project directory.

`ALLOW_VOICE_SYNC` defaults to disabled. Enable it only on a trusted local instance for a deliberate provider sync. Synthesizing speech uses an external provider; do not send private text. No provider request was made during the audit.

## Behavior and checks

Input is bounded to 1–5000 nonblank characters. Unknown voices are rejected, unavailable ElevenLabs voices are disabled, and provider failures show a user-facing message. API keys are no longer stored by this UI in browser localStorage. The frontend build and backend syntax checks passed. Local API checks covered missing voices, blank/oversized text, disabled sync and absent provider configuration without contacting providers.

## Limitations

This is a local prototype. It has no user authentication, persistent rate limit, billing, job queue or automatic audio retention cleanup. Generated audio in `backend/static` can be accessed by anyone able to access the instance. Do not expose this server publicly until those controls are added. Provider voice permissions and pricing must be reviewed before use. Synced provider catalogs should not be committed because they may include account-specific names.
