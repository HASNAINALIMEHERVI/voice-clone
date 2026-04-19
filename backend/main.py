import os
import uuid
import json
import edge_tts
import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from pydantic import BaseModel
from typing import List, Optional
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AuraAI")

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)
DEFAULT_API_KEY = os.getenv("ELEVENLABS_API_KEY")

PORT = int(os.environ.get("PORT", 8000))

app = FastAPI(title="Aura AI - Production Nexus")

# Directories
BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATA_DIR = os.path.join(BASE_DIR, "data")
VOICES_FILE = os.path.join(DATA_DIR, "voices.json")

for d in [STATIC_DIR, DATA_DIR]:
    if not os.path.exists(d): os.makedirs(d)

# app.mount moved below middleware for better CORS handling

    allow_headers=["*"],
)

# Force CORS on all responses (including StaticFiles)
@app.middleware("http")
async def add_cors_header(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Mount static files AFTER middleware
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

def load_voices() -> List[dict]:
    try:
        with open(VOICES_FILE, "r") as f:
            return json.load(f)
    except:
        return []

@app.get("/")
async def root():
    return {"message": "Aura AI TTS Engine Active"}

@app.get("/voices")
async def get_voices():
    return load_voices()

@app.post("/sync-elevenlabs")
async def sync_elevenlabs(api_key: Optional[str] = Form(None)):
    current_key = api_key or DEFAULT_API_KEY
    if not current_key:
        raise HTTPException(status_code=400, detail="No API Key found.")
    
    try:
        client = ElevenLabs(api_key=current_key)
        response = client.voices.get_all()
        
        # Only interested in cloned/personal voices for syncing
        external_voices = []
        for v in response.voices:
            if v.category in ["cloned", "generated", "professional"]:
                external_voices.append({
                    "id": v.voice_id,
                    "name": f"{v.name} (ElevenLabs)",
                    "engine": "elevenlabs",
                    "voice_code": v.voice_id,
                    "description": f"External voice synced from ElevenLabs Nexus."
                })
        
        # Merge with existing voices (avoid duplicates)
        current_voices = load_voices()
        voice_ids = {v['id'] for v in current_voices}
        
        new_voices = []
        for ev in external_voices:
            if ev['id'] not in voice_ids:
                new_voices.append(ev)
        
        if new_voices:
            with open(VOICES_FILE, "w") as f:
                json.dump(current_voices + new_voices, f, indent=4)
        
        return {"status": "success", "added_count": len(new_voices), "message": f"Successfully synced {len(new_voices)} new voices."}
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/synthesize")
async def synthesize(
    voice_id: str = Form(...),
    text: str = Form(...),
    api_key: Optional[str] = Form(None)
):
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")

    current_key = api_key or DEFAULT_API_KEY
    output_filename = f"aura_{uuid.uuid4().hex}.mp3"
    output_path = os.path.join(STATIC_DIR, output_filename)

    voices = load_voices()
    voice_meta = next((v for v in voices if v['id'] == voice_id), None)
    
    if not voice_meta:
        # Fallback to a default if not found
        engine = "edge-tts"
        voice_code = "en-US-ChristopherNeural"
    else:
        engine = voice_meta['engine']
        voice_code = voice_meta['voice_code']

    logger.info(f"Synthesizing: Engine={engine}, Voice={voice_code}")

    try:
        if engine == "elevenlabs" and current_key:
            client = ElevenLabs(api_key=current_key)
            audio_generator = client.text_to_speech.convert(
                voice_id=voice_code,
                text=text,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
            with open(output_path, "wb") as f:
                for chunk in audio_generator: f.write(chunk)
            msg = f"Generated via {voice_meta['name']} (ElevenLabs)"
        else:
            # Multi-lingual detection (simple)
            # Edge-TTS uses voice_code directly
            logger.info(f"Edge-TTS Start: {voice_code}")
            communicate = edge_tts.Communicate(text, voice_code)
            await communicate.save(output_path)
            logger.info(f"Edge-TTS Done: {output_path} (Size: {os.path.getsize(output_path)} bytes)")
            msg = f"Generated via {voice_meta['name']} (EdgeAI)"
        
        return {
            "status": "success",
            "audio_url": f"/static/{output_filename}",
            "message": msg
        }
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
