# Live price setup

BuildYourPC keeps its core recommendation engine free of paid AI dependencies. Live pricing is optional and uses official/authorized sources.

## Supported live providers in this build

- **eBay Browse API** — searches live purchasable listings using an application access token. eBay documents that Browse API search methods require an application access token via client-credentials flow. https://developer.ebay.com/develop/api/buy/browse_api
- **Best Buy Products API** — provides product pricing and availability. Best Buy documents near-real-time product pricing and API rate limits; its commerce/API terms apply. https://developer.bestbuy.com/apis and https://developer.bestbuy.com/legal
- **JSON-LD product pages** — optional, explicit product URLs only. The app parses Schema.org Product/Offer JSON-LD from URLs you explicitly configure. Do not use this against sites whose terms/robots prohibit automated fetching.

## Environment variables

Set in Render (never in frontend code):

```text
ADMIN_TOKEN=choose-a-long-random-secret
EBAY_CLIENT_ID=...
EBAY_CLIENT_SECRET=...
EBAY_MARKETPLACE_ID=EBAY_US
BESTBUY_API_KEY=...
LIVE_PRICE_SYNC_ENABLED=1
FX_API_ENABLED=1
```

Frankfurter is used for cached daily FX data without an API key. https://frankfurter.dev/

## Syncing prices

Manual/CLI:

```bash
python tools/sync_live_prices.py --country US --providers ebay,bestbuy
```

Protected API (use from an external scheduler or your own admin tooling):

```http
POST /api/admin/sync-live
X-Admin-Token: YOUR_ADMIN_TOKEN
Content-Type: application/json

{"country":"US","providers":["ebay","bestbuy"]}
```

This endpoint is intentionally protected. On Render Free, the web service may sleep; a periodic external scheduler can wake it and call this endpoint. Do not create aggressive minute-level polling; daily or several-times-daily sync is sufficient for price display.

## Freshness policy

Fresh live offers override the reference/demo catalog. The app marks live prices stale after the configured window (`LIVE_PRICE_MAX_AGE_HOURS`, default 48h), then falls back to clearly labeled reference prices instead of pretending old data is current.

## Important data-quality rule

The app never claims a price is live unless it came from a configured live source. Affiliate links are optional and must be supplied only when you have the right to use them.
