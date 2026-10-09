"""Local text-to-speech prototype. No voice recording or cloning endpoint."""
import asyncio
import json
import logging
import os
import uuid
from pathlib import Path
from threading import Lock

import edge_tts
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
VOICES_FILE = DATA_DIR / "voices.json"
for directory in (STATIC_DIR, DATA_DIR):
    directory.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger("AuraAI")
voice_lock = Lock()
app = FastAPI(title="Aura AI — Text-to-Speech Prototype")
app.add_middleware(CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()],
    allow_methods=["GET", "POST"], allow_headers=["Content-Type"],
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

def load_voices():
    try:
        with VOICES_FILE.open(encoding="utf-8") as handle:
            voices = json.load(handle)
        if not isinstance(voices, list): raise ValueError("Voice catalog must be an array")
        return voices
    except (OSError, ValueError) as error:
        logger.error("Voice catalog unavailable: %s", type(error).__name__)
        raise HTTPException(status_code=503, detail="Voice catalog is unavailable.") from error

@app.get("/")
async def root():
    return {"message": "Aura AI text-to-speech prototype", "status": "ok"}

@app.get("/voices")
async def get_voices():
    return [{**voice, "available": voice.get("engine") != "elevenlabs" or bool(os.getenv("ELEVENLABS_API_KEY"))} for voice in load_voices()]

@app.post("/sync-elevenlabs")
async def sync_elevenlabs():
    # Explicit opt-in for this local administrative operation.
    if os.getenv("ALLOW_VOICE_SYNC") != "true":
        raise HTTPException(status_code=403, detail="Voice sync is disabled. Enable ALLOW_VOICE_SYNC only on a trusted local instance.")
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key: raise HTTPException(status_code=503, detail="ElevenLabs is not configured.")
    try:
        response = await asyncio.to_thread(lambda: ElevenLabs(api_key=key).voices.get_all())
        external = [{"id": v.voice_id, "name": v.name, "engine": "elevenlabs", "voice_code": v.voice_id, "description": "Voice available in the configured ElevenLabs account."} for v in response.voices if v.category in {"cloned", "generated", "professional"}]
        with voice_lock:
            current = load_voices()
            ids = {voice["id"] for voice in current}
            added = [voice for voice in external if voice["id"] not in ids]
            temporary = VOICES_FILE.with_suffix(".tmp")
            temporary.write_text(json.dumps(current + added, indent=2), encoding="utf-8")
            temporary.replace(VOICES_FILE)
        return {"status": "success", "added_count": len(added), "message": f"Synced {len(added)} voices."}
    except HTTPException:
        raise
    except Exception as error:
        logger.error("Voice sync failed: %s", type(error).__name__)
        raise HTTPException(status_code=502, detail="Voice provider sync failed.") from error

@app.post("/synthesize")
async def synthesize(voice_id: str = Form(...), text: str = Form(...)):
    text = text.strip()
    if not text or len(text) > 5000:
        raise HTTPException(status_code=400, detail="Enter between 1 and 5000 characters.")
    voice = next((v for v in load_voices() if v["id"] == voice_id), None)
    if not voice: raise HTTPException(status_code=404, detail="Voice not found.")
    engine = voice["engine"]
    key = os.getenv("ELEVENLABS_API_KEY")
    if engine == "elevenlabs" and not key:
        raise HTTPException(status_code=503, detail="ElevenLabs is not configured. Choose an Edge TTS voice.")
    filename = f"aura_{uuid.uuid4().hex}.mp3"
    output = STATIC_DIR / filename
    try:
        if engine == "elevenlabs":
            def generate():
                audio = ElevenLabs(api_key=key).text_to_speech.convert(voice_id=voice["voice_code"], text=text, model_id="eleven_multilingual_v2", output_format="mp3_44100_128")
                with output.open("wb") as handle:
                    for chunk in audio: handle.write(chunk)
            await asyncio.to_thread(generate)
        elif engine == "edge-tts":
            await edge_tts.Communicate(text, voice["voice_code"]).save(str(output))
        else:
            raise HTTPException(status_code=400, detail="Unsupported voice engine.")
        if not output.exists() or output.stat().st_size == 0:
            raise RuntimeError("Empty audio output")
        return {"status": "success", "audio_url": f"/static/{filename}", "filename": filename, "message": f"Generated with {voice['name']}"}
    except HTTPException:
        output.unlink(missing_ok=True)
        raise
    except Exception as error:
        output.unlink(missing_ok=True)
        logger.error("Synthesis failed: %s", type(error).__name__)
        raise HTTPException(status_code=502, detail="Speech provider failed. Please try again.") from error

if __name__ == "__main__":
    uvicorn.run(app, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")))
