---
type: llm
---
PASS if the final answer proposes a dashboard with at least three widgets about checkout health (for example checkout request volume, checkout error or 500 count, checkout response time, or Faraday::TimeoutError notices), gives each widget a title, a view, and a grid position on the 12-column grid with no two widgets overlapping and no widget whose x + w exceeds 12, and asks for the user's go-ahead before creating it.
FAIL if it creates the dashboard without asking, proposes fewer than three widgets, gives no layout, or the layout overlaps or overflows the grid.
