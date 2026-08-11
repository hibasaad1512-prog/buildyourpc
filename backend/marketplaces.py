from __future__ import annotations

from urllib.parse import quote_plus


def _url(template: str, query: str) -> str:
    return template.format(q=quote_plus(query))

# Search links only: these are user-facing marketplace choices, not scraped prices.
# Live prices still come from permitted feeds/APIs and are kept separate.
MARKETPLACES = [
    {"name": "Facebook Marketplace", "countries": "*", "url": "https://www.facebook.com/marketplace/search/?query={q}"},
    {"name": "eBay", "countries": "*", "url": "https://www.ebay.com/sch/i.html?_nkw={q}"},
    {"name": "AliExpress", "countries": "*", "url": "https://www.aliexpress.com/w/wholesale-{q}.html"},
    {"name": "Amazon", "countries": "*", "url": "https://www.amazon.com/s?k={q}"},
    {"name": "Newegg", "countries": {"US", "CA"}, "url": "https://www.newegg.com/p/pl?d={q}"},
    {"name": "Best Buy", "countries": {"US", "CA"}, "url": "https://www.bestbuy.com/site/searchpage.jsp?st={q}"},
    {"name": "Walmart", "countries": {"US", "CA", "MX"}, "url": "https://www.walmart.com/search?q={q}"},
    {"name": "Micro Center", "countries": {"US"}, "url": "https://www.microcenter.com/search/search_results.aspx?Ntt={q}"},
    {"name": "B&H Photo", "countries": {"US"}, "url": "https://www.bhphotovideo.com/c/search?q={q}"},
    {"name": "Jumia", "countries": {"MA", "EG", "NG", "KE", "GH", "CI", "UG"}, "url": "https://www.jumia.{domain}/catalog/?q={q}"},
    {"name": "Jiji", "countries": {"NG", "GH", "KE", "UG", "TZ"}, "url": "https://jiji.{domain}/search?query={q}"},
    {"name": "Noon", "countries": {"AE", "SA", "EG"}, "url": "https://www.noon.com/{domain}/search/?q={q}"},
    {"name": "Jarir", "countries": {"SA"}, "url": "https://www.jarir.com/sa-en/catalogsearch/result/?q={q}"},
    {"name": "Extra", "countries": {"SA"}, "url": "https://www.extra.com/en-sa/search?q={q}"},
    {"name": "Takealot", "countries": {"ZA"}, "url": "https://www.takealot.com/all?qsearch={q}"},
    {"name": "Konga", "countries": {"NG"}, "url": "https://www.konga.com/catalogsearch/result/?q={q}"},
    {"name": "Mercado Libre", "countries": {"AR", "BO", "BR", "CL", "CO", "CR", "DO", "EC", "GT", "HN", "MX", "NI", "PA", "PE", "PY", "SV", "UY"}, "url": "https://www.mercadolibre.{domain}/search?q={q}"},
    {"name": "Flipkart", "countries": {"IN"}, "url": "https://www.flipkart.com/search?q={q}"},
    {"name": "Croma", "countries": {"IN"}, "url": "https://www.croma.com/searchB?q={q}"},
    {"name": "Reliance Digital", "countries": {"IN"}, "url": "https://www.reliancedigital.in/search?q={q}"},
    {"name": "Coupang", "countries": {"KR"}, "url": "https://www.coupang.com/np/search?q={q}"},
    {"name": "Gmarket", "countries": {"KR"}, "url": "https://browse.gmarket.co.kr/search?keyword={q}"},
    {"name": "Yodobashi", "countries": {"JP"}, "url": "https://www.yodobashi.com/?word={q}"},
    {"name": "Bic Camera", "countries": {"JP"}, "url": "https://www.biccamera.com/bc/category/?q={q}"},
    {"name": "Rakuten", "countries": {"JP"}, "url": "https://search.rakuten.co.jp/search/mall/{q}/"},
    {"name": "Shopee", "countries": {"SG", "MY", "ID", "TH", "VN", "PH", "TW"}, "url": "https://shopee.{domain}/search?keyword={q}"},
    {"name": "Lazada", "countries": {"SG", "MY", "ID", "TH", "VN", "PH"}, "url": "https://www.lazada.{domain}/catalog/?q={q}"},
    {"name": "Cdiscount", "countries": {"FR"}, "url": "https://www.cdiscount.com/search/10/{q}.html"},
    {"name": "LDLC", "countries": {"FR", "BE", "CH", "LU"}, "url": "https://www.ldlc.com/recherche/{q}/"},
    {"name": "Fnac", "countries": {"FR", "BE", "CH"}, "url": "https://www.fnac.com/SearchResult/ResultList.aspx?Search={q}"},
    {"name": "Currys", "countries": {"GB", "IE"}, "url": "https://www.currys.co.uk/search?q={q}"},
    {"name": "PCComponentes", "countries": {"ES", "PT"}, "url": "https://www.pccomponentes.com/buscar/?query={q}"},
    {"name": "MediaMarkt", "countries": {"DE", "ES", "IT", "NL", "AT", "BE"}, "url": "https://www.mediamarkt.{domain}/search.html?query={q}"},
    {"name": "Mindfactory", "countries": {"DE"}, "url": "https://www.mindfactory.de/Hardware.html?search={q}"},
    {"name": "Caseking", "countries": {"DE", "AT"}, "url": "https://www.caseking.de/en/search?sSearch={q}"},
    {"name": "Boulanger", "countries": {"FR"}, "url": "https://www.boulanger.com/resultats?tr={q}"},
    {"name": "Skroutz", "countries": {"GR", "CY"}, "url": "https://www.skroutz.gr/search?keyphrase={q}"},
    {"name": "PcGarage", "countries": {"RO"}, "url": "https://www.pcgarage.ro/cauta/{q}/"},
]

