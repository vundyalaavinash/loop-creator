import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Builder } from "../Builder";

(window as any).__LC_PORT__ = 5001;
global.fetch = vi.fn().mockResolvedValue({ json: async () => [] } as any);

test("renders all 7 form sections", () => {
  render(<MemoryRouter><Builder /></MemoryRouter>);
  expect(screen.getByText(/Loop Type/i)).toBeInTheDocument();
  expect(screen.getAllByText(/Task/i)[0]).toBeInTheDocument();
  expect(screen.getAllByText(/Goal/i)[0]).toBeInTheDocument();
  expect(screen.getAllByText(/Context/i)[0]).toBeInTheDocument();
  expect(screen.getAllByText(/Generator/i)[0]).toBeInTheDocument();
  expect(screen.getByText(/GEPA Params/i)).toBeInTheDocument();
  expect(screen.getByText(/Preview/i)).toBeInTheDocument();
});

test("Save button is present", () => {
  render(<MemoryRouter><Builder /></MemoryRouter>);
  expect(screen.getByText("Save")).toBeInTheDocument();
});
