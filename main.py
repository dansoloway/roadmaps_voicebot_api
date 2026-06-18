# Voice API for Roadmaps — deploy as main.py on api.roadmaps.fit
# Canonical copy also lives at: roadmaps_daniel/voice/api_3/fish_server_main.py
#
# Design: stateless proxy to fish.audio. No local audio files. MP3 is streamed
# through memory in chunks. Persistent storage is on the PHP web server
# (roadmapvoicebot.org/voice/output/), not this box.

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from fish_audio_sdk import Session, TTSRequest

load_dotenv()

FISH_AUDIO_API_KEY = os.environ.get("FISH_AUDIO_API_KEY")
if not FISH_AUDIO_API_KEY:
    raise RuntimeError("Set FISH_AUDIO_API_KEY (see .env.example)")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session = Session(FISH_AUDIO_API_KEY)


@app.get("/")
async def home():
    return {"message": "Fish Audio API (generate-narration, clone-voice)"}


@app.post("/clone-voice/")
async def clone_voice(
    title: str = Form(...),
    description: str = Form(...),
    voices: UploadFile = File(...),
):
    """Create a voice model; audio is forwarded to fish.audio (not saved locally)."""
    try:
        voice_data = [await voices.read()]
        model = session.create_model(
            title=title,
            description=description,
            voices=voice_data,
        )
        return {"model_id": model.id, "message": "Voice model created successfully."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/generate-narration/")
async def generate_narration(
    model_id: str = Form(...),
    text: str = Form(...),
):
    """Stream MP3 from fish.audio without buffering the full file on disk."""
    try:
        request = TTSRequest(text=text, reference_id=model_id)

        def iter_audio():
            for chunk in session.tts(request):
                yield chunk

        return StreamingResponse(iter_audio(), media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
