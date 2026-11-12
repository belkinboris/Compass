# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, марафон, партия m004: правки, которые review.py не умеет.

ЧТО ЧИНИТ (доказательства — в докстроке pipeline/ingest/fixes/reread_2026_11_12_m004.py,
тексты — data/inbox/triage/sources_2026-11-12_m004.json):
  * g7ca174fd — дата 2025-06-22 → 2025-07-22: переход 99,9% по ЕГРЮЛ (ФНС на сайте и datanewton)
    записан 22 июля, «22 июня» — ошибка «Коммерсанта»; словами «22 июля» день нигде не назван,
    поэтому review.py его не примет.
  * gda5d56f5 — дата 2025-05-01 → 2025: «1 мая» выдумано (статья от 19 мая, реестр АО показывает
    только единственного акционера с 01.08.2025); где искали других источников — accepted_notes.
  * g8cc36866 — дата 2025-01-13 → 2026-01-13 (перенос года: Consul Group — «первая крупная сделка
    2026 года», закрытие 13 января); покупатель — АО «Виннер» текстом, ссылка на профиль ГК «Таврос»
    снята («Таврос» участие отрицает).
  * g549ddd5a — продавец «Эксойл» (ООО «ЭКСОЙЛ», ИНН 7718635169, в истории «Агроинвеста» не
    значится) → «КГА Холдинг ЛЛС», у которой ЭФКО получила 68,6% «Агроинвеста» 27.08.2025.
  * ga2af8643 — ИНН предмета: профиль был сопоставлен с белгородским ООО «Электрощит-К»
    (3121010168); настоящее — калужское ООО «Электрощит-К°», ИНН 4001005954, ОГРН 1024000514504
    (datanewton, saby.ru, nec.pro: завод в Калужской области).
  * g54dc2165 — показатели: выручка 2021 года 1,4 млрд ₽ — по СПАРК в Interfax (английский текст, review.py
    числа из него не засчитывает), у RB.ru опечатка «11,4 млрд».
  * gadd238c3 — описание профиля «Рестера»: год покупки 2025 → 2026.
  * g2d69802d — консультант Unicorn без клиента → «финансовый консультант продавца» (поле не проза,
    review.py требует дословности).
  * accepted_notes: где искали продавца и вторые источники (g2d69802d, g7074c53b, gda5d56f5).
  * отпечатки прежних записей таблицы (fixes_archive) в proofread_absorbed на всех полях, которые
    переписала партия, — иначе test_no_duplicate_fix_for_one_field и
    test_review_table_is_applied_and_not_pending.

Каждая правка проверяет старое значение (assert); повторный запуск — «уже применено».
Запуск — внутри pipeline/reread_apply.py (после review.py --write):
    python3 pipeline/archive/2026-11/reread_oneoff_m004.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_oneoff_m004.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, ROOT)

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REG_JSON = os.path.join(ROOT, 'pipeline', 'fns_registry.json')
BY = 'вычитка 12 ноября 2026, партия m004'

DN_RO = 'https://datanewton.ru/contragents/1091310001090/history/timeline'
Q_RO = ('2025-07-22 OLD: None | NEW: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ЛИКЕРОВОДОЧНЫЙ ЗАВОД "САРАНСКИЙ" '
        '(ОГРН: 1071326004111) 99.9%')
Q_ME = ('Застройщик просит кирпича Группа «Развитие» приобрела завод «Меакир» 19.05.2025, 20:35')
Q_SG = ('Первая крупная сделка 2026 года на московском рынке На этой неделе «Ароса-логистика» завершила продажу '
        'бывшего гипермаркета Selgros на Боровском шоссе')
Q_SG2 = 'В сделку, которая закрылась 13 января, вошли участок на 6,9 га'
Q_SG3 = ('UPD: Представитель «Тавроса», впрочем, уверяет, что группа не участвовала в этой сделке, а АО «Виннер» '
         'просто является ее партнером по ряду проектов')
Q_EF = ('Компания "ЭФКО" увеличила с 31,4% до 100% долю в ООО "Агроинвест" … Ранее 68,6% принадлежали катарской '
        '"КГА Холдинг ЛЛС", владельцы которой не раскрывались. Изменения отражены в ЕГРЮЛ с 27 августа.')

