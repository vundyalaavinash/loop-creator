import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { LoopList } from "../LoopList";

(window as any).__LC_PORT__ = 5001;

test("shows empty state when no loops", async () => {
  global.fetch = vi.fn().mockResolvedValue({
    json: async () => [],
  } as any);
  render(<MemoryRouter><LoopList /></MemoryRouter>);
  await waitFor(() =>
    expect(screen.getByText(/No loops yet/)).toBeInTheDocument()
  );
});

test("renders loop rows", async () => {
  global.fetch = vi.fn().mockResolvedValue({
    json: async () => [
      { id: "loop1", name: "loop1", loop_type: "coding",
        last_modified: 0, best_score: 0.85, active: false },
    ],
  } as any);
  render(<MemoryRouter><LoopList /></MemoryRouter>);
  await waitFor(() => expect(screen.getByText("loop1")).toBeInTheDocument());
  expect(screen.getByText("coding")).toBeInTheDocument();
  expect(screen.getByText("85%")).toBeInTheDocument();
});
