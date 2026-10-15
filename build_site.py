#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Buduje docs/index.html z tabelą historii cen (cała historia, nie tylko ostatni dzień)."""

import json
import os

KURS_ZAPAS = 3.90
ALARM = 5500

def fmt(v):
    return "—" if v is None else f"{v:,}".replace(",", " ")

def main():
    dane = json.load(open("data/ceny.json", encoding="utf-8")) if os.path.exists("data/ceny.json") else []

    wiersze = []
    for d in reversed(dane):  # najnowszy na górze
        pln = d.get("price_pln")
        alarm = ' <span class="alarm">⚠ ALARM ≤5 500</span>' if pln and pln <= ALARM else ""
        wiersze.append(
            f"<tr><td>{d.get('date')}</td>"
            f"<td>{fmt(d.get('price_usd'))} $</td>"
            f"<td>{fmt(pln)} zł{alarm}</td>"
            f"<td>{d.get('kurs') or '—'}</td>"
            f"<td><a href='{d.get('source') or '#'}'>{(d.get('title') or d.get('source') or '')[:60]}</a></td>"
            f"<td>{fmt(d.get('n_cen_w_wyniku'))}</td></tr>"
        )

    najt = min((d["price_pln"] for d in dane if d.get("price_pln")), default=None)
    tabela = "\n".join(wiersze) or "<tr><td colspan='6'>Brak danych — pierwszy run jeszcze się nie odbył</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="pl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WAW→PER monitor cen lotów</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;color:#222}}
h1{{font-size:1.4rem}} table{{border-collapse:collapse;width:100%;font-size:.9rem}}
th,td{{border:1px solid #ddd;padding:6px 8px;text-align:left}}
th{{background:#f4f4f4;position:sticky;top:0}}
.alarm{{color:#b00;font-weight:bold}}
.note{{color:#666;font-size:.85rem}}
</style></head><body>
<h1>✈️ Warszawa → Perth — monitor cen</h1>
<p><b>Kryteria:</b> wylot 26–28.01.2027, powrót 12–14.02.2027 · 1 przesiadka ≥2–2,5 h · czas ≤ ~25 h ·
próg alarmu ≤ 5 500 zł/os. dorosłej · kurs NBP bieżącego dnia.<br>
<span class="note">Cena = obserwowana w agregatorach (Kayak/Cheapflights/Momondo) — przed zakupem zweryfikuj ręcznie.
Szacunek za 2 osoby (dorosły + dziecko 13 l.): ×1,75–2,00.</span></p>
<p><b>Najtańsza w historii: {fmt(najt)} zł</b> · wpisów: {len(dane)} · ostatnia aktualizacja: {dane[-1]['date'] if dane else '—'}</p>
<table><thead><tr><th>Data</th><th>Cena USD</th><th>Cena PLN</th><th>Kurs NBP</th><th>Źródło</th><th>Obserwacji</th></tr></thead>
<tbody>{tabela}</tbody></table>
<p class="note">Dane: <a href="data/ceny.json">data/ceny.json</a> · aktualizacja codziennie ~08:00 czasu PL.</p>
</body></html>"""
    os.makedirs("docs", exist_ok=True)
    open("docs/index.html", "w", encoding="utf-8").write(html)
    print(f"docs/index.html zbudowany ({len(dane)} wpisów, najtańsza {najt} zł)")


if __name__ == "__main__":
    main()