Q_MF = ('Yedinyfaktor LLC, which was registered in 2010, closed 2021 with a net profit of 898.6 million rubles on '
        'sales revenue of 1.4 billion rubles, the SPARK-Interfax system showed. … Выручка компании по итогам 2021 '
        'года составила 11,4 млрд рублей (против 792 млн в 2020 году), чистая прибыль — 898,6 млн рублей (против '
        '335,6 млн в 2020 году).')
Q_GR = 'Советником в сделке со стороны продавца выступал инвестбанк Unicorn, указано на сайте банка.'

# (карточка, поле, старое, новое, цитата, адрес) — поля-факты, правка с fact_log
SET = [
    ('g7ca174fd', 'date', '2025-06-22', '2025-07-22', Q_RO, DN_RO),
    ('g7ca174fd', 'date_basis', None, 'registry', Q_RO, DN_RO),
    ('gda5d56f5', 'date', '2025-05-01', '2025', Q_ME, 'https://www.kommersant.ru/doc/7735639'),
    ('g8cc36866', 'date', '2025-01-13', '2026-01-13', Q_SG + ' … ' + Q_SG2, 'https://t.me/expertsconsulgroup/702'),
    ('g8cc36866', 'date_basis', None, 'closing', Q_SG2, 'https://t.me/filatofff/5692'),
    ('g8cc36866', 'buyer', 'gcaccecb1', None, Q_SG3, 'https://t.me/filatofff/5692'),
    ('g8cc36866', 'buyer_name', None, 'АО «Виннер»', Q_SG3, 'https://t.me/filatofff/5692'),
    ('g549ddd5a', 'seller', '«Эксойл»', '«КГА Холдинг ЛЛС»', Q_EF, 'https://www.interfax.ru/business/1044618'),
    ('g549ddd5a', 'seller_id', 'gecb9dad0', None, Q_EF, 'https://www.interfax.ru/business/1044618'),
    ('g54dc2165', 'eco.target_fin',
     'Выручка компании за 2021 год составила 1,4 млрд рублей против 792 млн в 2020 году, чистая прибыль — 898,6 млн '
     'рублей против 335,6 млн в 2020 году.',
     'По данным СПАРК, выручка oneFactor за 2021 год — 1,4 млрд ₽, чистая прибыль — 898,6 млн ₽; годом ранее — '
     '792 млн ₽ и 335,6 млн ₽.', Q_MF, 'https://interfax.com/newsroom/top-stories/86561/'),
    ('g2d69802d', 'eco.finadv', 'Unicorn', 'Unicorn — финансовый консультант продавца', Q_GR,
     'https://shoppers.media/news/26121_krupneisii-proizvoditel-miasa-pticy-resurs-kupil-makaronnyi-biznes-granmulino'),
]
RETRACT = [('g8cc36866', 'buyer_name', 'ГК «Таврос»'), ('g549ddd5a', 'seller', '«Эксойл»')]
NOTES = {
    'g8cc36866': {'searched': 'первоисточники заметки @dealsma — t.me/filatofff/5692 и t.me/expertsconsulgroup/702 '
                              '(Consul Group); WebSearch («Виннер» Таврос Selgros Боровское шоссе; АО «Виннер» ИНН) — '
                              'публикаций в деловых СМИ нет; OpenSanctions (АО «Виннер», ИНН 9728096456); '
                              'retail.ru о продаже Selgros «Ароса-логистике» (ноябрь 2024).'},
    'gda5d56f5': {'searched': 'Коммерсантъ-Прикамье (19.05.2025, сообщение «Развития» и цитаты Раева и '
                              'Россахацкого); WebSearch в двух формулировках («Меакир» «Развитие» кирпичный завод '
                              'Березники; Меакир 2025 купила) — других публикаций о сделке нет; EMIS (профиль без '
                              'владельцев); реестр ФНС на сайте (АО: единственный акционер ООО «ИСГ «Развитие» '
                              'с 01.08.2025); datanewton (поиск не ответил). Дня сделки в источниках нет — дата годом.'},
    'g2d69802d': {'no_profile.seller': 'продавец ТД «Алтан» по ЕГРЮЛ — Галина Маганова (с 20.06.2025 до '
                                       '12.12.2025, datanewton), но в сделку вошли еще два АО (НПФ «Алтан», '
                                       'Поспелихинский КХП), акционеров которых реестр не показывает; Shoppers, '
                                       'Коммерсантъ, «Атмосфера» продавца не называют, Unicorn — консультант '
                                       'продавца без имени клиента. Продавец одной из четырех компаний на всю '
                                       'сделку не обобщается (docs/card_parties.md) — история в law.struct.'},
    'g7074c53b': {'no_profile.seller': 'инвестиция: 45% «Альтера Капитал» получила 10.01.2025 за счет уступки '
                                       'долей совладельцами (по ЕГРЮЛ — Сьянова 50→18,34%, Артюшев и Кудинов '
                                       '25→18,33%), деньги, по словам фонда, идут на разработки — названо в '
                                       'law.struct; отдельной продажи нет',
                  'searched': 'Коммерсантъ (24.01.2025); WebSearch («Альтера Капитал» «Селтек»; Селтек '
                              'Biocellium инвестиции; Андросов косметика) — других публикаций нет; реестр ФНС '
                              'на сайте (история участников ООО «Селтек»).'},
}
DESC = [('gd1907243',
         'Производитель растворов для перитонеального диализа; в 2025 году ГК «Фармасинтез» купила 70% акций у '
         'Ижевского электромеханического завода «Купол» (концерн «Алмаз-Антей»).',
         'Производитель растворов для перитонеального диализа, дочерняя компания Ижевского электромеханического '
         'завода «Купол» (концерн «Алмаз-Антей»); в июле 2026 года ГК «Фармасинтез» купила 70% его акций.')]
