import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import userEvent from "@testing-library/user-event";
import { FileEditor } from "../FileEditor";

(window as any).__LC_PORT__ = 5001;

// Mock Monaco (heavy, not needed for unit test)
vi.mock("@monaco-editor/react", () => ({
  default: ({ value }: { value: string }) => (
    <textarea data-testid="monaco" defaultValue={value} />
  ),
}));

test("renders path input and file tree heading", async () => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => [{ name: "app.py", path: "/p/app.py", is_dir: false }],
  } as any);

  render(<MemoryRouter><FileEditor /></MemoryRouter>);
  const input = screen.getByPlaceholderText(/path/i);
  expect(input).toBeInTheDocument();

  await userEvent.type(input, "/p");
  await userEvent.keyboard("{Enter}");
  await waitFor(() =>
    expect(screen.getByText("app.py")).toBeInTheDocument()
  );
});
