# Security notes

- Keep `ADMIN_TOKEN` server-side and use a long random value.
- Never expose retailer credentials, affiliate management keys, database passwords or AI keys in frontend files.
- Restrict `CORS_ORIGINS` in production to the real frontend origin(s).
- Validate every imported price row and only import data from verified sources.
- Never scrape a retailer against its terms.
- Use parameterized SQL (the app does).
- If authentication is added later, hash passwords with a strong password-hashing function and add CSRF protection to state-changing browser routes.
- Add a real background scheduler for price-watch alerts rather than relying on request traffic.
- Move from SQLite to managed PostgreSQL before meaningful public traffic.
