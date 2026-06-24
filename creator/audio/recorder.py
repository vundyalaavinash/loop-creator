def record_audio() -> bytes:
    import sounddevice as sd
    import numpy as np
    import wave, io

    sample_rate = 16000
    print("Recording... press Enter to stop.")
    chunks = []

    def callback(indata, frames, time, status):
        chunks.append(indata.copy())

    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16", callback=callback):
        input()

    if not chunks:
        raise RuntimeError("No audio recorded — check your microphone input")
    audio = np.concatenate(chunks, axis=0)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio.tobytes())
    return buf.getvalue()
