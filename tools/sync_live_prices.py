from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app import sync_live_prices  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync live prices from configured official/affiliate APIs.")
    parser.add_argument("--country", default="US")
    parser.add_argument("--providers", default="ebay,bestbuy")
    parser.add_argument("--products", default="", help="Comma-separated catalog product IDs; empty means all eligible products.")
    args = parser.parse_args()
    providers = [x.strip().lower() for x in args.providers.split(",") if x.strip()]
    products = [x.strip() for x in args.products.split(",") if x.strip()] or None
    result = sync_live_prices(args.country.upper(), products, providers)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
