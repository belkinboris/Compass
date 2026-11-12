# -*- coding: utf-8 -*-
"""Вычитка, марафон 12 ноября 2026, партия m045, вторая часть: правки вне таблицы FIXES.

  gaa0f4fb7 Marathon Group / Grow Food — продавцами стояли МКООО «Винда Лимитед» и фонд
    Add Venture: ни один источник их продавцами не называет, «Винда» — владелец 99%
    ООО «ГФ Трейд», и состав его участников после сделки не менялся (доля куплена выше
    по цепочке). Продавец снят, где искали — в accepted_notes. Дата 01.12.2023 — заглушка:
    о закрытой сделке Forbes сообщил 1 февраля 2024 года (date_basis publication). Сумма —
    оценка Forbes: «(по оценке)». Показатели сервиса стояли в «Оценке» — перенесены в
    «Показатели компании».
  g9016d7ac Fix Price — дата 01.12.2023 — заглушка, дня сделки в источниках нет (раскрытие
    29.12.2023): дата годом. «Цель сделки» описывала причину продавца — она в контексте.
  g1e2b16c3 S8 / Bridgestone — 7,5–9,8 млрд ₽ — оценка аналитика, «Коммерсантъ»: «Сумма сделки
    не раскрывается». Предмет — доли двух ООО, а не описание завода.
  g19186bb9 «Хайв» / T.one — «Оценка» повторяла финансы из «Показателей».
  g3db7d882 «Румелко» / «Кашин луг» — покупатель по ЕГРЮЛ — ООО «Румелко» (ИНН 7727160666,
    ОГРН 1027700069121), а не ООО «Румелко-Агро» (ИНН 6909008255, профиль g934fd312):
    Интерфакс: «Румелко» владеет лишь 21,51% «Румелко-Агро». Заведен профиль «Румелко».
    В «Экономисте» вместо суммы лежала фраза статьи.

    python3 pipeline/archive/2026-11/reread_m045_b.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_m045_b.py --write
Повторный запуск ничего не ломает («уже применено»).
"""
import copy
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REGISTRY_PY = os.path.join(ROOT, 'pipeline', 'fns_registry.py')
BY = 'вычитка m045, 12.11.2026'
U = '(уже применено)'

DP = 'https://www.dp.ru/a/2024/02/01/vladelec-magnita-kupil-peterburgskij'
GF_Q = 'Сумма сделки оценивается в 4–4,5 млрд рублей.'
GF_DATE_Q = ('Инвестиционная компания Marathon Group Александра Винокурова стала совладельцем сервиса по доставке '
             'готовых продуктовых наборов Grow Food . О покупке рассказали Forbes источники на рынке продовольственного '
             'ретейла и в сегменте доставки питания. По словам собеседников издания, сделка уже закрыта.')
GF_VAL_OLD = ('За девять месяцев оборот вырос на 15,8% год к году, до 3,1 млрд ₽. Число заказов прибавило 26,3%, до '
              '608 400. Средний чек в III квартале 2023 снизился на 2,8% год к году, до 5845 ₽.')
KFP = 'https://www.kommersant.ru/doc/6440783'
FP_Q = ('Сооснователь Fix Price Хачатрян продал свою долю и вышел из совета директоров ритейлера 29.12.2023, 20:05 '
        'Сооснователь сети Fix Price (MOEX: FIXP ) бизнесмен Артем Хачатрян продал свою долю 35,2%')
KBR = 'https://www.kommersant.ru/doc/6412480'
BR_Q = 'Сумма сделки не раскрывается, но активы Continental, как писал «Ъ» , обошлись S8 в 7–10 млрд руб.'
BR_SHARE_Q = ('Запись от 2023-12-26: вышел из участников — БРИДЖСТОУН ЮРОП, ОАО (ИНН None), доля была 100.0%, стала None%.')
BR_REG = 'https://projectcompass.ru/api/companies/gb9ce9a5d/fns'
IK1 = 'https://www.interfax.ru/business/934043'
KL_Q = 'Запись от 2023-11-27: вошел в участники — ООО "РУМЕЛКО" (ИНН 7727160666), доля была None%, стала 80.0%.'
KL_REG = 'https://projectcompass.ru/api/companies/ge59f3526/fns'
IK2 = 'https://www.interfax.ru/business/952354'
KL_SUM_Q = ('Сумма сделки по покупке холдингом "Румелко" (принадлежит основному владельцу НЛМК Владимиру Лисину) 80% '
            'агрохозяйства "Кашин луг" (Тверская область) составляет 589 млн рублей.')
NEW_ID = 'g515248f7'

