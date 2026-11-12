# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026 (марафон, партия m054, третья часть): правки, которые не ложатся в FIXES.

Что чинит: суммы-оценки с границей («до N млн ₽ (по оценке)» — review.py такой формат
не разбирает), пустое поле вместо фактов не по адресу, покупатель по реестру (новый профиль
формального покупателя) и описания профилей сторон, где стояли неподтвержденные факты
(цена-оценка как цена, число точек и состав группы, которых нет в источниках). Каждая правка
факта — с цитатой источника через fact_edit_guard.log.

    python3 pipeline/archive/2026-11/reread_oneoff_m054c.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_oneoff_m054c.py --write

База перечитывается прямо перед записью; на каждое поле — assert на старое значение;
повторный запуск ничего не меняет («уже применено»).
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REG = os.path.join(ROOT, 'pipeline', 'fns_registry.json')
BY = 'вычитка m054, 12 ноября 2026'

# (id карточки, поле, было, стало, цитата, адрес)
Q_AMR = ('2023-05-15: было — нет; стало — ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "СМАРТ СЕРВИС НОРД" '
         '(ОГРН: 1221800025688) 100%; (3 788 200 532,23 руб.)')
U_AMR = 'https://datanewton.ru/api/v2/history?ogrn=1027809227050&startDate=2000-01-01&attributes=OWNERS'
Q_AMR_SUM = 'Сумма сделки, как и планировалось, составила 100 млн евро.'
U_AMR_SUM = 'https://www.vedomosti.ru/business/news/2023/05/16/975217-polskii-franchaizi-kfc-zakril-sdelku-po-prodazhe-215-restoranov'
DEALS = [
    # g61a8095f (AmRest/KFC): предметом стояло ООО «Юнирест» — держатель мастер-франшизы, купленный у
    # Yum! Brands отдельной сделкой (своя карточка). AmRest продал 100% ООО «АмРест» (ОГРН 1027809227050):
    # по ЕГРЮЛ 15.05.2023 доли AmRest Sp. z o.o. (55,28%) и AmRest Acquisition Subsidiary Ltd (44,72%)
    # перешли к ООО «Смарт Сервис Норд» (ОГРН 1221800025688, гендиректор Константин Котов).
    ('g61a8095f', 'target', 'gf15f54d1', 'gamrestru', Q_AMR, U_AMR),
    ('g61a8095f', 'buyer', 'g3104e805', 'gsmartnord', Q_AMR, U_AMR),
    ('g61a8095f', 'date', '2023-05-16', '2023-05-15', Q_AMR, U_AMR),
    ('g61a8095f', 'date_basis', None, 'registry', '', ''),
    # Одна цена — одно написание в обоих полях (находка sum_fields_differ).
    ('g61a8095f', 'sum', '100 млн €', '€100 млн', Q_AMR_SUM, U_AMR_SUM),
    # Оценка 2022 года без автора и с рассуждением «сравнивать нельзя» — ни в одном открытом источнике.
    ('g61a8095f', 'eco.val',
     'В начале 2022 года, когда из-за санкций против ВТБ сорвалась другая продажа, аналитики оценивали весь '
     'российский бизнес AmRest в 5–6 млрд ₽, а с учетом рисков — вдвое меньше. Это заметно ниже фактической '
     'цены сделки, закрытой в 2023 году (100 млн €), но относится к другому периоду и несостоявшемуся '
     'покупателю, поэтому сравнивать напрямую нельзя.', '—', '', ''),
]

# (id профиля, поле, было, стало); legal_short ставится, только если его еще нет.
PROFILES = [
    ('g059b01f5', 'legal_short', None, 'АО «УК «Архыз»»'),
    ('ge99c6248', 'legal_short', None, 'АО «Кавказ.РФ»'),
    ('g4ef5175f', 'legal_short', None, 'АО «Газпромбанк Лизинг»'),
    ('g8649c80c', 'legal_short', None, 'ООО «Рейма»'),
    ('g3104e805', 'desc',
     'Компания Константина Котова и Андрея Осколкова; выкупила у AmRest и Yum! Brands российский бизнес KFC '
     '— 215 и 70 ресторанов соответственно.',
     'Компания Константина Котова и Андрея Осколкова (ГК «Фуд-сервис»). В 2023 году купила у Yum! Brands '
     '70 ресторанов KFC и мастер-франшизу, подписала договор о покупке бизнеса AmRest; доли АмРеста '
     'получило ООО «Смарт Сервис Норд».'),
]

