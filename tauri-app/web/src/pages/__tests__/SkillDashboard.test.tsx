import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { SkillDashboard } from "../SkillDashboard";

(window as any).__LC_PORT__ = 5001;

test("renders skill name and run button", () => {
  render(
    <MemoryRouter initialEntries={["/skills/myskill/run"]}>
      <Routes>
        <Route path="/skills/:name/run" element={<SkillDashboard />} />
      </Routes>
    </MemoryRouter>
  );
  expect(screen.getByText(/myskill/i)).toBeInTheDocument();
  expect(screen.getByRole("button", { name: /Run/i })).toBeInTheDocument();
});
