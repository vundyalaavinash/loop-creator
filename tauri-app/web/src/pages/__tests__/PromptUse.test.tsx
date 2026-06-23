import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { PromptUse } from "../PromptUse";
import { vi } from "vitest";

(window as any).__LC_PORT__ = 5001;

test("renders variable inputs from spec", async () => {
  global.fetch = vi.fn()
    .mockResolvedValueOnce({ json: async () => ({ name: "commit-msg", variables: ["diff", "context"], description_goal: "", generator: {cli:"claude",model:""}, judge: {cli:"claude",rubric:"",model:""}, gepa: {} }) } as any)
    .mockResolvedValue({ json: async () => ({}) } as any);

  render(
    <MemoryRouter initialEntries={["/prompts/commit-msg/use"]}>
      <Routes>
        <Route path="/prompts/:name/use" element={<PromptUse />} />
      </Routes>
    </MemoryRouter>
  );
  await waitFor(() => expect(screen.getByLabelText(/diff/i)).toBeInTheDocument());
  expect(screen.getByLabelText(/context/i)).toBeInTheDocument();
});

test("submits variables and shows resolved text", async () => {
  global.fetch = vi.fn()
    .mockResolvedValueOnce({ json: async () => ({ name: "commit-msg", variables: ["diff"], description_goal: "", generator: {cli:"claude",model:""}, judge: {cli:"claude",rubric:"",model:""}, gepa: {} }) } as any)
    .mockResolvedValueOnce({ json: async () => ({ resolved: "Write commit for added login." }) } as any);

  render(
    <MemoryRouter initialEntries={["/prompts/commit-msg/use"]}>
      <Routes>
        <Route path="/prompts/:name/use" element={<PromptUse />} />
      </Routes>
    </MemoryRouter>
  );
  await waitFor(() => screen.getByLabelText(/diff/i));
  fireEvent.change(screen.getByLabelText(/diff/i), { target: { value: "added login" } });
  fireEvent.click(screen.getByRole("button", { name: /Fill/i }));
  await waitFor(() => expect(screen.getByText(/Write commit for added login/)).toBeInTheDocument());
});
