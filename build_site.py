#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Buduje docs/index.html z tabelą historii cen (cała historia, nie tylko ostatni dzień)."""

import json
import os
import shutil
import base64

KURS_ZAPAS = 3.90
ALARM = 5500

def gen_tfs(dep, d1, arr, d2):
    """Deep-link Google Flights (protobuf tfs=): daty wpisane w URL."""
    def dep_ap(c): return b'\x6a\x07\x08\x01\x12\x03' + c.encode()
    def arr_ap(c): return b'\x72\x07\x08\x01\x12\x03' + c.encode()
    def seg(a, d, b):
        body = dep_ap(a) + b'\x12\x0a' + d.encode() + arr_ap(b)
        return b'\x1a' + bytes([len(body)]) + body
    payload = (b'\x08\x1c\x10\x02'
        + seg(dep, d1, arr) + seg(arr, d2, dep)
        + b'\x70\x01'
        + b'\x82\x01\x0b\x08' + b'\xff'*9 + b'\x01'
        + b'\x40\x01\x48\x01\x98\x01\x01')
    return base64.urlsafe_b64encode(payload).decode().rstrip('=')

GF_BASE = "https://www.google.com/travel/flights/search?tfs={TFS}&hl=pl&gl=PL&curr=PLN"

def urls():
    w = [("27.01 → 13.02", "2027-01-27", "2027-02-13"),
         ("26.01 → 12.02", "2027-01-26", "2027-02-12"),
         ("28.01 → 14.02", "2027-01-28", "2027-02-14")]
    return {n: GF_BASE.replace("{TFS}", gen_tfs("WAW", a, "PER", b)) for n, a, b in w}

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
    u = urls()

    # Oferta ręczna usera (kombinacja multi-airline, niewidoczna w standardowych wynikach GF):
    OFERTA_USERA = ("https://www.google.com/travel/flights/booking?tfs=CBwQAhqBARIKMjAyNy0wMS0yNiIfCgNXQVcSCjIwMjctMDEtMjYaA1NISioCRzkyAzYwNiIfCgNTSEoSCjIwMjctMDEtMjYaA0tVTCoCRzkyAzgwMCIfCgNLVUwSCjIwMjctMDEtMjcaA1BFUioCQUsyAzYwNmoHCAESA1dBV3IHCAESA1BFUhqBARIKMjAyNy0wMi0xMiIfCgNQRVISCjIwMjctMDItMTIaA0tVTCoCQUsyAzYwNyIeCgNLVUwSCjIwMjctMDItMTMaA0lTVCoCVEsyAjYzIiAKA0lTVBIKMjAyNy0wMi0xMxoDV0FXKgJUSzIEMTc2NWoHCAESA1BFUnIHCAESA1dBV0ABSAFwAYIBCwj___8BmAEB&tfu=CnxDalJJVlZCRVZHVnRWVTV0YlRSQlFXSXhVRUZDUnkwdExTMHRMUzB0TFhaMFltZDBPVUZCUVVGQlIzSlNVMll3UVhwTlJDMUJFaEZCU3pZd04zeFVTell6ZkZSTE1UYzJOUm9MQ0xpQ0lCQUNHZ05RVEU0NEhIRFJuQWc9EgYIACACKAEiAwoBMQ&hl=pl&gl=PL&curr=PLN")

    # Dzisiejsze oferty z Chrome/Google Flights, przefiltrowane twarde kryteria
    oferty = []
    if os.path.exists("data/oferty_dzis.json"):
        try:
            oferty = [o for o in json.load(open("data/oferty_dzis.json", encoding="utf-8")).get("oferty", []) if o.get("ok")]
            oferty.sort(key=lambda x: x["cena_zl"])
        except Exception:
            oferty = []
    oferty_rows = []
    for o in oferty[:8]:
        cz = f"{o['czas_h']}h{o.get('czas_min', 0):02d}" if o.get("czas_h") is not None else "—"
        _pm = o.get("przesiadki_min") or []
        _pg = o.get("przesiadki_gdzie") or []
        prz = "; ".join(f"{x//60}h{x%60:02d} {g}" for x, g in zip(_pm, _pg)) or "bezpośrednio"
        warn = ' <span class="alarm">⚠ ≤5 500</span>' if o["cena_zl"] <= ALARM else ""
        oferty_rows.append(
            f"<tr><td>{o['wariant']}</td><td><b>{o['cena_zl']:,}</b> zł{warn}</td>"
            f"<td>{o['linie']}</td><td>{o['przesiadki']}</td><td>{cz}</td><td>{prz}</td></tr>"
        )
    oferta_tbl = ("\n".join(oferty_rows)
                  or "<tr><td colspan='6'>Brak ofert spełniających kryteria w ostatnim pomiarze</td></tr>")

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
<p><b>Kryteria:</b> wylot 26–28.01.2027, powrót 12–14.02.2027 · przesiadka ≥2–2,5 h · czas lotu ≤ 28 h ·
próg alarmu ≤ 5 500 zł/os. dorosłej · kurs NBP bieżącego dnia.<br>
<span class="note">Ceny czytane bezpośrednio z Google Flights (Chrome na serwerze, codziennie).
Szacunek za 2 osoby (dorosły + dziecko 13 l.): ×1,75–2,00.</span></p>
<p><b>Wyniki na żywo — linki z datami i filtrami wpisanej w adres (klik = lista wyników):</b></p>
<p>🥇 <a href="{u['27.01 → 13.02']}" target="_blank"><b>Google Flights — 27.01 → 13.02</b></a> · <a href="{u['26.01 → 12.02']}" target="_blank">26.01 → 12.02</a> · <a href="{u['28.01 → 14.02']}" target="_blank">28.01 → 14.02</a></p>
<p>🧭 <a href="https://www.skyscanner.pl/transport/loty/waw/per/270127/270213?adultsv2=1&cabinclass=economy&rtn=1" target="_blank"><b>Skyscanner — 27.01 → 13.02</b></a> (daty w adresie; filtr „czas ≤28 h" ustaw suwakiem w panelu — Skyscanner nie przyjmuje go z URL) · <a href="https://www.skyscanner.pl/transport/loty/waw/per/270126/270212?adultsv2=1&cabinclass=economy&rtn=1" target="_blank">26.01 → 12.02</a> · <a href="https://www.skyscanner.pl/transport/loty/waw/per/270128/270214?adultsv2=1&cabinclass=economy&rtn=1" target="_blank">28.01 → 14.02</a></p>
<p><b>Najtańsza w historii: {fmt(najt)} zł</b> · wpisów: {len(dane)} · ostatnia aktualizacja: {dane[-1]['date'] if dane else '—'}</p>
<div style="background:#eaf7ea;border:1px solid #8c8;padding:10px;margin:10px 0">
<b>🎯 Oferta do weryfikacji ręcznej (kombinacja 3 przewoźników — niewidoczna w standardowych wynikach GF):</b><br>
<b>26.01 → 12.02, 2 przesiadki — zgłoszona cena ~5 200 zł/os. tam i z powrotem</b><br>
Tam 26.01: WAW →Szarja (Air Arabia G9606, 12:45–20:35) → Kuala Lumpur (G9 800, ~22:35–09:20+1) → Perth (AirAsia X AK606, ~13:25–19:05, 27.01). Powrót 12.02: PER →KUL (AK607, ~22:15–05:35+1) → Istambuł (TK63, 09:45–15:35, 13.02) → WAW (TK1765, ~19:15–21:00).<br>
Czasy z rozkładów: tam ~24 h 20 min ✓, powrót ~27 h 45 min–28 h 45 min (na granicy 28 h — zweryfikuj przy wyborze).<br>
Przesiadki ≥2 h na obu kierunkach. <a href="{OFERTA_USERA}" target="_blank"><b>Otwórz ofertę w Google Flights →</b></a>
</div>
<h2 style="font-size:1.1rem">Dzisiejsze oferty (Google Flights, przefiltrowane: ≤28 h, przesiadka ≥2 h, maks 2 przesiadki, od najtańszej)</h2>
<table><thead><tr><th>Wariant</th><th>Cena/os.</th><th>Linie</th><th>Przesiadki</th><th>Czas</th><th>Przesiadka (czas, miejsce)</th></tr></thead>
<tbody>{oferta_tbl}</tbody></table>
<h2 style="font-size:1.1rem">Historia pomiarów</h2>
<table><thead><tr><th>Data</th><th>Cena USD</th><th>Cena PLN</th><th>Kurs NBP</th><th>Źródło</th><th>Obserwacji</th></tr></thead>
<tbody>{tabela}</tbody></table>
<p class="note">Dane: <a href="data/ceny.json">data/ceny.json</a> · aktualizacja codziennie ~08:00 czasu PL.</p>
</body></html>"""
    os.makedirs("docs", exist_ok=True)
    open("docs/index.html", "w", encoding="utf-8").write(html)
    os.makedirs("docs/data", exist_ok=True)
    if os.path.exists("data/ceny.json"):
        shutil.copy("data/ceny.json", "docs/data/ceny.json")
    print(f"docs/index.html zbudowany ({len(dane)} wpisów, najtańsza {najt} zł)")


if __name__ == "__main__":
    main()
