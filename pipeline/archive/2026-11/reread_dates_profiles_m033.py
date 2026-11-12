# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, партия m033: правки, которые review.py не принимает.

ЧТО ЧИНИТ.
  g5e0f6a47 («Салаватстекло» / «Уфанет»): дата 2024-05-01 — заглушка; день сделки неизвестен («сделка могла
    состояться около трех недель назад» — Ъ 6745706 от 4 июня 2024 года), поэтому дата годом (docs/card_status_dates.md:
    снятие дня — разовым скриптом). eco.sum «Не раскрыта (EV оценена в 21 млрд ₽)»: оценки 21 млрд ₽ нет ни в одном
    источнике (Ъ, Абирег, UFA1, ComNews; в ComNews — 6 млрд ₽ за 60% по Делицыну, она в eco.val) — снята.
  g61e63e94 («Агрокомплекс» / завод в Медведовской): продавец PepsiCo → АО «Вимм-Билль-Данн» (Интерфакс 962844:
    завод «ранее принадлежавшего компании "Вимм-Билль-Данн"»). Пара seller/seller_id правится вместе: review.py
    ссылку на профиль не принимает (сверяет id с цитатой).
  Профили предметов: g78c042b5 «молочный завод в ст. Медведовской» → «Медведовский молочный завод» (Ъ 7909448);
    g85f1b0b8 «ООО «ЭЙЧ-ЭС-БИ-СИ БАНК »» (капслок и пробел) → «ООО «Эйч-эс-би-си Банк (РР)»» (РИА, 29.05.2024).

    python3 pipeline/archive/2026-11/reread_dates_profiles_m033.py           # сухой прогон
    python3 pipeline/archive/2026-11/reread_dates_profiles_m033.py --write

  Часть 2 партии:
  g54843952 (ТРЦ «Город Косино»): продавец ТЭН → ЗПИФ «Актив-премьер траст» (Ведомости: «Владельцем половины этого
    объекта был закрытый паевой инвестиционный фонд (ЗПИФ) «Актив-премьер траст», связанный с группой ТЭН»); ссылка
    на профиль ТЭН снимается вместе с текстом, ТЭН — в контексте.
  gc0ba024d (Telega.in): продавец «Холдинг Mirafox» → Людмила Мельникова (ЕГРЮЛ ООО «Телекот»: вышла 27.04.2024 со
    100%); Mirafox — основатель сервиса в 2016 году (Ъ), продавцом его не называет ни один источник.
  g8ff9bdf8 (ЦДМ) и g1a6f4fec (WeWork): сумма — оценка аналитиков («10–20 млрд ₽ (по оценке)» нет ни в одном
    источнике; «≈1,5 млрд ₽» — расчет, которого нет в источниках) → «Не раскрыта»: оценка — не цена сделки.
  Описания профилей, повторявшие снятые факты (цена по оценке, «структура ВТБ», Mirafox как продавец, O1 Properties
    как покупатель), переписаны по источникам.

Базу читает прямо перед записью; на каждое поле — assert на старое значение; повторный запуск — «уже применено».
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'reread m033 (2026-11-12)'
K67 = 'https://www.kommersant.ru/doc/6745706'
IF = 'https://www.interfax.ru/business/962844'

K13 = 'https://www.kommersant.ru/doc/6835929'
VED = ('https://www.vedomosti.ru/realty/articles/2023/05/26/976988-gruppa-ten-vishla-iz-sostava-sobstvennikov-'
       'torgovo-razvlekatelnogo-tsentra?from=newsline')
REG_T = 'https://projectcompass.ru/api/companies/g2ba29ec2/fns'
MAIL = 'https://finance.mail.ru/article/gruppa-kompaniy-kievskaya-ploschad-vykupila-centralnyy-detskiy-magazin-60651863/'
RBWW = 'https://rb.ru/news/wework-prodazha-biznesa/'
_VED_Q = ('Владельцем половины этого объекта был закрытый паевой инвестиционный фонд (ЗПИФ) «Актив-премьер траст», '
          'связанный с группой ТЭН.')
_REG_Q = '2024-04-27 left: Мельникова Людмила Вадимовна (100.0 → None)'
_CDM_Q = 'Условия сделки там не раскрыли.'
_WW_Q = 'Сумма сделки не раскрывается.'

