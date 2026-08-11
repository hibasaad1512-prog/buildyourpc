from __future__ import annotations

import csv
import io
import logging
import json
import os
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
from functools import wraps

from werkzeug.security import generate_password_hash, check_password_hash

import requests

from .live_prices import BestBuyClient, EbayClient, LIVE_MAX_AGE_HOURS, fetch_jsonld_offer, best_matching_offers
from .currency_config import CURRENCY_CONFIG, exported_config, get_currency
from .marketplaces import marketplace_offers

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = Path(os.getenv("BUILDYOURPC_DB_PATH", str(DATA_DIR / "buildyourpc.sqlite3"))).expanduser()
CATALOG_PATH = DATA_DIR / "catalog.json"

app = Flask(__name__, static_folder=str(ROOT / "frontend"), static_url_path="")
logger = logging.getLogger(__name__)
app.config["JSON_SORT_KEYS"] = False
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "*")
CORS(app, resources={r"/api/*": {"origins": [x.strip() for x in ALLOWED_ORIGINS.split(",")] if ALLOWED_ORIGINS != "*" else "*", "supports_credentials": True}})

with CATALOG_PATH.open("r", encoding="utf-8") as f:
    CATALOG = json.load(f)

KO_FI_URL = os.getenv("KO_FI_URL", "https://ko-fi.com/simbawwyy00")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
LIVE_PRICE_SYNC_ENABLED = os.getenv("LIVE_PRICE_SYNC_ENABLED", "1") != "0"
FX_API_ENABLED = os.getenv("FX_API_ENABLED", "1") != "0"
# Never make end-user recommendation requests depend on an external FX service.
# Live refresh is an explicit/admin action; normal requests use cached rates or
# the centralized fallback table. This is especially important for Render free.
FX_AUTO_REFRESH = os.getenv("FX_AUTO_REFRESH", "0") == "1"
FX_CACHE_HOURS = float(os.getenv("FX_CACHE_HOURS", "24"))
FX_BOOTSTRAP_DONE = False


FX_TO_USD = {code: float(cfg["rateToUSD"]) for code, cfg in CURRENCY_CONFIG.items()}


def db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=15, isolation_level=None, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout=15000")
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA synchronous=NORMAL")
    return con


