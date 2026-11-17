# Client library docs

Install and configuration steps live in the Honeybadger docs, not in this skill. Every docs
page is also served as Markdown: drop the trailing slash and append `.md`
(`/lib/ruby/` → `/lib/ruby.md`). The full catalog, including a complete reference per
library, is https://docs.honeybadger.io/llms.txt.

## Pick the page

When several rows match, use the most specific framework (Rails over Ruby, Next.js over
React or Node.js, Laravel over PHP, Django over Python, Go HTTP over Go). If nothing matches, start from the
library's root page (`/lib/<language>.md`) or https://docs.honeybadger.io/lib/other.md.

| Platform | Detect from | Docs |
| --- | --- | --- |
| Rails | `rails` in `Gemfile` | [Rails](https://docs.honeybadger.io/lib/ruby/integration-guides/rails-exception-tracking.md) |
| Sinatra | `sinatra` in `Gemfile` | [Sinatra](https://docs.honeybadger.io/lib/ruby/integration-guides/sinatra-exception-tracking.md) |
| Hanami | `hanami` in `Gemfile` | [Hanami](https://docs.honeybadger.io/lib/ruby/integration-guides/hanami-exception-tracking.md) |
| Rack | `config.ru` without a more specific framework | [Rack](https://docs.honeybadger.io/lib/ruby/integration-guides/rack-exception-tracking.md) |
| Ruby on AWS Lambda | Ruby runtime in `serverless.yml` or `template.yaml` | [AWS Lambda](https://docs.honeybadger.io/lib/ruby/integration-guides/aws-lambda-exception-tracking.md) |
| Ruby | `Gemfile`, `*.gemspec` | [Ruby](https://docs.honeybadger.io/lib/ruby/integration-guides/ruby-exception-tracking.md) |
| Next.js | `next` | [Next.js](https://docs.honeybadger.io/lib/javascript/integration/nextjs.md) |
| React Native | `react-native`, `expo` | [React Native](https://docs.honeybadger.io/lib/javascript/integration/react-native.md) |
| React | `react` without a more specific framework | [React](https://docs.honeybadger.io/lib/javascript/integration/react.md) |
| Vue 3 | `vue` 3.x | [Vue 3](https://docs.honeybadger.io/lib/javascript/integration/vue3.md) |
| Vue 2 | `vue` 2.x | [Vue 2](https://docs.honeybadger.io/lib/javascript/integration/vue2.md) |
| Angular | `@angular/core` | [Angular](https://docs.honeybadger.io/lib/javascript/integration/angular.md) |
| Ember | `ember-source` | [Ember](https://docs.honeybadger.io/lib/javascript/integration/ember.md) |
| Stimulus | `@hotwired/stimulus` | [Stimulus](https://docs.honeybadger.io/lib/javascript/integration/stimulus.md) |
| Node.js | `package.json` for a server without a more specific framework | [Node.js](https://docs.honeybadger.io/lib/javascript/integration/node.md) |
| Chrome extension | `manifest.json` with `manifest_version` | [Chrome extension](https://docs.honeybadger.io/lib/javascript/integration/chrome-extension.md) |
| Browser JavaScript | Plain JS, static sites, CDN script | [Browser](https://docs.honeybadger.io/lib/javascript/integration/browser.md) |
| Lumen | `laravel/lumen-framework` in `composer.json` | [Lumen](https://docs.honeybadger.io/lib/php/integration/lumen.md) |
| Laravel | `laravel/framework` in `composer.json` | [Laravel](https://docs.honeybadger.io/lib/php/integration/laravel.md) |
| WordPress | `wp-config.php`, `wp-content/` | [WordPress](https://docs.honeybadger.io/lib/php/integration/wordpress.md) |
| PHP | `composer.json` | [PHP](https://docs.honeybadger.io/lib/php/integration/other.md) |
| Django | `django` | [Django](https://docs.honeybadger.io/lib/python/integrations/django.md) |
| Flask | `flask` | [Flask](https://docs.honeybadger.io/lib/python/integrations/flask.md) |
| Python (incl. FastAPI, Starlette, Celery, AWS Lambda) | `requirements.txt`, `pyproject.toml`, `Pipfile`, `uv.lock` | [Python](https://docs.honeybadger.io/lib/python/integrations/other.md) |
| Phoenix or Plug | `phoenix` or `plug` in `mix.exs` | [Phoenix](https://docs.honeybadger.io/lib/elixir/integrations/phoenix.md) |
| Elixir | `mix.exs` | [Elixir](https://docs.honeybadger.io/lib/elixir/integrations/other.md) |
| Go HTTP server | `go.mod`, and the app serves `net/http` handlers (directly or through a router such as chi or gorilla/mux) | [Go HTTP](https://docs.honeybadger.io/lib/go/integrations/http.md) |
| Go | `go.mod` (CLIs, workers, anything else) | [Go](https://docs.honeybadger.io/lib/go/integrations/other.md) |
| Java | `pom.xml`, `build.gradle` (non-Android) | [Java](https://docs.honeybadger.io/lib/java.md) |
| .NET | `*.csproj`, `*.sln` | [.NET](https://docs.honeybadger.io/lib/dotnet.md) |
| Apple (iOS, macOS, visionOS) | `Package.swift`, `Podfile`, `*.xcodeproj` | [Cocoa](https://docs.honeybadger.io/lib/cocoa.md) |
| Crystal | `shard.yml` | [Crystal](https://docs.honeybadger.io/lib/crystal.md) |
| Clojure | `project.clj`, `deps.edn` | [Clojure](https://docs.honeybadger.io/lib/clojure.md) |

## Beyond install

Follow links from the platform page rather than guessing URLs. Under each library's path:

- `errors/` — context, breadcrumbs, environments, filtering sensitive data, reducing noise,
  deployment tracking
- `insights/` — automatic instrumentation, logs, custom events
- The configuration reference — every option, including region-specific endpoints and the
  switch for reporting from development environments

## Readable backtraces

- JavaScript source maps: https://docs.honeybadger.io/lib/javascript/errors/using-source-maps.md
- Apple dSYMs: https://docs.honeybadger.io/lib/cocoa/errors/using-dsyms.md
