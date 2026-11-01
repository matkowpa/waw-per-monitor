import json, collections
d = json.load(open('/opt/data/cache/scratch/wpc/data/oferty_dzis.json', encoding='utf-8'))
ok = [o for o in d['oferty'] if o.get('ok')]
odr = d.get('odrzucone', [])
print("data:", d['data'], "OK:", len(ok), "odrzucone(top10):", len(odr))
print("\n=== TOP 8 OK ===")
for o in ok[:8]:
    cz = f"{o['czas_h']}h{o['czas_min']:02d}"
    pr = " | ".join(f"{m//60}h{m%60:02d} {g}" for m, g in zip(o['przesiadki_min'], o['przesiadki_gdzie']))
    print(f"{o['cena_zl']} zl | {o['linie']} | {o['przesiadki']} prz | {cz} | {pr} | {o['wariant']}")

print("\n=== NAJTAŃSZA PER WARIANT (top 12) ===")
per = {}
for o in ok:
    per.setdefault(o['wariant'], o)
for w, o in sorted(per.items(), key=lambda kv: kv[1]['cena_zl'])[:12]:
    print(f"{w}: {o['cena_zl']} zl {o['linie']} {o['czas_h']}h{o['czas_min']:02d}")

print("\n=== LINIE (min cena, liczba ofert OK) ===")
ag = collections.defaultdict(list)
for o in ok:
    ag[o['linie']].append(o['cena_zl'])
for k, v in sorted(ag.items(), key=lambda kv: min(kv[1])):
    print(f"{k}: min {min(v)} zl, n={len(v)}")

print("\n=== PROGI ===")
for p in (6000, 6500, 7000, 7500, 8000):
    print(p, sum(1 for o in ok if o['cena_zl'] <= p))

print("\n=== ODRZUCONE 3 ===")
for o in odr[:3]:
    cz = f"{o['czas_h']}h{(o['czas_min'] or 0):02d}" if o['czas_h'] else '?'
    print(f"{o['cena_zl']} zl | {o['linie']} | {o['przesiadki']} prz | {cz} | {o['wariant']} | {o['powod_odrzucenia']}")

print("\n=== ODRZUCONE wg powodu (top) ===")
c = collections.Counter(o['powod_odrzucenia'].split('(')[0][:40] for o in odr)
for k, v in c.most_common(6):
    print(v, k)

print("\n=== ALARM? min =", ok[0]['cena_zl'], "prog 5500 ===")
