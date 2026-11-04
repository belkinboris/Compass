"""Профили и ИНН для карточек выходов иностранцев (4 ноября 2026): покупатели и покупаемые компании, чей ИНН
нашелся по ЕГРЮЛ через api-fns.ru (ac по имени + проверка egr). Запуск: [--write] (нужен API_FNS_KEY)."""
import hashlib, json, os, sys, time
import httpx
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from pipeline import fns_registry as fr
P = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json'); R = os.path.join(ROOT, 'pipeline', 'fns_registry.json')
KEY = os.environ['API_FNS_KEY']
# (id карточки, роль, имя профиля, ИНН, описание, нужен статус «Действующее», предложение в контекст)
ITEMS = [
 ('g9c218ea2', 'target', 'ООО «СТГТ»', '7804027534', 'Российская компания по ремонту и сервису газовых турбин (Ленинградская область), бывшая «Сименс Технологии газовых турбин».', True,
  'Прямой владелец СТГТ по ЕГРЮЛ — нидерландская Modern Gas Turbine Technologies Holding B.V. (прежнее название — Siemens Gas Turbine Technologies Holding B.V.), 100%.'),
 ('g3e6171f4', 'target', 'ООО «Ново Пакаджинг ББ»', '4003014954', 'Производитель гофрированной бумаги и картона в Балабаново (Калужская область), бывшая «Стора Энсо Пакаджинг ББ».', True,
  'По ЕГРЮЛ раньше 100% ООО «Ново Пакаджинг ББ» принадлежало финской «Стора Энсо Пакаджинг»; с 20.05.2022 — ООО «Новопак» (100%).'),
 ('gd1dabb38', 'buyer', 'ООО «Кселаб»', '9715436610', 'Московская холдинговая компания Антона и Светланы Бородихиных, купила российский бизнес Xerox.', True, None),
 ('g08c11c6b', 'buyer', 'ООО «Торговые галереи»', '7743427211', 'Московская компания «Кама капитал» (Тагир Шаймарданов) по управлению торговой недвижимостью; купила российскую структуру Ceetrus.', True, None),
 ('g14acee12', 'buyer', 'ООО «Палп Инвест»', '7842205435', 'Холдинг Тимура Габидуллина; в 2022 году купил российские активы Sylvamo со Светогорским ЦБК. Позже преобразован в АО «Палп Инвест» (ИНН 5032383309).', False, None),
]
def egr(inn):
    for _ in range(5):
        try:
            r = httpx.get('https://api-fns.ru/api/egr', params={'req': inn, 'key': KEY}, timeout=40).json()
            return (r.get('items') or [{}])[0].get('ЮЛ') or {}
        except Exception:
            time.sleep(2)
    return {}
d = json.load(open(P, encoding='utf-8')); by = {x['id']: x for x in d['deals']}; reg = json.load(open(R, encoding='utf-8'))
inns = {r['inn'] for r in reg if r.get('inn')}; names = {c['name'] for c in d['companies'].values()}
for cid, role, name, inn, desc, need_live, sent in ITEMS:
    card = by[cid]; ent = egr(inn)
    assert fr.inn_is_valid(inn), inn
    st = ent.get('Статус'); adr = (ent.get('Адрес') or {}).get('АдресПолн', '')
    assert (st == 'Действующее') or not need_live, (cid, inn, st)
    assert ent.get('НаимСокрЮЛ'), (cid, inn, 'ЕГРЮЛ пуст')
    if inn in inns or name in names: print('!! уже есть', cid, name, inn); continue
    pid = 'g' + hashlib.sha1(('profile:inn:' + cid + role).encode()).hexdigest()[:8]
    print(cid, role, name, inn, '|', st, '|', adr[:50])
    d['companies'][pid] = {'name': name, 'ind': card.get('ind') or 'Не определена', 'desc': desc, 'kpi': ['Профиль', 'Автоматический'], 'legal_short': name}
    reg.append({'company_id': pid, 'decision': 'confirmed', 'inn': inn, 'date': '2026-11-04',
                'reason': '%s (ОГРН %s): ИНН по ЕГРЮЛ (api-fns.ru, поиск по имени и проверка карточки: %s, %s), 4 ноября 2026.' % (ent.get('НаимПолнЮЛ'), ent.get('ОГРН'), st.lower(), adr[:60])})
    card[role] = pid
    if role == 'buyer': card.pop('buyer_name', None)
    notes = card.get('accepted_notes') or {}
    (notes.get('no_profile') or {}).pop(role, None)
    if notes.get('no_profile') is not None and not notes['no_profile']: notes.pop('no_profile')
    card['accepted_notes'] = notes
    if sent and sent not in (card['eco'].get('context') or ''):
        card['eco']['context'] = ((card['eco'].get('context') or '').rstrip() + ' ' + sent).strip()
    time.sleep(0.2)
# Лукойл — покупатель карточки Shell: профиль уже есть
c = by['g889097b8']; c['buyer'] = 'g5c8c6494'; c.pop('buyer_name', None)
n = c.get('accepted_notes') or {}; (n.get('no_profile') or {}).pop('buyer', None)
if n.get('no_profile') is not None and not n['no_profile']: n.pop('no_profile')
c['accepted_notes'] = n
if '--write' in sys.argv:
    json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); open(P, 'a').write('\n')
    json.dump(reg, open(R, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); open(R, 'a').write('\n'); print('Записано.')
