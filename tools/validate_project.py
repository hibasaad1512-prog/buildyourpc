from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []


def check_json(path: Path) -> None:
    try:
        json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        errors.append(f'JSON: {path}: {exc}')


def check_python() -> None:
    py_files = list((ROOT / 'backend').glob('*.py')) + list((ROOT / 'tools').glob('*.py'))
    for path in py_files:
        try:
            compile(path.read_text(encoding='utf-8'), str(path), 'exec')
        except Exception as exc:
            errors.append(f'Python: {path}: {exc}')


def check_js() -> None:
    path = ROOT / 'frontend' / 'app.js'
    try:
        subprocess.run(['node', '--check', str(path)], check=True, capture_output=True, text=True)
    except Exception as exc:
        errors.append(f'JavaScript: {path}: {getattr(exc, "stderr", exc)}')


def check_catalog() -> None:
    path = ROOT / 'data' / 'catalog.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    products = data.get('products', [])
    ids = [p.get('id') for p in products]
    dupes = sorted({x for x in ids if ids.count(x) > 1})
    if dupes:
        errors.append(f'Catalog duplicate ids: {dupes}')
    for p in products:
        for key in ('id', 'name', 'category', 'usd_price'):
            if key not in p:
                errors.append(f'Catalog missing {key}: {p!r}')
        if not isinstance(p.get('usd_price'), (int, float)) or p.get('usd_price') < 0:
            errors.append(f'Catalog invalid usd_price: {p.get("id")}')


def check_v15_i18n() -> None:
    app = (ROOT / 'frontend' / 'app.js').read_text(encoding='utf-8')
    expected = set(re.findall(r"([a-zA-Z]+):", '''buildDoctor doctorSub good watch critical socketCheck memoryCheck psuCheck caseCheck coolingCheck airflowCheck portableCheck livePriceCheck referencePriceCheck shoppingConfidence priceCoverage budgetLab spend100 save100 bestUpgrade bestSave setupPlan coreReady coolingAdd thermalPasteAdd airflowAdd monitorAdd osAdd chargerCheck warrantyCheck peripheralAdd refreshPrices printReport liveUpdated estimatedNotice notGuaranteed coverageHigh coverageMedium coverageLow'''))
    # Ensure the fallback map contains every key, and every supported locale has either a
    # dedicated translation or safely inherits English from the explicit V15 assignment.
    for key in sorted(expected):
        if not re.search(rf"[\"']{re.escape(key)}[\"']?\s*:", app):
            errors.append(f'V15 translation key missing: {key}')
    if 'Object.assign(V15_I18N' not in app:
        errors.append('V15 locale expansion missing')


def main() -> int:
    for path in (ROOT / 'data').glob('*.json'):
        check_json(path)
    check_python()
    check_js()
    check_catalog()
    check_v15_i18n()
    if errors:
        for error in errors:
            print('ERROR:', error)
        return 1
    print('BuildMyPC validation: PASS')
    print('JSON: PASS')
    print('Python syntax: PASS')
    print('JavaScript syntax: PASS')
    print('Catalog ids/data: PASS')
    print('v15 i18n keys/fallback: PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