REG_NEW = {'company_id': 'g52e854a8', 'decision': 'confirmed', 'inn': '4001005954',
           'reason': 'ООО «Электрощит-К°», ИНН 4001005954, ОГРН 1024000514504, Калужская область, ОКВЭД '
                     '«производство трансформаторов», гендиректор Гайк Гаспарян — тот же, что в сообщении завода '
                     '(EnergyLand, 16.12.2025); владелец с 04.06.2025 — АО «Энергия Инноваций» (группа «НЭК») по '
                     'datanewton и saby.ru. Прежняя запись (3121010168, белгородское ООО «Электрощит-К», Кокорин) — '
                     'тезка. Вычитка 12 ноября 2026 (партия m004).',
           'date': '2026-11-12'}
# Поля, которые партия переписала: FIXES (review.py) и SET этого файла.
TOUCHED = {
    'g54dc2165': ['title', 'date', 'date_basis', 'eco.share', 'eco.context', 'eco.rationale', 'extra', 'eco.target_fin'],
    'g7ae9bb53': ['title', 'date', 'date_basis', 'eco.share', 'eco.rationale', 'eco.target_fin', 'eco.context'],
    'g2d69802d': ['eco.share', 'eco.rationale', 'law.struct', 'eco.target_fin', 'eco.finadv', 'extra', 'eco.context'],
    'g99be4c1d': ['title', 'eco.share', 'law.struct', 'law.appr', 'extra'],
    'g61eca68c': ['title', 'eco.share', 'eco.val', 'eco.target_fin', 'eco.rationale', 'extra', 'eco.context'],
    'g7ca174fd': ['title', 'eco.share', 'law.struct', 'eco.target_fin', 'eco.fin', 'eco.fin_context',
                  'eco.context', 'extra', 'date', 'date_basis'],
    'gadd238c3': ['title', 'eco.share', 'eco.context', 'eco.rationale', 'eco.fin_context', 'extra'],
    'ga2af8643': ['title', 'seller', 'extra', 'eco.context'],
    'g549ddd5a': ['title', 'date', 'date_basis', 'eco.share', 'law.struct', 'law.appr', 'eco.val', 'extra', 'eco.context',
                  'seller', 'seller_id'],
    'gda5d56f5': ['title', 'eco.share', 'eco.rationale', 'eco.context', 'extra', 'date'],
    'g8cc36866': ['title', 'eco.share', 'eco.context', 'extra', 'date', 'date_basis', 'buyer', 'buyer_name'],
    'g7074c53b': ['type', 'title', 'date_basis', 'eco.share', 'law.struct', 'eco.rationale', 'eco.context'],
}


