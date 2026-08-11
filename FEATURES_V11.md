# BuildMyPC v11 — Experience Upgrade

Built on `BuildMyPC-final-v10-no-accounts.zip`.

## Added
- Price Hunt panel for every recommendation.
- Search-all-stores modal using the existing marketplace search URLs and live/reference offer data.
- Build Score with overall, performance, compatibility, upgradeability, and budget-fit signals.
- Why this build explanation based on the server-side recommendation.
- Compatible lower-cost alternatives for desktop parts.
- Richer result cards, mobile layout, RTL support, hover/motion polish, and a premium-style visual hierarchy.

## Intentionally not added
- No user accounts.
- No login/signup.
- No user database.
- No Premium subscription/payment flow.

## Validation
- Python syntax checked for all `.py` files.
- JavaScript syntax checked for all `.js` files.
- Final ZIP created after the changes.
- Flask runtime was not started in this build environment because the runtime dependencies are not installed here; they remain declared in `requirements.txt` for deployment.
