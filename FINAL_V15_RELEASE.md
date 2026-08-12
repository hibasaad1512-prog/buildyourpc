# BuildYourPC v15 — Foundation Complete

This is the final foundation release before real payment work.

## Product experience
- Build Doctor: final practical compatibility and buying checks.
- Shopping Confidence: tells users how much of the build has verified live price coverage.
- Budget Lab: shows a data-driven “spend a little more” and “save a little” direction.
- Setup Plan: separates core hardware from cooler, thermal paste, airflow, monitor, OS and peripherals.
- Refresh Prices: reruns the recommendation to refresh live market data when configured.
- Print / Save as PDF: browser print flow with a dedicated clean report stylesheet.
- Single in-app store comparison modal: no multi-popup retailer spam.
- Stronger PC snapshot and power/cooling context.
- Compact project support card remains optional and unobtrusive.

## Compatibility/catalog foundation
- Added reference catalog entries for CPU coolers, thermal paste, case fans, 2TB NVMe and 32GB DDR4.
- Desktop selection now includes a compatible CPU cooler instead of leaving cooling as a hidden afterthought.
- Cooler socket compatibility is enforced during selection and budget fallback.
- Live sync can include CPU coolers.
- Catalog stores now have numeric reference prices so JSON sorting and fallback logic stay safe.

## Pricing policy
- LIVE means a fresh offer from an enabled provider/feed.
- SEARCH means a retailer/marketplace search link without a verified captured price.
- REFERENCE means a local catalog reference and is never presented as a live price.
- BuildYourPC does not claim to know the absolute cheapest listing on the entire web.

## Reliability / QA
- All project JSON files parse successfully.
- Python syntax checks pass.
- JavaScript syntax checks pass with Node.
- Catalog product ids are unique and required fields are validated.
- Runtime smoke tests passed for desktop, laptop, prebuilt, USD and MAD cases.
- The final response payloads successfully serialize to JSON.
- No account/login/payment system is included in this foundation release.

## Payment stage intentionally postponed
This release does not add real payment processing. Payment can be layered on after this foundation is accepted and the checkout provider is chosen.
