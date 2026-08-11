"""Retailer feed contracts for BuildYourPC.

Use official product feeds, affiliate feeds, merchant APIs, or permitted datasets.
Do not scrape a retailer unless its terms permit it.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import csv
import json


@dataclass(frozen=True)
class Offer:
    store: str
    product_id: str
    name: str
    price: float
    currency: str
    country: str
    url: str
    availability: str = "unknown"
    captured_at: str | None = None
    affiliate_url: str | None = None
    source: str = "feed"


class RetailerProvider:
    name = "abstract"

    def search(self, *, query: str, country: str, currency: str) -> Iterable[Offer]:
        raise NotImplementedError


class CSVProvider(RetailerProvider):
    """Local importer for a retailer CSV export."""
    name = "csv"

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def search(self, *, query: str, country: str, currency: str) -> Iterable[Offer]:
        q = query.lower().strip()
        with self.path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if q and q not in (row.get("name", "") + " " + row.get("product_id", "")).lower():
                    continue
                if row.get("country") not in {country, "*", ""}:
                    continue
                yield Offer(
                    store=row["store"], product_id=row["product_id"], name=row.get("name", row["product_id"]),
                    price=float(row["price"]), currency=row.get("currency", currency), country=row.get("country", country),
                    url=row["product_url"], availability=row.get("availability", "unknown"),
                    captured_at=row.get("captured_at"), affiliate_url=row.get("affiliate_url"), source=row.get("source", "csv"),
                )


class JSONProvider(RetailerProvider):
    """Local importer for a normalized JSON export."""
    name = "json"

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def search(self, *, query: str, country: str, currency: str) -> Iterable[Offer]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        q = query.lower().strip()
        for row in data:
            hay = (row.get("name", "") + " " + row.get("product_id", "")).lower()
            if q and q not in hay:
                continue
            if row.get("country") not in {country, "*", ""}:
                continue
            yield Offer(
                store=row["store"], product_id=row["product_id"], name=row.get("name", row["product_id"]),
                price=float(row["price"]), currency=row.get("currency", currency), country=row.get("country", country),
                url=row["product_url"], availability=row.get("availability", "unknown"),
                captured_at=row.get("captured_at"), affiliate_url=row.get("affiliate_url"), source=row.get("source", "json"),
            )
