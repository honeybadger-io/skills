# Errors

## The error model

Honeybadger groups error occurrences by fingerprint: a *fault* is one unique error within a project, and each occurrence of it is a *notice*. A fault carries the error class, message, component/action, environment, tags, and an optional assignee; its notices carry the occurrence details (backtrace, request, params, context, session, hostname, revision).

## Lifecycle and states

- **Unresolved** — the default state; the error is open.
- **Resolved** — marked fixed. If the error occurs again it automatically REOPENS and a notification is sent. By default a deploy also auto-resolves every open error in its environment (`resolve_errors_on_deploy`, on by default, per-project).
- **Ignored** — new occurrences are DISCARDED (not recorded as notices) and never notify, until unignored.
- **Paused** — notifications are snoozed. Occurrences ARE still recorded.
- **Pending resolution** — marked to resolve automatically at the next deploy.
- **Assigned** — a user owns the fault.

## Search

- Combine filters with spaces (AND). Repeating a key ORs its values.
- Bare terms full-text search the error class and message.
- Negate a filter with a leading `-`: `-is:resolved`.
- Quote values containing spaces: `message:"undefined method"`.
- `component#action` is shorthand for `component:X action:Y`.

### Filter reference

`class`, `component`, `action`, `environment`, `is:assigned`, `is:ignored`, `is:resolved`, `is:paused`, `is:pending_resolution`, `has:comment`, `tag`, `assignee`, `created`, `created.before`, `created.after`, `last_occurred.before`, `last_occurred.after`, `occurred`, `message`, `file`, `hostname`, `revision`, `request.*`, `params.*`, `context.*`, `session.*`.

### Semantics and traps

- The default error list excludes resolved and ignored faults. A search for "what's broken" should include `-is:resolved -is:ignored`.
- Never invent filter keys. An unrecognized filter silently becomes a full-text search.
- There is NO sort token. Sorting is the separate `order` parameter (`recent`, `frequent`).
- For relative periods, use the `.after:` forms: `last_occurred.after:"24 hours ago"`.
