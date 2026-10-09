---
expect:
  project_id: number
  name: string
  query: string
  evaluation_period: string
  lookback_lag: string
  trigger_config: string
---

Created alarm nW4xC7yQ2tLa "{{input.name}}" in project {{input.project_id}}. State: initial (first evaluation at the next {{input.evaluation_period}} boundary). evaluation_period: {{input.evaluation_period}}, lookback_lag: {{input.lookback_lag}}, trigger_config: {{input.trigger_config}}. The query was saved exactly as submitted. URL: https://app.honeybadger.io/projects/{{input.project_id}}/insights/alarms/nW4xC7yQ2tLa
