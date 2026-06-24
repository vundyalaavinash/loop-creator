import io
from typing import TYPE_CHECKING


class WhisperTranscriber:
    def __init__(self, backend: str, model: str, openai_api_key: str = ""):
        self.backend = backend
        self.model = model
        self.openai_api_key = openai_api_key

    def transcribe(self, audio_bytes: bytes) -> str:
        if self.backend == "local":
            return self._transcribe_local(audio_bytes)
        if self.backend == "openai":
            return self._transcribe_openai(audio_bytes)
        raise ValueError(f"Unknown backend: {self.backend!r}")

    def _transcribe_local(self, audio_bytes: bytes) -> str:
        from faster_whisper import WhisperModel
        model = WhisperModel(self.model)
        segments, _ = model.transcribe(io.BytesIO(audio_bytes))
        return "".join(s.text for s in segments).strip()

    def _transcribe_openai(self, audio_bytes: bytes) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=self.openai_api_key)
        result = client.audio.transcriptions.create(
            model=self.model,
            file=("audio.wav", audio_bytes, "audio/wav"),
        )
        return result.text
