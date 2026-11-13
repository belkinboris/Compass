# -*- coding: utf-8 -*-
"""Вычитка-марафон 13 ноября 2026, партия m236 (часть 2): правки, которые review.py не принимает.

Статьи открыты заново (curl) и сохранены save_source.py (day 2026-11-12_m236).

g0be89c20 (Elari): покупатель — diHouse (New Retail, 01.02.2024: «Компания diHouse (входит в группу
  ЛАНИТ)… приобрела российский бизнес ELARI»), а стоял профиль группы «Ланит» с юрлицом
  ООО «Л Венчурс» (это Lanit Ventures, к сделке отношения не имеет) — сторона текстом ООО «ДиХаус»
  (участник ООО «Элари Айти» по ЕГРЮЛ); 1 февраля — день статьи «Известий», дня сделки нет — дата
  годом; «сам бренд» — разговорно.
c51d0bb64 (ВТБ / WB Банк): заголовок по стандарту; предмет назван — миноритарная доля в WB Банке и
  финтех-активах RWB (Коммерсантъ, слова первого зампреда ВТБ Дмитрия Пьянова).
c76599765 (Райкин Plaza Hotel): статуса не было — «Обсуждается» (объект выставлен на продажу,
  покупателя нет); 650 млн ₽ — запрашиваемая цена объявления, а не цена сделки: в sum «Не раскрыта»,
  цифра в eco.val и заголовке («выставлена на продажу за N ₽»); предмет назван.
c36556448 (Библио-Глобус): eco.share — перечень продавцов вместо доли; продавали долю в ООО.
cad103bca (Invest AG / РКС): заголовок по стандарту; в extra — чужая сделка (Anapolis Residence и
  Ava Group), снята.
gad241bb3 (Новамедика Иннотех): «сам Бабий» — разговорно.

    python3 pipeline/archive/2026-11/reread_oneoff_m236b.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_m236b', '2026-11-13'
NR = 'https://new-retail.ru/novosti/retail/dihouse_priobrela_rossiyskiy_biznes_elari/'
CN = 'https://www.comnews.ru/content/231358/2024-02-01/2024-w05/1009/chasnoe-delo-izrailskiy-razrabotchik-gadzhetov-elari-prodal-aktivy-rf'
IFX = 'https://www.kommersant.ru/doc/8910238'
FD = 'https://www.frontdesk.ru/news/raykin-plaza-hotel-ishchet-novogo-hozyaina'
KB = 'https://www.kommersant.ru/doc/7312900'
KR = 'https://www.kommersant.ru/doc/6998296'
VN = 'https://www.vedomosti.ru/business/articles/2025/10/19/1148112-rosnano-prodala-ploschadku'

GD = None
EDITS = [
    ('g0be89c20', 'title', 'ГК «Ланит» купила российские активы израильской Elari', 'diHouse купил российский бизнес Elari',
     'Компания diHouse (входит в группу ЛАНИТ)', NR, None),
    ('g0be89c20', 'buyer', 'gb5bc9e57', None,
     'Компания diHouse (входит в группу ЛАНИТ) — покупатель; профиль группы «Ланит» с юрлицом ООО «Л Венчурс» к сделке не относится',
     NR, None),
    ('g0be89c20', 'buyer_name', GD, 'ООО «ДиХаус»',
     'Компания diHouse (входит в группу ЛАНИТ); ЕГРЮЛ, ООО «Элари Айти» (ИНН 9717153367): участник ООО «ДИХАУС» 99,99%',
     NR, None),
    ('g0be89c20', 'date', '2024-02-01', '2024',
     'Известия 01.02.2024: «Структуры одного из крупнейших в РФ IT-холдингов, "Ланита", купили российский бизнес» — день сделки не назван',
     CN, None),
    ('g0be89c20', 'eco.context',
     'сам бренд Elari и его международный бизнес остаются за прежними владельцами.', 
     'бренд Elari и его международный бизнес остаются за прежними владельцами.',
     'Компания diHouse (входит в группу ЛАНИТ)', NR, 'SUB'),
    ('c51d0bb64', 'title', 'Партнерство Wildberries и ВТБ по развитию WB Банка', 'ВТБ собирается купить долю в WB Банке',
     'сделке по покупке миноритарной доли в WB-банке и финтех-активах', IFX, None),
    ('c51d0bb64', 'asset', None, 'Миноритарная доля в WB Банке и финтех-активах группы RWB',
     'сделке по покупке миноритарной доли в WB-банке и финтех-активах', IFX, None),
    ('c76599765', 'status', None, 'Обсуждается',
     'Фонд поддержки и развития культуры имени Аркадия Райкина выставил на продажу отель Райкин Plaza Hotel 4* в Москве',
     FD, None),
    ('c76599765', 'asset', None, 'Гостиница «Райкин Plaza Hotel» (Москва, Шереметьевская улица)',
     'Гостиница Райкин Plaza Hotel расположена в районе метро Марьина роща', FD, None),
    ('c76599765', 'sum', '650 млн ₽', 'Не раскрыта',
     'запрашиваемая цена - 0,65 миллиарда рублей — цена объявления, а не цена сделки', FD, 'sum'),
    ('c76599765', 'eco.sum', '650 млн ₽', 'Не раскрыта',
     'запрашиваемая цена - 0,65 миллиарда рублей — цена объявления, а не цена сделки', FD, None),
    ('c76599765', 'sum_basis', 'auction_start', None,
     'запрашиваемая цена - 0,65 миллиарда рублей', FD, None),
    ('c76599765', 'accepted_notes.searched', None,
     'Искали покупателя и итог продажи 13 ноября 2026: поиск «Райкин Plaza» продажа (RU), «фонд Райкина» '
     'недвижимость, Коммерсантъ, РБК Недвижимость, площадка Сбербанк-АСТ, Frontdesk.ru — других сообщений '
     'о продаже нет, покупатель не назван.',
     'Фонд поддержки и развития культуры имени Аркадия Райкина выставил на продажу отель', FD, None),
    ('c36556448', 'eco.share', 'Продавцы: Юлия Туголукова (77,25%) и Борис Есенькин (22,75%).',
     'Доля в ООО «Торговый дом «Библио-Глобус»»',
     'ЕГРЮЛ, ООО «Торговый дом «Библио-Глобус»» (ИНН 7701023055): участники Туголукова Юлия Борисовна 77,25%, '
     'Есенькин Борис Семенович 22,75%', KB, None),
    ('cad103bca', 'title',
     'Invest AG и «РКС Девелопмент» могут обменяться долями в проектах в Нахабино и Булатниково',
     '«РКС Девелопмент» может купить у Invest AG 80% «РКС-Булатниково»',
     'Invest AG и ГК «РКС Девелопмент» планируют поделить совместные проекты', KR, None),
    ('cad103bca', 'extra',
     'По неофициальным данным, Invest AG собирается продать следующие очереди ЖК Anapolis Residence под Анапой '
     'краснодарскому застройщику Ava Group Вагана Арутюняна; в Ava Group сказали, что такой информации у них нет.',
     '', 'другая сделка Invest AG (Anapolis Residence) — не об этой сделке', KR, None),
    ('gad241bb3', 'eco.context', 'но сам Бабий связь', 'но Владимир Бабий связь',
     'Роснано продало площадку', VN, 'SUB'),
]
DATE_BASIS = {}


def get(c, path):
    cur = c
    for k in path.split('.'):
        cur = (cur or {}).get(k)
    return cur


def put(c, path, val):
    ks = path.split('.')
    cur = c
    for k in ks[:-1]:
        cur = cur.setdefault(k, {})
    cur[ks[-1]] = val


def apply(data):
    by = {d['id']: d for d in data['deals']}
    n = 0
    for cid, path, old, new, quote, url, retract in EDITS:
        c = by[cid]
        if retract == 'SUB':
            cur = get(c, path)
            if new in cur and old not in cur:
                continue
            assert cur.count(old) == 1, (cid, path)
            new_full = cur.replace(old, new)
            put(c, path, new_full)
            fact_edit_guard.log(c, path, new_full, quote, url, BY, DAY)
            n += 1
            continue
        if get(c, path) == new:
            continue
        assert get(c, path) == old, (cid, path, get(c, path))
        if new is None and path in ('buyer', 'sum_basis'):
            c.pop(path, None)
        else:
            put(c, path, new)
        if retract:
            lst = c.setdefault('retracted', {}).setdefault(retract, [])
            if old not in lst:
                lst.append(old)
        fact_edit_guard.log(c, path, new, quote, url, BY, DAY)
        n += 1
    for cid, basis in DATE_BASIS.items():
        if by[cid].get('date_basis') != basis:
            by[cid]['date_basis'] = basis
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