CARD_EDITS = [
    ('gaa0f4fb7', 'date', '2023-12-01', '2024-02-01', GF_DATE_Q, DP),
    ('gaa0f4fb7', 'date_basis', None, 'publication', None, None),
    ('gaa0f4fb7', 'sum', '4–4,5 млрд ₽', '4–4,5 млрд ₽ (по оценке)', GF_Q, DP),
    ('gaa0f4fb7', 'eco.sum', '4–4,5 млрд ₽', '4–4,5 млрд ₽ (по оценке)', GF_Q, DP),
    ('gaa0f4fb7', 'seller', 'МКООО «Винда Лимитед» и венчурный фонд Add Venture', None,
     'Согласно данным ЕГРЮЛ, ООО "ГФ Трейд" (юрлицо Grow Food) принадлежит ООО "Единорог" (1%) и МКООО "Винда Лимитед" (99%). '
     'Последняя была зарегистрирована на Кипре, но в июле 2023 года провела редомициляцию в Калининград. '
     'Сведения о двух владельцах компании не раскрываются.', DP),
    ('gaa0f4fb7', 'eco.target_fin', '—', GF_VAL_OLD, None, None),
    ('g9016d7ac', 'date', '2023-12-01', '2023', FP_Q, KFP),
    ('g9016d7ac', 'eco.rationale',
     'Артем Хачатрян, один из основателей Fix Price (MOEX: FIXP), продал долю и вышел из совета директоров; причина — '
     'семейные обстоятельства. Fix Price Group PLC раскрыла это на сайте раскрытия корпоративной информации.', '—', None, None),
    ('g1e2b16c3', 'sum', '7,5–9,8 млрд ₽ (по оценке)', 'Не раскрыта', BR_Q, KBR),
    ('g1e2b16c3', 'eco.sum', '7,5–9,8 млрд ₽ (по оценке)', 'Не раскрыта', BR_Q, KBR),
    ('g1e2b16c3', 'eco.share', 'Завод Bridgestone в Ульяновске: запущен в 2016, выпускает 2,4 млн шин в год, вложено около 12,5 млрд ₽.',
     '100% долей в ООО «Бриджстоун тайер мануфэкчуринг СНГ» и ООО «Бриджстоун СНГ»', BR_SHARE_Q, BR_REG),
    ('g19186bb9', 'eco.val',
     'Выручка «Т.Один» в 2022 году — 3,4 млн ₽ против 3,3 млн ₽ годом ранее. Чистая прибыль за 2022 год составила 465 тыс. ₽, '
     'тогда как в 2021 году компания получила 4,1 млн ₽ чистого убытка.', '—', None, None),
    ('g3db7d882', 'buyer', 'g934fd312', NEW_ID, KL_Q, KL_REG),
    ('g3db7d882', 'eco.sum',
     'Сумма сделки по покупке холдингом «Румелко» (принадлежит основному владельцу НЛМК Владимиру Лисину) 80% агрохозяйства '
     '«Кашин луг» (Тверская область) составляет 589 млн рублей.', '589 млн ₽', KL_SUM_Q, IK2),
]
RETRACT = [('gaa0f4fb7', 'seller', 'МКООО «Винда Лимитед» и венчурный фонд Add Venture'),
           ('g1e2b16c3', 'sum', '7,5–9,8 млрд ₽ (по оценке)')]
NOTES = [('gaa0f4fb7', 'seller',
          'Продавец не назван. ЕГРЮЛ ООО «ГФ Трейд»: 99% у МКООО «Винда Лимитед», 1% у ООО «Единорог», состав после '
          'июля 2023 года не менялся — доля куплена выше по цепочке, владельцы «Винды» не раскрываются (Деловой Петербург). '
          'Forbes (капча), Коммерсантъ, Деловой Петербург, TAdviser, поиск по «Marathon Group Grow Food продавец» — продавца '
          'не называют; Add Venture — ранний инвестор (около 330 млн ₽), о продаже им доли источники не пишут. Вычитка m045, 12.11.2026.')]

PROFILE_NEW = (NEW_ID, {
    'name': 'Румелко', 'ind': 'Агро', 'legal_short': 'ООО «Румелко»',
    'desc': 'Агрохолдинг Владимира Лисина, основного владельца НЛМК: молочное животноводство и выращивание кормов в '
            'Тверской и Калужской областях и Алтайском крае. Владеет 21,51% ООО «Румелко-Агро».',
    'kpi': ['Профиль', 'Автоматический']})

PROFILE_EDITS = [
    ('g27010a1f', 'legal_short', None, 'ООО «ГФ Трейд»'),
    ('gc5df9ed1', 'legal_short', None, 'ООО «Марафон Групп»'),
    ('g4cd83394', 'legal_short', None, 'ПАО «Фикс Прайс»'),
    ('gb9ce9a5d', 'legal_short', None, 'ООО «Кордиант Ульяновск»'),
    ('ge59f3526', 'legal_short', None, 'ООО «Кашин луг»'),
]

