import json
u = json.load(open('/opt/data/tools/gf_urls.json', encoding='utf-8'))
for k in ["24.01 → 12.02", "25.01 → 12.02", "28.01 → 12.02", "26.01 → 12.02", "24.01 → 10.02", "28.01 → 10.02"]:
    print(k, "->", u.get(k))
