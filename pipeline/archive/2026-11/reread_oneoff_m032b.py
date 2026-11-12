# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m032 (марафон), вторая часть: правки, которые review.py и write_card.py не берут.

ЧТО ЧИНИТ (по статьям, сохраненным save_source.py):
  * gaa0ca672 (Softline / «МД Аудит»): заголовок по стандарту; дата 2024-06-26 — день публикации Ведомостей
    («в июне приобрела»), дня сделки нет ни в одном тексте — год; правовая форма предмета; где искали продавца.
  * g5a1ee21e (НЛМК / Cleveland-Cliffs): заголовок по стандарту («может купить» — слух); предмет назван (заводы в
    Индиане и Пенсильвании); сумма — «более $500 млн» по оценке источников, а не «$500 млн»; финансы дивизиона
    2021 года не нашлись ни в одном источнике — сняты; Primetals (награда заводу) — источник не про сделку.
  * g39218eec (Softline / «Визитек»): заголовок повторял заголовок Коммерсанта; описание профиля.
  * gd84abf3e («Био-Тон» / «Конезавод «Самарский»»): продавцы — по ЕГРЮЛ (АК&М): ООО «Большечерниговский
    комбикормовый завод» и Виктор Димитриев, а не группа «Василина»; дата 14 мая нигде не названа — год.
  * g56e609e3 (Metsä / ВЛП): отрасль «ГМК и добыча» → «Лесопром»; предмет назван; заголовок; правовая форма.
  * g073bf58b (BASF / «Лакра Синтез»): дата 2024-05-07 — день распоряжения Президента, а закрытие — по ЕГРЮЛ к
    1 июля 2024 года (Interfax), дня в источниках нет — год; цель «может стать выходом на рынок» — догадка
    редакции без автора — снята; заголовок по стандарту; правовая форма покупателя.

Поиск источников:
  gaa0ca672 — Ведомости (открытая часть), CNews (13.03.2025, раскрытие Softline), ComNews (пресс-релиз, добавлен);
              продавец «Кам» (Армения) — владельцы нигде не названы, армянский реестр недоступен.
  g5a1ee21e — Bloomberg (пейвол), GMK Center (пересказ, добавлен), Recycling Today (обрыв), Steel Market Update,
              поиск исхода переговоров 2025 года — новостей о закрытии или срыве нет.
  g39218eec — Коммерсантъ 6727734, CNews 13.03.2025 (добавлен); реестр — party_legal_names.py.
  gd84abf3e — АК&М, oboz.info, реестр ООО «Агрохолдинг «Василина» (Виктор Димитриев 100%).
  g56e609e3 — Коммерсантъ 6692044, vlp.eco; «1 млн га и лесосека 2,3 млн м3» ни в одном тексте не найдены.
  g073bf58b — Коммерсантъ 6688909, MRC, Interfax.com (добавлен).

ЗАПУСК: без ключа — сухой прогон; --write — запись (база перечитывается прямо перед записью,
assert на старое значение, повторный запуск — «уже применено»).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, ROOT)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
MISSING = object()
BY = 'reread m032 2026-11-12'

V7 = 'https://www.vedomosti.ru/technology/articles/2024/06/26/1046177-softline-hochet-rasshiritsya-za-schet-sdelok-ma'
G8 = 'https://gmk.center/news/cleveland-cliffs-vedet-peregovory-o-pokupke-amerikanskih-zavodov-nlmk-bloomberg/'
K9 = 'https://www.kommersant.ru/doc/6727734'
A10 = 'https://www.akm.ru/news/kompaniya_bio_ton_kupila_dva_selkhozpredpriyatiya_v_samarskoy_oblasti/'
O10 = 'https://oboz.info/nazvany-100-samyh-bogatyh-vladeltsev-agrobiznesa-v-samarskoj-oblasti/'
K11 = 'https://www.kommersant.ru/doc/6692044'
K12 = 'https://www.kommersant.ru/doc/6688909'
I12 = 'https://interfax.com/newsroom/top-stories/103868/'
PRIMETALS = ['Primetals Technologies', 'https://www.primetals.com/en/news/nlmk-indiana-receives-gold-reliability-achievement-award-for-eaf-upgrade-with-primetals-technologies/']

Q7 = '«Дочка» Softline SL Soft (разработчик бизнес-приложений) в июне приобрела контролирующую долю в «МД Аудит».'
Q8 = ('Активы НЛМК – металлургические мощности в Индиане и Пенсильвании – при возможной продаже могут быть оценены более '
      'чем в $500 млн.')
Q8b = ('Американский производитель стали Cleveland-Cliffs ведет переговоры о приобретении активов крупнейшего российского '
       'производителя стали ПАО «Новолипецкий металлургический комбинат» (НЛМК) в США.')
Q9 = 'SL Soft (принадлежит Softline) приобрела 100% разработчика технологий для охраны труда на производстве Visitech'
Q10 = ('Доли ООО «Серноводский элеватор» были выкуплены у ООО «Большечерниговский комбикормовый завод» (77.76%) и у двух '
       'физических лиц (21.43%).')