def init_db() -> None:
    con = db()
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS builds (
            id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            views INTEGER NOT NULL DEFAULT 0,
            shares INTEGER NOT NULL DEFAULT 0,
            user_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            plan TEXT NOT NULL DEFAULT 'free' CHECK(plan IN ('free','premium')),
            premium_until TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS auth_sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            expires_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_auth_sessions_expiry ON auth_sessions(expires_at);

        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            build_id TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, build_id),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            store TEXT NOT NULL,
            country TEXT NOT NULL,
            currency TEXT NOT NULL,
            price REAL NOT NULL,
            availability TEXT DEFAULT 'unknown',
            product_url TEXT NOT NULL,
            affiliate_url TEXT,
            captured_at TEXT NOT NULL,
            source TEXT DEFAULT 'manual'
        );
        CREATE INDEX IF NOT EXISTS idx_prices_product_country ON prices(product_id, country);
        CREATE TABLE IF NOT EXISTS watchlist (
            id TEXT PRIMARY KEY,
            build_id TEXT,
            product_id TEXT,
            email TEXT,
            threshold REAL,
            currency TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT NOT NULL,
            build_id TEXT,
            product_id TEXT,
            country TEXT,
            meta TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS fx_rates (
            base TEXT NOT NULL,
            quote TEXT NOT NULL,
            rate REAL NOT NULL,
            captured_at TEXT NOT NULL,
            source TEXT NOT NULL,
            PRIMARY KEY(base, quote)
        );
        CREATE TABLE IF NOT EXISTS sync_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT NOT NULL,
            country TEXT,
            requested INTEGER NOT NULL DEFAULT 0,
            imported INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL,
            message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=NORMAL")
    except sqlite3.DatabaseError:
        logger.warning("SQLite WAL mode could not be enabled; continuing with the configured journal mode.")
    # Lightweight migration for databases created before account support.
    try:
        cols = {row[1] for row in con.execute("PRAGMA table_info(builds)").fetchall()}
        if "user_id" not in cols:
            con.execute("ALTER TABLE builds ADD COLUMN user_id INTEGER")
        con.execute("CREATE INDEX IF NOT EXISTS idx_builds_user_id ON builds(user_id)")
    except sqlite3.DatabaseError:
        logger.exception("Could not migrate builds table")
    con.commit()
    con.close()


init_db()

SESSION_COOKIE = "byp_session"
SESSION_DAYS = int(os.getenv("SESSION_DAYS", "30"))
PREMIUM_AVAILABLE = os.getenv("PREMIUM_AVAILABLE", "0") == "1"
PREMIUM_FEATURES = [
    "Advanced price tracking",
    "Build history",
    "Upgrade planner",
    "Advanced compatibility insights",
    "Premium deal ranking",
]


def _iso_after_days(days: int) -> str:
    from datetime import timedelta
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _clean_email(value: Any) -> str:
    return str(value or "").strip().lower()


def _public_user(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if not row:
        return None
    premium_until = row["premium_until"]
    now = datetime.now(timezone.utc).isoformat()
    active = row["plan"] == "premium" and bool(premium_until and premium_until > now)
    return {
        "id": row["id"],
        "email": row["email"],
        "display_name": row["display_name"],
        "plan": "premium" if active else "free",
        "premium_active": active,
        "premium_until": premium_until,
        "created_at": row["created_at"],
    }


def _session_token_from_request() -> str | None:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        return token
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    return None


def current_user() -> sqlite3.Row | None:
    token = _session_token_from_request()
    if not token:
        return None
    con = db()
    row = con.execute(
        """SELECT u.* FROM auth_sessions s
           JOIN users u ON u.id=s.user_id
           WHERE s.token=? AND s.expires_at>?""",
        (token, datetime.now(timezone.utc).isoformat()),
    ).fetchone()
    con.close()
    return row


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    con = db()
    con.execute(
        "INSERT INTO auth_sessions(token,user_id,expires_at) VALUES(?,?,?)",
        (token, user_id, _iso_after_days(SESSION_DAYS)),
    )
    con.commit()
    con.close()
    return token


def delete_session(token: str | None) -> None:
    if not token:
        return
    con = db()
    con.execute("DELETE FROM auth_sessions WHERE token=?", (token,))
    con.commit()
    con.close()


def auth_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify({"error": {"code": "AUTH_REQUIRED", "message": "Please sign in to continue."}}), 401
        return fn(user, *args, **kwargs)
    return wrapped


def premium_required(fn):
    @wraps(fn)
    def wrapped(user, *args, **kwargs):
        public = _public_user(user)
        if not public or not public["premium_active"]:
            return jsonify({"error": {"code": "PREMIUM_REQUIRED", "message": "This feature is reserved for BuildYourPC Premium."}}), 403
        return fn(user, *args, **kwargs)
    return wrapped


def _cached_fx_from_eur() -> dict[str, float]:
    rates: dict[str, float] = {"EUR": 1.0}
    con = db()
    rows = con.execute("SELECT quote, rate, captured_at FROM fx_rates WHERE base='EUR'").fetchall()
    con.close()
    now = datetime.now(timezone.utc)
    for row in rows:
        try:
            captured = datetime.fromisoformat(row["captured_at"].replace("Z", "+00:00"))
            if (now - captured).total_seconds() <= FX_CACHE_HOURS * 3600:
                rates[str(row["quote"]).upper()] = float(row["rate"])
        except Exception:
            continue
    return rates


def _safe_requests_json(response: requests.Response) -> Any:
    content_type = (response.headers.get("content-type") or "").lower()
    body = response.text.strip()
    if not body:
        return {}
    if "json" not in content_type and not body.startswith(("{", "[")):
        raise ValueError("FX provider returned a non-JSON response")
    try:
        return response.json()
    except ValueError as exc:
        raise ValueError("FX provider returned malformed JSON") from exc


def refresh_fx_rates() -> dict[str, float]:
    if not FX_API_ENABLED:
        return {}
    try:
        r = requests.get("https://api.frankfurter.dev/v2/rates", params={"base": "EUR"}, timeout=6)
        r.raise_for_status()
        data = _safe_requests_json(r)
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        con = db()
        for row in data:
            if row.get("quote") and row.get("rate"):
                con.execute(
                    "INSERT INTO fx_rates(base,quote,rate,captured_at,source) VALUES(?,?,?,?,?) ON CONFLICT(base,quote) DO UPDATE SET rate=excluded.rate,captured_at=excluded.captured_at,source=excluded.source",
                    ("EUR", row["quote"].upper(), float(row["rate"]), now, "frankfurter"),
                )
        con.commit(); con.close()
        return _cached_fx_from_eur()
    except Exception:
        return _cached_fx_from_eur()


def ensure_fx_cache() -> None:
    global FX_BOOTSTRAP_DONE
    if FX_BOOTSTRAP_DONE or not FX_API_ENABLED or not FX_AUTO_REFRESH:
        return
    FX_BOOTSTRAP_DONE = True
    if len(_cached_fx_from_eur()) < 5:
        refresh_fx_rates()


def _eur_to_usd() -> float:
    rates = _cached_fx_from_eur()
    return float(rates.get("USD", FX_TO_USD.get("EUR", 0.92) and (1.0 / FX_TO_USD["EUR"])))


def _validated_currency(currency: str) -> str:
    code = str(currency or "USD").upper()
    get_currency(code)
    return code


def usd_from_local(value: float, currency: str) -> float:
    code = _validated_currency(currency)
    if code == 'USD':
        return float(value)
    ensure_fx_cache()
    rates = _cached_fx_from_eur()
    if code in rates and "USD" in rates:
        return (float(value) / rates[code]) * rates["USD"]
    return float(value) / float(CURRENCY_CONFIG[code]["rateToUSD"])


def local_from_usd(value: float, currency: str) -> float:
    code = _validated_currency(currency)
    if code == 'USD':
        return float(value)
    ensure_fx_cache()
    rates = _cached_fx_from_eur()
    if code in rates and "USD" in rates:
        return (float(value) / rates["USD"]) * rates[code]
    return float(value) * float(CURRENCY_CONFIG[code]["rateToUSD"])


def fmt_money(value: float, currency: str) -> float:
    cfg = get_currency(currency)
    return round(local_from_usd(value, currency), int(cfg["decimalDigits"]))


def catalog_products(device: str | None = None, category: str | None = None) -> list[dict[str, Any]]:
    items = CATALOG.get("products", [])
    if device:
        items = [p for p in items if p.get("device") == device]
    if category:
        items = [p for p in items if p.get("category") == category]
    return items


def enrich_catalog() -> None:
    """Assign compatibility attributes to the reference catalog in memory.

    Live imports can supply these fields directly. The reference catalog keeps them
    generic and clearly marked as demo data.
    """
    for p in CATALOG.get("products", []):
        pid = p.get("id", "")
        if p.get("category") == "cpu":
            if pid == "cpu-7600":
                p.update(socket="AM5", memory_type="DDR5", tdp=65, core_class="mid")
            elif pid == "cpu-7800x3d":
                p.update(socket="AM5", memory_type="DDR5", tdp=120, core_class="high")
            else:
                p.update(socket="AM4", memory_type="DDR4", tdp=65, core_class="entry")
        elif p.get("category") == "motherboard":
            if pid == "b650":
                p.update(socket="AM5", memory_type="DDR5", wifi=p.get("wifi", 100), form_factor="ATX")
            else:
                p.update(socket="AM4", memory_type="DDR4", wifi=p.get("wifi", 100), form_factor="mATX")
        elif p.get("category") == "ram":
            p["memory_type"] = "DDR5" if pid == "ram-32" else "DDR4"
        elif p.get("category") == "gpu":
            watts = {"gpu-7800xt": 700, "gpu-4070s": 650, "gpu-7600xt": 550, "gpu-6600": 450}.get(pid, 450)
            p["recommended_psu_w"] = watts
        elif p.get("category") == "psu":
            p["wattage"] = 650 if pid == "psu-650" else 500
        elif p.get("category") == "case":
            p["supports"] = ["ATX", "mATX"]
        elif p.get("category") in {"prebuilt", "laptop", "used"}:
            p.setdefault("condition", "new" if p.get("device") != "used" else "used")
            p.setdefault("warranty_months", 12 if p.get("device") != "used" else 3)


enrich_catalog()


def current_offers(product: dict[str, Any], country: str, currency: str) -> list[dict[str, Any]]:
    offers: list[dict[str, Any]] = []
    try:
        con = db()
        rows = con.execute(
            "SELECT store, price, currency, availability, product_url, affiliate_url, captured_at, source FROM prices WHERE product_id = ? AND country IN (?, '*') ORDER BY price ASC",
            (product["id"], country),
        ).fetchall()
        con.close()
    except sqlite3.DatabaseError as exc:
        logger.warning("price lookup failed for %s/%s: %s", product.get("id"), country, exc)
        rows = []
    now = datetime.now(timezone.utc)
    for row in rows:
        captured_at = row["captured_at"]
        stale = True
        try:
            captured = datetime.fromisoformat(str(captured_at).replace("Z", "+00:00"))
            stale = (now - captured).total_seconds() > LIVE_MAX_AGE_HOURS * 3600
        except Exception:
            pass
        offers.append(
            {
                "store": row["store"],
                "price": round(float(row["price"]), 2),
                "currency": row["currency"],
                "url": row["affiliate_url"] or row["product_url"],
                "availability": row["availability"],
                "affiliate_ready": bool(row["affiliate_url"]),
                "captured_at": captured_at,
                "source": row["source"],
                "stale": stale,
                "live": row["source"] != "reference-demo" and not stale,
            }
        )
    live = [o for o in offers if o["live"]]
    # Always expose market choices even when a live feed exists. Live offers are
    # ranked first; reference and marketplace search links remain clearly labeled.
    reference: list[dict] = []
    existing_names = {str(o.get("store") or "") for o in offers}
    query = quote_plus(product["name"])
    for store in product.get("stores", []):
        market_ok = not store.get("countries") or country in store["countries"] or "*" in store["countries"]
        if not market_ok:
            continue
        # Keep offer prices numeric in the API. Formatting belongs to the frontend;
        # returning strings like "799 MAD" breaks numeric sorting and downstream
        # market-price selection, which was the root cause of laptop/used failures.
        price = round(local_from_usd(float(store["usd_price"]), currency), 2)
        name = store["name"]
        existing_names.add(name)
        reference.append(
            {
                "store": name,
                "price": price,
                "currency": currency,
                "url": store.get("url") or store.get("base_url") or f"https://www.google.com/search?q={query}",
                "availability": store.get("availability", "Reference price — verify store"),
                "affiliate_ready": bool(store.get("affiliate_ready", False)),
                "captured_at": None,
                "source": "reference-demo",
                "stale": False,
                "live": False,
            }
        )
    try:
        marketplace = marketplace_offers(product_name=product["name"], country=country, currency=currency, existing_names=existing_names)
    except Exception as exc:
        logger.warning("marketplace link generation failed for %s/%s: %s", product.get("id"), country, exc)
        marketplace = []
    if live:
        return sorted(live, key=lambda x: float(x.get("price") or 0)) + reference[:2] + marketplace
    return sorted(reference, key=lambda x: float(x.get("price") or 0)) + marketplace


def market_price_usd(product: dict[str, Any], country: str, currency: str) -> tuple[float, bool, str]:
    offers = current_offers(product, country, currency)
    live = [o for o in offers if o.get("live")]
    if live:
        cheapest = min(live, key=lambda x: usd_from_local(float(x["price"]), x["currency"]))
        return usd_from_local(float(cheapest["price"]), cheapest["currency"]), True, cheapest["store"]
    return float(product["usd_price"]), False, "Reference catalog"


def with_market_prices(items: list[dict[str, Any]], country: str, currency: str) -> list[dict[str, Any]]:
    updated: list[dict[str, Any]] = []
    for item in items:
        clone = dict(item)
        price, live, source = market_price_usd(item, country, currency)
        clone["usd_price"] = price
        clone["_live_price"] = live
        clone["_price_source"] = source
        updated.append(clone)
    return updated


def compatible(cpu: dict[str, Any], motherboard: dict[str, Any], ram: dict[str, Any]) -> bool:
    return (
        cpu.get("socket") == motherboard.get("socket")
        and ram.get("memory_type") == motherboard.get("memory_type")
    )


def score_product(product: dict[str, Any], need: dict[str, Any], budget_remaining: float, *, role: str = "primary") -> float:
    use_cases = set(need.get("use_cases", []))
    games = set(need.get("games", []))
    prefs = set(need.get("preferences", []))
    laptop_prefs = set(need.get("laptop_preferences", []))
    resolution = need.get("resolution") or "smart"
    target_fps = int(need.get("target_fps") or 0)

    score = 0.0
    score += float(product.get("value", 0)) * 0.34
    score += float(product.get("performance", 0)) * 0.24
    score += float(product.get("availability_score", 70)) * 0.08
    score += float(product.get("upgrade_score", 50)) * 0.10

    if "Gaming" in use_cases:
        score += float(product.get("gaming", 0)) * 0.12
    if "Streaming" in use_cases:
        score += float(product.get("streaming", 0)) * 0.05
    if "Creation" in use_cases:
        score += float(product.get("creation", 0)) * 0.05
    if "AI" in use_cases:
        score += float(product.get("creation", 0)) * 0.03

    if "Quiet" in prefs:
        score += float(product.get("quiet", 0)) * 0.06
    if "Future-proof" in prefs:
        score += float(product.get("upgrade_score", 0)) * 0.06
    if "Small" in prefs:
        score += float(product.get("compact", 0)) * 0.05
    if "Wi-Fi" in prefs:
        score += float(product.get("wifi", 0)) * 0.03

    if product.get("device") == "laptop":
        if "Lightweight" in laptop_prefs:
            score += max(0.0, 3.0 - float(product.get("weight_kg", 3.0))) * 4.0
        if "Long battery" in laptop_prefs:
            score += float(product.get("battery_wh", 50)) * 0.035
        if "High refresh" in laptop_prefs:
            score += float(product.get("refresh_hz", 60)) * 0.02
        if "Large screen" in laptop_prefs:
            score += float(product.get("display_size", 14)) * 0.45
        if "Creator" in laptop_prefs:
            score += float(product.get("creation", 0)) * 0.07
        if "Portable" in laptop_prefs:
            score += float(product.get("compact", 0)) * 0.06

    if resolution == "1440p":
        score += float(product.get("performance", 0)) * 0.04
    elif resolution == "4K":
        score += float(product.get("performance", 0)) * 0.07

    # FPS is a floor, not a maximize-at-all-costs target.
    perf = float(product.get("performance", 0))
    if target_fps >= 240 and perf >= 95:
        score += 4
    elif target_fps >= 165 and perf >= 90:
        score += 4
    elif target_fps >= 144 and perf >= 82:
        score += 4
    elif target_fps >= 120 and perf >= 76:
        score += 3
    elif target_fps >= 60 and perf >= 60:
        score += 2

    score += min(12, 3 * len(games.intersection(set(product.get("games", [])))))

    price = float(product.get("usd_price", 9999))
    if price <= budget_remaining:
        headroom = budget_remaining - price
        # Reward sensible use of money, not simply spending everything.
        if budget_remaining and 0.10 <= headroom / budget_remaining <= 0.40:
            score += 5
        elif headroom < budget_remaining * 0.05:
            score -= 2
    else:
        score -= min((price - budget_remaining) * 8, 30)
    return round(score, 3)


def fps_estimate(need: dict[str, Any], gpu: dict[str, Any] | None) -> dict[str, Any] | None:
    if not gpu or gpu.get("category") != "gpu":
        return None
    perf = float(gpu.get("performance", 0))
    resolution = need.get("resolution") or "1080p"
    target = int(need.get("target_fps") or 0)
    multiplier = {"1080p": 1.00, "1440p": 0.72, "4K": 0.48}.get(resolution, 0.92)
    # Clearly labeled engine estimate rather than benchmark claim.
    low = round(max(30, 55 + (perf - 60) * 2.0) * multiplier)
    high = round(max(low + 10, 78 + (perf - 60) * 2.5) * multiplier)
    note = "Reference estimate — actual FPS varies by game, settings, drivers and CPU."
    target_status = None
    if target:
        target_status = "clears-target" if high >= target else "below-target"
        if low >= target:
            target_status = "comfortably-clears"
    return {"resolution": resolution, "low": low, "high": high, "target": target or None, "target_status": target_status, "note": note}


def choose_desktop(need: dict[str, Any], usd_budget: float, mode: str = "smart") -> dict[str, Any]:
    existing = set(need.get("existing_parts", []))
    if "Nothing" in existing:
        existing.clear()
    products = CATALOG["products"]
    cpus = with_market_prices(catalog_products("desktop", "cpu"), need.get("country", "US"), need.get("currency", "USD"))
    mobos = with_market_prices(catalog_products("desktop", "motherboard"), need.get("country", "US"), need.get("currency", "USD"))
    rams = with_market_prices(catalog_products("desktop", "ram"), need.get("country", "US"), need.get("currency", "USD"))
    gpus = with_market_prices(catalog_products("desktop", "gpu"), need.get("country", "US"), need.get("currency", "USD"))
    psus = with_market_prices(catalog_products("desktop", "psu"), need.get("country", "US"), need.get("currency", "USD"))
    cases = with_market_prices(catalog_products("desktop", "case"), need.get("country", "US"), need.get("currency", "USD"))
    ssds = with_market_prices(catalog_products("desktop", "ssd"), need.get("country", "US"), need.get("currency", "USD"))

    if existing and "cpu" in existing:
        cpus = []
    if existing and "motherboard" in existing:
        mobos = []
    if existing and "ram" in existing:
        rams = []
    if existing and "gpu" in existing:
        gpus = []
    if existing and "psu" in existing:
        psus = []
    if existing and "case" in existing:
        cases = []
    if existing and "ssd" in existing:
        ssds = []

    # Find the platform first so socket + memory type cannot drift apart.
    base_pool = cpus or with_market_prices(catalog_products("desktop", "cpu"), need.get("country", "US"), need.get("currency", "USD"))
    cpu_rank = {"smart": 1.0, "speed": 1.12, "beast": 1.20}.get(mode, 1.0)
    ranked_cpus = sorted(base_pool, key=lambda p: score_product(p, need, usd_budget) * cpu_rank, reverse=True)
    selected_cpu = None
    selected_mobo = None
    selected_ram = None
    best_tuple = None
    for cpu in ranked_cpus:
        compatible_mobos = [m for m in (mobos or with_market_prices(catalog_products("desktop", "motherboard"), need.get("country", "US"), need.get("currency", "USD"))) if m.get("socket") == cpu.get("socket")]
        for mobo in compatible_mobos:
            compatible_rams = [r for r in (rams or with_market_prices(catalog_products("desktop", "ram"), need.get("country", "US"), need.get("currency", "USD"))) if r.get("memory_type") == mobo.get("memory_type")]
            for ram in compatible_rams:
                fixed = sum(float(p["usd_price"]) for p in [cpu, mobo, ram] if p)
                if fixed > usd_budget * 0.92:
                    continue
                s = score_product(cpu, need, usd_budget) + score_product(mobo, need, usd_budget) * 0.30 + score_product(ram, need, usd_budget) * 0.25
                if best_tuple is None or s > best_tuple[0]:
                    best_tuple = (s, cpu, mobo, ram)
    if best_tuple:
        _, selected_cpu, selected_mobo, selected_ram = best_tuple

    minimums = {
        "cpu": selected_cpu,
        "motherboard": selected_mobo,
        "ram": selected_ram,
    }
    parts: dict[str, dict[str, Any]] = {k: v for k, v in minimums.items() if v}

    chosen_gpu = max(gpus, key=lambda p: score_product(p, need, usd_budget * 0.60)) if gpus else None
    if chosen_gpu:
        parts["gpu"] = chosen_gpu

    chosen_ssd = max(ssds, key=lambda p: score_product(p, need, usd_budget * 0.20)) if ssds else None
    if chosen_ssd:
        parts["ssd"] = chosen_ssd

    def current_total() -> float:
        return sum(float(v["usd_price"]) for v in parts.values())

    if psus:
        needed_w = (parts.get("gpu") or {}).get("recommended_psu_w", 450)
        compatible_psus = [p for p in psus if p.get("wattage", 0) >= needed_w]
        parts["psu"] = min(compatible_psus or psus, key=lambda p: p["usd_price"])
    if cases:
        board = parts.get("motherboard")
        form_factor = board.get("form_factor") if board else "ATX"
        compatible_cases = [c for c in cases if form_factor in c.get("supports", ["ATX", "mATX"])]
        parts["case"] = min(compatible_cases or cases, key=lambda p: p["usd_price"])

    # Ensure budget fit by swapping GPU first, then other flex categories.
    order = ["gpu", "cpu", "ssd", "ram", "motherboard", "psu", "case"]
    candidates = {
        "gpu": gpus, "cpu": cpus, "ssd": ssds, "ram": rams,
        "motherboard": mobos, "psu": psus, "case": cases,
    }
    total = current_total()
    while total > usd_budget and any(candidates.get(k) for k in order):
        swapped = False
        for cat in order:
            current = parts.get(cat)
            if not current:
                continue
            for alt in sorted(candidates.get(cat, []), key=lambda p: p["usd_price"]):
                if alt["id"] == current["id"]:
                    continue
                if cat == "cpu" and parts.get("motherboard") and alt.get("socket") != parts["motherboard"].get("socket"):
                    continue
                if cat == "motherboard" and parts.get("cpu") and alt.get("socket") != parts["cpu"].get("socket"):
                    continue
                if cat == "ram" and parts.get("motherboard") and alt.get("memory_type") != parts["motherboard"].get("memory_type"):
                    continue
                proposed = total - float(current["usd_price"]) + float(alt["usd_price"])
                if proposed <= total:
                    parts[cat] = alt
                    total = proposed
                    swapped = True
                    break
            if swapped:
                break
        if not swapped:
            break

    # Final sanity: if parts are still over budget, use the cheapest compatible set.
    if total > usd_budget * 1.001:
        cheapest: dict[str, dict[str, Any]] = {}
        for cat, pool in candidates.items():
            if not pool:
                continue
            if cat == "cpu": cheapest[cat] = min(pool, key=lambda p: p["usd_price"])
            elif cat == "motherboard":
                base = cheapest.get("cpu") or parts.get("cpu")
                opts = [p for p in pool if not base or p.get("socket") == base.get("socket")]
                if opts: cheapest[cat] = min(opts, key=lambda p: p["usd_price"])
            elif cat == "ram":
                base = cheapest.get("motherboard") or parts.get("motherboard")
                opts = [p for p in pool if not base or p.get("memory_type") == base.get("memory_type")]
                if opts: cheapest[cat] = min(opts, key=lambda p: p["usd_price"])
            elif cat == "psu":
                gpu = parts.get("gpu") or {}
                need_w = gpu.get("recommended_psu_w", 450)
                opts = [p for p in pool if p.get("wattage", 0) >= need_w]
                if opts: cheapest[cat] = min(opts, key=lambda p: p["usd_price"])
            else:
                cheapest[cat] = min(pool, key=lambda p: p["usd_price"])
        parts.update({k: v for k, v in cheapest.items() if k not in existing})
        total = sum(float(v["usd_price"]) for v in parts.values())

    selected = list(parts.values())
    gpu = parts.get("gpu")
    performance = round(sum(float(p.get("performance", 0)) for p in selected) / max(len(selected), 1) + 7)
    value = round(sum(float(p.get("value", 0)) for p in selected) / max(len(selected), 1) + 5)
    target_fps = int(need.get("target_fps") or 0)
    if mode == "speed":
        performance = min(99, performance + 4)
        value = max(0, value - 2)
    elif mode == "beast":
        performance = min(99, performance + 7)
        value = max(0, value - 5)

    estimate = fps_estimate(need, gpu)
    target_status = estimate.get("target_status") if estimate else None
    reasons = [
        "The budget is treated as a ceiling, not a reason to buy the most expensive option.",
        "FPS is treated as a floor: once the target is comfortably met, extra spend must earn its place.",
        "The engine checks CPU socket, motherboard platform, RAM type, PSU headroom and case support before finalizing a desktop build.",
    ]
    if target_fps and target_status in {"clears-target", "comfortably-clears"}:
        reasons.append(f"Your {target_fps}+ FPS target is already covered in the engine estimate, so we avoid spending purely for bigger numbers.")
    elif target_fps and target_status == "below-target":
        reasons.append(f"The selected budget does not comfortably reach {target_fps} FPS in the reference estimate; we keep the warning visible instead of pretending it does.")
    if need.get("existing_parts"):
        reasons.append("Existing compatible parts are excluded from the shopping list to preserve your budget.")

    result_parts = []
    for p in selected:
        result_parts.append(
            {
                "id": p["id"], "category": p["category"], "name": p["name"], "brand": p.get("brand", ""),
                "price": fmt_money(float(p["usd_price"]), need.get("currency", "USD")),
                "currency": need.get("currency", "USD"), "performance": p.get("performance", 0),
                "why": p.get("why", "Balanced choice for your goal."),
                "offers": current_offers(p, need.get("country", "US"), need.get("currency", "USD")),
                "specs": {k: p.get(k) for k in ["socket", "memory_type", "wattage", "recommended_psu_w", "condition", "warranty_months"] if k in p},
            }
        )
    return {
        "type": "desktop", "title": {"smart": "The Smart Buy", "speed": "The Speed Demon", "beast": "The Beast"}.get(mode, "The Smart Buy"),
        "tagline": {
            "smart": "Strong performance without paying for headroom you will not use.",
            "speed": "Push performance where it actually changes the experience.",
            "beast": "The highest sensible performance we can fit inside your ceiling.",
        }.get(mode, "Strong performance without paying for headroom you will not use."),
        "total": round(local_from_usd(total, need.get("currency", "USD")), 2),
        "currency": need.get("currency", "USD"), "performance_fit": min(99, performance),
        "value_score": min(99, value), "future_score": min(99, round(value * 0.72 + performance * 0.28)),
        "parts": result_parts, "reasons": reasons, "fps_estimate": estimate,
        "data_mode": "reference-demo" if not any(o.get("source") != "reference-demo" for p in result_parts for o in p["offers"]) else "live-plus-reference",
    }


def build_single_device(need: dict[str, Any], usd_budget: float, device: str) -> dict[str, Any]:
    # Portable devices are products, not collections of desktop components.
    # Keep the laptop path explicitly constrained to the laptop category.
    if device == "laptop":
        source = catalog_products("laptop", "laptop")
    elif device in {"prebuilt", "used"}:
        source = catalog_products(device, device) or catalog_products(device)
    else:
        source = catalog_products(device)
    candidates = with_market_prices(source, need.get("country", "US"), need.get("currency", "USD"))
    if not candidates:
        raise ValueError(f"No reference catalog items for {device} yet.")
    ranked = sorted(candidates, key=lambda p: score_product(p, need, usd_budget), reverse=True)
    within_budget = [p for p in ranked if float(p["usd_price"]) <= usd_budget]
    if within_budget:
        chosen = within_budget[0]
        budget_match = "within-budget"
    else:
        # A strict spec match may not exist at this budget. Choose the nearest
        # priced product instead of failing the request or silently returning an
        # arbitrary/highest-ranked product far outside the user's budget.
        chosen = min(ranked, key=lambda p: abs(float(p["usd_price"]) - usd_budget))
        budget_match = "closest-available"
    price = float(chosen["usd_price"])
    budget_delta_local = round(abs(local_from_usd(price - usd_budget, need.get("currency", "USD"))), 2)
    label = {"laptop": "Laptop", "prebuilt": "Prebuilt", "used": "Used / Refurbished"}.get(device, "Device")
    offers = current_offers(chosen, need.get("country", "US"), need.get("currency", "USD"))
    estimate = fps_estimate(need, chosen if device != "prebuilt" else None)
    reasons = [
        "The recommendation respects your budget before chasing headline specifications.",
        "For used/refurbished options, verify seller history, warranty, battery health and return policy before buying.",
        "Live market feeds should replace reference offers before public launch in each country.",
    ]
    nearby_options = []
    for alt in ranked:
        if alt.get("id") == chosen.get("id"):
            continue
        alt_price = float(alt.get("usd_price", 0))
        if not nearby_options or len(nearby_options) < 3:
            nearby_options.append({
                "id": alt["id"], "name": alt["name"], "brand": alt.get("brand", ""),
                "price": round(local_from_usd(alt_price, need.get("currency", "USD")), 2),
                "currency": need.get("currency", "USD"), "performance": alt.get("performance", 0),
                "value": alt.get("value", 0), "why": alt.get("why", ""),
                "offers": current_offers(alt, need.get("country", "US"), need.get("currency", "USD")),
            })
    if budget_match == "closest-available":
        reasons.insert(1, f"No catalog product matched the exact target budget; the engine selected the closest available option (about {budget_delta_local} away in the selected currency).")
    return {
        "type": device, "title": f"Best-fit {label}", "tagline": chosen.get("why", "Best fit in the reference catalog."),
        "total": round(local_from_usd(price, need.get("currency", "USD")), 2), "currency": need.get("currency", "USD"),
        "budget_match": budget_match, "budget_delta": budget_delta_local,
        "performance_fit": min(99, chosen.get("performance", 0)), "value_score": min(99, chosen.get("value", 0)),
        "future_score": min(99, chosen.get("upgrade_score", 0)),
        "parts": [{"id": chosen["id"], "category": device, "name": chosen["name"], "brand": chosen.get("brand", ""),
                   "price": round(local_from_usd(price, need.get("currency", "USD")), 2), "currency": need.get("currency", "USD"),
                   "performance": chosen.get("performance", 0), "why": chosen.get("why", ""), "offers": offers,
                   "specs": {k: chosen.get(k) for k in ["condition", "warranty_months"] if k in chosen}}],
        "reasons": reasons, "fps_estimate": estimate, "nearby_options": nearby_options,
        "device_details": {
            "is_portable_product": device == "laptop",
            "product_only": device in {"laptop", "prebuilt", "used"},
            "category": "laptop" if device == "laptop" else device,
            "specs": {
                k: chosen.get(k) for k in [
                    "cpu_model", "gpu_model", "ram_gb", "storage_gb", "storage_type",
                    "display_size", "display_resolution", "refresh_hz", "weight_kg",
                    "battery_wh", "os", "screen_type", "warranty_months", "condition"
                ] if chosen.get(k) not in (None, "")
            } if device == "laptop" else {},
        },
        "data_mode": "reference-demo" if not any(o.get("source") != "reference-demo" for o in offers) else "live-plus-reference",
    }


def _safe_reference_offer(product: dict[str, Any], currency: str) -> dict[str, Any]:
    """Build one deterministic reference offer without DB, FX service or marketplace dependencies."""
    price = round(local_from_usd(float(product.get("usd_price", 0)), currency), 2)
    store = (product.get("stores") or [{"name": "Reference catalog", "base_url": "https://www.google.com/search?q=" + quote_plus(product.get("name", ""))}])[0]
    return {
        "store": store.get("name", "Reference catalog"),
        "price": price,
        "currency": currency,
        "url": store.get("base_url") or ("https://www.google.com/search?q=" + quote_plus(product.get("name", ""))),
        "availability": "Reference price — verify before buying",
        "affiliate_ready": False,
        "captured_at": None,
        "source": "reference-fallback",
        "stale": False,
        "live": False,
    }


def _reference_fallback_recommendation(payload: dict[str, Any]) -> dict[str, Any]:
    """Fail-open recommendation used only when the normal engine cannot complete.

    It deliberately avoids SQLite price feeds, external providers and marketplace
    generation. The user still gets a useful result instead of a generic 500.
    """
    device = str(payload.get("device_type", "desktop") or "desktop").lower()
    if device == "not_sure":
        device = "laptop" if payload.get("portability") or "Laptop" in payload.get("preferences", []) else "desktop"
    currency = str(payload.get("currency", "USD")).upper()
    budget = float(payload.get("budget", 0) or 0)
    usd_budget = usd_from_local(budget, currency)
    if device in {"laptop", "prebuilt", "used"}:
        pool = catalog_products(device, device) or catalog_products(device)
        if not pool:
            raise ValueError(f"No reference catalog items for {device}.")
        ranked = sorted(pool, key=lambda p: (abs(float(p.get("usd_price", 0)) - usd_budget), -float(p.get("value", 0))))
        chosen = ranked[0]
        local_price = round(local_from_usd(float(chosen.get("usd_price", 0)), currency), 2)
        delta = round(abs(local_price - budget), 2)
        nearby = []
        for p in ranked[1:4]:
            nearby.append({
                "id": p["id"], "name": p["name"], "brand": p.get("brand", ""),
                "price": round(local_from_usd(float(p.get("usd_price", 0)), currency), 2),
                "currency": currency, "performance": p.get("performance", 0),
                "value": p.get("value", 0), "why": p.get("why", ""),
                "offers": [_safe_reference_offer(p, currency)],
            })
        result = {
            "type": device, "title": f"Best-fit { {'laptop':'Laptop','prebuilt':'Prebuilt','used':'Used / Refurbished'}.get(device, 'Device') }",
            "tagline": chosen.get("why", "Best fit from the reference catalog."),
            "total": local_price, "currency": currency,
            "budget_match": "within-budget" if local_price <= budget else "closest-available",
            "budget_delta": delta, "performance_fit": min(99, int(chosen.get("performance", 0))),
            "value_score": min(99, int(chosen.get("value", 0))), "future_score": min(99, int(chosen.get("upgrade_score", 0))),
            "parts": [{
                "id": chosen["id"], "category": device, "name": chosen["name"], "brand": chosen.get("brand", ""),
                "price": local_price, "currency": currency, "performance": chosen.get("performance", 0),
                "why": chosen.get("why", ""), "offers": [_safe_reference_offer(chosen, currency)],
                "specs": {k: chosen.get(k) for k in ["condition", "warranty_months"] if k in chosen},
            }],
            "reasons": [
                "Reference fallback used because the live recommendation path was temporarily unavailable.",
                "The closest product to your budget was selected instead of failing the request.",
            ],
            "fps_estimate": fps_estimate(payload, chosen if device == "desktop" else None),
            "data_mode": "reference-fallback",
            "nearby_options": nearby,
            "device_details": {
                "is_portable_product": device == "laptop", "product_only": device in {"laptop", "prebuilt", "used"},
                "category": "laptop" if device == "laptop" else device,
                "specs": {k: chosen.get(k) for k in [
                    "cpu_model", "gpu_model", "ram_gb", "storage_gb", "storage_type", "display_size",
                    "display_resolution", "refresh_hz", "weight_kg", "battery_wh", "os", "screen_type", "warranty_months", "condition"
                ] if chosen.get(k) not in (None, "")},
            },
        }
        result["query"] = {"budget": budget, "currency": currency, "device_type": payload.get("device_type", device), "country": payload.get("country", "US")}
        result["alternatives"] = [dict(result, alternatives=None)]
        result["alternatives"][0].pop("alternatives", None)
        return result
    # Desktop fallback: deliberately simple and deterministic.
    parts = []
    categories = ["cpu", "motherboard", "ram", "gpu", "ssd", "psu", "case"]
    remaining = usd_budget
    for cat in categories:
        pool = catalog_products("desktop", cat)
        if not pool:
            continue
        chosen = min(pool, key=lambda p: float(p.get("usd_price", 0)))
        if float(chosen.get("usd_price", 0)) <= remaining or not parts:
            parts.append(chosen); remaining -= float(chosen.get("usd_price", 0))
    if not parts:
        raise ValueError("No reference desktop catalog items available.")
    total_usd = sum(float(p.get("usd_price", 0)) for p in parts)
    out_parts = [{
        "id": p["id"], "category": p["category"], "name": p["name"], "brand": p.get("brand", ""),
        "price": round(local_from_usd(float(p.get("usd_price", 0)), currency), 2), "currency": currency,
        "performance": p.get("performance", 0), "why": p.get("why", ""), "offers": [_safe_reference_offer(p, currency)],
        "specs": {k: p.get(k) for k in ["socket", "memory_type", "wattage", "recommended_psu_w"] if k in p},
    } for p in parts]
    return {
        "type": "desktop", "title": "Reference Desktop", "tagline": "A safe reference build from the catalog.",
        "total": round(local_from_usd(total_usd, currency), 2), "currency": currency,
        "performance_fit": min(99, round(sum(float(p.get("performance", 0)) for p in parts) / len(parts))),
        "value_score": min(99, round(sum(float(p.get("value", 0)) for p in parts) / len(parts))),
        "future_score": min(99, round(sum(float(p.get("upgrade_score", 0)) for p in parts) / len(parts))),
        "parts": out_parts, "reasons": ["Reference fallback used because the live recommendation path was temporarily unavailable."],
        "data_mode": "reference-fallback", "alternatives": [],
    }


def recommend_build(payload: dict[str, Any]) -> dict[str, Any]:
    budget = float(payload.get("budget", 0))
    currency = str(payload.get("currency", "USD")).upper()
    usd_budget = usd_from_local(budget, currency)
    device = str(payload.get("device_type", "not_sure") or "not_sure").lower()
    # Unknown device is decided by a compact heuristic, not by AI.
    if device == "not_sure":
        if "Laptop" in payload.get("preferences", []) or payload.get("portability"):
            device = "laptop"
        else:
            device = "desktop"
    if device == "custom":
        device = "desktop"
    if device == "desktop":
        return choose_desktop(payload, usd_budget, "smart")
    if device in {"laptop", "prebuilt", "used"}:
        return build_single_device(payload, usd_budget, device)
    raise ValueError("Unsupported device type. Choose desktop, laptop, prebuilt, or used.")


def event(name: str, *, build_id: str | None = None, product_id: str | None = None, country: str | None = None, meta: dict | None = None) -> None:
    try:
        con = db()
        con.execute(
            "INSERT INTO events(event_name,build_id,product_id,country,meta) VALUES(?,?,?,?,?)",
            (name, build_id, product_id, country, json.dumps(meta or {})),
        )
        con.commit(); con.close()
    except sqlite3.DatabaseError as exc:
        # Analytics must never turn a successful user action into a 500.
        logger.warning("event logging skipped for %s: %s", name, exc)


def _store_price_rows(product_id: str, offers: list[Any], country: str) -> int:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    con = db(); count = 0
    for offer in offers:
        if getattr(offer, "price", None) is None or not getattr(offer, "url", None):
            continue
        con.execute(
            "INSERT INTO prices(product_id,store,country,currency,price,availability,product_url,affiliate_url,captured_at,source) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (product_id, offer.store, country, offer.currency, float(offer.price), offer.availability, offer.url, None, getattr(offer, "captured_at", None) or now, offer.source),
        )
        count += 1
    con.commit(); con.close()
    return count


def sync_product_prices(product: dict[str, Any], country: str, providers: list[str]) -> dict[str, Any]:
    query = product.get("search_query") or product.get("name")
    found: list[Any] = []
    if "ebay" in providers:
        marketplace = os.getenv("EBAY_MARKETPLACE_ID", "EBAY_US").strip()
        # eBay marketplace access varies by application; use the configured marketplace.
        try:
            found.extend(EbayClient().search(query))
        except Exception as exc:
            return {"product_id": product["id"], "offers": 0, "error": f"eBay: {exc}"}
    if "bestbuy" in providers and country == "US":
        try:
            found.extend(BestBuyClient().search(query))
        except Exception as exc:
            return {"product_id": product["id"], "offers": len(found), "error": f"Best Buy: {exc}"}
    # Optional, explicitly configured JSON-LD sources. This never guesses a store URL.
    for source in product.get("live_sources", []):
        try:
            found.extend(fetch_jsonld_offer(source["url"], source.get("store", "Web store")))
        except Exception as exc:
            return {"product_id": product["id"], "offers": len(found), "error": f"JSON-LD source: {exc}"}
    dedupe = {}
    for offer in found:
        key = (offer.store, round(float(offer.price), 2), offer.url)
        dedupe[key] = offer
    # Keep the cheapest few offers; raw API results can contain duplicates/variants.
    offers = best_matching_offers(query, list(dedupe.values()), limit=6)
    imported = _store_price_rows(product["id"], offers, country)
    return {"product_id": product["id"], "offers": imported, "provider_results": len(found)}


def sync_live_prices(country: str, product_ids: list[str] | None = None, providers: list[str] | None = None) -> dict[str, Any]:
    providers = providers or [p for p, enabled in [("ebay", bool(os.getenv("EBAY_CLIENT_ID") and os.getenv("EBAY_CLIENT_SECRET"))), ("bestbuy", bool(os.getenv("BESTBUY_API_KEY")))] if enabled]
    if not providers:
        return {"ok": False, "message": "No live price provider credentials are configured.", "providers": []}
    products = CATALOG.get("products", [])
    if product_ids:
        wanted = set(product_ids); products = [p for p in products if p.get("id") in wanted]
    results = []
    for product in products:
        if product.get("category") in {"cpu", "gpu", "ram", "motherboard", "ssd", "psu", "case", "laptop", "prebuilt", "used"} or product.get("device") in {"laptop", "prebuilt", "used"}:
            results.append(sync_product_prices(product, country, providers))
    return {"ok": True, "country": country, "providers": providers, "products": len(results), "results": results, "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}


@app.errorhandler(400)
def handle_400(err):
    return jsonify({"error": {"code": "BAD_REQUEST", "message": "The request could not be processed."}}), 400


@app.errorhandler(404)
def handle_404(err):
    if request.path.startswith("/api/"):
        return jsonify({"error": {"code": "NOT_FOUND", "message": "The requested API resource was not found."}}), 404
    return err


@app.errorhandler(500)
def handle_500(err):
    app.logger.exception("Unhandled server error: %s", err)
    if request.path.startswith("/api/"):
        return jsonify({"error": {"code": "INTERNAL_SERVER_ERROR", "message": "The server could not complete this request."}}), 500
    return err


@app.get("/api/health")
def health():
    # Keep this endpoint intentionally dependency-free: it is used to wake a sleeping
    # Render instance before a user submits the heavier recommendation request.
    response = jsonify({"ok": True, "service": "BuildYourPC API", "time": datetime.now(timezone.utc).isoformat()})
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@app.get("/api/config")
def config():
    return jsonify({
        "brand": "BuildYourPC", "tagline": "Your money. Your needs. Your PC.", "kofi": KO_FI_URL,
        "currencies": exported_config(), "countries": CATALOG.get("countries", []),
        "languages": CATALOG.get("languages", []), "games": CATALOG.get("games", []),
        "live_price_data": LIVE_PRICE_SYNC_ENABLED and bool(os.getenv("EBAY_CLIENT_ID") or os.getenv("BESTBUY_API_KEY")),
        "live_price_providers": [x for x, ok in [("eBay", bool(os.getenv("EBAY_CLIENT_ID") and os.getenv("EBAY_CLIENT_SECRET"))), ("Best Buy", bool(os.getenv("BESTBUY_API_KEY")))] if ok],
        "auth": {"enabled": True, "session_days": SESSION_DAYS},
        "premium": {"available": PREMIUM_AVAILABLE, "launch_phase": "active" if PREMIUM_AVAILABLE else "coming-soon", "features": PREMIUM_FEATURES},
        "live_price_max_age_hours": LIVE_MAX_AGE_HOURS,
        "fx_live": bool(_cached_fx_from_eur()),
        "notes": [
            "Fresh retailer/API offers override reference prices when available.",
            "Reference prices remain visibly labeled when live market data is unavailable.",
            "FX rates can be refreshed from Frankfurter and cached locally for low-cost global currency display.",
        ],
    })


@app.get("/api/explore")
def explore():
    con = db()
    rows = con.execute("SELECT id, payload, created_at, views, shares FROM builds ORDER BY created_at DESC LIMIT 18").fetchall()
    total_builds = con.execute("SELECT COUNT(*) FROM builds").fetchone()[0]
    total_views = con.execute("SELECT COALESCE(SUM(views),0) FROM builds").fetchone()[0]
    total_shares = con.execute("SELECT COALESCE(SUM(shares),0) FROM builds").fetchone()[0]
    con.close()
    live = []
    for row in rows:
        try:
            payload = json.loads(row["payload"])
        except (TypeError, ValueError):
            logger.warning("Skipping malformed saved build payload %s", row["id"])
            continue
        live.append({
            "id": row["id"], "created_at": row["created_at"], "views": row["views"], "shares": row["shares"],
            "title": payload.get("title", "Shared build"), "total": payload.get("total"), "currency": payload.get("currency", "USD"),
            "performance_fit": payload.get("performance_fit"), "value_score": payload.get("value_score"),
            "type": payload.get("type", "desktop"), "query": payload.get("query", {}),
        })
    curated = [
        {"id": "reference-sweet-spot", "title": "Sweet Spot", "label": "BEST VALUE", "total": 824, "currency": "USD", "performance_fit": 94, "type": "reference"},
        {"id": "reference-quiet", "title": "Silent Desk", "label": "QUIET", "total": 1049, "currency": "USD", "performance_fit": 91, "type": "reference"},
        {"id": "reference-fast", "title": "Fast & Focused", "label": "TRENDING", "total": 689, "currency": "USD", "performance_fit": 92, "type": "reference"},
    ]
    return jsonify({"stats": {"builds": total_builds, "views": total_views, "shares": total_shares}, "live": live, "curated": curated})


@app.post("/api/recommend")
def recommend():
    payload = request.get_json(silent=True) or {}
    try:
        budget = float(payload.get("budget", 0))
    except (TypeError, ValueError):
        return jsonify({"error": {"code": "INVALID_BUDGET", "message": "Enter a valid budget."}}), 400
    if not (budget == budget and abs(budget) != float("inf")):
        return jsonify({"error": {"code": "INVALID_BUDGET", "message": "Enter a valid budget."}}), 400
    payload["currency"] = str(payload.get("currency", "USD")).upper()
    try:
        currency_cfg = get_currency(payload["currency"])
    except ValueError as exc:
        return jsonify({"error": {"code": "UNSUPPORTED_CURRENCY", "message": str(exc)}}), 400
    if budget < currency_cfg["minimum"] or budget > currency_cfg["maximum"]:
        return jsonify({"error": {"code": "BUDGET_OUT_OF_RANGE", "message": f"Budget must be between {currency_cfg['minimum']} and {currency_cfg['maximum']} {payload['currency']}."}}), 400
    payload["country"] = str(payload.get("country", "US")).upper()
    for key in ("use_cases", "games", "preferences", "existing_parts"):
        if payload.get(key) is None:
            payload[key] = []
        elif not isinstance(payload.get(key), list):
            return jsonify({"error": {"code": "INVALID_FIELD", "message": f"{key} must be a list."}}), 400
    if payload.get("target_fps") not in (None, ""):
        try:
            payload["target_fps"] = int(payload["target_fps"])
        except (TypeError, ValueError):
            return jsonify({"error": {"code": "INVALID_FPS", "message": "Target FPS must be a number."}}), 400
    try:
        base = recommend_build(payload)
    except ValueError as exc:
        logger.warning("recommend validation/build error: %s", exc, extra={"country": payload.get("country"), "currency": payload.get("currency")})
        return jsonify({"error": {"code": "BUILD_UNAVAILABLE", "message": str(exc)}}), 422
    except (KeyError, TypeError, IndexError, sqlite3.DatabaseError) as exc:
        logger.exception("recommend data/database error for country=%s currency=%s", payload.get("country"), payload.get("currency"))
        try:
            base = _reference_fallback_recommendation(payload)
        except Exception:
            return jsonify({"error": {"code": "BUILD_DATA_ERROR", "message": "The build catalog could not produce a valid recommendation. Please retry."}}), 500
    except Exception:
        logger.exception("unexpected recommendation failure for country=%s currency=%s device=%s", payload.get("country"), payload.get("currency"), payload.get("device_type"))
        try:
            base = _reference_fallback_recommendation(payload)
        except Exception:
            return jsonify({"error": {"code": "RECOMMENDATION_ERROR", "message": "The recommendation service failed safely. Please retry."}}), 500
    # Alternative views use the same constraint set but reweight the engine rather than maxing raw FPS blindly.
    # Never allow an optional alternative to turn a successful primary recommendation into a 500.
    if base["type"] == "desktop":
        alternatives = []
        usd_budget = usd_from_local(budget, payload["currency"])
        for mode in ("smart", "speed", "beast"):
            try:
                alternatives.append(choose_desktop(payload, usd_budget, mode))
            except Exception:
                logger.exception("optional desktop alternative failed: mode=%s", mode)
        if not alternatives:
            snapshot = {k: v for k, v in base.items() if k != "alternatives"}
            alternatives = [snapshot]
    else:
        # Keep the primary recommendation and an independent snapshot as the
        # first alternative. Do NOT put `base` itself inside its `alternatives`
        # list: that creates a circular reference and Flask/json.dumps returns
        # HTTP 500 for every non-desktop device (laptop/prebuilt/used).
        snapshot = {k: v for k, v in base.items() if k != "alternatives"}
        alternatives = [snapshot]
    base["alternatives"] = alternatives
    base["query"] = {
        "budget": budget, "currency": payload["currency"], "device_type": payload.get("device_type", "not_sure"),
        "country": payload["country"], "use_cases": payload.get("use_cases", []), "games": payload.get("games", []),
        "target_fps": payload.get("target_fps"), "resolution": payload.get("resolution"), "existing_parts": payload.get("existing_parts", []),
        "laptop_preferences": payload.get("laptop_preferences", []),
    }
    event("recommendation_created", country=payload["country"], meta={"device": base["type"], "budget": budget, "currency": payload["currency"]})
    return jsonify(base)



@app.get("/api/auth/me")
def auth_me():
    user = current_user()
    return jsonify({"authenticated": bool(user), "user": _public_user(user)})


@app.post("/api/auth/register")
def auth_register():
    payload = request.get_json(silent=True) or {}
    email = _clean_email(payload.get("email"))
    password = str(payload.get("password") or "")
    display_name = str(payload.get("display_name") or email.split("@")[0] or "Builder").strip()[:60]
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({"error": {"code": "INVALID_EMAIL", "message": "Enter a valid email address."}}), 400
    if len(password) < 8:
        return jsonify({"error": {"code": "WEAK_PASSWORD", "message": "Password must be at least 8 characters."}}), 400
    con = db()
    try:
        cur = con.execute(
            "INSERT INTO users(email,password_hash,display_name) VALUES(?,?,?)",
            (email, generate_password_hash(password), display_name),
        )
        user_id = cur.lastrowid
        con.commit()
        row = con.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    except sqlite3.IntegrityError:
        con.close()
        return jsonify({"error": {"code": "EMAIL_EXISTS", "message": "An account with this email already exists."}}), 409
    con.close()
    token = create_session(user_id)
    resp = jsonify({"ok": True, "user": _public_user(row)})
    resp.set_cookie(SESSION_COOKIE, token, max_age=SESSION_DAYS * 86400, httponly=True, secure=request.is_secure, samesite="Lax", path="/")
    return resp, 201


@app.post("/api/auth/login")
def auth_login():
    payload = request.get_json(silent=True) or {}
    email = _clean_email(payload.get("email"))
    password = str(payload.get("password") or "")
    con = db()
    row = con.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    con.close()
    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify({"error": {"code": "INVALID_LOGIN", "message": "Email or password is incorrect."}}), 401
    token = create_session(row["id"])
    resp = jsonify({"ok": True, "user": _public_user(row)})
    resp.set_cookie(SESSION_COOKIE, token, max_age=SESSION_DAYS * 86400, httponly=True, secure=request.is_secure, samesite="Lax", path="/")
    return resp


@app.post("/api/auth/logout")
def auth_logout():
    delete_session(_session_token_from_request())
    resp = jsonify({"ok": True})
    resp.delete_cookie(SESSION_COOKIE, path="/")
    return resp


@app.get("/api/account/builds")
@auth_required
def account_builds(user):
    con = db()
    rows = con.execute(
        "SELECT id,payload,created_at,views,shares FROM builds WHERE user_id=? ORDER BY created_at DESC LIMIT 50",
        (user["id"],),
    ).fetchall()
    con.close()
    builds = []
    for row in rows:
        try:
            payload = json.loads(row["payload"])
        except Exception:
            payload = {}
        builds.append({"id": row["id"], "created_at": row["created_at"], "views": row["views"], "shares": row["shares"], "payload": payload})
    return jsonify({"builds": builds})


@app.post("/api/account/favorites")
@auth_required
def favorite_build(user):
    payload = request.get_json(silent=True) or {}
    build_id = str(payload.get("build_id") or "")
    if not build_id:
        return jsonify({"error": {"code": "BUILD_REQUIRED", "message": "Build ID is required."}}), 400
    con = db()
    if not con.execute("SELECT 1 FROM builds WHERE id=?", (build_id,)).fetchone():
        con.close()
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Build not found."}}), 404
    con.execute("INSERT OR IGNORE INTO favorites(user_id,build_id) VALUES(?,?)", (user["id"], build_id))
    con.commit()
    con.close()
    return jsonify({"ok": True})


@app.get("/api/account/favorites")
@auth_required
def get_favorites(user):
    con = db()
    rows = con.execute("SELECT build_id,created_at FROM favorites WHERE user_id=? ORDER BY created_at DESC", (user["id"],)).fetchall()
    con.close()
    return jsonify({"favorites": [dict(r) for r in rows]})


@app.get("/api/premium/status")
def premium_status():
    user = current_user()
    return jsonify({
        "available": PREMIUM_AVAILABLE,
        "authenticated": bool(user),
        "premium_active": bool(user and _public_user(user)["premium_active"]),
        "features": PREMIUM_FEATURES,
    })


@app.get("/api/premium/feature/<feature>")
@auth_required
@premium_required
def premium_feature(user, feature):
    return jsonify({"ok": True, "feature": feature, "status": "enabled"})


@app.post("/api/builds")
def save_build():
    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"error": {"code": "EMPTY_PAYLOAD", "message": "Missing build payload."}}), 400
    query = payload.get("query") or {}
    if query.get("currency"):
        try:
            cfg = get_currency(query["currency"])
            budget = float(query.get("budget", 0))
            if budget < cfg["minimum"] or budget > cfg["maximum"]:
                return jsonify({"error": {"code": "BUDGET_OUT_OF_RANGE", "message": "Build budget is outside the allowed range."}}), 400
        except (ValueError, TypeError):
            return jsonify({"error": {"code": "INVALID_BUILD", "message": "Build currency or budget is invalid."}}), 400
    build_id = secrets.token_urlsafe(8).replace("-", "").replace("_", "")[:12]
    user = current_user()
    con = db()
    con.execute(
        "INSERT INTO builds (id, payload, user_id) VALUES (?, ?, ?)",
        (build_id, json.dumps(payload), user["id"] if user else None),
    )
    con.commit(); con.close()
    event("build_saved", build_id=build_id, country=payload.get("query", {}).get("country"))
    return jsonify({"id": build_id, "url": f"/build/{build_id}"})


@app.post("/api/builds/<build_id>/share")
def share_build(build_id: str):
    con = db()
    row = con.execute("SELECT id FROM builds WHERE id=?", (build_id,)).fetchone()
    if not row:
        con.close(); return jsonify({"error": {"code": "NOT_FOUND", "message": "Build not found"}}), 404
    con.execute("UPDATE builds SET shares = shares + 1 WHERE id=?", (build_id,))
    con.commit(); con.close(); event("build_shared", build_id=build_id)
    return jsonify({"ok": True})


@app.get("/api/products/<product_id>/price-history")
def price_history(product_id: str):
    currency = request.args.get("currency", "USD").upper()
    country = request.args.get("country", "US").upper()
    con = db()
    rows = con.execute(
        "SELECT store, price, currency, captured_at, source FROM prices WHERE product_id=? AND country IN (?, '*') ORDER BY captured_at ASC",
        (product_id, country),
    ).fetchall()
    con.close()
    history = [dict(r) for r in rows]
    if not history:
        product = next((x for x in CATALOG.get("products", []) if x.get("id") == product_id), None)
        if not product:
            return jsonify({"error": "Product not found"}), 404
        now_price = float(product["usd_price"])
        # No synthetic history: transparency matters more than a pretty fake chart.
        return jsonify({"product_id": product_id, "currency": currency, "country": country, "history": [], "live": False, "current_reference_price": fmt_money(now_price, currency)})
    return jsonify({"product_id": product_id, "currency": currency, "country": country, "history": history, "live": any(h["source"] != "manual-import" for h in history)})


@app.get("/api/builds/<build_id>")
def get_build(build_id: str):
    con = db()
    row = con.execute("SELECT * FROM builds WHERE id=?", (build_id,)).fetchone()
    if not row:
        con.close(); return jsonify({"error": "Build not found"}), 404
    con.execute("UPDATE builds SET views=views+1 WHERE id=?", (build_id,))
    con.commit(); con.close()
    event("build_viewed", build_id=build_id)
    return jsonify({"id": row["id"], "payload": json.loads(row["payload"]), "views": row["views"] + 1, "shares": row["shares"]})


@app.post("/api/watch")
def watch():
    payload = request.get_json(silent=True) or {}
    if not (payload.get("build_id") or payload.get("product_id")):
        return jsonify({"error": "Build or product is required."}), 400
    watch_id = secrets.token_urlsafe(8)
    con = db(); con.execute(
        "INSERT INTO watchlist(id,build_id,product_id,email,threshold,currency) VALUES(?,?,?,?,?,?)",
        (watch_id, payload.get("build_id"), payload.get("product_id"), payload.get("email"), payload.get("threshold"), payload.get("currency", "USD")),
    ); con.commit(); con.close()
    return jsonify({"ok": True, "id": watch_id, "message": "Saved for future price alerts."})


@app.get("/api/fx/refresh")
def refresh_fx_endpoint():
    if ADMIN_TOKEN and request.headers.get("X-Admin-Token") != ADMIN_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    rates = refresh_fx_rates()
    return jsonify({"ok": bool(rates), "currencies": len(rates), "source": "Frankfurter/central-bank reference data"})


@app.post("/api/admin/sync-live")
def sync_live_endpoint():
    if not ADMIN_TOKEN or request.headers.get("X-Admin-Token") != ADMIN_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    payload = request.get_json(silent=True) or {}
    country = str(payload.get("country") or "US").upper()
    providers = [str(x).lower() for x in payload.get("providers", []) if str(x).lower() in {"ebay", "bestbuy"}]
    product_ids = payload.get("product_ids") if isinstance(payload.get("product_ids"), list) else None
    result = sync_live_prices(country, product_ids, providers or None)
    event("live_price_sync", country=country, meta={"providers": result.get("providers"), "products": result.get("products", 0)})
    return jsonify(result)


@app.get("/api/admin/stats")
def admin_stats():
    if ADMIN_TOKEN and request.headers.get("X-Admin-Token") != ADMIN_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    con = db()
    result = {
        "builds": con.execute("SELECT COUNT(*) FROM builds").fetchone()[0],
        "views": con.execute("SELECT COALESCE(SUM(views),0) FROM builds").fetchone()[0],
        "shares": con.execute("SELECT COALESCE(SUM(shares),0) FROM builds").fetchone()[0],
        "price_rows": con.execute("SELECT COUNT(*) FROM prices").fetchone()[0],
        "watches": con.execute("SELECT COUNT(*) FROM watchlist").fetchone()[0],
    }
    con.close(); return jsonify(result)


@app.post("/api/admin/import-prices")
def import_prices():
    if not ADMIN_TOKEN or request.headers.get("X-Admin-Token") != ADMIN_TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    uploaded = request.files.get("file")
    if not uploaded:
        return jsonify({"error": "Upload a CSV file using field name 'file'."}), 400
    text = uploaded.stream.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    required = {"product_id", "store", "country", "currency", "price", "product_url"}
    if not required.issubset(set(reader.fieldnames or [])):
        return jsonify({"error": f"Missing columns. Required: {', '.join(sorted(required))}"}), 400
    now = datetime.now(timezone.utc).isoformat()
    con = db(); count = 0
    for row in reader:
        con.execute(
            "INSERT INTO prices(product_id,store,country,currency,price,availability,product_url,affiliate_url,captured_at,source) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (row["product_id"], row["store"], row["country"], row["currency"], float(row["price"]), row.get("availability", "unknown"), row["product_url"], row.get("affiliate_url") or None, row.get("captured_at") or now, row.get("source") or "manual-import"),
        ); count += 1
    con.commit(); con.close()
    return jsonify({"ok": True, "rows_imported": count})


@app.get("/admin")
def admin_page():
    html = """
    <!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
    <title>BuildYourPC Admin</title>
    <style>body{font-family:Inter,system-ui;background:#09090c;color:#eee;margin:0;padding:28px}.card{max-width:980px;margin:auto;background:#121219;border:1px solid #292536;border-radius:22px;padding:28px}.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}.stat{background:#171720;padding:16px;border-radius:16px}.muted{color:#9b94ab}code{color:#b98cff}input,select,button{font:inherit}input,select{background:#0f0f15;border:1px solid #2b2638;color:#fff;padding:10px;border-radius:10px}.row{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0}.btn{border:1px solid #6f45a8;background:#9b5cff;color:#0b0810;font-weight:800;padding:11px 15px;border-radius:11px;cursor:pointer}.out{white-space:pre-wrap;background:#0c0c11;border:1px solid #252131;border-radius:14px;padding:14px;color:#bdb5ca;min-height:80px}@media(max-width:800px){.grid{grid-template-columns:repeat(2,1fr)}}
    </style></head><body><div class='card'><h1>BuildYourPC Admin</h1>
    <p class='muted'>Live pricing is optional. Use official/authorized APIs or feeds only. eBay Browse requires an application access token; Best Buy requires its API key and its terms apply.</p>
    <div class='row'><input id='token' placeholder='ADMIN_TOKEN' style='min-width:280px'><button class='btn' id='saveToken'>Save token</button></div>
    <div id='stats' class='grid'>Loading…</div>
    <hr style='border-color:#292536;margin:28px 0'><h2>Live price sync</h2><div class='row'><input id='country' value='US' style='width:110px'><label><input type='checkbox' id='ebay' checked> eBay</label><label><input type='checkbox' id='bestbuy' checked> Best Buy</label><button class='btn' id='sync'>Sync live prices</button><button class='btn' id='fx'>Refresh FX</button></div>
    <div id='out' class='out'>Waiting…</div>
    <hr style='border-color:#292536;margin:28px 0'><h2>Manual feeds</h2><p class='muted'>CSV endpoint: <code>POST /api/admin/import-prices</code> with X-Admin-Token. Required: product_id, store, country, currency, price, product_url.</p>
    </div><script>
    const tokenEl=document.getElementById('token');tokenEl.value=sessionStorage.getItem('byp_admin_token')||'';
    const readJson=async r=>{const raw=await r.text();let x={};try{x=raw?JSON.parse(raw):{}}catch{x={error:{message:'Invalid server response'}}}if(!r.ok)throw new Error(x.error?.message||x.error||`${r.status} ${r.statusText}`);return x};
    document.getElementById('saveToken').onclick=()=>{sessionStorage.setItem('byp_admin_token',tokenEl.value);loadStats();};
    async function loadStats(){try{const r=await fetch('/api/admin/stats',{headers:{Accept:'application/json','X-Admin-Token':tokenEl.value}});const x=await readJson(r);document.getElementById('stats').innerHTML=Object.entries(x).map(([k,v])=>`<div class='stat'><div class='muted'>${k}</div><strong>${v}</strong></div>`).join('')}catch(e){document.getElementById('stats').innerHTML=`<div class='muted'>${e.message}</div>`}}
    document.getElementById('sync').onclick=async()=>{const providers=[];if(document.getElementById('ebay').checked)providers.push('ebay');if(document.getElementById('bestbuy').checked)providers.push('bestbuy');document.getElementById('out').textContent='Syncing…';try{const r=await fetch('/api/admin/sync-live',{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json','X-Admin-Token':tokenEl.value},body:JSON.stringify({country:document.getElementById('country').value.toUpperCase(),providers})});document.getElementById('out').textContent=JSON.stringify(await readJson(r),null,2);loadStats()}catch(e){document.getElementById('out').textContent=e.message}};
    document.getElementById('fx').onclick=async()=>{document.getElementById('out').textContent='Refreshing FX…';try{const r=await fetch('/api/fx/refresh',{headers:{Accept:'application/json','X-Admin-Token':tokenEl.value}});document.getElementById('out').textContent=JSON.stringify(await readJson(r),null,2)}catch(e){document.getElementById('out').textContent=e.message}};
    loadStats();
    </script></body></html>
    """
    return html


@app.get("/build/<build_id>")
def build_page(build_id: str):
    return send_from_directory(app.static_folder, "index.html")


@app.get("/sitemap.xml")
def sitemap():
    base = request.host_url.rstrip("/")
    con = db(); rows = con.execute("SELECT id, created_at FROM builds ORDER BY created_at DESC LIMIT 5000").fetchall(); con.close()
    urls = [f"<url><loc>{base}/</loc></url>", f"<url><loc>{base}/#builder</loc></url>"]
    for row in rows:
        urls.append(f"<url><loc>{base}/build/{row['id']}</loc><lastmod>{str(row['created_at'])[:10]}</lastmod></url>")
    xml = "<?xml version='1.0' encoding='UTF-8'?><urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>" + "".join(urls) + "</urlset>"
    return app.response_class(xml, mimetype="application/xml")


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def static_files(path: str):
    candidate = ROOT / "frontend" / path
    if candidate.exists() and candidate.is_file():
        return send_from_directory(ROOT / "frontend", path)
    return send_from_directory(ROOT / "frontend", "index.html")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
