# BuildYourPC v16 — Result Rendering Fix

Fixed the blank-results regression reported on mobile.

Root cause: the renderer required `result.query` and silently returned when older backend responses did not echo the request metadata.

Fixes:
- Frontend attaches the request payload to successful recommendation responses when `query` is missing.
- `renderResults()` now reconstructs query metadata from current state instead of hiding a valid result.
- Backend always returns `query` metadata as a final response guard.
- Cache-busting version updated from v15 to v16.

Validation:
- Python syntax OK
- JavaScript syntax OK
