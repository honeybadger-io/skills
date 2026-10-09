---
type: regex
pattern: "sync_leads\\.py[^\\n]*&&[^\\n]*curl"
target: last_message
---
The cron line reports with curl, chained after the script with && so a failed run does not report. The URL may be inline or in an environment variable.
