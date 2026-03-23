#!/usr/bin/env python3
"""
AgriTracker - Weekly official site scraper
Run: python scraper.py
"""

import json, re, time, sys
from datetime import datetime
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("pip install requests beautifulsoup4")
    sys.exit(1)

HEADERS = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
MONTHS = {"january":1,"february":2,"march":3,"april":4,"may":5,"june":6,"july":7,"august":8,"september":9,"october":10,"november":11,"december":12,"jan":1,"feb":2,"mar":3,"apr":4,"jun":6,"jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}

def fetch(url, delay=2.0):
    try:
        time.sleep(delay)
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  ⚠ {url}: {e}")
        return None

def parse_date(raw):
    raw = raw.replace("\n"," ").strip()
    pat = re.compile(r"([A-Za-z]+)\s+(\d{1,2})\s*[-–]\s*([A-Za-z]+\s+)?(\d{1,2}),?\s*(\d{4})",re.I)
    m = pat.search(raw)
    if not m: return None
    sm = MONTHS.get(m.group(1).lower())
    sd = int(m.group(2))
    em = MONTHS.get((m.group(3) or m.group(1)).strip().lower())
    ed = int(m.group(4))
    yr = int(m.group(5))
    if not sm or not em: return None
    return {"year":yr,"start":f"{yr}-{sm:02d}-{sd:02d}","end":f"{yr}-{em:02d}-{ed:02d}"}

def scrape(url):
    html = fetch(url)
    if not html: return []
    soup = BeautifulSoup(html,"html.parser")
    text = soup.get_text(" ",strip=True)
    results = []
    for chunk in re.split(r'[|\n]',text):
        p = parse_date(chunk)
        if p and p["year"] >= 2025:
            results.append(p)
    return results[:8]

def main():
    data_path = Path(__file__).parent / "data" / "fairs.json"
    with open(data_path,"r",encoding="utf-8") as f:
        data = json.load(f)

    total_changed = 0
    for fair in data["fairs"]:
        url = fair.get("url","")
        print(f"\n[{fair['id']}] {url}")
        if not url: continue
        rows = scrape(url)
        if not rows: print("  no dates found"); continue
        changed = False
        for row in rows:
            yk = str(row["year"])
            ex = fair["dates"].get(yk)
            if ex and not isinstance(ex,type(None)) and ex.get("confirmed") and ex.get("start")==row["start"]:
                continue
            if ex and isinstance(ex,dict) and ex.get("confirmed"):
                continue
            fair["dates"][yk] = {"start":row["start"],"end":row["end"],"confirmed":False}
            print(f"  ✓ {yk}: {row['start']}~{row['end']}")
            changed = True
        if changed: total_changed += 1

    if total_changed > 0:
        data["meta"]["last_updated"] = datetime.utcnow().strftime("%Y-%m-%d")
        with open(data_path,"w",encoding="utf-8") as f:
            json.dump(data,f,ensure_ascii=False,indent=2)
        print(f"\n✅ Updated {total_changed} fair(s).")
    else:
        print("\n— No changes.")
    return total_changed

if __name__ == "__main__":
    sys.exit(0 if main()>=0 else 1)
