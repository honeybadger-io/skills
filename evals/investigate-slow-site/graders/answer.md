---
type: llm
---
PASS if the final answer (1) names GET /search (SearchController#index) as where the slowdown started, with numbers; (2) gives the cause: a surge of Googlebot requests to /search (about 90% of that traffic) ran the slow product search query (the ILIKE query on products) thousands of times and loaded the database, which also slowed other pages; (3) says there was no deploy and no error spike behind it; AND (4) proposes a concrete fix, such as keeping crawlers off /search (robots.txt, rate limiting) and/or making the search query cheaper (an index or full-text search).
FAIL if it blames a deploy or an error, stops at "search was slow" without the traffic source, or gives no fix.