Q10b = 'В 2024 году «Био-Тон» приобрел два актива другого крупного агробизнесмена, бенефициара холдинга «Василина» Виктора Димитриева.'
Q11 = 'В периметр сделки вошли ООО «Мется Свирь» и ООО «Мется Форест Подпорожье»'
Q12 = ('Lakra Sintez LLC, one of Russia\'s largest producers of paints and varnishes, has become the sole owner of BASF '
       'Wostok')
Q12b = 'Президент РФ Владимир Путин разрешил производителю ЛКМ «Лакра Синтез» приобрести 100% ООО «БАСФ Восток»'

OPS = [
 # ---------------------------------------------------------------- gaa0ca672
 {'op': 'set', 'id': 'gaa0ca672', 'field': 'title', 'old': 'ГК Softline приобрела контроль в «МД Аудит»',
  'new': 'Softline купил контроль в «МД Аудит»', 'q': (Q7, V7)},
 {'op': 'set', 'id': 'gaa0ca672', 'field': 'date', 'old': '2024-06-26', 'new': '2024', 'q': (Q7, V7)},
 {'op': 'note', 'id': 'gaa0ca672', 'path': 'no_profile.seller',
  'new': 'Softline купил 75% армянского ООО «Кам», владельца «МД Аудит»; кто владел «Кам» и продал долю, не называют '
         'ни Ведомости, ни CNews (раскрытие Softline), ни пресс-релиз (ComNews); российский реестр показывает только '
         '«Кам», армянский реестр недоступен.'},
 {'op': 'company', 'cid': 'gb1cb0cd9', 'field': 'legal_short', 'old': MISSING, 'new': 'ООО «МД Аудит»'},
 # ---------------------------------------------------------------- g5a1ee21e
 {'op': 'set', 'id': 'g5a1ee21e', 'field': 'title', 'old': 'НЛМК продает американские заводы Cleveland-Cliffs',
  'new': 'Cleveland-Cliffs может купить американские заводы НЛМК', 'q': (Q8b, G8)},
 {'op': 'set', 'id': 'g5a1ee21e', 'field': 'asset', 'old': MISSING,
  'new': 'Заводы НЛМК в Индиане и Пенсильвании (NLMK USA)', 'q': (Q8, G8)},
 {'op': 'set', 'id': 'g5a1ee21e', 'field': 'sum', 'old': '$500 млн (по оценке)', 'new': 'Более $500 млн (по оценке)',
  'q': (Q8, G8)},
 {'op': 'set', 'id': 'g5a1ee21e', 'field': 'eco.sum', 'old': '$500 млн (по оценке)', 'new': 'Более $500 млн (по оценке)',
  'q': (Q8, G8)},
 {'op': 'set', 'id': 'g5a1ee21e', 'field': 'eco.target_fin',
  'old': 'В 2021 году выручка американского дивизиона составила $3,2 млрд, EBITDA — $1 млрд.', 'new': '—'},
 {'op': 'srcdrop', 'id': 'g5a1ee21e', 'new': PRIMETALS},
 {'op': 'company', 'cid': 'gaf725105', 'field': 'legal_short', 'old': MISSING, 'new': 'ПАО «НЛМК»'},
 # ---------------------------------------------------------------- g39218eec
 {'op': 'set', 'id': 'g39218eec', 'field': 'title', 'old': 'Softline купила разработчика ПО для охраны труда Visitech',
  'new': 'Softline купил ООО «Визитек»', 'q': (Q9, K9)},
 {'op': 'company', 'cid': 'gae065db1', 'field': 'desc',
  'old': 'Разработчик ПО для охраны труда (бренд Visitech); в 2024 году его 100% купил Softline за 62 млн ₽ и акции на '
         '100 млн ₽, эксперты оценили бизнес в 75–150 млн ₽.',
  'new': 'Разработчик ПО для охраны труда на промышленных предприятиях (бренд Visitech). В 2024 году его 100% купил '
         'Softline за 62 млн ₽ и акции на 100 млн ₽.'},
 # ---------------------------------------------------------------- gd84abf3e
 {'op': 'set', 'id': 'gd84abf3e', 'field': 'title',
  'old': 'Холдинг «Био-тон» приобрел сельскохозяйственные активы у Агрохолдинга «Василина»',
  'new': '«Био-Тон» купил конезавод «Самарский» и «Серноводский элеватор»', 'q': (Q10b, O10)},
 {'op': 'set', 'id': 'gd84abf3e', 'field': 'seller', 'old': 'Агрохолдинг «Василина»',
  'new': 'Виктор Димитриев и ООО «Большечерниговский комбикормовый завод»', 'q': (Q10 + ' … ' + Q10b, A10)},
 {'op': 'set', 'id': 'gd84abf3e', 'field': 'seller_id', 'old': 'g50b7bb62', 'new': MISSING},
 {'op': 'set', 'id': 'gd84abf3e', 'field': 'seller_src', 'old': 'title', 'new': 'text'},
 {'op': 'set', 'id': 'gd84abf3e', 'field': 'date', 'old': '2024-05-14', 'new': '2024', 'q': (Q10b, O10)},
 # ---------------------------------------------------------------- g56e609e3
 {'op': 'set', 'id': 'g56e609e3', 'field': 'title',
  'old': 'Metsä Group продала лесопромышленные активы в Ленинградской области группе «Вологодские лесопромышленники»',
  'new': 'ГК «Вологодские лесопромышленники» купила российские компании Metsä Group', 'q': (Q11, K11)},
 {'op': 'set', 'id': 'g56e609e3', 'field': 'asset', 'old': MISSING,
  'new': 'ООО «Мется Свирь» и ООО «Мется Форест Подпорожье»', 'q': (Q11, K11)},
 {'op': 'set', 'id': 'g56e609e3', 'field': 'ind', 'old': 'ГМК и добыча', 'new': 'Лесопром'},
 {'op': 'company', 'cid': 'ga0f5c079', 'field': 'legal_short', 'old': MISSING,
  'new': 'АО «ГК «Вологодские лесопромышленники»»'},
 # ---------------------------------------------------------------- g073bf58b
 {'op': 'set', 'id': 'g073bf58b', 'field': 'title',
  'old': 'BASF продал подмосковный завод лакокрасочных материалов компании «Лакра Синтез»',
  'new': '«Лакра Синтез» купила «БАСФ Восток» у BASF', 'q': (Q12b, K12)},
 {'op': 'set', 'id': 'g073bf58b', 'field': 'date', 'old': '2024-05-07', 'new': '2024', 'q': (Q12, I12)},
 {'op': 'set', 'id': 'g073bf58b', 'field': 'eco.rationale',
  'old': 'Для «Лакра Синтез» покупка «БАСФ Восток» может стать выходом на рынок лакокрасочных материалов для автопрома.',
  'new': '—'},
 {'op': 'company', 'cid': 'g34aa2579', 'field': 'legal_short', 'old': MISSING, 'new': 'ООО «Лакра Синтез»'},
]



