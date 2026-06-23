import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { PromptBuilder } from "../PromptBuilder";

(window as any).__LC_PORT__ = 5001;

test("renders all form fields", () => {
  render(<MemoryRouter><PromptBuilder /></MemoryRouter>);
  expect(screen.getByLabelText(/Prompt Name/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/Description Goal/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/Variables/i)).toBeInTheDocument();
});

test("submits new prompt", async () => {
  global.fetch = vi.fn().mockResolvedValue({ json: async () => ({ name: "myprompt" }) } as any);
  render(<MemoryRouter><PromptBuilder /></MemoryRouter>);
  fireEvent.change(screen.getByLabelText(/Prompt Name/i), { target: { value: "myprompt" } });
  fireEvent.change(screen.getByLabelText(/Description Goal/i), { target: { value: "Make commits" } });
  fireEvent.click(screen.getByRole("button", { name: /Save/i }));
  await waitFor(() => expect(fetch).toHaveBeenCalledWith(
    expect.stringContaining("/api/prompts"), expect.objectContaining({ method: "POST" }),
  ));
});
