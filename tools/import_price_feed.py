from __future__ import annotations

import argparse
import csv
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data' / 'buildyourpc.sqlite3'

REQUIRED = {'product_id','store','country','currency','price','product_url'}


def main() -> None:
    ap = argparse.ArgumentParser(description='Import a verified retailer CSV into BuildYourPC SQLite.')
    ap.add_argument('csv_path')
    ap.add_argument('--source', default='manual-import')
    args = ap.parse_args()
    path = Path(args.csv_path)
    rows = list(csv.DictReader(path.read_text(encoding='utf-8-sig').splitlines()))
    headers = set(rows[0].keys()) if rows else set()
    missing = REQUIRED - headers
    if missing:
        raise SystemExit(f'Missing columns: {sorted(missing)}')
    con = sqlite3.connect(DB)
    con.execute('CREATE TABLE IF NOT EXISTS prices (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id TEXT, store TEXT, country TEXT, currency TEXT, price REAL, availability TEXT, product_url TEXT, affiliate_url TEXT, captured_at TEXT, source TEXT)')
    now = datetime.now(timezone.utc).isoformat()
    for r in rows:
        con.execute('INSERT INTO prices(product_id,store,country,currency,price,availability,product_url,affiliate_url,captured_at,source) VALUES(?,?,?,?,?,?,?,?,?,?)', (r['product_id'],r['store'],r['country'],r['currency'],float(r['price']),r.get('availability','unknown'),r['product_url'],r.get('affiliate_url') or None,r.get('captured_at') or now,args.source))
    con.commit(); con.close()
    print(f'Imported {len(rows)} price rows.')

if __name__ == '__main__':
    main()
