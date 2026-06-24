import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { PromptDashboard } from "../PromptDashboard";

(window as any).__LC_PORT__ = 5001;

test("renders prompt name and run button", () => {
  render(
    <MemoryRouter initialEntries={["/prompts/commit-msg/run"]}>
      <Routes>
        <Route path="/prompts/:name/run" element={<PromptDashboard />} />
      </Routes>
    </MemoryRouter>
  );
  expect(screen.getByText(/commit-msg/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Run/i })).toBeInTheDocument();
});
