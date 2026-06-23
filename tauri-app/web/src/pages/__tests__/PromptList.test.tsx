import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { PromptList } from "../PromptList";

(window as any).__LC_PORT__ = 5001;

test("shows empty state", async () => {
  global.fetch = vi.fn().mockResolvedValue({ json: async () => [] } as any);
  render(<MemoryRouter><PromptList /></MemoryRouter>);
  await waitFor(() => expect(screen.getByText(/No prompts yet/)).toBeInTheDocument());
});

test("renders prompt rows", async () => {
  global.fetch = vi.fn().mockResolvedValue({
    json: async () => [{ name: "commit-msg", description_goal: "Generate commit messages", last_modified: 0 }],
  } as any);
  render(<MemoryRouter><PromptList /></MemoryRouter>);
  await waitFor(() => expect(screen.getByText("commit-msg")).toBeInTheDocument());
});
