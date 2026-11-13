# -*- coding: utf-8 -*-
"""Вычитка, партия m104 (13 ноября 2026), часть 3: три карточки золотой выборки
аналитики (pipeline/gold/analytics_gold.json) — правка по фактам вместе со строками
выборки и повторным подтверждением доли.

ЗАЧЕМ ОТДЕЛЬНО. Отпечаток подтвержденной доли (`facts.card_hash(deal, 'stake')`)
считается по `title`, `eco.share`, `asset`, `stake_acquired`: любая правка заголовка
или «Предмета / доли» переводит долю, подтвержденную двумя чтениями, в `stale`, и
`test_gold_multiple_shown_matches_verified_facts` краснеет. Поэтому прежние партии
(m050, m060) оставляли у g756f35a3 и gff93974e заголовок и долю не по стандарту.
Путь: поле правится, затем те же два чтения доли (значение, объект, событие и
цитата не изменились — меняется только формулировка карточки) заново проходят
`facts_confirm.write_readings(..., asked=('stake',))`: цитата снова сверяется с
текстом статьи в кэше data/inbox/raw, факт получает отпечаток новой карточки.
Если меняется само значение доли или ее объект — прежние чтения не годятся,
нужны два новых (pipeline/FACTS_READING_BRIEF.md).

  * gc4c76129 — МТС / TicketsCloud. По ЕГРЮЛ ООО «Тикетсклауд» (ОГРН 1187746558560):
    31.08.2023 «Тикетсклауд Лтд» — 85%, Егор Егерев — 15%; 08.09.2023 «Тикетсклауд
    Лтд» (85%) вышел, вошло ООО «МТС Лайв» (85%); 23.12.2024 «МТС Лайв» — 100%.
    Покупатель — ООО «МТС Лайв» (дочерняя компания ПАО «МТС», Интерфакс), продавец —
    Ticketscloud Ltd (vc.ru: «МТС получит 85%, которые принадлежат Ticketscloud Ltd»),
    доля 85%. Сумма: «до 900 млн ₽» — цена выкупа со слов источников РБК «при
    выполнении согласованных бизнес-показателей» → «до 900 млн ₽ (по оценке)»,
    sum_basis «reported»; «500 млн – 2 млрд ₽» — оценки всей компании источниками
    Коммерсанта, не цена — в eco.val.
  * g756f35a3 — «Первая образцовая типография»: заголовок по стандарту, доля —
    «100% акций АО …» (Коммерсантъ: «купил 100% акций АО «Первая образцовая
    типография» у государства»), площади зданий — в финансы предмета.
  * gff93974e — SmartDeal: доля по форме «100% доли в ООО «Практика Успеха»».

    python3 pipeline/archive/2026-11/reread_deferred_m104c.py           # сухой прогон
    python3 pipeline/archive/2026-11/reread_deferred_m104c.py --write   # запись

Повторный запуск ничего не ломает: правка, которая уже стоит, пропускается.
"""
import copy
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
GOLD = os.path.join(ROOT, 'pipeline', 'gold', 'analytics_gold.json')
BY = 'вычитка m104'
MISSING = object()

TC_REG = 'https://datanewton.ru/api/v2/history?ogrn=1187746558560&startDate=2000-01-01&attributes=OWNERS'
VC_TC = 'https://vc.ru/money/821716-mts-kupil-85-v-platforme-dlya-prodazhi-biletov-i-organizacii-meropriyatiy-ticketscloud'
HABR_TC = 'https://habr.com/ru/news/758758/'
IFX_TC = 'https://www.interfax.ru/business/1000319'
KOM_TPO = 'https://www.kommersant.ru/doc/6111899'

Q_TC_REG = ('8 сентября 2023 года: выбыл участник "ТИКЕТСКЛАУД ЛТД" (85%); вошел участник ООО "МТС ЛАЙВ" (85%). '
            '23 декабря 2024 года: доля ООО "МТС ЛАЙВ" изменилась с 85% до 100%.')
Q_TC_SELLER = ('МТС получит 85%, которые принадлежат Ticketscloud Ltd — зарубежному юрлицу, зарегистрированному на '
               'Британских Виргинских островах.')
Q_TC_SUM = ('По данным источников РБК, сумма выкупа составит до 900 млн рублей «при выполнении согласованных '
            'бизнес-показателей».')
