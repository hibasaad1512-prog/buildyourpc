# BuildMyPC stabilization patch

## Fixed
- Language switching now updates the actual interface text, title, placeholders, RTL direction, and persists per browser/device via localStorage.
- English, French, Arabic, and Spanish have full UI translations for the main experience. Other listed languages use a clear English fallback instead of showing broken translation keys.
- Currency formatting follows the selected UI language and selected currency.
- Algeria is mapped to DZD and Moroccan markets to MAD.
- Live FX values are bootstrapped/cached when available, with local fallbacks for core currencies.
- Intermittent SQLite locking risk reduced with WAL, busy timeout, and foreign key enforcement.
- Recommendation errors now return meaningful structured API responses and are logged server-side instead of surfacing as generic server failures.
- Frontend API parsing reports unexpected/non-JSON success responses safely and logs a useful preview for debugging.
- Marketplace options are no longer Amazon-only: global and regional search links now include Facebook Marketplace, eBay, AliExpress, Jumia, Mercado Libre, Noon, Newegg, Best Buy, Walmart, Micro Center, B&H, Takealot, Coupang, Gmarket, Shopee, Lazada, Fnac, LDLC, Currys, PCComponentes, MediaMarkt, Mindfactory, Caseking, and more where relevant to the selected country.
- Live retailer prices remain separate from marketplace search links; search links never pretend to be live prices.
- Double-submit prevention remains enabled for recommendation/save/share actions.

## Validation performed
- Python syntax compilation passed for backend and tools.
- JavaScript syntax check passed with `node --check frontend/app.js`.
- Static regression checks confirmed DZD configuration and marketplace integrations are present.

## Environment limitation
A full Flask/HTTP browser integration test could not be executed in this environment because Flask is not installed and package installation is unavailable. The project still declares its production dependencies in `requirements.txt` for Render deployment.
