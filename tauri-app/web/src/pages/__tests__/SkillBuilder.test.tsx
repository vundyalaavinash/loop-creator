import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { SkillBuilder } from "../SkillBuilder";

(window as any).__LC_PORT__ = 5001;

test("renders all form fields", () => {
  render(<MemoryRouter><SkillBuilder /></MemoryRouter>);
  expect(screen.getByLabelText(/Skill Name/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/Description Goal/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/Category/i)).toBeInTheDocument();
});

test("submits new skill and navigates", async () => {
  global.fetch = vi.fn().mockResolvedValue({ json: async () => ({ name: "newskill" }) } as any);
  render(<MemoryRouter><SkillBuilder /></MemoryRouter>);
  fireEvent.change(screen.getByLabelText(/Skill Name/i), { target: { value: "newskill" } });
  fireEvent.change(screen.getByLabelText(/Description Goal/i), { target: { value: "Do reviews" } });
  fireEvent.click(screen.getByRole("button", { name: /Save/i }));
  await waitFor(() => expect(fetch).toHaveBeenCalledWith(
    expect.stringContaining("/api/skills"),
    expect.objectContaining({ method: "POST" }),
  ));
});
