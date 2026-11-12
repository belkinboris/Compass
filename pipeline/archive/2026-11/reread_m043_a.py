# -*- coding: utf-8 -*-
"""Вычитка, марафон 12 ноября 2026, партия m043 (часть a): поля, которые таблица правок не берет.

gd133363d (Kismet/ППР): год 2024 → 2023 (Интерфакс 15 августа 2023 года, «приобрела»; в реестре
  ППР смена участника 14.08.2023); второй источник — Retail.ru; описание профиля ППР без
  «в 2024 году его купила…» (неверный год и пересказ сделки в профиле).
g5ddac2b5 («Триумф Молл»): по ЕГРЮЛ 15.08.2023 100% ООО «Инвестиционно-ипотечная компания»
  (собственник ТРЦ) перешли от ООО «Грос» (группа «Сбербанк Капитал») к ООО «Инвестлайн»
  (Дмитрий Быков из «Аптекарского» 50% и ООО «Доминион» 50%); «Ведомости»: покупатель —
  структура Central Properties и «Аптекарского». Было: покупатель — «Аптекарский», продавец пуст,
  Сбербанк — «финансовый консультант» (он продавал как залоговый кредитор), дата 10 августа
  (день статьи). Заголовок — по стандарту.
g1d76aeb5 (Multispace/«Stone Курская»): сумма «5–6 млрд ₽ (по оценке)» не найдена ни в одном
  источнике (Ведомости, Ъ, поиск) — снята в retracted; дата — год (день статьи не день события);
  предмет назван; заголовок «может выкупить» при статусе «Не состоялась» — переписан.
g6e3bcb70 (Рэнера/«Кама»): год 2024 → 2022 (Ъ: покупка следует из отчетности за 2022 год;
  Habr: «В 2022 году… приобрела структура Росатома «Рэнера»»); покупатель — ООО «Рэнера»
  (новый профиль), а не профиль группы «Росатом».

Запуск: python3 pipeline/archive/2026-11/reread_m043_a.py [--write]
"""
import copy
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'вычитка m043, 12.11.2026'
IFX = 'https://www.interfax.ru/business/916354'
RETAIL = 'https://www.retail.ru/news/novym-sobstvennikom-kompanii-peredovye-platezhnye-resheniya-stala-kismet-capital-group/'
VED_TM = 'https://www.vedomosti.ru/realty/articles/2023/08/10/989374-central-properties-nashla-partnera-na-pokupku-torgovogo-tsentra'
REG_IIK = 'https://datanewton.ru/api/v2/history?ogrn=1036405019144&startDate=2000-01-01&attributes=OWNERS'
VED_MS = 'https://www.vedomosti.ru/realty/articles/2023/08/11/989571-set-gibkih-ofisov-multispace-mozhet-vikupit-biznes-tsentr'
KOM_KAMA = 'https://www.kommersant.ru/doc/6122479'
RENERA = 'g' + hashlib.md5('Рэнера Росатом'.encode()).hexdigest()[:8]


def setf(card, field, old, new, quote, url):
    """Поле-факт с assert на старое значение и цитатой в fact_log; повтор — «уже применено»."""
    path = field.split('.')
    obj = card
    for p in path[:-1]:
        obj = obj.setdefault(p, {})
    cur = obj.get(path[-1])
    if cur == new:
        return False
    assert cur == old, '%s %s: ожидали %r, стоит %r' % (card['id'], field, old, cur)
    obj[path[-1]] = new
    if field not in ('eco.sum',):
        fact_edit_guard.log(card, field, new, quote, url, BY)
    return True


def add_src(card, label, url):
    if url not in [u for _l, u in card.get('src') or []]:
        card.setdefault('src', []).append([label, url])
        return True
    return False