DEALS = [
    ('g5e0f6a47', 'date', '2024-05-01', '2024',
     'По информации «Ъ-Уфа» , сделка могла состояться около трех недель назад на фоне интереса к мажоритарному '
     'пакету акций уфимской компании со стороны депутата Госдумы Александра Хинштейна.', K67),
    ('g5e0f6a47', 'eco.sum', 'Не раскрыта (EV оценена в 21 млрд ₽)', 'Не раскрыта',
     'Какой пакет акций «Уфанета» перешел «Салаватстеклу», не сообщается.', K67),
    ('g61e63e94', 'seller', 'PepsiCo', 'АО «Вимм-Билль-Данн»',
     'закрыл сделку по покупке молочного завода в Тимашевском районе Краснодарского края, ранее принадлежавшего '
     'компании "Вимм-Билль-Данн" (ВБД, объединяет молочные активы PepsiCo Inc.)', IF),
    ('g61e63e94', 'seller_id', 'g40ed26e7', 'g7e678842',
     'ранее принадлежавшего компании "Вимм-Билль-Данн" (ВБД, объединяет молочные активы PepsiCo Inc.)', IF),
    ('g54843952', 'seller', 'ТЭН', 'ЗПИФ «Актив-премьер траст»', _VED_Q, VED),
    ('g54843952', 'seller_id', 'g8eabc0bc', None, _VED_Q, VED),
    ('gc0ba024d', 'seller', 'Холдинг Mirafox', 'Людмила Мельникова', _REG_Q, REG_T),
    ('gc0ba024d', 'seller_id', 'g3e3d7bb1', None, _REG_Q, REG_T),
    ('g8ff9bdf8', 'sum', '10–20 млрд ₽ (по оценке)', 'Не раскрыта', _CDM_Q, MAIL),
    ('g8ff9bdf8', 'eco.sum', '10–20 млрд ₽ (по оценке)', 'Не раскрыта', _CDM_Q, MAIL),
    ('g1a6f4fec', 'sum', '≈1,5 млрд ₽ (по оценке)', 'Не раскрыта', _WW_Q, RBWW),
    ('g1a6f4fec', 'eco.sum', '≈1,5 млрд ₽ (по оценке)', 'Не раскрыта', _WW_Q, RBWW),
]
DESCS = [
    ('g0cd87ec1', 'Крупнейший в России детский торговый центр на Лубянке (74,11 тыс. кв. м), памятник регионального '
                  'значения; в 2024 году его купила ГК «Киевская площадь» у ГК «Галс-Девелопмент».'),
    ('gad5c199b', 'Оператор коворкингов WeWork в России (четыре площадки в Москве, около 18 тыс. кв. м); в 2024 году '
                  'все доли купило ООО «Спейс 1» (Space 1), общество переименовано в ООО «Спейс 1 Джет».'),
    ('gfb064332', 'Инвестиционная компания Евгения Зальцмана и Андрея Кондратюка; в 2024 году купила сервис нативной '
                  'рекламы в Telegram Telega.in.'),
    ('g2ba29ec2', 'Сервис размещения нативной рекламы у блогеров в Telegram (ООО «Телекот»), запущен холдингом Mirafox в '
                  '2016 году; в 2024 году его купил Ultimate Capital.'),
    ('g4368835d', 'Сеть сервисных офисов Space 1 (ООО «Спейс 1»), запущенная в 2019 году как проект O1 Properties; по '
                  'СПАРК, в 2024 году 95% компании принадлежало Петру Букину.'),
]
# Правовая форма сторон (находка party_legal_form): party_legal_names.py --write в репетиции не дозвался до реестра
# (сброс соединения) у двух профилей — имя с формой по строке реестра из досье reread_queue.py.
LEGAL = [
    ('g67ec9e45', 'АО «Фирма «Агрокомплекс» им. Н. И. Ткачева»'),   # АО ФИРМА "АГРОКОМПЛЕКС" ИМ. Н.И.ТКАЧЕВА, ИНН 2328000083
    ('g631adee6', 'АО НТЦ «Модуль»'),                                # АО НТЦ "МОДУЛЬ", ИНН 7714009178
    ('gdccff9b3', 'АО «НПО «КИС»»'),                                 # АО "НПО "КИС", ИНН 9705178310
    ('gf0ac5fc7', 'ООО «Газпромбанк-инвест»'),                       # ООО "ГАЗПРОМБАНК-ИНВЕСТ", ИНН 7612031791
    ('g4368835d', 'ООО «Спейс 1»'),                                  # ООО "СПЕЙС 1", ИНН 9710076201
    ('g356c40a0', 'АО «Уфанет»'),                                    # Ъ 6745706: «АО «Уфанет» создано в 2005 году»
    ('g8b1870bc', 'АО «Салаватстекло»'),                             # АО "САЛАВАТСТЕКЛО", ИНН 0266004050
    ('g71229bfd', 'ООО «Агро Эко»'),                                 # ООО "АГРО ЭКО", ИНН 5836657101 (запись партии: реестр не ответил)
]
PROFILES = [
    ('g78c042b5', 'молочный завод в ст. Медведовской', 'Медведовский молочный завод'),
    ('g85f1b0b8', 'ООО «ЭЙЧ-ЭС-БИ-СИ БАНК »', 'ООО «Эйч-эс-би-си Банк (РР)»'),
]


def get(card, field):
    cur = card
    for p in field.split('.'):
        cur = cur.get(p) if isinstance(cur, dict) else None
    return cur


def put(card, field, value):
    parts = field.split('.')
    cur = card
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    cur[parts[-1]] = value


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))          # перечитано прямо перед записью
    by = {d['id']: d for d in data['deals']}
    changed = 0
    for cid, field, old, new, quote, url in DEALS:
        card = by[cid]
        cur = get(card, field)
        if cur == new:
            print('уже применено: %s %s' % (cid, field))
            continue
        assert cur == old, '%s %s: в базе %r, ожидали %r' % (cid, field, cur, old)
        put(card, field, new)
        fact_edit_guard.log(card, field, new, quote, url, BY)
        print('%s %s: %r -> %r' % (cid, field, old, new))
        changed += 1
    for cid, old, new in PROFILES:
        co = data['companies'][cid]
        if co.get('name') == new:
            print('уже применено: профиль %s' % cid)
            continue
        assert co.get('name') == old, 'профиль %s: %r' % (cid, co.get('name'))
        co['name'] = new
        print('профиль %s: %r -> %r' % (cid, old, new))
        changed += 1
    for cid, desc in DESCS:
        co = data['companies'][cid]
        if co.get('desc') == desc:
            print('уже применено: описание %s' % cid)
            continue
        co['desc'] = desc
        print('описание %s' % cid)
        changed += 1
    for cid, short in LEGAL:
        co = data['companies'][cid]
        if co.get('legal_short'):
            print('уже есть legal_short: %s %r' % (cid, co['legal_short']))
            continue
        co['legal_short'] = short
        print('legal_short %s: %r' % (cid, short))
        changed += 1
    if write and changed:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('записано: %d' % changed)
    elif not write:
        print('сухой прогон: %d правок; запись — --write' % changed)


if __name__ == '__main__':
    main('--write' in sys.argv)
