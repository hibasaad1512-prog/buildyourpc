# BuildYourPC AdSense setup

The Google AdSense publisher snippet is installed in `frontend/index.html`.

The project deliberately does **not** enable Auto ads. There is one responsive banner location near the bottom of the page. It stays hidden until you set a real AdSense **ad unit slot ID** in the page.

Set `window.BUILDYOURPC_ADSENSE_SLOT_ID` to the slot ID Google gives you for the display ad unit. Do not invent the slot ID.

`frontend/ads.txt` contains the publisher authorization entry for `ca-pub-3776235953985777`.
