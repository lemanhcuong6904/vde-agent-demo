# Chart Agent demo

This plugin converts exact, version-pinned VHop demo artifacts into validated chart
specifications. It never queries the warehouse at runtime and never calls upstream
agents. Copy `.env.example` to `.env`, supply `OPENAI_API_KEY`, then set
`LLM_MODEL=gpt-4o-mini` (the default) to use OpenAI for bounded visual-language
suggestions.

The deterministic core remains authoritative for values, scope, validation, chart
compatibility, fallback, hashes and persistence.
