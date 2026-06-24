import { useState, useRef, useCallback } from "react";
import { getBaseUrl } from "../types";

export function useTranscribe() {
  const [isRecording, setIsRecording] = useState(false);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  const startRecording = useCallback(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRef.current = stream;
    const recorder = new MediaRecorder(stream);
    chunksRef.current = [];
    recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
    recorder.start();
    recorderRef.current = recorder;
    setIsRecording(true);
  }, []);

  const stopAndTranscribe = useCallback((): Promise<string> => {
    return new Promise((resolve, reject) => {
      const recorder = recorderRef.current;
      if (!recorder) { reject(new Error("Not recording")); return; }
      recorder.onstop = async () => {
        setIsRecording(false);
        streamRef.current?.getTracks().forEach(t => t.stop());
        streamRef.current = null;
        const blob = new Blob(chunksRef.current, { type: "audio/wav" });
        const formData = new FormData();
        formData.append("audio", blob, "audio.wav");
        try {
          const res = await fetch(`${getBaseUrl()}/api/transcribe`, {
            method: "POST",
            body: formData,
          });
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const data = await res.json();
          resolve(data.text as string);
        } catch (e) {
          reject(e);
        }
      };
      recorder.stop();
    });
  }, []);

  return { isRecording, startRecording, stopAndTranscribe };
}
