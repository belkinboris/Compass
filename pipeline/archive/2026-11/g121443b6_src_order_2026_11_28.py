"""g121443b6 («Государство передаст ВСК акции восьми обществ»): первым источником в посте —
распоряжение Правительства № 2411-р вместо указа № 601 (владелец, 28 ноября 2026: «вместо указа
другой источник напиши и пришли в консоль»). Меняется только порядок ссылок, состав тот же.
Запуск: без ключа — сухой, с --write — запись."""
import json, sys
P = 'static/data/pending.json'
UKAZ = 'https://rulaws.ru/president/Ukaz-Prezidenta-RF-ot-24.08.2026-N-601/'
RASP = 'https://rulaws.ru/goverment/Rasporyazhenie-Pravitelstva-RF-ot-07.09.2026-N-2411-r/'
d = json.load(open(P, encoding='utf-8'))
c = [x for x in d['cards'] if x.get('id') == 'g121443b6'][0]
src = c['src']
assert src[0][1] == UKAZ, src[0]
i = [k for k, s in enumerate(src) if s[1] == RASP][0]
new = [src[i]] + [s for k, s in enumerate(src) if k != i]
print([s[0] for s in new])
if '--write' in sys.argv:
    c['src'] = new
    json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('записано')
