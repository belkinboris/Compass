# -*- coding: utf-8 -*-
"""Вычитка 26 ноября 2026, партия r1126a: срыв сделки Carlyle, даты по событию, лишнее из полей.

Чего не умеет review.py: снятие поля до «—», перенос дня назад к году, дата по другому
событию, добавление источника в src.

g20d4cc38 (Carlyle/LUKOIL International GmbH): соглашение 29 января 2026 года истекло без
  одобрения OFAC (по сообщению LIG — в конце июля, по другим данным — в конце июня), 9 октября
  2026 года Carlyle подтвердила, что от покупки отказалась (ПРАЙМ, Фонтанка, РБК, Ведомости);
  позже LIG купил консорциум Боэли (отдельная карточка g707211ba). Статус «Обсуждается» →
  «Не состоялась», дата — день отказа Carlyle, заголовок по стандарту срыва. В «Условиях»
  стояли условия обмена акциями консорциума Боэли, в «Форме расчетов» — описание Carlyle,
  в «Дополнительно» — повтор структуры: поля сняты до «—». Доля — 100% LUKOIL International
  GmbH (ЛУКОЙЛ: «100% дочернего общества»). Источник о подписании Боэли добавлен в src.
gf145d639 (корпус ледокола «Арктика»): день «16 октября» — время заметки Би-порта, а не
  протокола (торги назначены на 15 октября, протокол рассмотрения заявок — до них; день
  протокола в статьях не назван) — дата снова годом. Предмет — с заглавной. «На территории
  России» в статьях нет.
g87b1733a (ММРП): решение Арбитражного суда Мурманской области — 3 октября 2022 года
  (Интерфакс, 3 февраля 2023 года); 5 октября — день заметки.

    python3 pipeline/archive/2026-11/reread_oneoff_r1126a.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_r1126a', '2026-11-26'

PRIME_EXIT = 'https://1prime.ru/20261009/carlyle-874108946.html'
Q_EXIT = ('Американская инвестиционная компания Carlyle подтвердила, что больше не пытается приобрести '
          'зарубежные активы "Лукойла"')
FONT = 'https://www.fontanka.ru/2026/11/03/76743851/'
Q_FONT = 'однако 9 октября 2026 года Carlyle официально подтвердила, что больше не рассматривает эту покупку'
IFX = 'https://www.interfax.ru/business/1070027'
Q_SHARE = ('ПАО "ЛУКОЙЛ" заключило соглашение с американской инвестиционной компанией Carlyle о продаже '
           'LUKOIL International GmbH (100% дочернего общества российской НК, владеющего зарубежными активами группы)')
V1125 = ['Ведомости', 'https://www.vedomosti.ru/business/articles/2026/11/25/1415357-boeli-podpisala']

BPORT = 'https://b-port.com/news/367211'
Q_BPORT = ('Сам аукцион признали несостоявшимся из-за участия только одного претендента. При этом комиссия '
           'постановила заключить договор с ООО «Авиавторресурс» по цене не менее начальной (минимальной). — '
           '«14:17 – 16 октября» — время заметки Би-порта; торги были назначены на 15 октября, протокол '
           'рассмотрения заявок — до них, его день в статьях не назван.')
ARKT_OLD = 'корпус атомного ледокола «Арктика» проекта 10520 (построен в 1974–1975 годах)'
ARKT_NEW = 'Корпус атомного ледокола «Арктика» проекта 10520 (построен в 1974–1975 годах)'
CTX_OLD = 'судно разделают на металлолом на территории России.'
CTX_NEW = 'корпус разделают на металлолом.'

MMRP = 'https://www.interfax.ru/russia/884548'
Q_MMRP = ('Арбитражный суд Мурманской области 3 октября 2022 года решил взыскать в доход государства '
          '100% акций ММРП по иску ФАС России.')


def apply(data):
    by = {d['id']: d for d in data['deals']}
    n = 0

    c = by['g20d4cc38']
    if c['status'] != 'Не состоялась':
        assert c['status'] == 'Обсуждается' and c['date'] == '2026-01-29', (c['status'], c['date'])
        assert c['title'] == 'Carlyle собирается купить LUKOIL International GmbH', c['title']
        c['status'] = 'Не состоялась'
        fact_edit_guard.log(c, 'status', 'Не состоялась', Q_EXIT, PRIME_EXIT, BY, DAY)
        c['date'] = '2026-10-09'
        c['date_basis'] = 'announcement'
        fact_edit_guard.log(c, 'date', '2026-10-09', Q_FONT, FONT, BY, DAY)
        c['title'] = 'Carlyle отказался от покупки LUKOIL International GmbH'
        fact_edit_guard.log(c, 'title', c['title'], Q_EXIT, PRIME_EXIT, BY, DAY)
        assert c['eco'].get('share') == '—', c['eco'].get('share')
        c['eco']['share'] = '100% LUKOIL International GmbH'
        fact_edit_guard.log(c, 'eco.share', c['eco']['share'], Q_SHARE, IFX, BY, DAY)
        assert c['law']['terms'].startswith('Сделка безналичная: замороженные бумаги'), c['law']['terms']
        c['law']['terms'] = '—'
        assert c['eco']['fin'].startswith('Carlyle — инвестиционная компания'), c['eco']['fin']
        c['eco']['fin'] = '—'
        assert c['extra'].startswith('ПАО ЛУКОЙЛ договорилось'), c['extra']
        c['extra'] = '—'
        if V1125[1] not in [s[1] for s in c['src']]:
            c['src'].append(list(V1125))
        n += 1

    c = by['gf145d639']
    if c['date'] != '2026':
        assert c['date'] == '2026-10-16', c['date']
        c['date'] = '2026'
        c.pop('date_basis', None)
        fact_edit_guard.log(c, 'date', '2026', Q_BPORT, BPORT, BY, DAY)
        n += 1
    if c.get('asset') == ARKT_OLD:
        c['asset'] = ARKT_NEW
        fact_edit_guard.log(c, 'asset', ARKT_NEW, 'Атомный ледокол «Арктика» проекта 10520 — корпус с надстройкой '
                            '(смена буквы на заглавную, без смены смысла)', BPORT, BY, DAY)
        n += 1
    if CTX_OLD in c['eco']['context']:
        c['eco']['context'] = c['eco']['context'].replace(CTX_OLD, CTX_NEW)
        n += 1

    c = by['g87b1733a']
    if c['date'] != '2022-10-03':
        assert c['date'] == '2022-10-05', c['date']
        c['date'] = '2022-10-03'
        c['date_basis'] = 'closing'
        fact_edit_guard.log(c, 'date', '2022-10-03', Q_MMRP, MMRP, BY, DAY)
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