def _walk(obj, parts):
    for p in parts:
        obj = obj.get(p, MISSING) if isinstance(obj, dict) else MISSING
    return obj


def _set(obj, field, value):
    parts = field.split('.')
    for p in parts[:-1]:
        obj = obj.setdefault(p, {})
    if value is MISSING:
        obj.pop(parts[-1], None)
    else:
        obj[parts[-1]] = value


def _apply(data, log):
    from fact_edit_guard import log as fact_log
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    for op in OPS:
        kind = op['op']
        if kind == 'company':
            prof = comps[op['cid']]
            cur = prof.get(op['field'], MISSING)
            if cur == op['new']:
                log.append('уже применено: профиль %s %s' % (op['cid'], op['field']))
                continue
            assert cur == op['old'] or (op['old'] is MISSING and cur is None), (op['cid'], op['field'], cur)
            prof[op['field']] = op['new']
            log.append('профиль %s %s' % (op['cid'], op['field']))
            continue
        card = deals[op['id']]
        if kind == 'set':
            cur = _walk(card, op['field'].split('.'))
            if cur == op['new'] or (op['new'] is MISSING and cur is MISSING):
                log.append('уже применено: %s %s' % (op['id'], op['field']))
                continue
            assert cur == op['old'], (op['id'], op['field'], cur)
            _set(card, op['field'], op['new'])
            if 'q' in op:
                fact_log(card, op['field'], None if op['new'] is MISSING else op['new'], op['q'][0], op['q'][1], BY)
            log.append('%s %s' % (op['id'], op['field']))
        elif kind == 'srcdrop':
            if op['new'] not in (card.get('src') or []):
                log.append('уже применено: %s src (снят)' % op['id'])
                continue
            card['src'].remove(op['new'])
            log.append('%s src: снят %s' % (op['id'], op['new'][0]))
        elif kind == 'retract':
            lst = card.setdefault('retracted', {}).setdefault(op['field'], [])
            for v in op['new']:
                if v not in lst:
                    lst.append(v)
            log.append('%s retracted.%s' % (op['id'], op['field']))
        elif kind == 'note':
            notes = card.setdefault('accepted_notes', {})
            cur = _walk(notes, op['path'].split('.'))
            if cur == op['new']:
                log.append('уже применено: %s accepted_notes.%s' % (op['id'], op['path']))
                continue
            assert cur is MISSING, (op['id'], op['path'], cur)
            _set(notes, op['path'], op['new'])
            log.append('%s accepted_notes.%s' % (op['id'], op['path']))
        else:
            raise AssertionError(kind)


def main(write=False):
    from pipeline import mass_edit_guard
    log = []
    data = json.load(open(DATA, encoding='utf-8'))
    _apply(data, log)
    print('\n'.join(log))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    fresh = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
    _apply(fresh, [])
    mass_edit_guard.check(json.load(open(DATA, encoding='utf-8')), fresh, os.environ.get('MASS_OK'))
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
