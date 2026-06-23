import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { SkillList } from "../SkillList";

(window as any).__LC_PORT__ = 5001;

test("shows empty state when no skills", async () => {
  global.fetch = vi.fn().mockResolvedValue({ json: async () => [] } as any);
  render(<MemoryRouter><SkillList /></MemoryRouter>);
  await waitFor(() => expect(screen.getByText(/No skills yet/)).toBeInTheDocument());
});

test("renders skill rows", async () => {
  global.fetch = vi.fn().mockResolvedValue({
    json: async () => [{ name: "my-reviewer", category: "code-review", last_modified: 0 }],
  } as any);
  render(<MemoryRouter><SkillList /></MemoryRouter>);
  await waitFor(() => expect(screen.getByText("my-reviewer")).toBeInTheDocument());
  expect(screen.getByText("code-review")).toBeInTheDocument();
});
