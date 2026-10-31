"""Nomi/«Гельтек» (g162de6fb): продавец по ЕГРЮЛ — владелец 15 октября 2026:
«ты снова не искал продавца?». История участников ООО «Компания новая
идея» (ОГРН 1157746005207, datanewton.ru), запись 13.10.2026: выбыли
Гукасян Игорь Семенович 25%, Заславский Андрей Александрович 25% и доля
самого общества 50% (перешла к нему в июне 2025 от вышедших Лобановых и
Карпеткина); вошло ООО «Гельтек РНД» 100%. Карточка снова уходит в консоль.
Без ключа — сухой прогон."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'static', 'data', 'pending.json')
ID = 'g162de6fb'
URL = 'https://datanewton.ru/contragents/1157746005207'
SELLER = 'Игорь Гукасян и Андрей Заславский'
STRUCT = ('По данным ЕГРЮЛ, 13 октября 2026 года из ООО «Компания новая идея» вышли Игорь Гукасян '
          '(гендиректор компании с 2015 года) и Андрей Заславский — у каждого было по 25%. Еще 50% '
          'числились за самой компанией: в июне 2025 года из нее вышли прежние совладельцы Сергей и '
          'Борис Лобановы и Андрей Карпеткин. Единственным участником стало ООО «Гельтек РНД».')
raw = open(P, encoding='utf-8').read()
pending = json.loads(raw)
c = next(x for x in pending['cards'] if x['id'] == ID)
assert not c.get('seller') and not c.get('seller_id'), c.get('seller')
assert c['law'].get('struct') in ('—', '', None), c['law'].get('struct')
c['seller'] = SELLER
c['law']['struct'] = STRUCT
c.setdefault('party_evidence', {})['seller'] = [{'value': SELLER, 'method': 'registry_owner_history', 'url': URL}]
if URL not in {s[1] for s in c.get('src') or [] if len(s) > 1}:
    c['src'].append(['ЕГРЮЛ: история участников ООО «Компания новая идея»', URL])
notes = c.setdefault('accepted_notes', {}).setdefault('no_profile', {})
notes['seller'] = 'физлица, профилей нет; найдены по истории участников ЕГРЮЛ (datanewton), запись 13.10.2026'
for k in ('draft_sent', 'post_draft_sent', 'post_preview'):
    c.pop(k, None)
print(ID, 'продавец:', SELLER)
if '--write' in sys.argv:
    open(P, 'w', encoding='utf-8').write(json.dumps(pending, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    print('записано')
