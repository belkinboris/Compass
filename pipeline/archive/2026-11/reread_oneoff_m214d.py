# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m214 (четвертая часть): то, чего не умеет review.py.

gdfce7e3d («Обсидиан»): «4,3–4,8 млрд ₽» — расчет Антона Калистратова (Commonwealth Partnership):
  «Детали сделки стороны не раскрывают. … Дом.РФ, по его мнению, мог заплатить за этот объект 4,3–4,8 млрд
  руб.» (Ведомости) — оценка, не цена: сумма «Не раскрыта» (оценки уже в eco.val). Этап «Сделка завершена» —
  пересказом вместо почти дословной заметки агрегатора, источник этапа — «Ведомости», а не mergers.ru.
gc5951fac (CARGO.RUN): 25% без контроля (Тимур Каримов сохранил 64,5%) — тип «Инвестиция»; по ЕГРЮЛ
  (pipeline/party_legal_names.py) 27.04.2026 вошли Вильде (13,5%) и Круглов (11,5%), доли Каримова,
  Ахметзяновой и Хамадеева уменьшились — дата по реестру; 4 августа — день новости. Сумма «Не раскрыта»;
  этап — пересказом (25 слов подряд из TAdviser).
gfa114edc («Персей»): сумма в обе графы — «Не раскрыта»; обещание раскрыть «в середине осени 2026 года» к
  13 ноября 2026 года не исполнено (поиск: CNews, Market Power, Anti-Malware — цены нет).

    python3 pipeline/archive/2026-11/reread_oneoff_m214d.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_m214d', '2026-11-12'
VED = 'https://www.vedomosti.ru/newspaper/articles/2026/08/03/1218273-domrf-zakril-sdelku-po-pokupke-biznes-tsentra-obsidian'
VED_Q = ('Детали сделки стороны не раскрывают. … С учетом возможного торга Дом.РФ, по его мнению, мог заплатить за этот '
         'объект 4,3–4,8 млрд руб.')
CN = 'https://www.cnews.ru/news/line/2026-08-04_atisu_i_cargorun_svyazhut_poisk_gruzov'
EGRUL = ('ЕГРЮЛ, ООО «Цифровизация транспорта» (ИНН 1650379003): 2026-04-27 joined Вильде Святослав Вольдемарович '
         '(13.5), Круглов Олег Анатольевич (11.5); Каримов Тимур Наилевич 86.0 → 64.5, Ахметзянова Алсу Рустамовна '
         '7.0 → 5.25, Хамадеев Шамиль Актасович 7.0 → 5.25')
COMNEWS = ('https://www.comnews.ru/digital-economy/content/246725/2026-08-04/2026-w32/1012/'
           'tantor-labs-zakryla-sdelku-mt-integraciey-subd-persey-i-usilila-pozicii-rynke-subd')
NOTES = {
    'gdfce7e3d': ('ЗПИФ недвижимости Дом.РФ под управлением ООО «Дом.РФ управление активами»',
                  'По выписке Росреестра 4 мая 2026 года бизнес-центр «Обсидиан» перешел к ЗПИФ недвижимости Дом.РФ; '
                  'продал его Business Club.',
                  ['Ведомости', VED]),
    'gc5951fac': ('В августе 2026 года стало известно',
                  'По ЕГРЮЛ 27 апреля 2026 года Святослав Вильде и Олег Круглов получили вместе 25% ООО «Цифровизация '
                  'транспорта»; стороны объявили о сделке 4 августа.',
                  ['CNews', CN]),
}


def set_sum(c, old_sum, old_eco, quote, url):
    if c.get('sum') == 'Не раскрыта' and c['eco'].get('sum') == 'Не раскрыта':
        return 0
    assert c.get('sum') == old_sum and c['eco'].get('sum') == old_eco, (c['id'], c.get('sum'), c['eco'].get('sum'))
    if old_sum:
        c.setdefault('retracted', {}).setdefault('sum', []).append(old_sum)
    c['sum'] = c['eco']['sum'] = 'Не раскрыта'
    fact_edit_guard.log(c, 'sum', 'Не раскрыта', quote, url, BY, DAY)
    fact_edit_guard.log(c, 'eco.sum', 'Не раскрыта', quote, url, BY, DAY)
    return 1


def apply(data):
    by = {d['id']: d for d in data['deals']}
    n = 0
    n += set_sum(by['gdfce7e3d'], '4,3–4,8 млрд ₽ (по оценке)', '4,3–4,8 млрд ₽ (по оценке)',
                 VED_Q + ' — оценка консультанта, не цена сделки.', VED)
    n += set_sum(by['gc5951fac'], None, 'Стоимость сделки стороны не раскрывают.',
                 'Стоимость сделки стороны не раскрывают.', CN)
    n += set_sum(by['gfa114edc'], None, 'Сумму сделки держат в тайне, но обещают раскрыть в середине осени 2026 г.',
                 'Сумму сделки держат в тайне, но обещают раскрыть в середине осени 2026 г. — к 13.11.2026 не раскрыта.',
                 'https://www.cnews.ru/news/top/2026-08-04_sozdatel_samogo_izvestnogo')
    c = by['gc5951fac']
    if c.get('type') != 'Инвестиция':
        assert c.get('type') == 'M&A', c.get('type')
        c['type'] = 'Инвестиция'
        fact_edit_guard.log(c, 'type', 'Инвестиция', 'Основатель и генеральный директор Cargo.Run Тимур Каримов '
                            'сохранил контроль над компанией с долей 64,5%.', CN, BY, DAY)
        n += 1
    if c['date'] != '2026-04-27':
        assert c['date'] == '2026-08-04', c['date']
        c['date'] = '2026-04-27'
        c['date_basis'] = 'registry'
        fact_edit_guard.log(c, 'date', '2026-04-27', EGRUL, '', BY, DAY)
        n += 1
    for cid, (start, note, src) in NOTES.items():
        ev = by[cid]['events'][0]
        if ev.get('note') != note:
            assert ev.get('note', '').startswith(start), cid
            ev['note'] = note
            ev['source'] = src
            if cid == 'gc5951fac':
                ev['date'] = '2026-04-27'
            n += 1
    return n


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = apply(data)
    if not n:
        print('Уже применено.')
        return 0
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    if not write:
        print('Сухой прогон: %d правок. Запись — с ключом --write.' % n)
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО: %d правок.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