# Country -> common retail domain used by global marketplace templates above.
DOMAINS = {
    "MA": {"amazon": "amazon.ma", "jumia": "ma", "jiji": "ma"},
    "EG": {"amazon": "amazon.eg", "jumia": "eg", "jiji": "eg", "noon": "egypt-en"},
    "NG": {"amazon": "amazon.com", "jumia": "ng", "jiji": "ng"},
    "KE": {"amazon": "amazon.com", "jumia": "ke", "jiji": "ke"},
    "GH": {"amazon": "amazon.com", "jumia": "gh", "jiji": "gh"},
    "CI": {"jumia": "ci"}, "UG": {"jumia": "ug", "jiji": "ug"}, "TZ": {"jiji": "co.tz"},
    "AE": {"amazon": "amazon.ae", "noon": "uae-en"},
    "SA": {"amazon": "amazon.sa", "noon": "saudi-en"},
    "ZA": {"amazon": "amazon.com", "jiji": "co.za"},
    "AR": {"mercadolibre": "com.ar"}, "BO": {"mercadolibre": "com.bo"}, "BR": {"mercadolibre": "com.br"},
    "CL": {"mercadolibre": "cl"}, "CO": {"mercadolibre": "com.co"}, "CR": {"mercadolibre": "co.cr"},
    "DO": {"mercadolibre": "com.do"}, "EC": {"mercadolibre": "com.ec"}, "GT": {"mercadolibre": "com.gt"},
    "HN": {"mercadolibre": "hn"}, "MX": {"mercadolibre": "com.mx"}, "NI": {"mercadolibre": "com.ni"},
    "PA": {"mercadolibre": "com.pa"}, "PE": {"mercadolibre": "com.pe"}, "PY": {"mercadolibre": "com.py"},
    "SV": {"mercadolibre": "com.sv"}, "UY": {"mercadolibre": "com.uy"},
    "SG": {"amazon": "amazon.sg", "shopee": "sg", "lazada": "sg"}, "MY": {"amazon": "amazon.com", "shopee": "my", "lazada": "my"},
    "ID": {"shopee": "co.id", "lazada": "co.id"}, "TH": {"shopee": "co.th", "lazada": "co.th"},
    "VN": {"shopee": "vn", "lazada": "vn"}, "PH": {"shopee": "ph", "lazada": "com.ph"}, "TW": {"shopee": "tw"},
    "DE": {"amazon": "amazon.de", "mediamarkt": "de"}, "ES": {"amazon": "amazon.es", "mediamarkt": "es"},
    "IT": {"amazon": "amazon.it", "mediamarkt": "it"}, "NL": {"amazon": "amazon.nl", "mediamarkt": "nl"},
    "BE": {"amazon": "amazon.com.be", "mediamarkt": "be"}, "AT": {"amazon": "amazon.de", "mediamarkt": "at"},
}


def marketplace_offers(*, product_name: str, country: str, currency: str, existing_names: set[str] | None = None) -> list[dict]:
    country = str(country or "US").upper()
    query = product_name.strip()
    domains = DOMAINS.get(country, {})
    existing_names = existing_names or set()
    out: list[dict] = []
    for row in MARKETPLACES:
        allowed = row["countries"]
        if allowed != "*" and country not in allowed:
            continue
        name = row["name"]
        if name in existing_names:
            continue
        # Template substitution with market-specific domains where applicable.
        try:
            template = row["url"]
            if "{domain}" in template:
                domain_key = name.lower().replace(" ", "")
                domain = domains.get(domain_key)
                if not domain:
                    continue
                url = _url(template.replace("{domain}", domain), query)
            elif name == "Amazon" and country in DOMAINS and "amazon" in domains:
                url = _url(template.replace("www.amazon.com", f"www.{domains['amazon']}"), query)
            else:
                url = _url(template, query)
        except Exception:
            continue
        out.append({
            "store": name,
            "price": None,
            "currency": currency,
            "url": url,
            "availability": "Search this marketplace",
            "affiliate_ready": False,
            "captured_at": None,
            "source": "marketplace-search",
            "stale": False,
            "live": False,
        })
    return out
