import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Settings } from "../Settings";

(window as any).__LC_PORT__ = 5001;

test("loads and displays current config", async () => {
  global.fetch = vi.fn()
    .mockResolvedValueOnce({ json: async () => ({ whisper_backend: "local", whisper_model: "base", openai_api_key: "" }) } as any)
    .mockResolvedValue({ json: async () => ({}) } as any);
  render(<MemoryRouter><Settings /></MemoryRouter>);
  await waitFor(() => expect(screen.getByDisplayValue("local")).toBeInTheDocument());
});

test("saves updated config", async () => {
  global.fetch = vi.fn()
    .mockResolvedValueOnce({ json: async () => ({ whisper_backend: "local", whisper_model: "base", openai_api_key: "" }) } as any)
    .mockResolvedValueOnce({ json: async () => ({ whisper_backend: "openai", whisper_model: "whisper-1", openai_api_key: "" }) } as any);
  render(<MemoryRouter><Settings /></MemoryRouter>);
  await waitFor(() => screen.getByDisplayValue("local"));
  fireEvent.change(screen.getByLabelText(/Whisper Backend/i), { target: { value: "openai" } });
  fireEvent.click(screen.getByRole("button", { name: /Save/i }));
  await waitFor(() => expect(fetch).toHaveBeenCalledWith(
    expect.stringContaining("/api/config"), expect.objectContaining({ method: "PUT" }),
  ));
});
