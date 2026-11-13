# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m223 (части 4–5): чего не умеет review.py.

gc65bacdf (Nielsen/GfK): отрасль «Не определена» → «Профессиональные услуги» (словарь review.py исследований рынка не
  знает): «Обе компании продолжат заниматься исследованиями потребительского рынка, аудитом розничной торговли»
  (Кинометро). Предмет — имена юрлиц: ООО «ГФК-Русь» и ООО «Эй Си Нильсен» (там же). Дата 25 сентября 2026 года —
  день записи в ЕГРЮЛ по ООО «Эй Си Нильсен».
gcb875d9e («Приосколье»): ЕГРЮЛ, АО «Приосколье» (ИНН 3123100360): 2025-02-03 left Бобрицкий Геннадий Алексеевич,
  joined ООО «УК «Приосколье»» (ИНН 9701252644 — бывшее ООО «Инвест-трейд» Сергея Феськова, участник с 2023-06-27);
  7 февраля 2025 года — смена гендиректора ООО «УК «Приосколье»», а не переход. Предмет — три общества, которыми
  «Инвест-трейд» стал владеть единолично («Коммерсантъ», 10 февраля 2025 года). Правовая форма покупателя — ООО.

    python3 pipeline/archive/2026-11/reread_oneoff_m223d.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_m223d', '2026-11-12'
KINO = 'https://www.kinometro.ru/news/show/name/nielsen_gfk_sale_25092026'
KOM = 'https://www.kommersant.ru/doc/7496153'
EGRUL = ('ЕГРЮЛ, АО «Приосколье» (ИНН 3123100360): 2025-02-03 left Бобрицкий Геннадий Алексеевич; 2025-02-03 joined '
         'ООО «УК «Приосколье»» (ИНН 9701252644, бывш. ООО «Инвест-трейд», участник — Феськов Сергей Геннадьевич с '
         '2023-06-27)')
Q_PRIO = ('Единственным владельцем трех структур белгородского аргрохолдинга «Приосколье» Геннадия Бобрицкого стало ООО '
          '«Инвест-трейд» Сергея Феськова, который возглавил их в конце января. Речь идет об АО «Приосколье», ЗАО '
          '«Краснояружская зерновая компания» и ЗАО «Новооскольский комбикормовый завод»')
ASSET_PRIO = 'АО «Приосколье», ЗАО «Краснояружская зерновая компания» и ЗАО «Новооскольский комбикормовый завод»'
SHARE_PRIO = ('100% акций АО «Приосколье», ЗАО «Краснояружская зерновая компания» и ЗАО «Новооскольский комбикормовый '
              'завод»')


def apply(data):
    by = {d['id']: d for d in data['deals']}
    comps = data['companies']
    n = 0
    c = by['gc65bacdf']
    if c['ind'] != 'Профессиональные услуги':
        assert c['ind'] == 'Не определена', c['ind']
        c['ind'] = 'Профессиональные услуги'
        n += 1
    new = 'ООО «ГФК-Русь» и ООО «Эй Си Нильсен»'
    if c.get('asset') != new:
        assert c.get('asset') == 'российские активы Nielsen и «ГФК-Русь»', c.get('asset')
        c['asset'] = new
        fact_edit_guard.log(c, 'asset', new, 'Отмечается, что 60% ООО «ГФК-Русь» приобрела компания Леоновича … По '
                            'данным ЕГРЮЛ, 25 сентября владельцем 100% ООО «Эй Си Нильсен» стало принадлежащее Леоновичу '
                            'ООО «Конверсия».', KINO, BY, DAY)
        n += 1
    if c.get('date_basis') != 'registry':
        c['date_basis'] = 'registry'
        n += 1
    c = by['gcb875d9e']
    if c['date'] != '2025-02-03':
        assert c['date'] == '2025-02-07', c['date']
        c['date'] = '2025-02-03'
        c['date_basis'] = 'registry'
        fact_edit_guard.log(c, 'date', '2025-02-03', EGRUL, '', BY, DAY)
        n += 1
    if c.get('asset') != ASSET_PRIO:
        assert c.get('asset', '').startswith('структуры группы «Приосколье»'), c.get('asset')
        c['asset'] = ASSET_PRIO
        fact_edit_guard.log(c, 'asset', ASSET_PRIO, Q_PRIO, KOM, BY, DAY)
        n += 1
    if c['eco'].get('share') != SHARE_PRIO:
        assert c['eco'].get('share') == '—', c['eco'].get('share')
        c['eco']['share'] = SHARE_PRIO
        fact_edit_guard.log(c, 'eco.share', SHARE_PRIO, Q_PRIO, KOM, BY, DAY)
        n += 1
    co = comps['g0cc44556']
    if co.get('legal_short') != 'ООО «Инвест-трейд»':
        assert not co.get('legal_short'), co.get('legal_short')
        co['legal_short'] = 'ООО «Инвест-трейд»'
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
    sys.exit(main('--write' in sys.argv[1:]))
