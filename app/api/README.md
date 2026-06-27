# Future API boundary

FastAPI is intentionally excluded from the MVP. A future API may expose
`GET /health` and `POST /run-report` by calling `ResearchService`; it must not
duplicate workflow or node logic.