def apply(data):
    deals = {d['id']: d for d in data['deals']}
    comp = data['companies']
    n = 0

    c = deals['gd133363d']
    n += setf(c, 'date', '2024', '2023',
              'Москва. 15 августа. INTERFAX.RU - Kismet Capital Group Ивана Таврина приобрела у американской '
              'Fleetcor Technologies 100% долей российского ООО "Передовые платежные решения" (ППР)', IFX)
    n += add_src(c, 'Retail.ru', RETAIL)
    p = comp['gdef372ce']
    new_desc = ('Финтех-оператор: процессинг корпоративных платежей за топливо по топливным картам на АЗС, '
                'а также за парковки, мойки, командировки и отели. Клиентов — более 70 тыс. юрлиц и ИП.')
    if p.get('desc') != new_desc:
        assert p['desc'].startswith('Платежный бизнес (ППР); в 2024 году'), p['desc']
        p['desc'] = new_desc
        n += 1

    c = deals['g5ddac2b5']
    reg_q = ('2023-08-15: было ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ГРОС" (ОГРН 1117746254240) 100.0% '
             '(10 350 000 руб.); стало ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ «ИНВЕСТЛАЙН» (ОГРН 1216400005843) 100.0%')
    n += setf(c, 'date', '2023-08-10', '2023-08-15', reg_q, REG_IIK)
    if c.get('date_basis') != 'registry':
        c['date_basis'] = 'registry'
    n += setf(c, 'buyer', 'gf72c212b', None,
              'покупателем стала структура инвесткомпании Central Properties и фирмы «Аптекарский»', VED_TM)
    n += setf(c, 'buyer_name', None, 'ООО «Инвестлайн»', reg_q, REG_IIK)
    n += setf(c, 'seller', None, 'ООО «Грос»', reg_q, REG_IIK)
    n += setf(c, 'eco.finadv', 'Сбербанк — финансовый консультант сделки', 'Публично не сообщалось',
              'По крайней мере, в 2021 г. Сбербанк, который выступал залоговым кредитором этого объекта, выставил '
              'его на продажу по цене в 4,2 млрд руб.', VED_TM)
    n += setf(c, 'title',
              'Компания «Аптекарский» стала партнером Central Properties по ТРЦ «Триумф Молл» в Саратове',
              'Структура Central Properties и «Аптекарского» купила ТРЦ «Триумф Молл» в Саратове',
              'По их словам, покупателем стала структура инвесткомпании Central Properties и фирмы «Аптекарский»', VED_TM)
    n += add_src(c, 'ЕГРЮЛ: история участников ООО «Инвестиционно-ипотечная компания»', REG_IIK)
    p = comp['g133f4b27']
    if p.get('legal_short') != 'ООО «Инвестиционно-ипотечная компания»':
        assert not p.get('legal_short')
        p['legal_short'] = 'ООО «Инвестиционно-ипотечная компания»'
        p['desc'] = ('Торгово-развлекательный центр площадью 58 тыс. кв. м на улице Зарубина в Саратове, построен '
                     'в 2010 году. Собственник — ООО «Инвестиционно-ипотечная компания».')
        n += 1

    c = deals['g1d76aeb5']
    n += setf(c, 'title', 'Multispace может выкупить бизнес-центр Stone Курская у девелопера Stone',
              'Сделка Multispace по покупке бизнес-центра «Stone Курская» не состоялась',
              'Однако в начале 2025 года в Stone заявили, что здание продано частному инвестору, не раскрыв подробностей.',
              'https://www.kommersant.ru/doc/8079485')
    n += setf(c, 'date', '2023-08-11', '2023',
              'Девелопер Stone договаривается с сетью гибких офисов Multispace о продаже ей офисного комплекса '
              '«Stone Курская» (15 600 кв. м)', VED_MS)
    if c.get('sum') != 'Не раскрыта':
        assert c['sum'] == '5–6 млрд ₽ (по оценке)' and c['eco']['sum'] == c['sum']
        c.setdefault('retracted', {}).setdefault('sum', []).append(c['sum'])
        c['sum'] = c['eco']['sum'] = 'Не раскрыта'
        fact_edit_guard.log(c, 'sum', 'Не раскрыта',
                            'Девелопер Stone договаривается с сетью гибких офисов Multispace о продаже ей офисного '
                            'комплекса «Stone Курская» (15 600 кв. м)', VED_MS, BY + ': сумма ни в одном источнике не названа')
        fact_edit_guard.log(c, 'eco.sum', 'Не раскрыта',
                            'Девелопер Stone договаривается с сетью гибких офисов Multispace о продаже ей офисного '
                            'комплекса «Stone Курская» (15 600 кв. м)', VED_MS, BY + ': сумма ни в одном источнике не названа')
        n += 1
    n += setf(c, 'asset', None, 'Бизнес-центр «Stone Курская» (15 600 кв. м, Костомаровский переулок, Москва)',
              'офисного комплекса «Stone Курская» (15 600 кв. м), расположенного в Костомаровском переулке рядом со ст. м. «Курская»',
              VED_MS)

    c = deals['g6e3bcb70']
    n += setf(c, 'date', '2024', '2022',
              'ООО «Рэнера» (структура «Росатома») приобрело долю в АО «Кама» почти за 6,2 млрд руб., следует из '
              'отчетности компании за 2022 год.', KOM_KAMA)
    if RENERA not in comp:
        comp[RENERA] = {'name': 'Рэнера', 'ind': 'Энергетика',
                        'desc': 'Структура «Росатома»: интегратор по системам накопления энергии, строит гигафабрику '
                                'аккумуляторов в Калининграде.',
                        'kpi': ['Профиль', 'Автоматический'], 'legal_short': 'ООО «Рэнера»'}
        n += 1
    n += setf(c, 'buyer', 'rosatom', RENERA,
              'ООО «Рэнера» (структура «Росатома») приобрело долю в АО «Кама» почти за 6,2 млрд руб.', KOM_KAMA)
    # Правовая форма сторон по реестру (сайт /api/companies/<id>/fns сбрасывал соединение — ставим здесь).
    for cid, legal in (('gdef372ce', 'ООО «ППР»'), ('gace55b64', 'АО «Стоунхедж»'), ('g0993ebfa', 'АО «Кама»')):
        if comp[cid].get('legal_short') != legal:
            assert not comp[cid].get('legal_short'), comp[cid].get('legal_short')
            comp[cid]['legal_short'] = legal
            n += 1
    return n


def main(argv):
    old = json.load(open(DATA, encoding='utf-8'))
    new = copy.deepcopy(old)
    n = apply(new)
    print('изменений: %d' % n)
    if not n:
        print('уже применено')
        return 0
    mass_edit_guard.check(old, new, os.environ.get('MASS_OK'))
    if '--write' in argv:
        cur = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
        apply(cur)
        json.dump(cur, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('записано')
    else:
        print('сухой прогон; запись — --write')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
