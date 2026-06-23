from __future__ import annotations

from fastapi import APIRouter, UploadFile, File

from creator.audio.whisper import WhisperTranscriber
from creator.config import load_config

router = APIRouter(prefix="/api/transcribe")


@router.post("")
async def transcribe(audio: UploadFile = File(...)):
    cfg = load_config()
    audio_bytes = await audio.read()
    t = WhisperTranscriber(
        backend=cfg.whisper_backend,
        model=cfg.whisper_model,
        openai_api_key=cfg.openai_api_key,
    )
    text = t.transcribe(audio_bytes)
    return {"text": text}
