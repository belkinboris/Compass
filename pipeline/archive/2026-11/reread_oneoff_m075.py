# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m075: разовая часть — стороны, даты, суммы, предмет, заметки, профили.

То, что не ложится в таблицу FIXES (ссылка на профиль, снятие суммы, год вместо дня, заметки приемки, описание
профиля). Каждая правка факта несет цитату источника (fact_edit_guard.log). Подробности и поиск — в докстроке
pipeline/ingest/fixes/reread_2026_11_12_m075.py.

    python3 pipeline/archive/2026-11/reread_oneoff_m075.py            # сухой прогон
    python3 pipeline/archive/2026-11/reread_oneoff_m075.py --write    # запись (базу перечитывает перед записью)

Повторный запуск ничего не ломает: уже примененное пропускается, перед правкой — assert на старое значение.
"""
import copy
import json
import os
import sys

BY = 'reread m075'
ONE_OFF = [('c2c719a9a',
  'target',
  None,
  'gc024b8c5',
  'Производитель оптической техники ЛОМО перешел под управление АО «Калашников». Соответствующие изменения были '
  'внесены в ЕГРЮЛ 14 мая.',
  'https://www.kommersant.ru/doc/6692847'),
 ('cbb730efc',
  'asset',
  None,
  '100% ООО «Ульяновский станкостроительный завод»',
  'Росимущество получило во временное управление 100% долей ООО "Ульяновский станкостроительный завод" (УСЗ), '
  'принадлежащих германской Gildemeister Beteiligungen GmbH.',
  'https://www.interfax.ru/business/946827'),
 ('cbfe737bd',
  'buyer',
  None,
  'g1d050dad',
  'До конца июня 2026 года в Сочи возобновится полноценная работа гостиничного комплекса «Имеретинский», который был '
  'закрыт с 2023 года после изъятия в интересах государства. Предыдущему владельцу — ООО «РогСибАл», которое '
  'связывают с миллиардером Олегом Дерипаской,— удалось вернуть актив. … Сторонам удалось договориться: по условиям '
  'соглашения, «Сириус» обязался вернуть компании семь корпусов прибрежного квартала и парковки, а «РогСибАл» '
  'предоставил федеральной территории имущественное право выкупа этих активов в приоритетном порядке, если они будут '
  'проданы, приводит данные из судебных документов начальник аналитического отдела «Риком-Траст» Олег Абелев.',
  'https://www.kommersant.ru/doc/8590858?tg'),
 ('cbfe737bd',
  'seller',
  None,
  'Федеральная территория «Сириус»',
  'Сторонам удалось договориться: по условиям соглашения, «Сириус» обязался вернуть компании семь корпусов '
  'прибрежного квартала и парковки, а «РогСибАл» предоставил федеральной территории имущественное право выкупа этих '
  'активов в приоритетном порядке, если они будут проданы, приводит данные из судебных документов начальник '
  'аналитического отдела «Риком-Траст» Олег Абелев.',
  'https://www.kommersant.ru/doc/8590858?tg'),
 ('cbfe737bd',
  'sum',
  '15–20 млрд ₽ (по оценке)',
  'Не раскрыта',
  'Стоимость этого имущества партнер NF Group Марина Малахатько оценивает в 16 млрд руб. Руководитель направления '
  'стратегического консалтинга Nikoliers Олег Германенко говорит о сумме в 15–20 млрд руб.',
  'https://www.kommersant.ru/doc/8590858?tg'),
 ('cbfe737bd',
  'eco.sum',
  '15–20 млрд ₽ (по оценке)',
  'Не раскрыта',
  'Стоимость этого имущества партнер NF Group Марина Малахатько оценивает в 16 млрд руб. Руководитель направления '
  'стратегического консалтинга Nikoliers Олег Германенко говорит о сумме в 15–20 млрд руб.',
  'https://www.kommersant.ru/doc/8590858?tg'),
 ('cbfe737bd',
  'date',
  '2026-04-17',
  '2024',
  'В июле 2024 года дело развернулось в пользу «РогСибАл». Тогда Хамовнический районный суд столицы восстановил '
  'права собственности на ряд объектов в комплексе «Имеретинский» суммарной площадью 54,6 тыс. кв. м со сроком '
  'передачи недвижимости в январе 2025 года, говорится в материалах дела.',
  'https://www.kommersant.ru/doc/8590858?tg')]
SET = []
RETRACT = [('cbfe737bd', 'sum', '15–20 млрд ₽ (по оценке)')]
NOTES = [('c90380a10',
  'searched',
  'покупатель назван только по неофициальным данным, брокер не назван: Ъ 16.08.2024 (первоисточник), '
  'finance.mail.ru, spmag.ru, investfuture.ru, investfunds.ru — все пересказывают Ъ; поиск по сайту и раскрытию '
  'Мосбиржи и новостям 2025–2026 годов о покупке брокера ничего не дал (вычитка 12.11.2026, m075)'),
 ('c90380a10',
  'no_profile.asset',
  'брокерская компания не названа ни в одном источнике: Ъ пишет лишь о «бутиковом брокере», который отказался от '
  'продажи (вычитка 12.11.2026, m075)'),
 ('cbfe737bd',
  'searched',
  'Ъ 17.04.2026 (8590858 и региональная 8591162), finance.mail.ru (пересказ Ъ), РБК 2023 (передача «Сириусу»), '
  'pravo.ru; дата мирового соглашения и сам текст в открытых источниках не найдены (вычитка 12.11.2026, m075)'),
 ('cbfe737bd',
  'no_inn.buyer',
  'ИНН ООО «РогСибАл» не найден: datanewton не ответил, в поиске — только платные карточки (вычитка 12.11.2026, '
  'm075)')]
COMPANY = [('g1d050dad',
  'desc',
  'Описание компании пока не добавлено.',
  'Владелец гостиничного комплекса «Имеретинский» в Сочи; учредитель — ООО «Имеретинская Ривьера».')]


def _get(obj, field):
    for p in field.split('.'):
        obj = obj.get(p) if isinstance(obj, dict) else None
    return obj


def _set(obj, field, value):
    parts = field.split('.')
    for p in parts[:-1]:
        obj = obj.setdefault(p, {})
    obj[parts[-1]] = value


def apply(data):
    import fact_edit_guard
    deals = {d['id']: d for d in data['deals']}
    for cid, field, old, new, quote, url in ONE_OFF:
        card = deals[cid]
        if _get(card, field) == new:
            continue
        assert _get(card, field) == old, (cid, field, _get(card, field))
        _set(card, field, new)
        fact_edit_guard.log(card, field, new, quote, url, BY)
    for cid, field, old, new in SET:
        if _get(deals[cid], field) == new:
            continue
        assert _get(deals[cid], field) == old, (cid, field, _get(deals[cid], field))
        _set(deals[cid], field, new)
    for cid, field, value in RETRACT:
        lst = deals[cid].setdefault('retracted', {}).setdefault(field, [])
        if value not in lst:
            lst.append(value)
    for cid, path, value in NOTES:
        notes = deals[cid].setdefault('accepted_notes', {})
        if _get(notes, path) == value:
            continue
        assert _get(notes, path) is None, (cid, path, _get(notes, path))
        _set(notes, path, value)
    for comp, field, old, new in COMPANY:
        c = data['companies'][comp]
        if c.get(field) == new:
            continue
        assert c.get(field) == old, (comp, field, c.get(field))
        c[field] = new


if __name__ == '__main__':
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    sys.path.insert(0, os.path.join(root, 'pipeline'))
    sys.path.insert(0, os.path.join(root, 'pipeline', 'ingest'))
    import mass_edit_guard  # noqa: E402
    path = os.path.join(root, 'static', 'data', 'deals_promoted.json')
    data = json.load(open(path, encoding='utf-8'))
    before = copy.deepcopy(data)
    apply(data)
    mass_edit_guard.check(before, data, os.environ.get('MASS_OK'))
    print('Разовая часть m075: полей %d, снятых %d, заметок %d, профилей %d — проверки пройдены.'
          % (len(ONE_OFF), len(RETRACT), len(NOTES), len(COMPANY)))
    if '--write' in sys.argv:
        fresh = json.load(open(path, encoding='utf-8'))
        before = copy.deepcopy(fresh)
        apply(fresh)
        mass_edit_guard.check(before, fresh, os.environ.get('MASS_OK'))
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(fresh, fh, ensure_ascii=False, indent=1)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')
