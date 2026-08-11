from __future__ import annotations

import ipaddress
import json
import os
import re
import socket
import time
from dataclasses import dataclass
from html import unescape
from typing import Any
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup


USER_AGENT = os.getenv(
    "PRICE_SYNC_USER_AGENT",
    "BuildYourPC/1.0 (+https://buildyourpc.example; price-sync)",
)
REQUEST_TIMEOUT = float(os.getenv("PRICE_SYNC_TIMEOUT", "10"))
LIVE_MAX_AGE_HOURS = float(os.getenv("LIVE_PRICE_MAX_AGE_HOURS", "48"))


@dataclass
class Offer:
    store: str
    price: float
    currency: str
    url: str
    availability: str = "unknown"
    source: str = "live"
    captured_at: str | None = None
    title: str = ""


def _is_private_host(hostname: str) -> bool:
    try:
        infos = socket.getaddrinfo(hostname, None)
    except Exception:
        return True
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return True
    return False


def validate_public_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only public http(s) URLs are allowed.")
    if _is_private_host(parsed.hostname):
        raise ValueError("Private/local destinations are blocked.")
    return url


def http_get(url: str, *, headers: dict[str, str] | None = None, params: dict[str, Any] | None = None) -> requests.Response:
    validate_public_url(url)
    merged = {"User-Agent": USER_AGENT, "Accept": "text/html,application/json;q=0.9,*/*;q=0.5"}
    if headers:
        merged.update(headers)
    response = requests.get(url, headers=merged, params=params, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    response.raise_for_status()
    return response


def _money(value: Any) -> float | None:
    try:
        n = float(str(value).replace(",", "").strip())
        return n if n >= 0 else None
    except (TypeError, ValueError):
        return None


def _availability(value: Any) -> str:
    text = str(value or "").lower()
    if "instock" in text or "in stock" in text or "available" in text:
        return "in_stock"
    if "outofstock" in text or "out of stock" in text:
        return "out_of_stock"
    return "unknown"


def parse_jsonld_product(html: str, page_url: str, store_name: str) -> list[Offer]:
    soup = BeautifulSoup(html, "html.parser")
    offers: list[Offer] = []

    def walk(obj: Any) -> None:
        if isinstance(obj, list):
            for item in obj:
                walk(item)
            return
        if not isinstance(obj, dict):
            return
        typ = obj.get("@type")
        types = typ if isinstance(typ, list) else [typ]
        if "Product" in types:
            raw_offers = obj.get("offers")
            raw_offers = raw_offers if isinstance(raw_offers, list) else [raw_offers]
            for raw in raw_offers:
                if not isinstance(raw, dict):
                    continue
                price = _money(raw.get("price", raw.get("lowPrice")))
                currency = str(raw.get("priceCurrency") or "USD").upper()
                if price is None:
                    continue
                url = raw.get("url") or page_url
                availability = _availability(raw.get("availability"))
                offers.append(Offer(store=store_name, price=price, currency=currency, url=url, availability=availability, source="jsonld", title=str(obj.get("name") or "")))
        for value in obj.values():
            if isinstance(value, (dict, list)):
                walk(value)

    for script in soup.find_all("script", attrs={"type": re.compile(r"application/ld\\+json", re.I)}):
        raw = script.string or script.get_text(" ", strip=True)
        if not raw:
            continue
        raw = unescape(raw)
        try:
            walk(json.loads(raw))
        except Exception:
            # Some sites embed multiple JSON objects or JS comments; ignore malformed blocks.
            continue
    return offers


def fetch_jsonld_offer(url: str, store_name: str) -> list[Offer]:
    response = http_get(url)
    offers = parse_jsonld_product(response.text, response.url, store_name)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for offer in offers:
        offer.captured_at = now
    return offers


class EbayClient:
    def __init__(self) -> None:
        self.client_id = os.getenv("EBAY_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("EBAY_CLIENT_SECRET", "").strip()
        self.marketplace = os.getenv("EBAY_MARKETPLACE_ID", "EBAY_US").strip() or "EBAY_US"
        self._token: str | None = None
        self._token_expiry = 0.0

    @property
    def enabled(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def token(self) -> str:
        if self._token and time.time() < self._token_expiry - 30:
            return self._token
        raw = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        import base64
        basic = base64.b64encode(raw).decode("ascii")
        response = requests.post(
            "https://api.ebay.com/identity/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        self._token = data["access_token"]
        self._token_expiry = time.time() + float(data.get("expires_in", 7200))
        return self._token

    def search(self, query: str, limit: int = 8) -> list[Offer]:
        if not self.enabled:
            return []
        token = self.token()
        response = requests.get(
            "https://api.ebay.com/buy/browse/v1/item_summary/search",
            headers={
                "Authorization": f"Bearer {token}",
                "X-EBAY-C-MARKETPLACE-ID": self.marketplace,
                "Accept": "application/json",
            },
            params={"q": query, "limit": limit, "filter": "buyingOptions:{FIXED_PRICE}"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        out: list[Offer] = []
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        for item in data.get("itemSummaries", []):
            price = item.get("price") or {}
            value = _money(price.get("value"))
            if value is None:
                continue
            out.append(
                Offer(
                    store="eBay",
                    price=value,
                    currency=str(price.get("currency") or "USD"),
                    url=item.get("itemWebUrl") or "https://www.ebay.com/",
                    availability="in_stock",
                    source="ebay-api",
                    captured_at=now,
                    title=str(item.get("title") or ""),
                )
            )
        return out


class BestBuyClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("BESTBUY_API_KEY", "").strip()

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, limit: int = 8) -> list[Offer]:
        if not self.enabled:
            return []
        response = requests.get(
            "https://api.bestbuy.com/v1/products",
            params={
                "apiKey": self.api_key,
                "format": "json",
                "pageSize": limit,
                "search": query,
                "show": "name,sku,salePrice,regularPrice,url,onlineAvailability",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        out: list[Offer] = []
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        for item in data.get("products", []):
            value = _money(item.get("salePrice", item.get("regularPrice")))
            if value is None:
                continue
            out.append(
                Offer(
                    store="Best Buy",
                    price=value,
                    currency="USD",
                    url=item.get("url") or "https://www.bestbuy.com/",
                    availability="in_stock" if item.get("onlineAvailability") else "unknown",
                    source="bestbuy-api",
                    captured_at=now,
                    title=str(item.get("name") or ""),
                )
            )
        return out


def token_overlap(query: str, title: str) -> float:
    stop = {"the", "and", "for", "with", "gb", "gaming", "desktop", "pc", "kit", "new"}
    q = {x for x in re.findall(r"[a-z0-9]+", query.lower()) if x not in stop and len(x) >= 2}
    t = {x for x in re.findall(r"[a-z0-9]+", title.lower()) if x not in stop and len(x) >= 2}
    if not q:
        return 0.0
    return len(q & t) / len(q)


def best_matching_offers(query: str, offers: list[Offer], *, limit: int = 4, threshold: float = 0.34) -> list[Offer]:
    # Keep only results that share enough model/brand tokens with the requested product.
    scored = [(token_overlap(query, o.title or query), o) for o in offers]
    filtered = [o for score, o in scored if score >= threshold or not o.title]
    unique: dict[tuple[str, float, str], Offer] = {}
    for offer in filtered:
        key = (offer.store, round(offer.price, 2), offer.url)
        unique[key] = offer
    return sorted(unique.values(), key=lambda x: x.price)[:limit]
