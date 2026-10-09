---
expect:
  project_id: number
  name: string
  schedule_type: [simple, cron]
---

{"id":"Vb2Kq9","name":"{{input.name}}","slug":"{{input.slug}}","state":"pending","schedule_type":"{{input.schedule_type}}","report_period":"{{input.report_period}}","grace_period":"{{input.grace_period}}","cron_schedule":"{{input.cron_schedule}}","cron_timezone":"{{input.cron_timezone}}","reported_at":null,"expected_at":null,"missed_count":0,"url":"https://api.honeybadger.io/v1/check_in/Vb2Kq9","details_url":"https://app.honeybadger.io/projects/{{input.project_id}}/check_ins"}