NEW = {
    'gamrestru': {'name': 'ООО «АмРест» (KFC в России)', 'legal_short': 'ООО «АмРест»', 'ind': 'Пищепром и напитки',
                  'desc': 'Бывшая российская компания AmRest: управляла 215 ресторанами KFC. С мая 2023 года '
                          'принадлежала ООО «Смарт Сервис Норд», с апреля 2026 года 75% — у ООО «Интернэшнл '
                          'ресторант брэндс».',
                  'kpi': ['Профиль', 'Автоматический']},
    'gsmartnord': {'name': 'Смарт Сервис Норд', 'legal_short': 'ООО «Смарт Сервис Норд»', 'ind': 'Пищепром и напитки',
                   'desc': 'Компания Константина Котова (гендиректор), владельца ГК «Фуд-сервис»; в 2023 году '
                           'получила 100% ООО «АмРест» с ресторанами KFC.',
                   'kpi': ['Профиль', 'Автоматический']},
}
NEW_REG = [
    {'company_id': 'gamrestru', 'decision': 'confirmed', 'inn': '7825335145', 'date': '2026-11-12',
     'reason': 'ООО «АмРест», ОГРН 1027809227050, ИНН 7825335145 (позже ООО «МайРест»): история участников '
               'ЕГРЮЛ (datanewton.ru) — до 15.05.2023 участники AmRest Sp. z o.o. и AmRest Acquisition '
               'Subsidiary Ltd; ИНН — companies.rbc.ru по тому же ОГРН.'},
    {'company_id': 'gsmartnord', 'decision': 'confirmed', 'inn': '1831208240', 'date': '2026-11-12',
     'reason': 'ООО «Смарт Сервис Норд», ОГРН 1221800025688, ИНН 1831208240, гендиректор Котов К. Ю. '
               '(datanewton.ru); тот же ОГРН — новый участник ООО «АмРест» со 100% с 15.05.2023 (ЕГРЮЛ); '
               'консультант Denuo называет его покупателем бизнеса AmRest (pravo.ru).'},
]

# Исправление строк реестра ФНС: (id профиля, старый ИНН, новый ИНН, причина).
# g059b01f5 («Курорт «Архыз»», предмет g2f572b66): к профилю был привязан ООО «Курорт»
# (ИНН 0900013563) по совпадению региона, а продавались акции АО «Управляющая компания
# «Архыз»» — ИНН 0900003460, ОГРН 1220900002179 (datanewton.ru; решение ФАС по ходатайству
# «Горных вершин» и companies.rbc.ru — тот же ИНН).
REG_FIX = [
    ('g059b01f5', '0900013563', '0900003460',
     'АО «УК «Архыз»», ИНН 0900003460, ОГРН 1220900002179 — общество, 100% акций которого продавал '
     '«Кавказ.РФ» («Интерфакс», 1 марта 2023 года); ИНН по datanewton.ru и решению ФАС по ходатайству '
     '«Горных вершин». Прежняя привязка к ООО «Курорт» (0900013563) была по региону и ошибочна.'),
]


def _get(card, field):
    if '.' in field:
        a, b = field.split('.', 1)
        return (card.get(a) or {}).get(b)
    return card.get(field)


def _set(card, field, value):
    if '.' in field:
        a, b = field.split('.', 1)
        card.setdefault(a, {})[b] = value
    else:
        card[field] = value


def apply_reg(rows):
    have = {r.get('company_id') for r in rows}
    n = 0
    for pid, old, new, reason in REG_FIX:
        row = next(r for r in rows if r.get('company_id') == pid)
        if row.get('inn') == new:
            continue
        assert row.get('inn') == old, (pid, row.get('inn'))
        row['inn'] = new
        row['reason'] = reason
        row['date'] = '2026-11-12'
        n += 1
    for row in NEW_REG:
        if row['company_id'] not in have:
            rows.append(dict(row))
            n += 1
    return n


def apply(data):
    by = {d['id']: d for d in data['deals']}
    comps = data['companies']
    done = 0
    for pid, prof in NEW.items():
        if pid in comps:
            print('уже применено: профиль %s' % pid)
            continue
        comps[pid] = dict(prof)
        done += 1
        print('новый профиль %s %s' % (pid, prof['name']))
    for cid, field, old, new, quote, url in DEALS:
        card = by[cid]
        cur = _get(card, field)
        if cur == new:
            print('уже применено: %s %s' % (cid, field))
            continue
        assert cur == old, (cid, field, cur)
        _set(card, field, new)
        if field in fact_edit_guard.FACT_FIELDS:
            fact_edit_guard.log(card, field, new, quote, url, BY)
        done += 1
        print('%s %s: %r → %r' % (cid, field, str(old)[:50], new))
    for pid, field, old, new in PROFILES:
        cur = comps[pid].get(field)
        if field == 'legal_short' and cur:
            print('уже есть legal_short: профиль %s — %s' % (pid, cur))
            continue
        if cur == new:
            print('уже применено: профиль %s %s' % (pid, field))
            continue
        assert cur == old, (pid, field, cur)
        comps[pid][field] = new
        done += 1
        print('профиль %s %s: %r → %r' % (pid, field, (old or '')[:50], new[:50]))
    return done


def main(argv):
    n = apply(json.load(open(BASE, encoding='utf-8')))
    n += apply_reg(json.load(open(REG, encoding='utf-8')))
    if '--write' not in argv:
        print('Сухой прогон: правок %d. Запись — --write.' % n)
        return 0
    data = json.load(open(BASE, encoding='utf-8'))
    apply(data)
    with open(BASE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    rows = json.load(open(REG, encoding='utf-8'))
    if apply_reg(rows):
        with open(REG, 'w', encoding='utf-8') as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
