import { renderHook, act } from "@testing-library/react";
import { usePrompt } from "../usePrompt";

(window as any).__LC_PORT__ = 5001;

function makeSSEBody(events: object[]): ReadableStream {
  const chunks = events.map(e => new TextEncoder().encode(`data: ${JSON.stringify(e)}\n\n`));
  let i = 0;
  return new ReadableStream({
    pull(controller) {
      if (i < chunks.length) controller.enqueue(chunks[i++]);
      else controller.close();
    },
  });
}

test("run sets isRunning then clears on done", async () => {
  const doneEvent = { generation: 1, variants: [{ prompt:"p", output:"o", score:0.9, reason:"r", generation:1 }], best_score: 0.9, event_type: "done" };
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    body: makeSSEBody([doneEvent]),
  } as any);

  const { result } = renderHook(() => usePrompt());
  await act(async () => { await result.current.run("myp"); });

  expect(result.current.isRunning).toBe(false);
  expect(result.current.bestVariant?.score).toBe(0.9);
});

test("stop aborts the run", () => {
  const { result } = renderHook(() => usePrompt());
  act(() => result.current.stop());
  expect(result.current.isRunning).toBe(false);
});