Q_TPO = 'Московский бизнесмен Денис Избрехт купил 100% акций АО «Первая образцовая типография» у государства.'

MTS_LIVE_ID = 'g0c041f6d'
MTS_LIVE = {'name': 'МТС Live', 'legal_short': 'ООО «МТС Лайв»', 'ind': 'Медиа',
            'desc': 'Дочерняя компания ПАО «МТС»: билетный и концертный бизнес группы.',
            'kpi': ['Профиль', 'Автоматический'],
            'holding': {'id': 'g69c88bc7', 'confidence': 'disclosed', 'source': ['Интерфакс', IFX_TC]}}

# (id карточки, поле через точку, старое значение, новое значение, цитата, адрес)
EDITS = [
    ('gc4c76129', 'buyer', 'g9cb5f756', MTS_LIVE_ID, Q_TC_REG, TC_REG),
    ('gc4c76129', 'seller', 'Егор Егерев', 'Ticketscloud Ltd', Q_TC_SELLER, VC_TC),
    ('gc4c76129', 'title', 'МТС купила TicketsCloud', 'МТС купила 85% TicketsCloud', Q_TC_SELLER, VC_TC),
    ('gc4c76129', 'sum', '500 млн – 2 млрд ₽', 'До 900 млн ₽ (по оценке)', Q_TC_SUM, VC_TC),
    ('gc4c76129', 'eco.sum', '500 млн – 2 млрд ₽', 'До 900 млн ₽ (по оценке)', Q_TC_SUM, VC_TC),
    ('gc4c76129', 'sum_basis', MISSING, 'reported', '', ''),
    ('gc4c76129', 'eco.share',
     'TicketsCloud: по объяснению Сергея Бабича, из личного кабинета площадка или организатор сразу договаривается с большинством билетных операторов. Распространителей среди контрагентов — 194.',
     '85% доли в ООО «Тикетсклауд»', Q_TC_SELLER, VC_TC),
    ('gc4c76129', 'eco.val',
     'Продюсер Colisium International Music Forum Сергей Бабич оценивает TicketsCloud в 2,2–2,4 млрд ₽.',
     'По неофициальным данным, всю компанию оценили в 500 млн – 1 млрд ₽, по другим — в 2 млрд ₽. Продюсер '
     'Colisium International Music Forum Сергей Бабич оценивает TicketsCloud в 2,2–2,4 млрд ₽.', '', ''),
    ('gc4c76129', 'eco.target_fin',
     'По данным СПАРК-Интерфакса, ООО «Тикетсклауд» зарегистрировано в 2018 году: 75,5% принадлежат Егору Егереву, 24,5% — британской TicketsCloud Ltd, которая владеет еще и ООО «Облако билетов». По итогам 2021 года выручка «Тикетсклауда» составила 111,6 млн ₽ при убытке 8 млн ₽.',
     'По итогам 2021 года выручка ООО «Тикетсклауд» составила 111,6 млн ₽ при убытке 8 млн ₽.', '', ''),
    ('gc4c76129', 'law.struct',
     'Сооснователь Ticketscloud Егор Егерев это подтвердил: у него и его партнера Катерины Кирилловой останется 15% компании.',
     'По ЕГРЮЛ, перед сделкой 85% ООО «Тикетсклауд» принадлежали Ticketscloud Ltd, 15% — Егору Егереву; '
     '8 сентября 2023 года 85% перешли ООО «МТС Лайв», дочерней компании МТС. Егор Егерев и его партнер '
     'Катерина Кириллова, по словам Егерева, сохранили 15%; 23 декабря 2024 года «МТС Лайв» довела долю до 100%.',
     '', ''),
    ('gc4c76129', 'extra',
     'МТС Entertainment свела управление билетными сервисами Ponominalu и Ticketland, чтобы купить TicketsCloud. Продает компанию ее основатель и CEO Егор Егерев. Среди инвесторов TicketsCloud — Starta Capital, Moscow Seed Fund, Александр Бородич, Игорь Мацанюк, Богдан Яровой и 2be.lu Investment. МТС Entertainment, дочерняя компания ПАО МТС, приобрела 85% доли в ООО «Тикетсклауд». По данным Rusprofile, выручка ООО «Тикетсклауд» по итогам 2022 года составила 212 млн ₽ (рост на 90% за год), прибыль — 80 млн ₽. Условие полного выкупа выполнено раньше срока: 23 декабря 2024 года «МТС Лайв» довела долю в «Тикетсклауд» с 85% до 100%. Выручка выросла с 212 млн ₽ в 2022 году до 785 млн ₽ в 2025 году.',
     'МТС Entertainment свела управление билетными сервисами Ponominalu и Ticketland, чтобы купить TicketsCloud. '
     'Среди инвесторов TicketsCloud — Starta Capital, Moscow Seed Fund, Александр Бородич, Игорь Мацанюк, Богдан '
     'Яровой и 2be.lu Investment. По данным Rusprofile, выручка ООО «Тикетсклауд» по итогам 2022 года составила '
     '212 млн ₽ (рост на 90% за год), прибыль — 80 млн ₽. Условие полного выкупа выполнено раньше срока: 23 декабря '
     '2024 года «МТС Лайв» довела долю в «Тикетсклауд» с 85% до 100%. Выручка выросла с 212 млн ₽ в 2022 году до '
     '785 млн ₽ в 2025 году.', '', ''),
    ('g756f35a3', 'title', 'Росимущество продало 100% акций АО «Первая образцовая типография» Денису Избрехту',
     'Денис Избрехт купил «Первую образцовую типографию» у Росимущества', Q_TPO, KOM_TPO),
    ('g756f35a3', 'eco.share',
     'Все акции АО «Первая образцовая типография»: почти 330 тыс. кв. м площадей и 44 тыс. кв. м офисов в Москве, на Пятницкой (38 051 кв. м) и Сущевском Валу (5865 кв. м).',
     '100% акций АО «Первая образцовая типография»', Q_TPO, KOM_TPO),
    ('g756f35a3', 'eco.target_fin',
     'По данным СПАРК, за 2022 год выручка «Первой образцовой типографии» составила 5,4 млрд ₽, чистая прибыль — 148,4 млн ₽.',
     'По данным СПАРК, за 2022 год выручка «Первой образцовой типографии» составила 5,4 млрд ₽, чистая прибыль — '
     '148,4 млн ₽. Типографии принадлежали почти 330 тыс. кв. м площадей и 44 тыс. кв. м офисов в Москве — на '
     'Пятницкой (38 051 кв. м) и Сущевском Валу (5865 кв. м).', '', ''),
    ('gff93974e', 'eco.share',
     'SmartDeal позволяет банкам и застройщикам регистрировать сделки в Росреестре. Компания основана в 2017 году.',
     '100% доли в ООО «Практика Успеха»',
     '«Циан» получил разрешение от регулирующих органов в соответствии с предварительным договором, заключенным сторонами в апреле 2023 года, и сообщает о закрытии основного этапа сделки по приобретению 100% долей в уставном капитале SmartDeal.',
     'https://smart-lab.ru/blog/news/942501.php'),
]

