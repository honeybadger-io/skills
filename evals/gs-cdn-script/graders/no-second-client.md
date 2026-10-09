---
type: llm
---
PASS if the answer notices that app/index.html already loads honeybadger.js from the CDN and configures it, and does not add a second Honeybadger client (such as the @honeybadger-io/js or @honeybadger-io/ember npm package) alongside it. Suggesting to replace the CDN script with the npm package, clearly as a replacement, is fine.
FAIL if it adds an npm Honeybadger package while keeping the CDN script, or does not notice the CDN script.
