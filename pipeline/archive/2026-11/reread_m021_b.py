# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m021, вторая часть: правки, которые review.py не берет.

ЧТО ЧИНИТ.
  * g433cfd40 («Ригла» / «Столичные аптеки»): снятый продавец Doreno Limited — в retracted (он из сделки 2024 года
    с долей Huduma Limited), где искали продавца — в accepted_notes; правовая форма покупателя (ООО «Ригла»).
  * gc3cb0d4d («Лента» / «Реми»): из «Как устроена сделка» снята смена гендиректора (Отпущенников) — ее нет ни в
    одном открытом тексте; в описании профиля «Реми» 116 магазинов → 115 (периметр сделки по Интерфаксу, New
    Retail, РИА); правовая форма предмета (ООО «Продукт-Эконом», ЕГРЮЛ).
  * gc3cb0d4d: предмет — долей в обществе по реестру (находка share_form).
  * g2534df99 («Верный»): сумма — оценки BGP Capital (с долгом) и Infoline, не цена → «Не раскрыта»; правовая форма
    предмета (ООО «Союз св. Иоанна Воина», ЕГРЮЛ); где искали покупателя.
  * g031152d0: правовая форма покупателя (АО «Росхим», ЕГРЮЛ).

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
BY = 'reread m021 2026-11-12'