RETRACT = [('gc4c76129', 'sum', '500 млн – 2 млрд ₽'), ('gc4c76129', 'seller', 'Егор Егерев')]

# Строки золотой выборки: (id, ключ, старое, новое)
GOLD_EDITS = [
    ('gc4c76129', 'title', 'МТС приобретает TicketsCloud', 'МТС купила 85% TicketsCloud'),
    ('gc4c76129', 'share', None, 85),
    ('gc4c76129', 'sum_basis', 'range', 'reported'),
    ('gc4c76129', 'why', '«500 млн – 2 млрд ₽» — диапазон с единицами по обе стороны тире; до 6 сентября такой диапазон не распознавался',
     'вычитка 13 ноября 2026: «500 млн – 2 млрд ₽» — оценки всей компании источниками Коммерсанта, не цена (в eco.val); '
     'цена — «до 900 млн ₽» со слов источников РБК при выполнении бизнес-показателей (reported, в расчеты не идет); '
     '85% по ЕГРЮЛ (08.09.2023: «Тикетсклауд Лтд» вышел, «МТС Лайв» вошло с 85%)'),
    ('g756f35a3', 'title', 'Росимущество продало 100% акций АО «Первая образцовая типография»',
     'Денис Избрехт купил «Первую образцовую типографию» у Росимущества'),
    ('gff93974e', 'title', 'ЦИАН через «Айриэлтор» приобретает 100% SmartDeal', '«Циан» через «Айриэлтор» купил 100% SmartDeal'),
]

