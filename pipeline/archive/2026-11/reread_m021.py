# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m021: правки, которые review.py не берет.

ЧТО ЧИНИТ.
  * Сумма-оценка аналитика вместо цены сделки (ga971155a «Гулливер», gcdec4f24 «Адамас», g9d9e7ab6
    «Группа Астра») → «Не раскрыта»; число остается в «Оценке» (eco.val), где назван оценщик, а у
    «Астры» оно без автора и не нашлось ни в одном открытом тексте. review.py «Не раскрыта» не принимает.
  * gcdec4f24: дата — день перехода доли по ЕГРЮЛ (26 января 2026: из ООО «АДАМАС АЙПИ» вышли
    АО «Форум Капитал» 99% и Илья Сильченко 1%, вошла ЭСЭЛЭЙЧ ГРУП ЛИМИТЕД 100%), а не день статьи;
    предмет (eco.share) — по реестру и Ъ; фраза с разговорным «сам» в контексте.
  * ga971155a: профиль сети «Гулливер» (g23deb0cc) был сопоставлен с ООО «ТК Лето» (ИНН 7327067461) —
    это оператор дискаунтеров «Победа», не «Гулливера» («Коммерсантъ» 22.01.2026: «Операционное юрлицо
    сети — АО «Гулливер»… Операционная компания этой сети [«Победа»] — ООО «ТК Лето»»). Решение реестра
    переписано на АО «Гулливер», ИНН 7326029150 (ОГРН 1077326001620: companies.rbc.ru и декларации
    пожарной безопасности МЧС, где собственник магазинов — АО «ГУЛЛИВЕР»), описание профиля исправлено.

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

KG = 'https://www.kommersant.ru/doc/8364093?from=top_main_4'
KA2 = 'https://www.kommersant.ru/doc/8380020'
FNS_ADAMAS = 'https://projectcompass.ru/api/companies/adamas/fns'
Q_ADAMAS_REG = ('ЕГРЮЛ, ООО «АДАМАС АЙПИ» (ИНН 9705156130): 2026-01-26 left: АО "ФОРУМ КАПИТАЛ" (99.0 → None); '
                '2026-01-26 left: Сильченко Илья Валерьевич (1.0 → None); 2026-01-26 joined: ЭСЭЛЭЙЧ ГРУП ЛИМИТЕД (None → 100.0)')
Q_ADAMAS_PERIM = ('По его словам, в периметр сделки вошли все дочерние структуры и товарные знаки холдинга, включая '
                  'розничные магазины и ООО «Белгородский ювелирный завод "Арт-Карат"».')
Q_GUL_EST = ('Гендиректор «Infoline-аналитики» Михаил Бурмистров предполагает, что запрашиваемая стоимость сети может '
             'составлять 4–5 млрд руб. Но рыночная оценка будет не выше 3–3,5 млрд руб., считает он.')
Q_AD_EST = 'Проведение сделки, стоимость которой оценивается максимум в 6,5 млрд руб.'
Q_ASTRA = 'Параметры еще обсуждаются.'
RBC_ASTRA = 'https://pro.rbc.ru/demo/696b9bad9a794713f85d7afd'

