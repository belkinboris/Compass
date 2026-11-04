"""legal_short профилей предметов новых карточек изъятий (4 ноября 2026).
Названия — из реестра ФНС (party_legal_names.py, сухой прогон) и из прочитанных статей; кавычки выправлены."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
P = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
SHORT = {'g193370bd': 'АО КБ «Агропромкредит»', 'g097e34b2-target': 'ООО «Южгазэнерджи»', 'gf0622a24': 'АО «Рольф»',
         'gfd4e10ae': 'АО «Концерн «Покровский»', 'g2c4a5a61': 'АО «КР Пропертиз»', 'ga1db6755': 'АО «Уралбиофарм»',
         'g7bddf214': 'АО «ЧЭМК»', 'g4a98b303': 'ООО «Роквул»', 'gambertalvis': 'АО «Амбер Талвис»',
         'baltika': 'ООО «Пивоваренная компания «Балтика»', 'g2ea24925': 'ООО «ПКМТП»'}
d = json.load(open(P, encoding='utf-8'))
for cid, short in SHORT.items():
    comp = d['companies'][cid]
    assert not comp.get('legal_short'), cid
    comp['legal_short'] = short
if '--write' in sys.argv:
    json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')
