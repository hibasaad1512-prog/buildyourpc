# BuildYourPC

A premium, global-first PC/laptop/prebuilt recommendation experience. The user gives a budget and optional goals; the recommendation engine builds a sensible option and compares available offers.

## What is live in this build

- Elegant black + purple responsive UI (mobile + desktop).
- Wizard-style discovery where only budget is required.
- Desktop, laptop, prebuilt, custom and used/refurbished flows.
- Recommendation engine with compatibility checks and a budget-first scoring philosophy.
- FPS treated as a floor/goal rather than a reason to overspend.
- Smart Buy / Speed Demon / The Beast variants.
- What-if reruns for budget, FPS, quietness and future-proofing.
- Shareable builds and exploration feed.
- Store offer cards with freshness/live labels.
- Price history storage and price-watch storage.
- Admin page for feed imports, live sync and FX refresh.
- Sitemap and SEO metadata.
- Ko-fi support button.

## Live price strategy

The project does **not** pretend its bundled reference catalog is live pricing. When fresh official/authorized data exists, it overrides the reference catalog.

Configured live connectors:

1. eBay Browse API (application access token / client credentials).
2. Best Buy Products API.
3. Optional JSON-LD Product/Offer parsing for explicitly configured public product URLs where automated fetching is permitted.
4. CSV merchant/affiliate feeds via `tools/import_price_feed.py`.

### Render variables

See `.env.example`. Put API credentials in Render environment variables only. Never ship them in frontend code.

### Live sync

Manual CLI:

```bash
python tools/sync_live_prices.py --country US --providers ebay,bestbuy
```

Protected endpoint:

```http
POST /api/admin/sync-live
X-Admin-Token: YOUR_ADMIN_TOKEN
Content-Type: application/json
{"country":"US","providers":["ebay","bestbuy"]}
```

Because Render Free can sleep, call the protected endpoint from a gentle external scheduler (for example once or a few times per day). Do not poll every minute.

### Price freshness

Fresh live rows older than `LIVE_PRICE_MAX_AGE_HOURS` are not presented as current. The UI falls back to clearly labeled reference offers instead.

## Global FX

The app can refresh cached currency rates from Frankfurter without an API key. The bundled FX table remains a fallback for offline use.

## Development

Install dependencies with:

```bash
pip install -r requirements.txt
```

Run locally:

```bash
python -m backend.app
```

Render start command:

```bash
gunicorn backend.app:app
```


## Accounts & Premium foundation

The site now includes a first-party account system built on SQLite:

- Email + password registration/login with server-side password hashing.
- Secure HTTP-only session cookie with configurable lifetime (`SESSION_DAYS`, default 30).
- Logged-in users automatically associate newly saved builds with their account.
- Account modal with saved-build history and favorites API.
- Premium feature gating is implemented as a launch-safe feature flag.
- `PREMIUM_AVAILABLE=0` keeps Premium in coming-soon mode; set it to `1` only when billing/entitlements are ready.
- Premium access is never granted just because the client claims it is enabled; the server checks the account entitlement.

Auth endpoints:
`GET /api/auth/me`, `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`.

Account endpoints:
`GET /api/account/builds`, `GET /api/account/favorites`, `POST /api/account/favorites`.

Premium endpoints:
`GET /api/premium/status`, `GET /api/premium/feature/<feature>`.

For production, keep the frontend/API same-origin where possible. If deploying the frontend separately, configure `CORS_ORIGINS` with the exact trusted origin(s) and keep HTTPS enabled.
