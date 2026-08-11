# BuildMyPC final stabilization patch

## Language system
- Language selection is stored in `localStorage` per browser/device; changing language on one device does not change another device.
- The picker only exposes locales with complete UI packs currently bundled, preventing the previous 90% translated / 10% English mixed-language state.
- Full UI packs are bundled for English, French, Arabic, Spanish, German, Italian, Portuguese, Turkish, Russian, Japanese, Korean, Chinese, Polish, Dutch, and Hindi.
- Shared result-card, error, marketplace, save/share, and navigation labels were added to the newer locale packs so they do not silently fall back to English.
- Arabic remains true RTL, including docks, cards, offer rows, actions, and layout alignment.
- Language selection persists after refresh on the same browser/device.

## Laptop recommendation path
- Laptop recommendations now use the laptop catalog only.
- Laptop results render as one complete purchasable laptop product, never as a desktop-component grid.
- Laptop result cards show the product, price, reason, and relevant store/marketplace offers.
- Desktop alternatives are not generated for laptop requests.
- FX/database work that was unnecessarily triggered for USD laptop requests was removed to reduce avoidable server latency/failure paths.

## API/server resilience
- Frontend API calls validate status, content type, body presence, and JSON shape before parsing.
- Non-JSON server responses no longer surface as `Failed JSON`.
- API/network errors are converted to localized user-facing messages while retaining detailed developer logs.
- Flask API 400/404/500 handlers return structured JSON for `/api/*` routes.
- Recommendation validation covers budget, currency, list fields, and FPS input.
- SQLite busy timeout/WAL/foreign-key settings were hardened for Render-style concurrency.
- Analytics/event failures cannot turn a successful user operation into HTTP 500.
- Price lookups fall back safely when the local price table is temporarily locked/unavailable.

## Currency system
- Currency configuration is centralized in `backend/currency_config.py`.
- Algeria is mapped to `DZD` (Algerian Dinar) and Morocco to `MAD`.
- Currency-specific minimum/maximum budget bounds are exported to the frontend.
- Frontend and backend validate finite numbers, supported currency codes, and per-currency bounds.
- `Intl.NumberFormat` is used for currency display according to the selected locale.
- USD avoids unnecessary FX-cache/network initialization.

## Marketplaces
- Marketplace choices are search links, not fake live prices.
- The list includes global platforms and country/region-specific options such as Facebook Marketplace, eBay, AliExpress, Jumia, Avito, Ouedkniss, Tayara, Haraj, Dubizzle, Leboncoin, Kleinanzeigen, Wallapop, Subito, Mercado Libre, Noon, Newegg, Best Buy, Walmart, Micro Center, B&H, Takealot, Jiji, Shopee, Lazada, Cdiscount, LDLC, Fnac, Currys, PCComponentes, MediaMarkt, Mindfactory, Caseking, Skroutz, PcGarage and others where configured.
- Live retailer prices remain separate from search links and only use explicitly configured feeds/APIs.

## Validation performed
- `node --check frontend/app.js` passed.
- Python bytecode compilation passed for the backend modules.
- Static checks confirm centralized currency config, DZD support, laptop-only filtering, portable result rendering, structured API error handling, language persistence, and marketplace mappings.

## Environment limitation
- A full live Flask + browser integration run could not be completed inside this execution environment because Flask is not installed locally and outbound package installation is unavailable. `requirements.txt` remains production-ready for Render deployment.
