---
type: llm
---
PASS if the final answer proposes one new widget for p95 response time (a BadgerQL query using percentile(95, duration) over request events, with a line, billboard, or similar view), places it on the grid without overlapping the four existing widgets (they fill rows 0 to 8: three widgets at y 0 with h 4 and one full-width widget at y 4 with h 4, so the new widget belongs at y 8 or below), says the four existing widgets (Requests per hour, Server errors, Slowest actions, Errors by class) stay as they are, and asks for the user's go-ahead before saving.
FAIL if it saves without asking, drops, renames, or re-creates an existing widget, proposes no concrete query or layout, or places the new widget where it overlaps an existing one.