DOC = os.path.join(ROOT, 'docs', 'analytics_acceptance.md')
DOC_HEAD = '## Правка карточки золотой выборки (13 ноября 2026)'
DOC_SECTION = "\n## Правка карточки золотой выборки (13 ноября 2026)\n\nУ карточки из `pipeline/gold/analytics_gold.json` подтвержденная двумя чтениями доля\nдержится отпечатком `facts.card_hash(deal, 'stake')` — он считается по `title`,\n`eco.share`, `asset`, `stake_acquired`. Правка заголовка или «Предмета / доли» сама\nпереводит долю в `stale`, и `test_gold_multiple_shown_matches_verified_facts`\nкраснеет; поэтому вычитка оставляла такие поля не по стандарту. Путь — один разовый\nскрипт: (1) правка полей карточки с `fact_edit_guard.log`; (2) правка строки выборки\n(`title`, `share`, `sum_basis`, `why`) по тем же фактам; (3) если значение доли, ее\nобъект и цитата не изменились — те же два чтения из `facts.stake.readings` заново через\n`facts_confirm.write_readings(paths, write=True, asked=('stake',))`: цитата снова\nсверяется с кэшем статей `data/inbox/raw`, отпечаток — по новой карточке. Изменилась\nсама доля или ее объект — прежние чтения не годятся, нужны два новых\n(`pipeline/FACTS_READING_BRIEF.md`). Отпечаток смены контроля (`nature`) тоже считается по заголовку — ее чтения подтверждаются так же (`asked=('nature',)`). Статьи чтений должны лежать в кэше `data/inbox/raw/*-articles.jsonl` (нет — скачать и положить), иначе основание останется «read». Тест не отключается. Образец —\n`pipeline/archive/2026-11/reread_deferred_m104c.py` (g756f35a3, gff93974e, gc4c76129).\n"


def doc_apply(write):
    """Путь правки карточки золотой выборки — в docs/analytics_acceptance.md (раздел в конце)."""
    text = open(DOC, encoding='utf-8').read()
    if DOC_HEAD in text:
        return 0
    if write:
        open(DOC, 'w', encoding='utf-8').write(text.rstrip('\n') + '\n' + DOC_SECTION)
    print('  docs/analytics_acceptance.md: + раздел «%s»' % DOC_HEAD[3:])
    return 1


RECONFIRM = ('g756f35a3', 'gff93974e')   # доля подтверждена двумя чтениями — подтвердить заново


def get(obj, path):
    for k in path.split('.'):
        if not isinstance(obj, dict) or k not in obj:
            return MISSING
        obj = obj[k]
    return obj


def put(obj, path, value):
    keys = path.split('.')
    for k in keys[:-1]:
        obj = obj.setdefault(k, {})
    if value is MISSING:
        obj.pop(keys[-1], None)
    else:
        obj[keys[-1]] = value


def apply(data):
    import fact_edit_guard
    done = 0
    comps = data['companies']
    if MTS_LIVE_ID not in comps:
        comps[MTS_LIVE_ID] = copy.deepcopy(MTS_LIVE)
        data.setdefault('match_keys', {})[MTS_LIVE_ID] = ['мтс live', 'мтс лайв']
        done += 1
        print('  + профиль %s %s' % (MTS_LIVE_ID, MTS_LIVE['legal_short']))
    # правовая форма предмета gc4c76129 по ЕГРЮЛ: ООО «Тикетсклауд», ИНН 7703459471
    if comps['g4b69137f'].get('legal_short') != 'ООО «Тикетсклауд»':
        assert comps['g4b69137f'].get('legal_short') is None
        comps['g4b69137f']['legal_short'] = 'ООО «Тикетсклауд»'
        done += 1
    cards = {d['id']: d for d in data['deals']}
    for cid, field, old, new, quote, url in EDITS:
        card = cards[cid]
        cur = get(card, field)
        if cur == new:
            continue
        assert cur == old, '%s %s: в базе %r, ожидали %r' % (cid, field, cur, old)
        put(card, field, new)
        if quote and field in fact_edit_guard.FACT_FIELDS:
            fact_edit_guard.log(card, field, None if new is MISSING else new, quote, url, BY)
        done += 1
        print('  %s %s: %r → %r' % (cid, field, str(old)[:60], str(new)[:60]))
    for cid, field, value in RETRACT:
        lst = cards[cid].setdefault('retracted', {}).setdefault(field, [])
        if value not in lst:
            lst.append(value)
            done += 1
    return done


