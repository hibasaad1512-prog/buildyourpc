# Verified retailer price feeds

BuildYourPC is structured to use official retailer feeds, affiliate feeds, merchant APIs, or other permitted datasets.

Do **not** scrape a store unless its terms permit it.

Use the provided CSV importer with these required columns:

- `product_id`
- `store`
- `country`
- `currency`
- `price`
- `product_url`

Optional:

- `affiliate_url`
- `availability`
- `captured_at`
- `source`

The demo catalog remains available as a transparent fallback until verified feeds are connected.