def get(card, field):
    obj = card
    for p in field.split('.'):
        obj = obj.get(p) if isinstance(obj, dict) else None
    return obj


def put(card, field, value):
    parts = field.split('.')
    obj = card
    for p in parts[:-1]:
        obj = obj.setdefault(p, {})
    if value is None:
        obj.pop(parts[-1], None)
    else:
        obj[parts[-1]] = value


def main(argv):
    write = '--write' in argv
    import fact_edit_guard
    import mass_edit_guard
    import review
    raw = open(DATA, encoding='utf-8').read()          # перечитать прямо перед записью
    data = json.loads(raw)
    old = json.loads(raw)
    by = {d['id']: d for d in data['deals']}
    done = 0
    for cid, field, was, new, quote, url in SET:
        card = by[cid]
        cur = get(card, field)
        if cur == new:
            print('уже применено: %s.%s' % (cid, field))
            continue
        assert cur == was, '%s.%s: в базе %r, ожидали %r' % (cid, field, cur, was)
        put(card, field, new)
        fact_edit_guard.log(card, field, new, quote, url, BY)
        print('%s.%s: %r → %r' % (cid, field, was, new))
        done += 1
    for cid, field, value in RETRACT:
        lst = by[cid].setdefault('retracted', {}).setdefault(field, [])
        if value not in lst:
            lst.append(value)
            done += 1
    for cid, notes in NOTES.items():
        acc = by[cid].setdefault('accepted_notes', {})
        for key, text in notes.items():
            if '.' in key:
                a, b = key.split('.')
                if acc.setdefault(a, {}).get(b) != text:
                    acc[a][b] = text
                    done += 1
            elif acc.get(key) != text:
                acc[key] = text
                done += 1
    for comp, was, new in DESC:
        cur = data['companies'][comp].get('desc')
        if cur != new:
            assert cur == was, '%s.desc: %r' % (comp, cur)
            data['companies'][comp]['desc'] = new
            done += 1
    # Отпечатки прежних записей таблицы на переписанных полях.
    for cid, fields in TOUCHED.items():
        card = by[cid]
        absorbed = card.setdefault('proofread_absorbed', {})
        for field in fields:
            recs = [f for f in review.FIXES if (f['id'], f['field']) == (cid, field)]
            prior = [f for f in recs if f['new'] != get(card, field)]   # стоящее значение — не прежнее
            for f in prior:
                fp = review.fix_fingerprint(f['new'])
                marks = absorbed.setdefault(field, [])
                if fp not in marks:
                    marks.append(fp)
                    done += 1
        if not absorbed:
            card.pop('proofread_absorbed', None)
    reg = json.load(open(REG_JSON, encoding='utf-8'))
    reg_cur = [e for e in reg if e.get('company_id') == REG_NEW['company_id']]
    reg_changed = not reg_cur or reg_cur[-1].get('inn') != REG_NEW['inn']
    if reg_changed:
        assert reg_cur and reg_cur[-1].get('inn') == '3121010168', reg_cur
        reg = [e for e in reg if e.get('company_id') != REG_NEW['company_id']] + [REG_NEW]
        done += 1
    print('изменений: %d' % done)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    if not done:
        return 0
    mass_edit_guard.check(old, data, key='reread')
    out = json.dumps(data, ensure_ascii=False, indent=1)
    if raw.endswith('\n'):
        out += '\n'
    open(DATA, 'w', encoding='utf-8').write(out)
    if reg_changed:
        rraw = open(REG_JSON, encoding='utf-8').read()
        rout = json.dumps(reg, ensure_ascii=False, indent=1)
        if rraw.endswith('\n'):
            rout += '\n'
        open(REG_JSON, 'w', encoding='utf-8').write(rout)
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
