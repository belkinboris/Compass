"""Профили и ИНН для карточек изъятий, где читатели ИНН не нашли (4 ноября 2026).
ИНН найден по ЕГРЮЛ через api-fns.ru (метод ac по имени, проверка методом egr: адрес, вид деятельности, участники);
история участников берется из egr. Запуск: [--write] (нужен API_FNS_KEY)."""
import hashlib, json, os, re, sys, time
import httpx
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from pipeline import fns_registry as fr
P = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json'); R = os.path.join(ROOT, 'pipeline', 'fns_registry.json')
KEY = os.environ['API_FNS_KEY']
MAP = {  # id карточки: (имя профиля, ИНН, описание)
 'gb92f7119': ('ООО «Селаникар»', '7706807818', 'Юрлицо платформы Carprice по продаже подержанных автомобилей.'),
 'g146df6ac': ('АО «Конти-Рус»', '4629046141', 'Кондитерская фабрика в Курске.'),
 'g4f9a1741': ('ООО «Инфорион»', '7715592358', 'Разработчик программного обеспечения и ИТ-решений.'),
 'g6f98005b': ('ООО «Статус комплайнс»', '7719404118', 'Оптовый поставщик компьютеров, периферии и программного обеспечения.'),
 'g225f7b5f': ('ООО «Энжэ Строй»', '5047159356', 'Строительная компания (NG Concept).'),
 'gece7ec74': ('ООО «Датацентр СК»', '7727175133', 'Строитель центров обработки данных.'),
 'g3a168646': ('ООО «Технокад»', '5009046312', 'Разработчик программ для кадастра.'),
 'gc81a4ae5': ('АО «Усть-Луга Ойл»', '4707013516', 'Нефтяной терминал в порту Усть-Луга.'),
 'g6c7dad8f': ('АО «Петрус»', '7704521059', 'Производитель пластмассовой упаковки (Мытищи).'),
 'gf475c186': ('ООО «Ланта»', '6829003413', 'Оператор связи в Тамбовской области.'),
 'gad9394d1': ('АО «Климовский специализированный патронный завод»', '5021011845', 'Производитель патронов (Подольск, микрорайон Климовск).'),
 'g91356870': ('АО «Научно-исследовательский институт полимерных материалов»', '5908051070', 'Научный институт в Перми.'),
 'gb2087bc9': ('АО «Сясьский ЦБК»', '4718011856', 'Целлюлозно-бумажный комбинат в Сясьстрое.'),
 'gfae91bd4': ('АО «Порт Пермь»', '5903004012', 'Речной порт на Каме в Перми.'),
 'g67feb893': ('ООО «Форси»', '7703774970', 'Владелец гостиницы Four Seasons на Охотном Ряду.'),
 'g2e8b9678': ('ООО «Реал Девелопмент»', '2540212733', 'Рыбопромысловая компания во Владивостоке.'),
}
def egr(inn):
    for _ in range(5):
        try:
            r = httpx.get('https://api-fns.ru/api/egr', params={'req': inn, 'key': KEY}, timeout=40).json()
            return (r.get('items') or [{}])[0].get('ЮЛ') or {}
        except Exception:
            time.sleep(2)
    return {}
KEEP = {'НПП', 'ООО', 'АО', 'ПАО', 'ГК', 'ЗАО', 'ОАО'}
def pretty(raw):
    """АО "НПП "ТОРИЙ"" -> АО «НПП «Торий»»: кавычка после пробела (или в начале) открывает, иначе закрывает;
    слова капсом — с заглавной (кроме аббревиатур)."""
    out = []
    for i, ch in enumerate(raw):
        if ch == '"':
            out.append('«' if i == 0 or raw[i - 1] == ' ' else '»')
        else:
            out.append(ch)
    s = ''.join(out)
    def fix(w):
        core = w.strip('«»')
        if core in KEEP or not core.isupper():
            return w
        i = w.index(core)
        return w[:i] + core.capitalize() + w[i + len(core):]
    return ' '.join(fix(w) for w in s.split(' '))
def owner_name(u):
    if u.get('УчрФЛ'): return u['УчрФЛ'].get('ФИОПолн')
    if u.get('УчрЮЛ'): return pretty(u['УчрЮЛ'].get('НаимСокрЮЛ') or '')
    if u.get('УчрРФСубМО'): return u['УчрРФСубМО']
    sv = (u.get('СвОргОсущПр') or {}).get('УчрЮЛ') or {}
    return (sv.get('НаимСокрЮЛ') or 'государственный орган').title() if sv else None
