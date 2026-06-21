import { renderHook, act } from "@testing-library/react";
import { useFiles } from "../useFiles";

const PORT = 5001;
(window as any).__LC_PORT__ = PORT;

test("listFiles fetches and returns file nodes", async () => {
  const nodes = [{ name: "a.py", path: "/p/a.py", is_dir: false }];
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => nodes,
  } as any);

  const { result } = renderHook(() => useFiles());
  await act(async () => {
    await result.current.listFiles("/p");
  });

  expect(result.current.files).toEqual(nodes);
  expect(fetch).toHaveBeenCalledWith(
    expect.stringContaining("/api/files?path=%2Fp")
  );
});
