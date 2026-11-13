# -*- coding: utf-8 -*-
"""Вычитка, партия m074 (12 ноября 2026): правки, которые не ложатся в таблицу FIXES.

Заголовки по стандарту (title_standard.py), даты по дню события, стороны и предмет
(профили), источники, снятые лишние поля. Каждая правка факта — с цитатой источника
(fact_edit_guard.log). Проза — через write_card.py (файлы written_*_m074.py).

    python3 pipeline/archive/2026-11/reread_oneoff_m074.py           # сухой прогон
    python3 pipeline/archive/2026-11/reread_oneoff_m074.py --write   # запись

Повторный запуск ничего не ломает: правка, которая уже стоит, пропускается.
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'вычитка m074'
MISSING = object()

FONT = 'https://www.fontanka.ru/2024/12/20/74907050/'
NR1 = 'https://new-retail.ru/novosti/retail/peterburgskiy_trts_zhemchuzhnaya_plaza_arestovan_po_resheniyu_suda/'
KOM1 = 'https://www.kommersant.ru/doc/7329390'
KOM2 = 'https://www.kommersant.ru/doc/7330299'
ZEL = 'https://datanewton.ru/api/v2/history?ogrn=1065050019605&startDate=2000-01-01&attributes=OWNERS'
RET = 'https://www.retail.ru/news/set-selgros-mozhet-okonchatelno-zakryt-biznes-v-rf-15-iyulya-2026-279934/'
KOM3 = 'https://www.kommersant.ru/doc/7552134'
RET2 = 'https://www.retail.ru/news/osnovnoy-vladelets-seti-aromatnyy-mir-perestal-byt-uchreditelem-kompanii-7-aprelya-2025-263221/'
DVIZH = 'https://dvizhenie.ru/media/2065/rosteh-prodal-aktivy-s-nedvizhimostyu-na-175-tys-kv-m-v-moskve-chastnomu-investoru'
TADV = 'https://www.tadviser.ru/index.php/Компания:Спецмагнит,_ТД'
VED_SM = 'https://www.vedomosti.ru/realty/articles/2024/08/07/1054260-struktura-rosteha-vistavila-na-prodazhu-aktivi-proizvoditelya-magnitov-spetsmagnit'
PRIME = 'https://1prime.ru/20240813/prodazha-850864699.html'
NR2 = 'https://new-retail.ru/novosti/retail/srv_group_mozhet_sorvat_prodazhu_trts_zhemchuzhnaya_plaza/'

# (id карточки, поле через точку, старое значение, новое значение, цитата, адрес)
# Новое MISSING — снять ключ. Цитата пустая — правка не факта (проза, служебное поле).
EDITS = [
    # c31a23b22 — SRV продала 50% «Жемчужной плазы» Central Properties
    ('c31a23b22', 'title',
     'Урегулирование спора между «Проспект групп», SRV Group и Central Properties за долю в ТРЦ «Жемчужная плаза»',
     'Central Properties купил 50% ТРЦ «Жемчужная плаза» у SRV',
     'Финский девелопер SRV продал последний актив в России компании Central Properties.', FONT),
    ('c31a23b22', 'date', '2024-12-01', '2024-12-20',
     'В рамках сделки, заключенной 20 декабря 2024 года, SRV продала свой последний актив в России', FONT),
    ('c31a23b22', 'target', MISSING, 'g3a6a6971',
     'SRV продала свой последний актив в России — 50-процентную долю в торговом центре „Жемчужная Плаза“ в Санкт-Петербурге', FONT),
    # cfdc0e962 — сорвавшаяся продажа доли SRV компании «Гео»
    ('cfdc0e962', 'title',
     'Судебный спор между «Гео» и владельцами ТЦ «Жемчужная плаза» из-за срыва продажи доли SRV Group',
     'SRV Group отказался продать 50% ТРЦ «Жемчужная плаза» компании «Гео»',
     'Именно «Гео» должна была стать покупателем доли SRV в «Жемчужной Плазе». Но уже в 2024 году финский девелопер вышел из переговоров.', FONT),
    ('cfdc0e962', 'buyer_name', MISSING, '«Гео»',
     'Покупателем доли SRV Group должна была стать фирма «Гео» (Geomare Investments Limited), связанная с девелопером из Екатеринбурга «Проспект групп».', NR1),
    ('cfdc0e962', 'seller', MISSING, 'SRV Group',
     'Финская SRV Group достигла соглашения с инвестиционной компанией Central Properties о продаже ей своей доли (50%)', NR2),
    ('cfdc0e962', 'seller_src', MISSING, 'text', '', ''),
    ('cfdc0e962', 'seller_id', MISSING, 'ge21c201f', '', ''),
    ('cfdc0e962', 'no_parties',
     'Судебный спор о сорванной продаже, а не сделка (сама продажа SRV → Central Properties — в карточке c31a23b22)',
     MISSING, '', ''),
    ('cfdc0e962', 'eco.target_fin',
     'Торговый центр построен в 2013 году, его относят к крупнейшим торговым комплексам Санкт-Петербурга. В нем работают, например, «Перекресток», «М.видео», «Детский мир», Lime и универмаг «Стокманн».',
     '—', '', ''),
    # cea87de0a — «Ароса-логистика» купила российский бизнес Selgros
    ('cea87de0a', 'title', 'Selgros продал 100% группы «Зельгрос Россия» компании «Ароса-Логистика»',
     '«Ароса-логистика» купила российский бизнес Selgros',
     'Компания «Ароса-логистика» приобрела у австрийской MCCR Beteiligungs GmbHh 100-процентную долю в группе компаний «Зельгрос Россия», владеющей гипермаркетами Selgros Cash&Carry', KOM2),
    ('cea87de0a', 'date', '2024-11-27', '2024-12-09',
     '9 декабря 2024 года: выбыл участник МЦЦР БЕТАЙЛИГУНГС ГМБХ 100.0% (10 100 000 руб.); вошел участник ООО "АРОСА-ЛОГИСТИКА" (ОГРН 1227700909743) 100.0%', ZEL),
    ('cea87de0a', 'seller', 'MCCR Beteiligungs GmbH (австрийский акционер Selgros)', 'MCCR Beteiligungs GmbH',
     'Продавцом выступает австрийская компания MCCR Beteiligungs GmbHh, получившая в 2022 году от швейцарской Coop активы ритейлера в РФ.', KOM1),
    # профиль «Selgros» реестр сопоставил с ООО «Зельгрос» — это сама покупаемая компания, а не продавец
    ('cea87de0a', 'seller_id', 'g5700b609', MISSING, '', ''),
    # cc63cf578 — продажа «Ароматного мира» не состоялась: братья Задорины разделили бизнес
    ('cc63cf578', 'title', 'Продажа сети алкомаркетов «Ароматный мир»',
     '«Севергрупп» отказался от покупки «Ароматного мира»',
     'Источник “Ъ”, близкий к Севергрупп, сообщил, что стороны действительно встречались полтора года назад по поводу возможной сделки, однако сейчас интереса к этом активу у компании нет и переговоров не ведется.', KOM3),
    # 2024-10-01 — выдуманный день; статья вышла 5 марта 2025 года, раздел бизнеса — апрель 2025 года
    ('cc63cf578', 'date', '2024-10-01', '2025',
     'Кроме того, в конце марта 2025 года из капитала «АМ ритейл» вышли София и Анна Задорины', RET2),
    ('cc63cf578', 'asset', MISSING, '«Ароматный мир»',
     'Сеть «Ароматный мир» может поменять собственника', KOM3),
    ('cc63cf578', 'seller', MISSING, 'Валерий и Павел Задорины',
     'На фоне корпоративного конфликта в сети алкомаркетов «Ароматный мир» ее собственники — братья Валерий и Павел Задорины — рассматривают возможность продажи бизнеса.', KOM3),
]

# (id, [имя, адрес]) — источник, открытый при вычитке
SOURCES = [
    ('cfdc0e962', ['Фонтанка.ру', FONT]),
    ('cfdc0e962', ['New Retail', NR1]),
    ('cfdc0e962', ['New Retail', NR2]),
    ('c31a23b22', ['New Retail', NR2]),
    ('cea87de0a', ['ЕГРЮЛ', ZEL]),
    ('cc63cf578', ['Retail.ru', RET2]),
    ('cea87de0a', ['Retail.ru', RET]),
]

# (id профиля, ключ, старое, новое)
COMPANY_EDITS = []


def get(obj, path):
    for k in path.split('.'):
        if not isinstance(obj, dict) or k not in obj:
            return MISSING
        obj = obj[k]
    return obj


def put(obj, path, value):
    keys = path.split('.')
    for k in keys[:-1]:
        obj = obj.setdefault(k, {})
    if value is MISSING:
        obj.pop(keys[-1], None)
    else:
        obj[keys[-1]] = value


def apply(data):
    import fact_edit_guard
    cards = {d['id']: d for d in data['deals']}
    comps = data['companies']
    done = 0
    for cid, field, old, new, quote, url in EDITS:
        card = cards[cid]
        cur = get(card, field)
        if cur == new:
            continue
        assert cur == old, '%s %s: в базе %r, ожидали %r' % (cid, field, cur, old)
        put(card, field, new)
        if quote and field in fact_edit_guard.FACT_FIELDS and new is not MISSING:
            fact_edit_guard.log(card, field, new, quote, url, BY)
        done += 1
        print('  %s %s: %r → %r' % (cid, field, str(old)[:70], str(new)[:70]))
    for cid, src in SOURCES:
        card = cards[cid]
        have = {s[1] for s in card.get('src') or [] if len(s) > 1} | \
               {s[1] for s in card.get('discovery_src') or [] if len(s) > 1}
        if src[1] not in have:
            card.setdefault('src', []).append(list(src))
            done += 1
            print('  %s src + %s' % (cid, src[1]))
    for pid, key, old, new in COMPANY_EDITS:
        p = comps[pid]
        cur = p.get(key, MISSING)
        if cur == new:
            continue
        assert cur == old, 'профиль %s %s: %r, ожидали %r' % (pid, key, cur, old)
        if new is MISSING:
            p.pop(key, None)
        else:
            p[key] = new
        done += 1
        print('  профиль %s %s → %r' % (pid, key, str(new)[:70]))
    return done


def main(argv):
    old = json.load(open(DATA, encoding='utf-8'))
    data = copy.deepcopy(old)
    n = apply(data)
    if not n:
        print('Уже применено.')
        return 0
    if '--write' not in argv:
        print('Сухой прогон: %d правок. Запись — с ключом --write.' % n)
        return 0
    import mass_edit_guard
    # Перечитать прямо перед записью (docs/card_editing.md).
    old = json.load(open(DATA, encoding='utf-8'))
    data = copy.deepcopy(old)
    apply(data)
    mass_edit_guard.check(old, data)
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано правок: %d' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
