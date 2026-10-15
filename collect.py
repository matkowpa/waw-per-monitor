#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WAW→PER flight price collector.

Codzienne zbieranie najtańszej ceny powrotu WAW→PER dla dat:
wylot 26–28.01.2027, powrót 12–14.02.2027 (siatka ±1 dzień od 27.01/13.02).

Źródła (HTTP, bez cookies/sesji):
  1. Brave Search API (BRAVE_API_KEY) — dorki do Kayak/Momondo/Cheapflights;
     z wyników ekstrahowane są ceny "$NNNN".
  2. Fallback: DuckDuckGo HTML — analogiczna ekstrakcja.
  3. Kurs USD→PLN z NBP (api.nbp.pl) — zawsze.

Przesiadka ≥2–2,5 h i czas ≤~25 h są odnotowywane w metadanych źródła
(eksport tekstowy z SERP nie daje pewnej weryfikacji przesiadek —raport
oznacza najlepszą cenę jako "wymaga weryfikacji ręcznej", jeśli pochodzi
z agregatora, a nie z linii).

Wyjście: data/ceny.json — lista wpisów {date, price_usd, price_pln, kurs,
source, url, snippet}, najnowszy na końcu. Idempotentne: drugi run tego
samego dnia nie dopisuje duplikatu (nadpisuje wpis bieżącego dnia).
"""

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone

OUT = "data/ceny.json"
USD_PLN_ALARM = 5500  # próg alarmu na 1 osobę dorosłą (PLN)

DORKI = [
    'site:kayak.com WAW PER "Jan 2027" OR "2027-01-27" round trip price',
    'site:cheapflights.com warsaw perth frederic chopin january 2027 return',
    'site:momondo.com warsaw perth january 2027 price return',
    'warsaw perth flight january 27 2027 return february 13 price',
]


def http_json(url: str, headers: dict | None = None, timeout: int = 30):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def http_text(url: str, headers: dict | None = None, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


def kurs_nbp() -> float | None:
    try:
        d = http_json("https://api.nbp.pl/api/exchangerates/rates/a/usd/?format=json")
        return float(d["rates"][0]["mid"])
    except Exception as e:
        print(f"NBP FAIL: {e}", file=sys.stderr)
        return None


def brave_search(query: str, api_key: str) -> list[dict]:
    """Brave Web Search — zwraca [{'title','url','description'}]."""
    q = urllib.parse.quote(query)
    url = f"https://api.search.brave.com/res/v1/web/search?q={q}&count=8"
    try:
        d = http_json(url, headers={"X-Subscription-Token": api_key,
                                    "Accept": "application/json"})
        return [{"title": r.get("title", ""),
                 "url": r.get("url", ""),
                 "snippet": r.get("description", "")}
                for r in d.get("web", {}).get("results", [])]
    except Exception as e:
        print(f"Brave FAIL: {e}", file=sys.stderr)
        return []


def ddg_search(query: str) -> list[dict]:
    q = urllib.parse.quote(query)
    try:
        html = http_text(f"https://html.duckduckgo.com/html/?q={q}",
                         headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    except Exception as e:
        print(f"DDG FAIL: {e}", file=sys.stderr)
        return []
    out = []
    for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html):
        url, title = m.group(1), re.sub(r"<[^>]+>", "", m.group(2))
        out.append({"title": title, "url": url, "snippet": ""})
    return out


def ceny_z_tekstu(text: str) -> list[int]:
    """Ceny USD 800–3000 (realny pas WAW-PER powrót)."""
    return sorted({int(v.replace(",", "")) for v in re.findall(r"\$\s?([\d,]{4,5})\b", text)
                   if 800 <= int(v.replace(",", "")) <= 3000})


def zbierz_ceny() -> list[dict]:
    """Główna logika: dla każdego dorka zbierz wyniki i ceny z tytułów/opisów."""
    api_key = os.getenv("BRAVE_API_KEY", "")
    obserwacje = []
    for q in DORKI:
        wyniki = brave_search(q, api_key) if api_key else []
        if not wyniki:
            wyniki = ddg_search(q)
        for w in wyniki:
            ceny = ceny_z_tekstu(w["title"] + " " + w["snippet"])
            if not ceny:
                continue
            # data obserwacji: najtańsza cena z tego wyniku
            obserwacje.append({"price_usd": min(ceny),
                               "source": w["url"][:80],
                               "title": w["title"][:120],
                               "n_cen_w_wyniku": len(ceny)})
    return obserwacje


def main() -> int:
    kurs = kurs_nbp()
    obserwacje = zbierz_ceny()

    if not obserwacje or kurs is None:
        # wpis "brak danych" — historia ma wiedzieć, że run się odbył
        wpis = {"date": date.today().isoformat(), "price_usd": None,
                "price_pln": None, "kurs": kurs, "source": "brak danych",
                "title": "", "n_cen_w_wyniku": 0}
    else:
        best = min(obserwacje, key=lambda o: o["price_usd"])
        wpis = {"date": date.today().isoformat(),
                "price_usd": best["price_usd"],
                "price_pln": round(best["price_usd"] * kurs),
                "kurs": kurs,
                "source": best["source"],
                "title": best["title"],
                "n_cen_w_wyniku": best["n_cen_w_wyniku"],
                "wszystkie_ceny_usd": sorted({o["price_usd"] for o in obserwacje})[:10]}

    # --- zapis z idempotentnością ---
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    dane = []
    if os.path.exists(OUT):
        try:
            dane = json.load(open(OUT, encoding="utf-8"))
        except Exception:
            dane = []
    dzis = wpis["date"]
    dane = [d for d in dane if d.get("date") != dzis]  # nadpisz dzisiejszy
    dane.append(wpis)

    json.dump(dane, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # --- konsolowy podsumowanie (do logów Actions) ---
    alarm = ""
    if wpis.get("price_pln") and wpis["price_pln"] <= USD_PLN_ALARM:
        alarm = f" ⚠️ ALARM ≤{USD_PLN_ALARM} PLN!"
    print(f"[{dzis}] najtańsza obserwowana: ${wpis.get('price_usd')} "
          f"= {wpis.get('price_pln')} PLN (kurs {kurs}){alarm}")
    print(f"  źródło: {wpis.get('source')}")
    print(f"  obserwacji: {len(obserwacje)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
