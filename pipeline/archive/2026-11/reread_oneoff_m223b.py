# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m223 (часть 2): чего не умеет review.py.

g4b00b18e («Парадиз»): день события у этапа «Сделка завершена» — 14 сентября 2026 года (как и дата карточки,
  «Коммерсантъ»: «Московские власти 14 сентября 2026 года продали помещение…»); правовая форма покупателя по
  реестру — ООО «Кинокомпания «Парадиз продакшнз»» (ИНН 7703135371; имя юрлица — в той же статье).
g69c83a3f (РСТИ/ПИК): «Стоимость сделки составит около 8 миллиардов рублей» — со слов источников «Делового
  Петербурга», неофициальная цена: «8 млрд ₽ (по оценке)». День подписания предварительного договора не назван
  (DP 23 сентября 2026 — день статьи) — дата годом. Предмет — 5,34 га (DP, «Коммерсантъ»), не 5,3 га.
  Первоисточник — «Деловой Петербург» (РИА пересказывает его) — первым в src; Рамблер о переговорах с «Геометрией».
gd8faa2c4 («Инфамед»): договор купли-продажи 50% подписан у нотариуса 28 декабря 2024 года (Vademecum, Фармвестник),
  переход доли в ЕГРЮЛ не записан (владелец по реестру — Николаев, 99,9%), решение суда о передаче 50% Хейфиц
  в силу не вступило — статус «Подписана», а не «Закрыта»; дата — день договора, а не 23 сентября 2026 года
  (решение по другому договору). Цена: «покупатель полностью уплатил продавцу указанную в договоре сумму – чуть
  более 7,5 миллиона рублей» (ПРАЙМ, 30 сентября 2026) — «≈7,5 млн ₽». Этап «Суд передал долю Оксане Хейфиц» —
  судебный, а не закрытие сделки.

    python3 pipeline/archive/2026-11/reread_oneoff_m223b.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_m223b', '2026-11-12'
RIA_RSTI = 'https://realty.ria.ru/20260923/ploschadka-2119747059.html'
DP = 'https://www.dp.ru/a/2026/09/23/rsti-planiruet-kupit-uchastok'
KOM_RSTI = 'https://www.kommersant.ru/doc/8974479'
RAMBLER = 'https://finance.rambler.ru/realty/56895602-pik-gotovitsya-prodat-svoy-uchastok-v-peterburge-za-8-mlrd-rubley/'
VADEM = ('https://vademec.ru/news/2025/07/22/sud-zapretil-benefitsiaru-infameda-izmenyat-status-regudostovereniy-'
         'na-miramistin-i-okomistin/')
PRIME30 = 'https://1prime.ru/20260930/sud-873808561.html'

Q_RSTI_SUM = ('Компания РСТИ подписала предварительный договор с ПИК и уже внесла задаток. Стоимость сделки составит '
              'около 8 миллиардов рублей, говорится в статье. — со слов источников «Делового Петербурга»: '
              'неофициальная цена')
Q_INF_SUM = ('Он принял во внимание, что покупатель полностью уплатил продавцу указанную в договоре сумму – чуть более '
             '7,5 миллиона рублей.')


