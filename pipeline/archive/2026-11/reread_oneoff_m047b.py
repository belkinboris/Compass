# -*- coding: utf-8 -*-
"""Вычитка базы, марафон 12 ноября 2026, партия m047 (вторая часть): правки вне FIXES.

ЧТО ЧИНИТ И ПОЧЕМУ (цитаты — в OPS; статьи сохранены save_source.py в
data/inbox/triage/sources_2026-11-12_m047.json, история участников ООО — datanewton):
  g91c0cb1e («Лента»/«Монетка») — продавец не был назван: по ЕГРЮЛ до сделки
      99,9999% ООО «РМ-Групп» держало ООО УК «РМ-Консалт» (запись 03.10.2023 —
      доля перешла, сведения о новом участнике закрыты). В extra снято
      утверждение о покупке «О'Кей» и других сетей — его нет в источниках.
  g09446477 («АБ Холдинг»/«Мозен») — продавец не был назван: по ЕГРЮЛ 04.10.2023
      номинал доли Олега Семибратова упал с 10 000 до 6 800,4 ₽ при неизменном
      капитале — он и продал 32% «АБ Холдингу».
  g0f7d3941 (Zielinski & Rozen/«Эксперт недвижимость») — в сумме стояла оценка
      консультанта CORE.XP (400–450 млн ₽), а не цена сделки: цена не раскрыта,
      оценка остается в «Оценке и дисконте».
  ga13c3ea7 (ЗТК «Тамань») — покупателем стоял Илья Косых, а долю, по словам
      гендиректора, купила ООО «Доставка морем» (Коммерсантъ): заведен профиль
      «Доставка морем». Дата «2023-10-01» — выдуманный день: Viterra продала
      долю в октябре 2023 года, дня нет ни в одном источнике — дата годом.

ПОЧЕМУ НЕ review.py: стороны по реестру, новый профиль, год даты, сумма
«Не раскрыта» и вырезка из прозы через таблицу правок не проходят.

Запуск: python3 pipeline/archive/2026-11/reread_oneoff_m047b.py [--write]
База перечитывается прямо перед записью; повторный запуск — «уже применено».
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'reread m047 (12.11.2026)'
FACT_FIELDS = {'eco.sum', 'eco.finadv', 'date_basis', 'sum_basis', 'date', 'seller', 'buyer', 'target', 'title', 'sum', 'seller_id', 'buyer_name', 'asset'}

# (вид, id, путь поля, старое, новое, цитата, адрес). Путь — через точку.
# Вид 'deal' — поле карточки, 'co' — поле профиля компании,
# 'mk' — псевдонимы профиля в match_keys (путь — id профиля),
# 'cut' — вырезать подстроку из поля карточки (старое — вырезаемый текст, новое — замена).
OPS = [
 # ------------------------------------------------------------ g91c0cb1e
 ('deal', 'g91c0cb1e', 'seller', None, 'ООО УК «РМ-Консалт»',
  'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ УПРАВЛЯЮЩАЯ КОМПАНИЯ "РМ-КОНСАЛТ" (ОГРН: 1096674002919) 99.9999%; (499 999,5 руб.) => Доступ к сведениям ограничен (запись ЕГРЮЛ ООО «РМ-Групп» от 03.10.2023)',
  'https://datanewton.ru/contragents/1069674070300/history/timeline'),
 ('deal', 'g91c0cb1e', 'party_evidence', None,
  {'seller': [{'value': 'ООО УК «РМ-Консалт»', 'method': 'registry_owner_history',
               'url': 'https://datanewton.ru/contragents/1069674070300/history/timeline'}]}, None, None),
 ('deal', 'g91c0cb1e', 'accepted_notes', None,
  {'no_profile': {'seller': 'ООО УК «РМ-Консалт» — участник ООО «РМ-Групп» (99,9999%) до записи ЕГРЮЛ 03.10.2023 (datanewton, история участников); в статьях о сделке продавец не назван, профиля у компании нет.'}},
  None, None),
 ('append', 'g91c0cb1e', 'src', None,
  ['ЕГРЮЛ: история участников ООО «РМ-Групп»', 'https://datanewton.ru/contragents/1069674070300/history/timeline'], None, None),
 ('cut', 'g91c0cb1e', 'extra', " Дальше по той же стратегии она купила «О'Кей», OBI Россия, ГК «Реми», «Молнию» и «Улыбку радуги».", '', None, None),
 # ------------------------------------------------------------ g09446477
 ('deal', 'g09446477', 'seller', None, 'Олег Семибратов',
  'СЕМИБРАТОВ ОЛЕГ МАЛИКОВИЧ 100.0% (10 000 руб.) → 68.004% (6 800,4 руб.); АКЦИОНЕРНОЕ ОБЩЕСТВО "АБ ХОЛДИНГ" вошел с 31.996% (3 199,6 руб.) (ЕГРЮЛ ООО «Мозен», запись 04.10.2023)',
  'https://datanewton.ru/contragents/1197847252580/history/timeline'),
 ('deal', 'g09446477', 'party_evidence', None,
  {'seller': [{'value': 'Олег Семибратов', 'method': 'registry_owner_history',
               'url': 'https://datanewton.ru/contragents/1197847252580/history/timeline'}]}, None, None),
 ('deal', 'g09446477', 'accepted_notes', None,
  {'no_profile': {'seller': 'физлицо, профиля нет; по ЕГРЮЛ (04.10.2023) доля Олега Семибратова уменьшилась со 100% до 68,004% при неизменном капитале — продал ее «АБ Холдингу»'}},
  None, None),
 ('append', 'g09446477', 'src', None,
  ['ЕГРЮЛ: история участников ООО «Мозен»', 'https://datanewton.ru/contragents/1197847252580/history/timeline'], None, None),
 # ------------------------------------------------------------ g0f7d3941
 ('deal', 'g0f7d3941', 'sum', '400–450 млн ₽ (по оценке)', 'Не раскрыта',
  'В «Галс» подтвердили факт сделки. … Старший директор CORE.XP Марина Малахатько считает, что сумма сделки могла составить 400–450 млн руб.',
  'https://www.kommersant.ru/doc/6252746'),
 ('deal', 'g0f7d3941', 'eco.sum', '400–450 млн ₽ (по оценке)', 'Не раскрыта',
  'Старший директор CORE.XP Марина Малахатько считает, что сумма сделки могла составить 400–450 млн руб.',
  'https://www.kommersant.ru/doc/6252746'),
 # ------------------------------------------------------------ ga13c3ea7
 ('newco', 'gdc5e0472', None, None,
  {'name': 'Доставка морем', 'legal_short': 'ООО «Доставка морем»', 'ind': 'Агро',
   'desc': 'Экспортер зерна; владелец — Илья Косых, гендиректор — Наталья Тугалева. В 2023 году купила 50% зернового терминала «Тамань».',
   'kpi': ['Профиль', 'Автоматический']}, None, None),
 ('mk', 'match_keys', 'gdc5e0472', None, ['доставка морем'], None, None),
 ('deal', 'ga13c3ea7', 'buyer', 'gfc56f0a6', 'gdc5e0472',
  'Наталья Тугалева подтвердила “Ъ”, что «Доставка морем» приобрела долю в ЗТКТ на рыночных условиях.',
  'https://www.kommersant.ru/doc/6612078'),
 ('deal', 'ga13c3ea7', 'date', '2023-10-01', '2023',
  'In October 2023, Viterra sold all of its Russian businesses for an aggregate consideration of $82 million',
  'https://www.sec.gov/Archives/edgar/data/1996862/000110465924097990/tm2419986d1_ex99-1.htm'),
 ('deal', 'ga13c3ea7', 'title', 'Viterra продала 50% Зернового терминального комплекса «Тамань» компании «Доставка морем»',
  '«Доставка морем» купила 50% зернового терминала «Тамань» у Viterra',
  'Наталья Тугалева подтвердила “Ъ”, что «Доставка морем» приобрела долю в ЗТКТ на рыночных условиях.',
  'https://www.kommersant.ru/doc/6612078'),
 ('cut', 'ga13c3ea7', 'extra', 'По отчетности терминала, сам Косых стал', 'По отчетности терминала, Илья Косых стал', None, None),
 ('co', 'gfc56f0a6', 'desc',
  'Собственник экспортера зерна «Доставка морем»; в 2023 году купил у Viterra 50% Зернового терминального комплекса «Тамань».',
  'Собственник экспортера зерна «Доставка морем»; по отчетности ЗТК «Тамань», с 2023 года косвенно владеет более чем 25% терминала.',
  None, None),
 ('co', 'g620a3108', 'desc',
  'Зерновой терминал на Кубани, совместное владение с ООО «Деметра-холдинг» (по 50%); в 2023 году долю Viterra купил Илья Косых, собственник экспортера зерна «Доставка морем».',
  'Зерновой терминал на Кубани; по 50% у ООО «Деметра-холдинг» и ООО «Доставка морем», купившей в 2023 году долю Viterra.',
  None, None),
]


def get(obj, path):
    if isinstance(obj, dict) and path in obj:
        return obj[path]
    for p in path.split('.'):
        obj = (obj or {}).get(p)
    return obj


def put(obj, path, value):
    if path.startswith('g') and '.' not in path:
        obj[path] = value
        return
    parts = path.split('.')
    for p in parts[:-1]:
        obj = obj.setdefault(p, {})
    obj[parts[-1]] = value


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
    deals = {d['id']: d for d in data['deals']}
    cos = data['companies']
    cos = cos if isinstance(cos, dict) else {c['id']: c for c in cos}
    changed = 0
    for kind, cid, path, old, new, quote, url in OPS:
        if kind == 'newco':
            if cid in cos:
                assert cos[cid].get('name') == new['name'], 'id %s занят другой компанией' % cid
                print('уже применено: профиль %s' % cid)
                continue
            assert not any(c.get('name') == new['name'] for c in cos.values()), 'профиль %r уже есть' % new['name']
            print('новый профиль %s %r' % (cid, new['name']))
            changed += 1
            if write:
                cos[cid] = dict(new)
            continue
        obj = cos.get(cid) if kind == 'co' else data['match_keys'] if kind == 'mk' else deals.get(cid)
        assert obj is not None, 'нет %s %s' % (kind, cid)
        if kind == 'append':
            cur = obj.get(path) or []
            if new in cur:
                print('уже применено: %s %s (добавление)' % (cid, path))
                continue
            print('%s %s: + %r' % (cid, path, new))
            changed += 1
            if write:
                obj[path] = cur + [new]
            continue
        cur = get(obj, path)
        if kind == 'cut':
            if old not in (cur or ''):
                assert new == '' or new in cur, '%s %s: нет ни старого, ни нового текста' % (cid, path)
                print('уже применено: %s %s (вырезка)' % (cid, path))
                continue
            assert (cur or '').count(old) == 1, '%s %s: вырезаемый текст не один' % (cid, path)
            value = cur.replace(old, new)
        else:
            if cur == new:
                print('уже применено: %s %s' % (cid, path))
                continue
            assert cur == old, '%s %s: в базе %r, ожидали %r' % (cid, path, cur, old)
            value = new
        print('%s %s: %r → %r' % (cid, path, str(cur)[:70], str(value)[:70]))
        changed += 1
        if write:
            put(obj, path, value)
            if kind == 'deal' and path in FACT_FIELDS and quote:
                fact_edit_guard.log(obj, path, value, quote, url, BY)
    if not write:
        print('Сухой прогон: %d правок. Запись — --write.' % changed)
        return
    if changed:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано: %d.' % changed)


if __name__ == '__main__':
    main('--write' in sys.argv)
