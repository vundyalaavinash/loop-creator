import { useState, useCallback, useRef } from "react";
import { GenerationEvent, Variant, getBaseUrl } from "../types";

export function useSkill() {
  const [events, setEvents] = useState<GenerationEvent[]>([]);
  const [bestVariant, setBestVariant] = useState<Variant | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const run = useCallback(async (name: string) => {
    setEvents([]);
    setBestVariant(null);
    setError(null);
    setIsRunning(true);

    const ctrl = new AbortController();
    abortRef.current = ctrl;

    try {
      const response = await fetch(`${getBaseUrl()}/api/skills/${name}/run`, {
        method: "POST",
        signal: ctrl.signal,
      });
      if (!response.body) throw new Error("No response body");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let sseBuffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        sseBuffer += decoder.decode(value, { stream: true });
        const parts = sseBuffer.split("\n\n");
        sseBuffer = parts.pop() ?? "";
        for (const part of parts) {
          const dataLine = part.split("\n").find((l) => l.startsWith("data: "));
          if (!dataLine) continue;
          try {
            const ev: GenerationEvent = JSON.parse(dataLine.slice(6));
            setEvents((prev) => [...prev, ev]);
            if (ev.event_type === "done" && ev.variants.length > 0) {
              setBestVariant(ev.variants[0]);
            }
          } catch {
            // malformed SSE line — skip
          }
        }
      }
    } catch (e) {
      if ((e as Error).name !== "AbortError") {
        setError(e instanceof Error ? e.message : "Unknown error");
      }
    } finally {
      setIsRunning(false);
    }
  }, []);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setIsRunning(false);
  }, []);

  return { events, bestVariant, isRunning, error, run, stop };
}