def apply(data):
    by = {d['id']: d for d in data['deals']}
    comps = data['companies']
    n = 0
    # g4b00b18e
    c = by['g4b00b18e']
    ev = c['events'][0]
    if ev['date'] != '2026-09-14':
        assert ev['kind'] == 'closed' and ev['date'] == '2026-09-23', ev
        ev['date'] = '2026-09-14'
        n += 1
    co = comps['g021348d9']
    if co.get('legal_short') != 'ООО «Кинокомпания «Парадиз продакшнз»»':
        assert not co.get('legal_short'), co.get('legal_short')
        co['legal_short'] = 'ООО «Кинокомпания «Парадиз продакшнз»»'
        n += 1
    # g69c83a3f
    c = by['g69c83a3f']
    new = '8 млрд ₽ (по оценке)'
    if c['sum'] != new:
        assert c['sum'] == '8 млрд ₽' and c['eco']['sum'] == 'Стоимость составит около 8 млрд рублей', c['sum']
        c['sum'] = new
        c['eco']['sum'] = new
        fact_edit_guard.log(c, 'sum', new, Q_RSTI_SUM, RIA_RSTI, BY, DAY)
        fact_edit_guard.log(c, 'eco.sum', new, Q_RSTI_SUM, RIA_RSTI, BY, DAY)
        n += 1
    if c['date'] != '2026':
        assert c['date'] == '2026-09-23', c['date']
        c['date'] = '2026'
        c.pop('date_basis', None)
        fact_edit_guard.log(c, 'date', '2026', 'РСТИ приобретает у ПИК участок … Компания РСТИ подписала предварительный '
                            'договор с ПИК и уже внесла задаток. — день подписания не назван, 23 сентября 2026 года — '
                            'день статьи', RIA_RSTI, BY, DAY)
        n += 1
    new_asset = 'Участок 5,34 га у Шкиперского протока в Петербурге'
    if c.get('asset') != new_asset:
        assert c.get('asset') == 'участок 5,3 га на Шкиперском протоке', c.get('asset')
        c['asset'] = new_asset
        fact_edit_guard.log(c, 'asset', new_asset, 'Девелопер РСТИ подписал предварительный договор о покупке у ГК '
                            'ПИК 5,34 га в районе Шкиперского протока с выходом к береговой линии Невы', KOM_RSTI, BY, DAY)
        n += 1
    urls = [s[1] for s in c['src']]
    if urls[0] != DP:
        dp = [s for s in c['src'] if s[1] == DP]
        assert dp, urls
        c['src'] = dp + [s for s in c['src'] if s[1] != DP]
        n += 1
    if RAMBLER not in urls:
        c['src'].append(['Рамблер', RAMBLER])
        n += 1
    # gd8faa2c4
    c = by['gd8faa2c4']
    if c['status'] != 'Подписана':
        assert c['status'] == 'Закрыта', c['status']
        c['status'] = 'Подписана'
        c.setdefault('retracted', {}).setdefault('status', []).append('Закрыта')
        fact_edit_guard.log(c, 'status', 'Подписана', 'Хугаева, с 2014 года единолично владевшая "Инфамедом", в '
                            'декабре 2024 года заключила с Хейфиц договор купли-продажи доли в 50% … В ЕГРЮЛ '
                            'собственником 99,9% ООО "Инфамед" указан Николаев. … Решение пока не вступило в силу.',
                            PRIME30, BY, DAY)
        n += 1
    if c['date'] != '2024-12-28':
        assert c['date'] == '2026-09-23', c['date']
        c['date'] = '2024-12-28'
        c['date_basis'] = 'signing'
        fact_edit_guard.log(c, 'date', '2024-12-28', 'Хугаева требует признать недействительным договор купли-продажи '
                            'доли в уставном капитале «Инфамеда» от 28 декабря 2024 года, заключенного между Хугаевой '
                            'и Хейфиц.', VADEM, BY, DAY)
        n += 1
    new = '≈7,5 млн ₽'
    if c.get('sum') != new:
        assert c.get('sum') is None and c['eco'].get('sum') == '—', (c.get('sum'), c['eco'].get('sum'))
        c['sum'] = new
        c['eco']['sum'] = new
        c['sum_basis'] = 'reported'
        fact_edit_guard.log(c, 'sum', new, Q_INF_SUM, PRIME30, BY, DAY)
        fact_edit_guard.log(c, 'eco.sum', new, Q_INF_SUM, PRIME30, BY, DAY)
        n += 1
    ev = c['events'][0]
    if ev['kind'] == 'closed':
        assert ev['title'] == 'Суд передал долю Оксане Хейфиц', ev
        ev['kind'] = 'court'
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
