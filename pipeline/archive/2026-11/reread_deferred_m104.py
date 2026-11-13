# -*- coding: utf-8 -*-
"""Вычитка, партия m104 (13 ноября 2026), часть 1: отложенные спорные случаи —
два слияния дублей и снятие двух карточек, которые не описывают сделку базы.

Владелец, 13 ноября 2026: «если после вычитки у тебя будут вопросы или отложенное
что-то, не жди моего ответа и постарайся сам все решить». Решения — по правилам
проекта (docs/base_duplicates.md, docs/card_status_dates.md, решение владельца
27 октября 2026 «база начинается с 2022 года»):

СЛИЯНИЯ (merge_duplicate_deals_batch.Merge — те же шаги, что у общего скрипта:
merged[drop] = keep, источники, этап, снятие записей таблицы правок дубля):
  * c2455b014 → g7e90c94a (Ghelamco, логопарк в Дмитрове/Ермолино 243 тыс. кв. м).
    c2455b014 — переговоры о продаже (Коммерсантъ, 01.12.2022), g7e90c94a — сама
    продажа Central Properties. Одна сделка: переговоры 2022 года — этап.
    После слияния выжившая карточка правится по источникам: по итогам 2025 года
    консультанты IBC Real Estate и NF Group включили «покупку российской компанией
    Central Properties логистического парка в Дмитрове, который принадлежал
    бельгийской компании Ghelamco» в десятку крупнейших сделок года (РБК
    Недвижимость) — статус «Закрыта»; дня закрытия нет ни в одном источнике
    (Ведомости 21.04.2025: «по одной версии, сделка уже закрыта», по другой — нет) —
    дата годом. 15–18,5 млрд ₽ — оценка стоимости актива (CRE) и оценка сделки
    консультантами (РБК), не цена: сумма «Не раскрыта», оценки — в eco.val.
    CORE.XP — консультант продавца (Коммерсантъ, 2022).
  * g7e470153 → g61cccee7 («Суточно.ру», фонды «ВИМ Инвестиций», 16%, март 2024):
    одна сделка, g61cccee7 вычитана (реестр, 6 источников); из дубля — источники.

СНЯТИЕ (как pipeline/archive/2026-11/remove_five_non_deals_2026_11_07.py: карточка
уходит из deals, записи таблицы правок — fix_files.drop_fixes_for, telegram_posts
и consumed_urls остаются):
  * g08b7a4e1 — МТС «приобрела права на персонажей «Фиксики»»: по AdIndex, «сделка
    предполагает эксклюзивную лицензию образов всех основных героев «Фиксиков» в
    течение трех лет» — лицензия, не переход прав и не доля (прецедент —
    лицензия «Союзмультфильма»). Не сделка.
  * g2544a5cb — «Клиника Литфонд»: ни одного источника о самой сделке. Искали:
    Ведомости, РБК, Vademecum (vademec.ru 21.05.2024 — смена гендиректора, о
    продаже ни слова), поиск по старому и новому названию (ЗАО «Центральная
    поликлиника Литфонда» → АО «Центральная поликлиника на Ленинградке», ИНН
    7714066169), реестр (АО — акционеров ЕГРЮЛ не показывает; сайт реестра не
    ответил), каталоги юрлиц. Единственная «ссылка» карточки — статья Ведомостей
    2014 года о пенсионных деньгах «Роснефти», не про клинику. Описание профиля
    с утверждением о покупке снимается тем же скриптом.
  Карточки gef939ff4 («СБК Премьер») и gfe21a083 («Опека», сделка 2021 года) решаются
  отдельными скриптами этой партии: у них есть записи в чужих живых файлах правок.

    python3 pipeline/archive/2026-11/reread_deferred_m104.py           # сухой прогон
    python3 pipeline/archive/2026-11/reread_deferred_m104.py --write   # запись

Повторный запуск ничего не ломает: слитое и снятое пропускается, правка, которая
уже стоит, пропускается.
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DISCREP = os.path.join(ROOT, 'pipeline', 'facts_discrepancies.json')
BY = 'вычитка m104'
MISSING = object()

KOM_GH = 'https://www.kommersant.ru/doc/5695016'
RBC_GH = 'https://realty.rbc.ru/news/693c00079a79475e5b2e7993'
VED_GH = 'https://www.vedomosti.ru/realty/articles/2025/04/21/1105536-belgiiskaya-ghelamco-prodala-aktiv-v-rossii?from=copy_text'
VAD_LIT = 'https://vademec.ru/news/2024/05/21/mariya-kolomentseva-vozglavila-polikliniki-litfonda/'

MERGES = [
    {'keep': 'g7e90c94a', 'drop': 'c2455b014',
     'reason': 'Ghelamco: переговоры о продаже логопарка в Дмитрове (2022) и сама продажа Central Properties (2025) — одна сделка, переговоры — этап.',
     'add_src': [['Коммерсантъ', KOM_GH]],
     'events': [{'kind': 'negotiations', 'date': '2022-12-01', 'title': 'Ghelamco ищет покупателя на логопарк',
                 'note': 'Ghelamco ищет покупателя на логопарк площадью 243 тыс. кв. м.',
                 'source': ['Коммерсантъ', KOM_GH]}]},
    {'keep': 'g61cccee7', 'drop': 'g7e470153',
     'reason': '«Суточно.ру»: вход пре-IPO фондов «ВИМ Инвестиций» в капитал (16%, март 2024) — одна сделка под двумя id.',
     'add_src': [['РБК', 'https://www.rbc.ru/business/09/01/2025/676eb1a99a794793a15bc0d3'],
                 ['АБН', 'https://abn.agency/2026/04/01/sutochno-ru-uvelichil-vyruchku-na-37-v-2025-godu/'],
                 ['АБН', 'https://abn.agency/2026/04/18/sutochno-ru-gotovo-k-ipo-no-zhdyot-uluchsheniya-rynochnoj-konyunktury/']]},
]

REMOVE = {
    'g08b7a4e1': 'персонажей «Фиксики»',
    'g2544a5cb': 'клиник Литфонда',
}

# (id карточки, поле через точку, старое значение, новое значение, цитата, адрес)
EDITS = [
    ('g7e90c94a', 'status', 'Подписана', 'Закрыта',
     'В десятку крупнейших сделок на рынке недвижимости уходящего года также попала покупка российской компанией Central Properties логистического парка в Дмитрове, который принадлежал бельгийской компании Ghelamco.', RBC_GH),
    ('g7e90c94a', 'date', '2025-04-21', '2025',
     'В десятку крупнейших сделок на рынке недвижимости уходящего года также попала покупка российской компанией Central Properties логистического парка в Дмитрове, который принадлежал бельгийской компании Ghelamco.', RBC_GH),
    ('g7e90c94a', 'title', 'Ghelamco продает складской комплекс в Дмитрове компании Central Properties',
     'Central Properties купил складской комплекс в Дмитрове у Ghelamco',
     'В десятку крупнейших сделок на рынке недвижимости уходящего года также попала покупка российской компанией Central Properties логистического парка в Дмитрове, который принадлежал бельгийской компании Ghelamco.', RBC_GH),
    ('g7e90c94a', 'sum', '15–18,5 млрд ₽ (по оценке)', 'Не раскрыта',
     'Рейтинг составлен с учетом оценки стоимости сделок, которую делали консультанты (если цена сделки была нераскрыта сторонами).', RBC_GH),
    ('g7e90c94a', 'eco.sum', '15–18,5 млрд ₽ (по оценке)', 'Не раскрыта',
     'Рейтинг составлен с учетом оценки стоимости сделок, которую делали консультанты (если цена сделки была нераскрыта сторонами).', RBC_GH),
    ('g7e90c94a', 'eco.val', '—',
     'Рыночную стоимость комплекса оценивают в 15–18,5 млрд ₽; консультанты IBC Real Estate и NF Group, '
     'составлявшие рейтинг крупнейших сделок 2025 года, называют для этой сделки 15–18 млрд ₽. В 2022 году '
     'Егор Дорофеев из Commonwealth Partnership оценивал логопарк в 9–11 млрд ₽, Денис Платов из Nikoliers — '
     'в 9,5–10 млрд ₽.', '', ''),
    ('g7e90c94a', 'law.appr',
     'Юридически сделка пока не закрыта, хотя все обязывающие документы стороны уже подписали. По неофициальным данным, правительственная комиссия выдала все нужные разрешения.',
     'По неофициальным данным, правительственная комиссия выдала все нужные разрешения.', '', ''),
    ('g7e90c94a', 'law.adv',
     [['Стороны сделки', 'Не раскрывались', 'Юридические консультанты в публичных источниках не раскрывались']],
     [['Консультант продавца', 'CORE.XP', 'Консультант Ghelamco при продаже логопарка']],
     'В Ghelamco и CORE.XP, выступающей консультантом сделки, от комментариев отказались.', KOM_GH),
    ('g7e90c94a', 'extra',
     'Сделка по продаже складского комплекса площадью 243 000 кв. м в Дмитрове закрыта или близка к закрытию. Покупателем выступила компания, связанная с Central Properties. Сделка совершена иностранным инвестором с дисконтом к рыночной стоимости.',
     'Ghelamco выставила на продажу свой единственный актив в России — логопарк с офисами площадью 243 тыс. кв. м '
     'и участок почти в 30 га в Ермолино рядом с Дмитровым — в конце 2022 года. Среди претендентов тогда называли '
     'Central Properties, «Венталл-Девелопмент», девелопера Vesper и консорциум Professional Logistics Technologies, '
     'созданный РФПИ, Mubadala и другими фондами. В апреле 2025 года, по неофициальным данным, стороны подписали все '
     'обязывающие документы; по одной версии, сделка тогда уже была закрыта, по другой — еще нет. Покупатель '
     'официально не назван: по неофициальным данным, им стала компания, связанная с Central Properties.', '', ''),
]

# (id, поле, значение) — снятое неверное значение (docs/card_editing.md, «Снятое значение — в retracted»)
RETRACT = [('g7e90c94a', 'sum', '15–18,5 млрд ₽ (по оценке)')]

# (id профиля, ключ, старое, новое)
COMPANY_EDITS = [
    ('g1c505567', 'desc',
     'Медицинская группа; в 2024 году ее 100% купили бывшие топ-менеджеры «Роснефти» и МКБ за 2,5–2,7 млрд ₽ (по оценке).',
     'Частный многопрофильный медицинский центр в Москве, открытый на базе советской поликлиники Литфонда: '
     'две поликлиники и стоматологическое отделение, основное здание — у метро «Аэропорт».'),
]


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


def merge_step(data, write):
    import merge_duplicate_deals_batch as mdb
    known_ind = mdb.industries()
    known_themes = {t for d in data['deals'] for t in (d.get('themes') or [])}
    todo, errors = [], []
    for spec in MERGES:
        if data.get('merged', {}).get(spec['drop']) == spec['keep']:
            continue
        m = mdb.Merge(data, spec, known_ind, known_themes)
        m.check()
        for line in m.plan:
            print(line)
        errors += m.errors
        todo.append(m)
    if errors:
        raise SystemExit('ОТКАЗ слияния: %s' % '; '.join(errors))
    for m in todo:
        m.apply()
        print('  слито %s -> %s' % (m.drop_id, m.keep_id))
    if todo:
        mdb.strip_fixes({m.drop_id for m in todo}, write=write)
    return len(todo)


def remove_step(data, write):
    import fix_files
    cards = {d['id']: d for d in data['deals']}
    targets = set((data.get('merged') or {}).values())
    gone = []
    for cid, expect in REMOVE.items():
        card = cards.get(cid)
        if card is None:
            continue
        assert expect in str(card.get('title')), (cid, card.get('title'))
        assert cid not in targets, '%s — цель слияния' % cid
        gone.append(cid)
        print('  СНИМАЕМ %s %s' % (cid, str(card.get('title'))[:70]))
    if gone:
        data['deals'] = [d for d in data['deals'] if d['id'] not in gone]
        for cid in gone:
            touched = fix_files.drop_fixes_for(cid, write=write)
            if touched:
                print('    записи таблицы правок сняты: %s' % ', '.join(os.path.basename(p) for p in touched))
    return gone


def edit_step(data):
    import fact_edit_guard
    cards = {d['id']: d for d in data['deals']}
    comps = data['companies']
    done = 0
    for cid, field, old, new, quote, url in EDITS:
        card = cards[cid]
        cur = get(card, field)
        if cur == new:
            continue
        assert cur == old, '%s %s: в базе %r, ожидали %r' % (cid, field, cur, old)
        put(card, field, new)
        if quote and field in fact_edit_guard.FACT_FIELDS and new is not MISSING:
            fact_edit_guard.log(card, field, new, quote, url, BY)
        done += 1
        print('  %s %s: %r → %r' % (cid, field, str(old)[:60], str(new)[:60]))
    for cid, field, value in RETRACT:
        lst = cards[cid].setdefault('retracted', {}).setdefault(field, [])
        if value not in lst:
            lst.append(value)
            done += 1
    for pid, key, old, new in COMPANY_EDITS:
        p = comps[pid]
        cur = p.get(key, MISSING)
        if cur == new:
            continue
        assert cur == old, 'профиль %s %s: %r, ожидали %r' % (pid, key, cur, old)
        p[key] = new
        done += 1
        print('  профиль %s %s → %r' % (pid, key, str(new)[:70]))
    return done


def drop_discrepancies(gone, write):
    if not gone or not os.path.exists(DISCREP):
        return
    q = json.load(open(DISCREP, encoding='utf-8'))
    kept = [r for r in q if r.get('id') not in gone]
    if len(kept) != len(q):
        print('  facts_discrepancies: снять %d строк' % (len(q) - len(kept)))
        if write:
            json.dump(kept, open(DISCREP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def run(data, write):
    n = merge_step(data, write)
    gone = remove_step(data, write)
    n += len(gone) + edit_step(data)
    drop_discrepancies(gone + [m['drop'] for m in MERGES], write)
    return n


def main(argv):
    write = '--write' in argv
    data = json.load(open(DATA, encoding='utf-8'))
    n = run(copy.deepcopy(data), write=False)
    if not n:
        print('Уже применено.')
        return 0
    if not write:
        print('Сухой прогон: %d изменений. Запись — с ключом --write.' % n)
        return 0
    import mass_edit_guard
    old = json.load(open(DATA, encoding='utf-8'))   # перечитать прямо перед записью
    data = copy.deepcopy(old)
    run(data, write=True)
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано изменений: %d' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