def history_sentence(ent):
    hist = (ent.get('История') or {}).get('Учредители') or []
    cur = [u for u in (ent.get('Учредители') or [])]
    if not cur and not hist: return ''
    def fmt(u): 
        p = u.get('Процент'); n = owner_name(u) or '?'
        return '%s (%s%%)' % (n, str(p).replace('.', ',')) if p else n
    now = cur[:3]
    if not now: return ''
    # предложение — только если все участники разобраны и актив перешел государству (иначе автотекст неточен)
    if any('?' in (fmt(u) or '?') for u in now): return ''
    if not any(re.search(r'Российская Федерация|РОСИМУЩЕСТВО|Росимущество|РОСТЕХ|Ростех|ТОРИЙ|Торий', fmt(u)) for u in now): return ''
    since = min(str(u.get('Дата') or '9999') for u in now)
    owners = [u for u in hist if u.get('ДатаОконч') and (u.get('УчрФЛ') or u.get('УчрЮЛ')) and str(u['ДатаОконч']) < since]
    last_end = max((str(u['ДатаОконч']) for u in owners), default=None)
    prev = [u for u in owners if str(u['ДатаОконч']) == last_end]
    prev_names = []
    seen = set()
    for u in prev:
        t = fmt(u)
        nm = owner_name(u)
        if nm in seen or not nm or '?' in t: continue
        seen.add(nm); prev_names.append(t)
    d = lambda s: '%s.%s.%s' % (s[8:10], s[5:7], s[:4])
    if not prev_names: return ''
    from datetime import date as _d
    if (_d.fromisoformat(since) - _d.fromisoformat(last_end)).days > 60: return ''
    if prev_names:
        return 'По истории участников ЕГРЮЛ до %s долями владели %s; с %s — %s.' % (d(str(prev[0]['ДатаОконч'])), ', '.join(prev_names[:3]), d(since), ', '.join(fmt(u) for u in now))
    return 'По ЕГРЮЛ с %s участник — %s.' % (d(since), ', '.join(fmt(u) for u in now))
d = json.load(open(P, encoding='utf-8')); by = {x['id']: x for x in d['deals']}; reg = json.load(open(R, encoding='utf-8'))
inns = {r['inn'] for r in reg if r.get('inn')}; names = {c['name'] for c in d['companies'].values()}
for cid, (name, inn, desc) in MAP.items():
    card = by[cid]
    ent = egr(inn)
    full = ent.get('НаимПолнЮЛ'); st = ent.get('Статус'); adr = (ent.get('Адрес') or {}).get('АдресПолн', '')
    assert fr.inn_is_valid(inn), inn
    assert st == 'Действующее', (cid, inn, st)
    pid = 'g' + hashlib.sha1(('profile:inn:' + cid).encode()).hexdigest()[:8]
    if inn in inns: print('!! ИНН уже в реестре', cid, inn); continue
    if name in names: print('!! имя уже есть', cid, name); continue
    sent = history_sentence(ent)
    print(cid, name, inn, '|', adr[:50], '|', sent[:220])
    d['companies'][pid] = {'name': name, 'ind': card.get('ind') or 'Не определена', 'desc': desc, 'kpi': ['Профиль', 'Автоматический'], 'legal_short': name}
    reg.append({'company_id': pid, 'decision': 'confirmed', 'inn': inn, 'date': '2026-11-04',
                'reason': '%s (ОГРН %s): ИНН по ЕГРЮЛ (api-fns.ru, поиск по имени и проверка карточки: действующее, %s), 4 ноября 2026.' % (full, ent.get('ОГРН'), adr[:60])})
    card['target'] = pid
    notes = card.get('accepted_notes') or {}
    (notes.get('no_profile') or {}).pop('target', None)
    if notes.get('no_profile') is not None and not notes['no_profile']: notes.pop('no_profile')
    if sent:
        notes.setdefault('seller_history', sent)
        ctx = card['eco'].get('context') or ''
        if 'По истории участников' not in ctx and 'По ЕГРЮЛ' not in ctx:
            card['eco']['context'] = (ctx.rstrip() + ' ' + sent).strip()
    card['accepted_notes'] = notes
    time.sleep(0.2)
if '--write' in sys.argv:
    json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); json.dump(reg, open(R, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print('Записано.')