OPS = [
 {'op': 'retract', 'id': 'g433cfd40', 'field': 'seller', 'new': ['Doreno Limited']},
 {'op': 'note', 'id': 'g433cfd40', 'path': 'no_profile.seller',
  'new': '«Ригла» стала арендатором помещений 62 аптек «Столичных аптек»; кто передал ей аптеки (АО «Столичные '
         'аптеки» или собственники помещений) и на каких условиях, Ъ 8270153 и Фармвестник не пишут; реестр АО «Столичные '
         'аптеки» акционеров не показывает. Doreno Limited — '
         'продавец 50% Huduma Limited в 2024 году, к этой сделке не относится.'},
 {'op': 'company', 'cid': 'g7313d9af', 'field': 'legal_short', 'old': MISSING, 'new': 'ООО «Ригла»'},
 {'op': 'replace', 'id': 'gc3cb0d4d', 'field': 'law.struct',
  'old': ' По данным СПАРК-Интерфакса, после закрытия сделки гендиректором «Продукт-Эконом» вместо Софьи Мишиной '
         'стал Игорь Отпущенников; дату назначения открытые источники не называют.',
  'new': ''},
 {'op': 'company', 'cid': 'gc91d0776', 'field': 'desc',
  'old': 'Продуктовый ритейлер на Дальнем Востоке (116 магазинов под брендами Реми, Ремисити и Экономыч); в 2025 году '
         'контрольную долю (67%) купила «Лента».',
  'new': 'Продуктовый ритейлер на Дальнем Востоке (115 магазинов под брендами «Реми», «РемиСити» и «Экономыч»); в '
         '2025 году контрольную долю (67%) купила «Лента».'},
 {'op': 'company', 'cid': 'gc91d0776', 'field': 'legal_short', 'old': MISSING, 'new': 'ООО «Продукт-Эконом»'},
 {'op': 'set', 'id': 'gc3cb0d4d', 'field': 'eco.share',
  'old': '67% долей сети «Реми» — 115 магазинов (87 в Приморье, 24 в Хабаровском крае, 4 в Сахалинской области) и логистика сети.',
  'new': '67% доли в ООО «Продукт-Эконом» (сеть «Реми»): 115 магазинов — 87 в Приморье, 24 в Хабаровском крае, 4 в '
         'Сахалинской области — и логистика сети.',
  'q': ('ЕГРЮЛ, ООО «Продукт-Эконом» (ИНН 2543111589): 2025-12-10 left: Сулеев Дмитрий Петрович (67.0 → None); '
        '2025-12-10 joined: ООО "ЛЕНТА" (None → 67.0) … к «Группе Лента» перешли 67% долей торговой сети «Реми». '
        'В периметр сделки войдут 115 торговых точек, включая 87 магазинов в Приморском крае, 24 магазина в Хабаровском крае',
        'https://projectcompass.ru/api/companies/gc91d0776/fns')},
 {'op': 'set', 'id': 'g2534df99', 'field': 'sum', 'old': '25–35 млрд ₽ (по оценке)', 'new': 'Не раскрыта',
  'q': ('Руководитель департамента M&A BGP Capital Иван Пешков оценивает бизнес «Верного» в 30–35 млрд руб. с учетом '
        'долга. … Оценка Infoline — 25 млрд руб.', 'https://www.kommersant.ru/doc/8158706')},
 {'op': 'set', 'id': 'g2534df99', 'field': 'eco.sum', 'old': '25–35 млрд ₽ (по оценке)', 'new': 'Не раскрыта',
  'q': ('Руководитель департамента M&A BGP Capital Иван Пешков оценивает бизнес «Верного» в 30–35 млрд руб. с учетом '
        'долга. … Оценка Infoline — 25 млрд руб.', 'https://www.kommersant.ru/doc/8158706')},
 {'op': 'retract', 'id': 'g2534df99', 'field': 'sum', 'new': ['25–35 млрд ₽ (по оценке)']},
 {'op': 'company', 'cid': 'gd853e266', 'field': 'legal_short', 'old': MISSING, 'new': 'ООО «Союз св. Иоанна Воина»'},
 {'op': 'note', 'id': 'g2534df99', 'path': 'no_profile.buyer',
  'new': 'Покупатель не определен: Ъ 8158706 и 8158724 называют претендентами крупнейшие сети («Лента» — по мнению '
         'Ивана Пешкова), Эксперт и Shopper\'s — пересказ; реестр ООО «Союз св. Иоанна Воина» — 100% у Эдпал Лимитед, '
         'перехода доли нет.'},
 {'op': 'company', 'cid': 'g936f9597', 'field': 'legal_short', 'old': MISSING, 'new': 'АО «Росхим»'},
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
        if kind == 'registry':
            continue
        if kind == 'company':
            prof = comps[op['cid']]
            cur = prof.get(op['field'], MISSING)
            if cur == op['new']:
                log.append('уже применено: профиль %s %s' % (op['cid'], op['field']))
                continue
            assert cur == op['old'], (op['cid'], op['field'], cur)
            prof[op['field']] = op['new']
            log.append('профиль %s %s' % (op['cid'], op['field']))
            continue
        card = deals[op['id']]
        if kind == 'set':
            cur = _walk(card, op['field'].split('.'))
            if cur == op['new']:
                log.append('уже применено: %s %s' % (op['id'], op['field']))
                continue
            assert cur == op['old'], (op['id'], op['field'], cur)
            _set(card, op['field'], op['new'])
            if 'q' in op:
                fact_log(card, op['field'], op['new'], op['q'][0], op['q'][1], BY)
            log.append('%s %s' % (op['id'], op['field']))
        elif kind == 'replace':
            cur = _walk(card, op['field'].split('.'))
            if op['old'] not in cur and (not op['new'] or op['new'] in cur):
                log.append('уже применено: %s %s (фраза)' % (op['id'], op['field']))
                continue
            assert cur.count(op['old']) == 1, (op['id'], op['field'])
            _set(card, op['field'], cur.replace(op['old'], op['new']))
            log.append('%s %s (фраза)' % (op['id'], op['field']))
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


def _registry(write, log):
    import fns_registry
    from fns_notes_to_registry import edit_registry_entry
    for op in OPS:
        if op['op'] != 'registry':
            continue
        cur = fns_registry.by_company_id().get(op['cid']) or {}  # noqa
        if cur.get('inn') == op['new']['inn']:
            log.append('уже применено: реестр %s' % op['cid'])
            continue
        assert cur.get('inn') == op['old_inn'], (op['cid'], cur)
        if write:
            assert edit_registry_entry(op['cid'], op['new'])
        log.append('реестр %s: ИНН %s → %s' % (op['cid'], op['old_inn'], op['new']['inn']))


def main(write=False):
    from pipeline import mass_edit_guard
    log = []
    data = json.load(open(DATA, encoding='utf-8'))
    _apply(data, log)
    _registry(False, log)
    print('\n'.join(log))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    fresh = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
    _apply(fresh, [])
    mass_edit_guard.check(json.load(open(DATA, encoding='utf-8')), fresh, os.environ.get('MASS_OK'))
    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    _registry(True, [])
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
