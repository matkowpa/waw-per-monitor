# waw-per-monitor

Monitor cen lotów **Warszawa (WAW) → Perth (PER)** — tam i z powrotem, 2 osoby (dorosły + dziecko 13 lat).

## 🌐 Strona z wynikami (live)

**👉 [https://matkowpa.github.io/waw-per-monitor/](https://matkowpa.github.io/waw-per-monitor/)**

Tabela codziennych cen (pełna historia, najnowsze na górze) + gotowe linki do wyników Google Flights z wpisanymi datami:
- wylot **26–28.01.2027**, powrót **12–14.02.2027**
- przesiadka ≥ 2–2,5 h, czas lotu ≤ 28 h
- próg alarmu: ≤ 5 500 zł/os.

## Jak działa

- **Codziennie 6:00 UTC (8:00 WAW)** — cron na serwerze Hermesa otwiera Google Flights w headless Chrome (deep-linki z datami zakodowanymi w parametrze `tfs=`), czyta realne wyniki (cena, linia, przesiadki, czas podróży) i dopisuje wpis do `data/ceny.json`, potem push → GitHub Actions przebudowuje stronę.
- **Brave Search API** (`BRAVE_API_KEY`) — drugie, zapasowe źródło obserwacji cen w `collect.py` (GitHub Actions).
- **Kurs** USD→PLN zawsze z NBP (api.nbp.pl) — ceny USD i PLN obok siebie w historii.
- **Idempotentność** — wpis danego dnia jest nadpisywany, historia nigdy się nie duplikuje.

## Pliki

- `data/ceny.json` — pełna historia pomiarów (data, cena USD/PLN, kurs, źródło)
- `collect.py` — zbieranie cen (Brave + NBP)
- `build_site.py` — buduje `docs/index.html` (tabela + deep-linki Google Flights)
- `.github/workflows/daily.yml` — Actions: zbieranie (Brave) + build strony
- `docs/` — publikowana strona (GitHub Pages)

## Powiązanie

Raport dzienny trafia też na Telegram (cron Hermesa). Historia w `ceny.json` pokazuje trend dzień po dniu.
