import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Settings } from "../Settings";

(window as any).__LC_PORT__ = 5001;

test("loads and displays whisper backend chips", async () => {
  global.fetch = vi.fn()
    .mockResolvedValueOnce({ json: async () => ({ whisper_backend: "local", whisper_model: "base", openai_api_key: "" }) } as any)
    .mockResolvedValue({ json: async () => ({}) } as any);
  render(<MemoryRouter><Settings /></MemoryRouter>);
  await waitFor(() => expect(screen.getByRole("button", { name: /local/i })).toBeInTheDocument());
  expect(screen.getByRole("button", { name: /openai/i })).toBeInTheDocument();
});

test("saves updated config", async () => {
  global.fetch = vi.fn()
    .mockResolvedValueOnce({ json: async () => ({ whisper_backend: "local", whisper_model: "base", openai_api_key: "" }) } as any)
    .mockResolvedValue({ json: async () => ({}) } as any);
  render(<MemoryRouter><Settings /></MemoryRouter>);
  await waitFor(() => screen.getByRole("button", { name: /openai/i }));
  fireEvent.click(screen.getByRole("button", { name: /openai/i }));
  fireEvent.click(screen.getByRole("button", { name: /Save Settings/i }));
  await waitFor(() => expect(fetch).toHaveBeenCalledWith(
    expect.stringContaining("/api/config"), expect.objectContaining({ method: "PUT" }),
  ));
});
