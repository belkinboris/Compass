"""Правки второй волны карточек изъятий (4 ноября 2026): основание даты, орган в «Согласованиях», кавычки и тире,
дубль ИНН у профиля-описания. Запуск: [--write]."""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
P = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json'); R = os.path.join(ROOT, 'pipeline', 'fns_registry.json')
d = json.load(open(P, encoding='utf-8')); by = {x['id']: x for x in d['deals']}; reg = json.load(open(R, encoding='utf-8'))
for i in ('g3ce2f801', 'gbe9338ea'):
    by[i]['date_basis'] = 'publication'
by['g06adc4cc']['law']['appr'] = 'Дело рассматривал Гагаринский суд Москвы. ' + by['g06adc4cc']['law']['appr']
for i in ('g91356870', 'gb2087bc9', 'gfae91bd4'):
    by[i]['law']['appr'] = by[i]['law']['appr'].replace(' - ', ' — ')
def close_nested(text):
    """«ООО «Имя»  -> «ООО «Имя»»: если после закрытой кавычки глубина осталась >0 и дальше конец имени."""
    out, depth, i = [], 0, 0
    while i < len(text):
        ch = text[i]; out.append(ch)
        if ch == '«': depth += 1
        elif ch == '»':
            depth -= 1
            nxt = text[i + 1:i + 4]
            while depth >= 1 and (i + 1 >= len(text) or nxt[:1] in ',;:).—' or nxt[:3] in (' и ', ' (', ' —', ' а ') or nxt[:1] == ' ' and nxt[1:2].islower() and not nxt.startswith(' г')):
                out.append('»'); depth -= 1
        i += 1
    return ''.join(out)
FIX = [('gb5b08042', 'eco', 'context'), ('g9b31784c', 'eco', 'context'), ('g7aa61dee', None, 'title'), ('g7aa61dee', 'eco', 'context'),
       ('g883bb708', 'eco', 'share'), ('ga58be220', 'eco', 'context'), ('g1475c63b', 'eco', 'share'), ('g6729202e', 'law', 'struct')]
for cid, sec, f in FIX:
    obj = by[cid][sec] if sec else by[cid]
    new = close_nested(obj[f])
    if new != obj[f]:
        print(cid, f, 'ок'); obj[f] = new
for r in reg:
    if r['company_id'] == 'g8b68e6e4' and r.get('inn') == '6905062011':
        r.update(decision='no_match', inn=None, date='2026-11-04',
                 reason='Профиль — описание структур, связанных с АО «Диэлектрические кабельные системы»; ИНН 6905062011 принадлежит самому АО — отдельный профиль g8dd89999 (4 ноября 2026).')
if '--write' in sys.argv:
    json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); json.dump(reg, open(R, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print('Записано.')