def gold_apply(gold):
    rows = {r['id']: r for r in gold['deals']}
    done = 0
    for cid, key, old, new in GOLD_EDITS:
        row = rows[cid]
        cur = row.get(key)
        if cur == new:
            continue
        assert cur == old, 'выборка %s %s: %r, ожидали %r' % (cid, key, cur, old)
        row[key] = new
        done += 1
        print('  выборка %s %s → %r' % (cid, key, str(new)[:70]))
    return done


def reconfirm_stake(data, write):
    """Те же два чтения — заново через facts_confirm (цитата сверяется с кэшем статей
    data/inbox/raw/*-articles.jsonl, отпечаток — по новой карточке). Доля — у обеих карточек;
    смена контроля (nature) — у g756f35a3: ее отпечаток тоже считается по заголовку.
    Пропускается факт, уже подтвержденный по новой карточке. Статьи двух чтений g756f35a3
    (Коммерсантъ 6111899, rupor73) положены в кэш data/inbox/raw/2026-11-13-m104-articles.jsonl."""
    import facts
    import facts_confirm
    cards = {d['id']: d for d in data['deals']}
    keys = {'stake': ('value', 'object', 'event', 'quote', 'source'),
            'nature': ('control_change', 'intragroup', 'quote', 'source')}
    total = 0
    for key, fields in keys.items():
        recs = {}
        for cid in RECONFIRM:
            fact = (cards[cid].get('facts') or {}).get(key) or {}
            basis = fact.get('control_change_basis') if key == 'nature' else fact.get('basis')
            if key == 'nature' and basis != 'verified' and not fact.get('readings'):
                continue
            if basis == 'verified' and fact.get('card_hash') == facts.card_hash(cards[cid], key):
                continue
            readings = fact.get('readings') or []
            assert len({r['reader'] for r in readings}) >= 2, '%s %s: нет двух чтений' % (cid, key)
            for r in readings[:2]:
                rec = {'id': cid, 'reader': r['reader'], 'unreadable': False,
                       'notes': 'повторное подтверждение после правки формулировки (вычитка m104)'}
                for k2 in keys:
                    rec[k2] = None
                for k2 in ('price', 'date', 'perimeter'):
                    rec[k2] = None
                rec[key] = {k: r[k] for k in fields if k in r}
                recs.setdefault(r['reader'], []).append(rec)
        if not recs:
            continue
        ids = sorted({x['id'] for rows in recs.values() for x in rows})
        total += len(ids)
        if not write:
            print('  %s: повторное подтверждение двумя чтениями — %s' % (key, ', '.join(ids)))
            continue
        tmp = tempfile.mkdtemp(prefix='m104c_')
        paths = []
        for reader, rows in recs.items():
            p = os.path.join(tmp, 'read-%s-%s.json' % (key, reader))
            json.dump(rows, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
            paths.append(p)
        code = facts_confirm.write_readings(paths, write=True, asked=(key,))
        assert code == 0, 'facts_confirm отказал (%s)' % key
        data = json.load(open(DATA, encoding='utf-8'))
        cards = {d['id']: d for d in data['deals']}
    return total


def main(argv):
    write = '--write' in argv
    data = json.load(open(DATA, encoding='utf-8'))
    gold = json.load(open(GOLD, encoding='utf-8'))
    n = apply(copy.deepcopy(data)) + gold_apply(copy.deepcopy(gold)) + doc_apply(write=False)
    if not write:
        probe = copy.deepcopy(data)
        apply(probe)
        n += reconfirm_stake(probe, write=False)
        print('Сухой прогон: %d правок. Запись — с ключом --write.' % n if n else 'Уже применено.')
        return 0
    import mass_edit_guard
    if n:
        old = json.load(open(DATA, encoding='utf-8'))   # перечитать прямо перед записью
        data = copy.deepcopy(old)
        apply(data)
        mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        gold = json.load(open(GOLD, encoding='utf-8'))
        if gold_apply(gold):
            json.dump(gold, open(GOLD, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            open(GOLD, 'a', encoding='utf-8').write('\n')
    doc_apply(write=True)
    data = json.load(open(DATA, encoding='utf-8'))
    m = reconfirm_stake(data, write=True)
    print('Записано правок: %d, доля подтверждена заново: %d' % (n, m))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
