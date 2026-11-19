---
expect:
  project_id: number
  dashboard_id: string
  title: string
  widgets: string
---

Updated dashboard {{input.dashboard_id}} "{{input.title}}" in project {{input.project_id}}. The widgets were saved exactly as submitted: widgets with an id were updated in place, and widgets without one were created and assigned ids. URL: https://app.honeybadger.io/projects/{{input.project_id}}/insights/dashboards/shop-overview-{{input.dashboard_id}}
