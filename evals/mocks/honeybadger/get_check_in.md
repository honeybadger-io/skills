---
expect:
  project_id: number
  check_in_id: string
---

{"id":"{{input.check_in_id}}","name":"Nightly sales report","slug":"nightly-sales-report","state":"pending","schedule_type":"cron","report_period":null,"grace_period":"30 minutes","cron_schedule":"30 2 * * *","cron_timezone":"UTC","reported_at":null,"expected_at":null,"missed_count":0,"url":"https://api.honeybadger.io/v1/check_in/{{input.check_in_id}}","details_url":"https://app.honeybadger.io/projects/{{input.project_id}}/check_ins"}
