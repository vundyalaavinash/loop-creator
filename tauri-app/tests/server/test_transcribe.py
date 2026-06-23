from unittest.mock import patch


def test_transcribe_returns_text(client):
    audio_bytes = b"RIFF....fake wav"
    with patch("lc_server.routes.transcribe.WhisperTranscriber") as MockT:
        MockT.return_value.transcribe.return_value = "hello world"
        r = client.post(
            "/api/transcribe",
            files={"audio": ("audio.wav", audio_bytes, "audio/wav")},
        )
    assert r.status_code == 200
    assert r.json()["text"] == "hello world"
