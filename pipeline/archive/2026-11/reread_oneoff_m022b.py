# -*- coding: utf-8 -*-
"""Разовая часть вычитки 12 ноября 2026 (марафон, партия m022, вторая часть): то, что не ложится в FIXES.

- суммы: оценка всех крупных магазинов «Магнита» стояла ценой сделки (g829e5f99) — «Не раскрыта»;
- предмет текстом там, где его не было (g5a22a31a — терминал в Азове и элеватор в Волгодонске;
  g829e5f99 — гипермаркеты «Магнита»);
- OBI (gcdd2b6de): дата 29.04.2025 — день статьи; сделка «Гермеса» на 65% закрыта по ЕГРЮЛ 11.07.2025
  (история участников ООО «ОБИ ФЦ», Интерфакс 14.07.2025); продавец текстом стоял в родительном падеже;
- где искали покупателя «Степи» и продавцов «Топ Систем».

    python3 pipeline/archive/2026-11/reread_oneoff_m022b.py           # сухо
    python3 pipeline/archive/2026-11/reread_oneoff_m022b.py --write   # запись; повторный запуск — «уже применено»
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'reread_oneoff_m022b (вычитка 12.11.2026)'

_ST = ('Агрохолдинг «Степь» (входит в АФК «Система») выставил на продажу портовые активы, рассказали “Ъ” три '
       'источника, слышавшие о планах компании. Речь идет о зерновом терминале в порту Азова и портовом элеваторе '
       'в Волгодонске.')
_MG = ('О том, что «Лента» рассматривает возможность приобрести гипермаркеты сети «Магнит», рассказал источник “Ъ” '
       'на розничном рынке.')
_MG_VAL = ('Все супермаркеты и гипермаркеты, находящихся у «Магнита» в собственности, могут стоить около 100 млрд '
           'руб., подсчитал партнер NF Group Станислав Бибик.')
_OBI = ('Москва. 14 июля. INTERFAX.RU - ООО "Гермес" закрыло сделку по приобретению 65% в трех юрлицах сети '
        'строительных гипермаркетов OBI, говорится в данных ЕГРЮЛ. [ЕГРЮЛ, ООО «ОБИ ФЦ», ИНН 7710439772: '
        '2025-07-11 доля ООО «ГЕРМЕС» 24,99 → 90%]')
_OBI_SELL = ('По их информации, бизнесмен уже получил долю в компании, выкупив ее у структур ХК «Синдика» Арсена '
             'Канокова. … Президент «Синдики» Олег Эскиндаров пояснил “Ъ”, что 25% в компании проданы новому стратегическому '
             'инвестору, не раскрыв имя покупателя и деталей сделки.')

# (id, поле, старое, новое, цитата, адрес)
_SET = [
    ('g5a22a31a', 'asset', None, 'Зерновой терминал в порту Азова и портовый элеватор в Волгодонске', _ST,
     'https://www.kommersant.ru/doc/7923855'),
    ('g829e5f99', 'asset', None, 'Гипермаркеты «Магнита»', _MG, 'https://www.kommersant.ru/doc/7777609'),
    ('g829e5f99', 'sum', '50–100 млрд ₽ (по оценке)', 'Не раскрыта', _MG_VAL, 'https://www.kommersant.ru/doc/7777609'),
    ('g829e5f99', 'eco.sum', '50–100 млрд ₽ (по оценке)', 'Не раскрыта', None, None),
    ('gcdd2b6de', 'date', '2025-04-29', '2025-07-11', _OBI, 'https://www.interfax.ru/business/1036100'),
    ('gcdd2b6de', 'date_basis', None, 'registry', None, None),
    ('gcdd2b6de', 'seller', 'Синдики', 'ХК «Синдика»', _OBI_SELL, 'https://www.kommersant.ru/doc/7693710'),
]

_RETRACT = [
    ('g829e5f99', 'sum', '50–100 млрд ₽ (по оценке)'),
]

_PROFILE = []
# Имя с правовой формой по ЕГРЮЛ (досье партии: АО АГРОХОЛДИНГ "СТЕПЬ" ИНН 7708813052; " ОБИ ФЦ" ООО
# ИНН 7710439772) — party_legal_names.py формы не вывел.
_LEGAL = [
    ('g63ba8735', 'АО «Агрохолдинг «Степь»»'),
    ('g79f93ccb', 'ООО «ОБИ ФЦ»'),
    ('ge0a3081f', 'ООО «СЛ Софт»'),
    ('gc4f56cd1', 'АО «Топ Системы»'),  # fns_registry: ИНН 7726601967; так пишут tflex.ru и РБК   # fns_registry: ООО «СЛ СОФТ», ИНН 9725114756
]

_NOTES = {
    'g5a22a31a': {
        'no_profile': {'buyer': (
            'Покупатель не найден: «Коммерсантъ» (29.07.2025), ATI.su и РБК Ростов пишут, что «Степь» не сошлась в '
            'цене с претендентами; сообщений о продаже терминала в Азове и элеватора в Волгодонске после июля 2025 '
            'года в открытых источниках нет.')},
        'searched': ['kommersant.ru/doc/7923855', 'news.ati.su (30.07.2025)',
                     'rostov.rbc.ru/rostov/freenews/6888ca1e9a7947c2401948f6 (не открылся)',
                     'party_legal_names.py g5a22a31a (АО «Агрохолдинг «Степь»)',
                     'WebSearch: Степь продала зерновой терминал Азов элеватор Волгодонск покупатель']},
    'gec433848': {
        'no_profile': {'seller': (
            'Продавец не назван: по РБК (пересказ Mergers.ru), на декабрь 2023 года АО «Топ Системы» принадлежало '
            'шести физлицам (Баранов, Бикулов, Ефремов, Козлов, Ксенофонтов, Кураскин, по 16–17%), но кто из них '
            'продал акции «Росатому», не сообщалось; у АО реестр акционеров не открыт. «Росатом» сделку не '
            'подтвердил.')},
        'searched': ['rbc.ru/technology_and_media/05/03/2025 (401; пересказ mergers.ru в data/inbox/raw)',
                     'tflex.ru (новость о меморандуме «Гринатома» и «Топ Систем»)',
                     'party_legal_names.py gec433848 (реестр недоступен)',
                     'WebSearch: Росатом 49% Топ Системы продавец акционеры']},
}


def _get(card, field):
    o = card
    for p in field.split('.'):
        o = o.get(p) if isinstance(o, dict) else None
    return o


def _set(card, field, value):
    parts = field.split('.')
    o = card
    for p in parts[:-1]:
        o = o.setdefault(p, {})
    o[parts[-1]] = value


def apply(data):
    deals = {d['id']: d for d in data['deals']}
    n = 0
    for cid, field, old, new, quote, url in _SET:
        card = deals[cid]
        cur = _get(card, field)
        if cur == new:
            continue
        assert cur == old, (cid, field, cur)
        _set(card, field, new)
        if quote:
            fact_edit_guard.log(card, field, new, quote, url, BY)
            if field == 'sum':                       # eco.sum — то же значение, та же цитата
                fact_edit_guard.log(card, 'eco.sum', new, quote, url, BY)
        n += 1
    for cid, field, value in _RETRACT:
        lst = deals[cid].setdefault('retracted', {}).setdefault(field, [])
        if value not in lst:
            lst.append(value)
            n += 1
    for comp, field, old, new in _PROFILE:
        c = data['companies'][comp]
        if old in (c.get(field) or ''):
            c[field] = c[field].replace(old, new)
            n += 1
        else:
            assert new in (c.get(field) or ''), (comp, c.get(field))
    for comp, short in _LEGAL:
        c = data['companies'][comp]
        if c.get('legal_short') != short:
            assert not c.get('legal_short'), (comp, c.get('legal_short'))
            c['legal_short'] = short
            n += 1
    for cid, notes in _NOTES.items():
        acc = deals[cid].setdefault('accepted_notes', {})
        for k, v in notes.items():
            if acc.get(k) != v and not (isinstance(v, dict) and all(acc.get(k, {}).get(a) == b for a, b in v.items())):
                if isinstance(v, dict):
                    acc.setdefault(k, {}).update(v)
                else:
                    acc[k] = v
                n += 1
    return n


if __name__ == '__main__':
    data = json.load(open(DATA, encoding='utf-8'))
    n = apply(data)
    print('Изменений: %d' % n if n else 'Уже применено.')
    if '--write' in sys.argv and n:
        fresh = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
        apply(fresh)
        json.dump(fresh, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано.')
    elif '--write' not in sys.argv:
        print('Сухой прогон. Запись — с ключом --write.')
