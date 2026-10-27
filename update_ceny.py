#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dopisuje dzisiejszy pomiar do data/ceny.json (price_pln = najtańsza oferta OK)."""
import json
import os
from datetime import date, datetime, timezone, timedelta

KURS = 3.9293  # NBP tabela 208/A/NBP/2026, effectiveDate 2026-10-26
DZIEN = datetime.now(timezone(timedelta(hours=2))).date().isoformat()

CENY = "data/ceny.json"
OFERTY = "data/oferty_dzis.json"

dane = json.load(open(CENY, encoding="utf-8")) if os.path.exists(CENY) else []
oferty = [o for o in json.load(open(OFERTY, encoding="utf-8"))["oferty"] if o.get("ok")]
oferty.sort(key=lambda o: o["cena_zl"])
naj = oferty[0]
pln = naj["cena_zl"]

rekord = {
    "date": DZIEN,
    "price_usd": round(pln / KURS, 1),
    "price_pln": pln,
    "kurs": KURS,
    "source": "https://www.google.com/travel/flights (gf-all.js)",
    "title": (f"GF siatka 35 par dat WAW-PER, {len(oferty)} ofert OK; "
              f"najtansza: {naj['wariant']} {naj['linie']}"),
    "n_cen_w_wyniku": len(oferty),
    "wszystkie_ceny_usd": [],
}

dane = [d for d in dane if d.get("date") != DZIEN]
dane.append(rekord)
dane.sort(key=lambda d: d["date"])
json.dump(dane, open(CENY, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

prev = next((d for d in reversed(dane[:-1]) if d.get("price_pln")), None)
print(f"zapisano {DZIEN}: {pln} zł | {rekord['price_usd']} $ | kurs {KURS} | ofert OK {len(oferty)}")
if prev:
    delta = pln - prev["price_pln"]
    print(f"vs {prev['date']} ({prev['price_pln']} zł): {delta:+d} zł ({delta / prev['price_pln'] * 100:+.1f}%)")
print(f"ALARM (<=5500): {'TAK' if pln <= 5500 else 'nie'}")
print(f"2 os. (1.75x-2.00x): {round(pln * 1.75)} - {round(pln * 2.00)} zł")
