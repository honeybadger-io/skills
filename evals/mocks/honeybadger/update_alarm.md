---
expect:
  project_id: number
  alarm_id: string
  name: string
  query: string
  evaluation_period: string
  lookback_lag: string
  trigger_config: string
---

Updated alarm {{input.alarm_id}} "{{input.name}}" in project {{input.project_id}}. evaluation_period: {{input.evaluation_period}}, lookback_lag: {{input.lookback_lag}}, trigger_config: {{input.trigger_config}}. The query was saved exactly as submitted; the alarm re-enters the initial state until its next evaluation. URL: https://app.honeybadger.io/projects/{{input.project_id}}/insights/alarms/{{input.alarm_id}}
