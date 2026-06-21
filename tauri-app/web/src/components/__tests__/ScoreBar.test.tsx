import { render, screen } from "@testing-library/react";
import { ScoreBar } from "../ScoreBar";

test("renders label and score percentage", () => {
  render(<ScoreBar label="Quality" score={0.75} />);
  expect(screen.getByText("Quality")).toBeInTheDocument();
  expect(screen.getByText("75%")).toBeInTheDocument();
});

test("renders teal bar with correct width", () => {
  const { container } = render(<ScoreBar label="Quality" score={0.5} />);
  const bar = container.querySelector(".bg-accent-teal");
  expect(bar).toHaveStyle({ width: "50%" });
});