REGISTRY_BLOCK = """
# Вычитка m045 — 2026-11-12 (pipeline/archive/2026-11/reread_m045_b.py).
REGISTRY += [
    {"company_id": 'g515248f7', "decision": "confirmed", "inn": '7727160666',
     "reason": 'Покупатель сделки g3db7d882 (вычитка m045, 12.11.2026). ООО «Румелко», ИНН 7727160666, ОГРН 1027700069121: (1) ЕГРЮЛ ООО «Кашин луг» (ИНН 6909009763) на нашем сайте — 27.11.2023 вошел ООО "РУМЕЛКО", ИНН 7727160666, 80%, с 29.04.2026 — 100%; (2) история участников на Датаньютоне по ОГРН 1106910000482 — запись 27.11.2023: ООО "РУМЕЛКО" (ОГРН 1027700069121) 80%; (3) Интерфакс 30.11.2023 и 25.03.2024: холдинг «Румелко» Владимира Лисина владеет 80% «Кашина луга» и 21,51% «Румелко-Агро». Не путать с ООО «Румелко-Агро» (ИНН 6909008255, профиль g934fd312).',
     "date": '2026-11-12'},
]
"""


def get(card, field):
    if '.' in field:
        a, b = field.split('.', 1)
        return (card.get(a) or {}).get(b)
    return card.get(field)


def put(card, field, value):
    if '.' in field:
        a, b = field.split('.', 1)
        card.setdefault(a, {})[b] = value
    else:
        card[field] = value


MY_IDS = ('gaa0f4fb7', 'geda130b6', 'g9016d7ac', 'g1e2b16c3', 'g19186bb9', 'g3db7d882')


def drop_fixed_baseline(data):
    """Исправленное старое нарушение правил текста уходит из text_rules_baseline.json."""
    import text_rules
    path = text_rules.BASELINE
    base = json.load(open(path, encoding='utf-8'))
    now = {fp for fp, did, *_ in text_rules.all_findings({'deals': [d for d in data['deals'] if d['id'] in MY_IDS]})}
    keep = [fp for fp in base['known'] if not (fp.split('|')[0] in MY_IDS and fp not in now)]
    if len(keep) != len(base['known']):
        print('  снято из списка старых нарушений: %d' % (len(base['known']) - len(keep)))
        base['known'] = keep
        json.dump(base, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))          # перечитываем прямо перед записью
    old = copy.deepcopy(data)
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    changed = 0
    pid, prof = PROFILE_NEW
    if pid not in comps:
        comps[pid] = dict(prof)
        print('  НОВЫЙ профиль %s %s' % (pid, prof['name']))
        changed += 1
    for cid, field, was, new, quote, url in CARD_EDITS:
        card = deals[cid]
        cur = get(card, field)
        if cur == new:
            print('  %s %s %s' % (cid, field, U))
            continue
        assert cur == was, '%s %s: ожидали %r, стоит %r' % (cid, field, was, cur)
        put(card, field, new)
        if quote and field in fact_edit_guard.FACT_FIELDS:
            fact_edit_guard.log(card, field, new, quote, url, BY)
        print('  ПРАВИМ %s %s: %r -> %r' % (cid, field, str(was)[:50], new))
        changed += 1
    for cid, field, value in RETRACT:
        r = deals[cid].setdefault('retracted', {}).setdefault(field, [])
        if value not in r:
            r.append(value)
            changed += 1
    for cid, role, text in NOTES:
        nb = deals[cid].setdefault('accepted_notes', {}).setdefault('no_profile', {})
        if nb.get(role) != text:
            nb[role] = text
            changed += 1
    for pid, field, was, new in PROFILE_EDITS:
        cur = comps[pid].get(field)
        if cur == new:
            print('  профиль %s %s %s' % (pid, field, U))
            continue
        if field == 'legal_short' and cur:
            print('  профиль %s %s уже стоит %r — не трогаем' % (pid, field, cur))
            continue
        assert cur == was, 'профиль %s %s: ожидали %r, стоит %r' % (pid, field, was, cur)
        comps[pid][field] = new
        print('  ПРАВИМ профиль %s %s' % (pid, field))
        changed += 1
    reg = open(REGISTRY_PY, encoding='utf-8').read()
    import fns_registry
    need_reg = NEW_ID not in fns_registry.by_company_id()
    print('  реестр ИНН: %s' % ('добавить ООО «Румелко»' if need_reg else U))
    if not write:
        print('Сухой прогон: правок %d. Запись — --write.' % changed)
        return 0
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK') or None)
    if changed:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    if need_reg:
        anchor = '\ndef by_company_id()'
        assert anchor in reg
        open(REGISTRY_PY, 'w', encoding='utf-8').write(reg.replace(anchor, REGISTRY_BLOCK + anchor, 1))
    drop_fixed_baseline(data)
    print('Записано правок: %d' % changed)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
