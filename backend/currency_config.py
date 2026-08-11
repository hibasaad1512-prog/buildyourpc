from __future__ import annotations

# One source of truth for currency display, validation and conversion fallback.
# Rates are local-currency units per USD and are intentionally used only as a
# resilient fallback when live EUR rates are unavailable.
CURRENCY_CONFIG = {
    'USD': {'name': 'US Dollar', 'symbol': '$', 'locale': 'en-US', 'decimalDigits': 0, 'rateToUSD': 1.0},
    'EUR': {'name': 'Euro', 'symbol': '€', 'locale': 'fr-FR', 'decimalDigits': 0, 'rateToUSD': 0.92},
    'GBP': {'name': 'British Pound', 'symbol': '£', 'locale': 'en-GB', 'decimalDigits': 0, 'rateToUSD': 0.79},
    'CAD': {'name': 'Canadian Dollar', 'symbol': 'CA$', 'locale': 'en-CA', 'decimalDigits': 0, 'rateToUSD': 1.37},
    'AUD': {'name': 'Australian Dollar', 'symbol': 'A$', 'locale': 'en-AU', 'decimalDigits': 0, 'rateToUSD': 1.53},
    'MAD': {'name': 'Moroccan Dirham', 'symbol': 'MAD', 'locale': 'fr-MA', 'decimalDigits': 0, 'rateToUSD': 9.6},
    'DZD': {'name': 'Algerian Dinar', 'symbol': 'دج', 'locale': 'ar-DZ', 'decimalDigits': 0, 'rateToUSD': 133.5},
    'AED': {'name': 'UAE Dirham', 'symbol': 'AED', 'locale': 'en-AE', 'decimalDigits': 0, 'rateToUSD': 3.67},
    'SAR': {'name': 'Saudi Riyal', 'symbol': 'SAR', 'locale': 'en-SA', 'decimalDigits': 0, 'rateToUSD': 3.75},
    'INR': {'name': 'Indian Rupee', 'symbol': '₹', 'locale': 'en-IN', 'decimalDigits': 0, 'rateToUSD': 83.5},
    'JPY': {'name': 'Japanese Yen', 'symbol': '¥', 'locale': 'ja-JP', 'decimalDigits': 0, 'rateToUSD': 150.0},
    'BRL': {'name': 'Brazilian Real', 'symbol': 'R$', 'locale': 'pt-BR', 'decimalDigits': 0, 'rateToUSD': 5.2},
    'TRY': {'name': 'Turkish Lira', 'symbol': '₺', 'locale': 'tr-TR', 'decimalDigits': 0, 'rateToUSD': 33.0},
    'CHF': {'name': 'Swiss Franc', 'symbol': 'CHF', 'locale': 'de-CH', 'decimalDigits': 0, 'rateToUSD': 0.90},
    'SEK': {'name': 'Swedish Krona', 'symbol': 'SEK', 'locale': 'sv-SE', 'decimalDigits': 0, 'rateToUSD': 10.5},
    'NOK': {'name': 'Norwegian Krone', 'symbol': 'NOK', 'locale': 'nb-NO', 'decimalDigits': 0, 'rateToUSD': 10.7},
    'DKK': {'name': 'Danish Krone', 'symbol': 'DKK', 'locale': 'da-DK', 'decimalDigits': 0, 'rateToUSD': 6.9},
    'PLN': {'name': 'Polish Zloty', 'symbol': 'PLN', 'locale': 'pl-PL', 'decimalDigits': 0, 'rateToUSD': 4.0},
    'CZK': {'name': 'Czech Koruna', 'symbol': 'CZK', 'locale': 'cs-CZ', 'decimalDigits': 0, 'rateToUSD': 23.0},
    'HUF': {'name': 'Hungarian Forint', 'symbol': 'HUF', 'locale': 'hu-HU', 'decimalDigits': 0, 'rateToUSD': 360.0},
    'RON': {'name': 'Romanian Leu', 'symbol': 'RON', 'locale': 'ro-RO', 'decimalDigits': 0, 'rateToUSD': 4.6},
    'ZAR': {'name': 'South African Rand', 'symbol': 'R', 'locale': 'en-ZA', 'decimalDigits': 0, 'rateToUSD': 18.0},
    'MXN': {'name': 'Mexican Peso', 'symbol': 'MX$', 'locale': 'es-MX', 'decimalDigits': 0, 'rateToUSD': 17.5},
    'NZD': {'name': 'New Zealand Dollar', 'symbol': 'NZ$', 'locale': 'en-NZ', 'decimalDigits': 0, 'rateToUSD': 1.65},
    'SGD': {'name': 'Singapore Dollar', 'symbol': 'S$', 'locale': 'en-SG', 'decimalDigits': 0, 'rateToUSD': 1.35},
    'HKD': {'name': 'Hong Kong Dollar', 'symbol': 'HK$', 'locale': 'en-HK', 'decimalDigits': 0, 'rateToUSD': 7.8},
    'CNY': {'name': 'Chinese Yuan', 'symbol': '¥', 'locale': 'zh-CN', 'decimalDigits': 0, 'rateToUSD': 7.2},
    'KRW': {'name': 'South Korean Won', 'symbol': '₩', 'locale': 'ko-KR', 'decimalDigits': 0, 'rateToUSD': 1350.0},
    'THB': {'name': 'Thai Baht', 'symbol': '฿', 'locale': 'th-TH', 'decimalDigits': 0, 'rateToUSD': 36.0},
    'IDR': {'name': 'Indonesian Rupiah', 'symbol': 'Rp', 'locale': 'id-ID', 'decimalDigits': 0, 'rateToUSD': 16000.0},
    'MYR': {'name': 'Malaysian Ringgit', 'symbol': 'RM', 'locale': 'ms-MY', 'decimalDigits': 0, 'rateToUSD': 4.7},
    'ILS': {'name': 'Israeli New Shekel', 'symbol': '₪', 'locale': 'he-IL', 'decimalDigits': 0, 'rateToUSD': 3.6},
    'TWD': {'name': 'New Taiwan Dollar', 'symbol': 'NT$', 'locale': 'zh-TW', 'decimalDigits': 0, 'rateToUSD': 32.5},
    'VND': {'name': 'Vietnamese Dong', 'symbol': '₫', 'locale': 'vi-VN', 'decimalDigits': 0, 'rateToUSD': 25000.0},
    'PHP': {'name': 'Philippine Peso', 'symbol': '₱', 'locale': 'en-PH', 'decimalDigits': 0, 'rateToUSD': 58.0},
    'UAH': {'name': 'Ukrainian Hryvnia', 'symbol': '₴', 'locale': 'uk-UA', 'decimalDigits': 0, 'rateToUSD': 41.0},
    'RUB': {'name': 'Russian Ruble', 'symbol': '₽', 'locale': 'ru-RU', 'decimalDigits': 0, 'rateToUSD': 90.0},
}

# Product-budget bounds are expressed independently in USD, then converted to
# each selected currency so every currency has its own stored, configurable limits.
BASE_MIN_USD = 150.0
BASE_MAX_USD = 10000.0


def get_currency(code: str) -> dict:
    code = str(code or 'USD').upper()
    if code not in CURRENCY_CONFIG:
        raise ValueError(f'Unsupported currency: {code}')
    cfg = dict(CURRENCY_CONFIG[code])
    rate = float(cfg['rateToUSD'])
    cfg['minimum'] = round(BASE_MIN_USD * rate)
    cfg['maximum'] = round(BASE_MAX_USD * rate)
    return cfg


def exported_config() -> dict[str, dict]:
    return {code: get_currency(code) for code in CURRENCY_CONFIG}
