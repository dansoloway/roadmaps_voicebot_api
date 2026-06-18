# Voice API for Roadmaps — deploy as main.py on api.roadmaps.fit
# Canonical copy also lives at: roadmaps_daniel/voice/api_3/fish_server_main.py

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import os
from io import BytesIO
from fish_audio_sdk import Session, TTSRequest

VOICE_PATH_ALLOWED_BASE = os.environ.get(
    "VOICE_PATH_ALLOWED_BASE",
    "/home/bitnami/htdocs/voice/output",
)

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
    voices: UploadFile = File(None),
    voice_path: str = Form(None),
):
    """Create a voice model by uploading audio, or by server path (for testing)."""
    try:
        if voice_path:
            path = os.path.normpath(voice_path)
            base = os.path.normpath(VOICE_PATH_ALLOWED_BASE)
            if not path.startswith(base) or ".." in path:
                raise HTTPException(status_code=400, detail="voice_path not allowed")
            if not os.path.isfile(path):
                raise HTTPException(status_code=404, detail=f"File not found: {path}")
            with open(path, "rb") as f:
                voice_data = [f.read()]
        elif voices and voices.filename:
            voice_data = [await voices.read()]
        else:
            raise HTTPException(
                status_code=400,
                detail="Provide either 'voices' file upload or 'voice_path'.",
            )
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
    """Generate narration audio; return raw MP3 bytes."""
    try:
        audio_chunks = session.tts(TTSRequest(text=text, reference_id=model_id))
        buffer = BytesIO()
        for chunk in audio_chunks:
            buffer.write(chunk)
        buffer.seek(0)
        return Response(content=buffer.getvalue(), media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
