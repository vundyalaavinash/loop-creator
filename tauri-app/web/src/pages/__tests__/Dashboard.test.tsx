import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { Dashboard } from "../Dashboard";

(window as any).__LC_PORT__ = 5001;

test("renders loop id and stop button", () => {
  global.fetch = vi.fn().mockResolvedValue({
    json: async () => ({ content: "" }),
    ok: true,
  } as any);

  render(
    <MemoryRouter initialEntries={["/loops/myloop/run"]}>
      <Routes>
        <Route path="/loops/:id/run" element={<Dashboard />} />
      </Routes>
    </MemoryRouter>
  );
  expect(screen.getByText("myloop")).toBeInTheDocument();
  expect(screen.getByText("Stop")).toBeInTheDocument();
});
