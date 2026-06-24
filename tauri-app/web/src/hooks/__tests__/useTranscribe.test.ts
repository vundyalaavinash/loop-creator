import { renderHook, act } from "@testing-library/react";
import { useTranscribe } from "../useTranscribe";

(window as any).__LC_PORT__ = 5001;

test("stopAndTranscribe posts audio and returns text", async () => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ text: "hello world" }),
  } as any);

  const mockMediaRecorder = {
    start: vi.fn(),
    stop: vi.fn(),
    ondataavailable: null as any,
    onstop: null as any,
  };
  const mockStream = {
    getTracks: vi.fn(() => [{ stop: vi.fn() }]),
  };
  (global as any).MediaRecorder = vi.fn(() => mockMediaRecorder);
  (global as any).navigator = {
    mediaDevices: { getUserMedia: vi.fn().mockResolvedValue(mockStream) },
  };

  const { result } = renderHook(() => useTranscribe());

  await act(async () => { await result.current.startRecording(); });
  mockMediaRecorder.ondataavailable?.({ data: new Blob(["audio"]) } as any);

  const textPromise = result.current.stopAndTranscribe();
  mockMediaRecorder.onstop?.();
  const text = await textPromise;
  expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/transcribe"), expect.any(Object));
});
