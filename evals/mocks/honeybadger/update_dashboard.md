---
expect:
  project_id: number
  dashboard_id: string
---

{"created_at":"2026-08-20T15:02:11.410Z","default_ts":"P1D","id":"{{input.dashboard_id}}","is_default":true,"links":{"web":"https://app.honeybadger.io/projects/{{input.project_id}}/insights/dashboards/shop-overview-{{input.dashboard_id}}"},"project_id":{{input.project_id}},"shared":true,"title":"Shop Overview","updated_at":"2026-10-08T12:00:00Z","widgets":{{input.widgets}}}