OPS = [
 # ---------------------------------------------------------------- ga971155a «Гулливер»
 {'op': 'set', 'id': 'ga971155a', 'field': 'sum', 'old': '3–3,5 млрд ₽ (по оценке)', 'new': 'Не раскрыта', 'q': (Q_GUL_EST, KG)},
 {'op': 'set', 'id': 'ga971155a', 'field': 'eco.sum', 'old': '3–3,5 млрд ₽ (по оценке)', 'new': 'Не раскрыта', 'q': (Q_GUL_EST, KG)},
 {'op': 'retract', 'id': 'ga971155a', 'field': 'sum', 'new': ['3–3,5 млрд ₽ (по оценке)']},
 {'op': 'note', 'id': 'ga971155a', 'path': 'no_profile.seller',
  'new': 'Ъ 22.01.2026: «Собственники компании не раскрываются» (ранее владельцами считались Игорь Старостин, '
         'Александр Сикачина, Игорь Любченков и их семьи); АО «Гулливер» — акционерное общество, акционеры в ЕГРЮЛ '
         'не видны; retail.ru (5 марта 2026) продавца не называет. Продавец не заводится.'},
 {'op': 'note', 'id': 'ga971155a', 'path': 'no_profile.buyer',
  'new': 'Покупатель не определен: «Магнит» отказался, X5 переговоров не ведет, «Лента» изучает актив (retail.ru, 5 марта '
         '2026); сообщений о сделке после этого в Ъ, retail.ru, sostav.ru, new-retail.ru, akm.ru не нашлось.'},
 {'op': 'company', 'cid': 'g23deb0cc', 'field': 'desc',
  'old': 'Розничная сеть из около 100 супермаркетов в Ульяновской области и Приволжье (операционная компания ООО «ТК ЛЕТО», '
         'выручка 114 млрд ₽ в 2024 году); в 2026 году выставлена на продажу за 3–3,5 млрд ₽ (по оценке).',
  'new': 'Ульяновская сеть продуктовых магазинов: 100 магазинов в Ульяновской и Саратовской областях. Операционное '
         'юрлицо — АО «Гулливер». В 2026 году собственники выставили сеть на продажу.'},
 {'op': 'company', 'cid': 'g23deb0cc', 'field': 'legal_short', 'old': MISSING, 'new': 'АО «Гулливер»'},
 {'op': 'registry', 'cid': 'g23deb0cc', 'old_inn': '7327067461', 'new': {
     'company_id': 'g23deb0cc', 'decision': 'confirmed', 'inn': '7326029150',
     'reason': 'АО «Гулливер», ИНН 7326029150, ОГРН 1077326001620, Ульяновск — операционное юрлицо сети («Коммерсантъ» '
               '22.01.2026: «Операционное юрлицо сети — АО «Гулливер»»); реквизиты совпадают в companies.rbc.ru и в '
               'декларациях пожарной безопасности МЧС (собственник магазинов — АО «ГУЛЛИВЕР»). Прежнее решение '
               '(ООО «ТК Лето», ИНН 7327067461) ошибочно: это оператор дискаунтеров «Победа» той же группы, его '
               'выбрали по неверному описанию профиля. Вычитка 12 ноября 2026 (партия m021).',
     'date': '2026-11-12'}},
 # ---------------------------------------------------------------- gcdec4f24 «Адамас»
 {'op': 'set', 'id': 'gcdec4f24', 'field': 'sum', 'old': '6,5 млрд ₽ (по оценке)', 'new': 'Не раскрыта', 'q': (Q_AD_EST, KA2)},
 {'op': 'set', 'id': 'gcdec4f24', 'field': 'eco.sum', 'old': '6,5 млрд ₽ (по оценке)', 'new': 'Не раскрыта', 'q': (Q_AD_EST, KA2)},
 {'op': 'retract', 'id': 'gcdec4f24', 'field': 'sum', 'new': ['6,5 млрд ₽ (по оценке)']},
 {'op': 'set', 'id': 'gcdec4f24', 'field': 'date', 'old': '2026-01-28', 'new': '2026-01-26', 'q': (Q_ADAMAS_REG, FNS_ADAMAS)},
 {'op': 'set', 'id': 'gcdec4f24', 'field': 'date_basis', 'old': MISSING, 'new': 'registry'},
 {'op': 'set', 'id': 'gcdec4f24', 'field': 'eco.share',
  'old': 'В периметр сделки вошли все дочерние структуры и товарные знаки холдинга, включая розничные магазины и ООО '
         '«Белгородский ювелирный завод „Арт-Карат“».',
  'new': '100% доли в ООО «АДАМАС АЙПИ» (99% — от АО «Форум Капитал», 1% — от Ильи Сильченко) со всеми дочерними компаниями '
         'и товарными знаками, включая сеть магазинов и ООО «Белгородский ювелирный завод „Арт-Карат“».',
  'q': (Q_ADAMAS_REG + ' … ' + Q_ADAMAS_PERIM, FNS_ADAMAS)},
 {'op': 'company', 'cid': 'adamas', 'field': 'legal_short', 'old': MISSING, 'new': 'ООО «АДАМАС АЙПИ»'},
 {'op': 'company', 'cid': 'gd726f8d8', 'field': 'legal_short', 'old': MISSING, 'new': 'АО «Форум Капитал»'},
 {'op': 'replace', 'id': 'gcdec4f24', 'field': 'eco.context',
  'old': 'Магазинами управляет АО «1-я ювелирная сеть», которым до 2022 года владел «Адамас-ювелирторг»; к 29 сентября '
         '2020 года его конкурсный управляющий продал акции сети на торгах Святославу Потапову, а сам «Адамас-ювелирторг» '
         'обанкротился и ликвидирован.',
  'new': 'Магазинами управляет АО «1-я ювелирная сеть». До 2022 года им владел «Адамас-ювелирторг»; после его '
         'банкротства конкурсный управляющий в 2020 году продал акции сети на торгах Святославу Потапову, а '
         '«Адамас-ювелирторг» ликвидирован.'},
 # ---------------------------------------------------------------- g9d9e7ab6 «Группа Астра»
 {'op': 'set', 'id': 'g9d9e7ab6', 'field': 'sum', 'old': '10,4–10,7 млрд ₽ (по капитализации, оценка для 20% пакета)',
  'new': 'Не раскрыта', 'q': (Q_ASTRA, RBC_ASTRA)},
 {'op': 'set', 'id': 'g9d9e7ab6', 'field': 'eco.sum', 'old': '10,4–10,7 млрд ₽ (по капитализации, оценка для 20% пакета)',
  'new': 'Не раскрыта', 'q': (Q_ASTRA, RBC_ASTRA)},
 {'op': 'retract', 'id': 'g9d9e7ab6', 'field': 'sum', 'new': ['10,4–10,7 млрд ₽ (по капитализации, оценка для 20% пакета)']},
 {'op': 'note', 'id': 'g9d9e7ab6', 'path': 'no_profile.buyer',
  'new': 'Покупатель не определен: «Росатом» (РБК, январь 2026) и 1С (Forbes, март 2026) — версии источников, «Росатом» '
         'их опровергал; Т1 (Ведомости, май 2026) — переговоры Дениса Фролова о личном пакете. Искали: РБК Pro, Forbes '
         '(капча), Ведомости, smart-lab, e-disclosure «Группы Астра» — сообщений о сделке нет.'},
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
            if op['new'] in cur:
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
        cur = fns_registry.by_company_id().get(op['cid']) or {}
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
