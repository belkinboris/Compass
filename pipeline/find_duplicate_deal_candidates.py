# -*- coding: utf-8 -*-
"""Кандидаты в дубли карточек сделок — по структурным полям, а не по заголовку.

ЗАЧЕМ. Тест `test_no_duplicate_deal_cards` ловит дубль по ДВУМ общим названиям
в кавычках при одной сумме — форма, которая не видит «Продажа Первой образцовой
типографии Денису Избрехту» рядом с «Росимущество продало 100% акций АО «Первая
образцовая типография» Денису Избрехт» (аудит перед бетой, раунд 2, 6 сентября
2026). Дубли рождались не от небрежности, а от того, что карточку заводили по
заметке владельца или по бэкфиллу mergers.ru, а проверка на дубль шла по id и
заголовку (см. CLAUDE.md, «Проверка на дубль по заголовку — не то же самое, что
поиск по базе»). Общий ПРОФИЛЬ предмета сделки — признак надёжнее любого
сравнения слов: у 13 из 17 пар, найденных этим правилом, предмет был одним и тем
же профилем при разных заголовках.

ПРАВИЛО. Две карточки — кандидат, если у них один профиль предмета
(`target`/`asset_id`) и при этом либо один год, либо одна сумма; или один
профиль покупателя при одной сумме и одном годе. Это СПИСОК ДЛЯ ЧТЕНИЯ, не
приговор: две покупки по 25% одной компании в одном году — консолидация, а не
дубль (ВЭБ.РФ/«Просвещение»), два раунда одного фонда на одну сумму — разные
сделки («ТилТех»). Прочитанные и признанные разными пары записываются в
`NOT_DUPLICATES` с причиной — иначе следующий прогон переоткроет их за токены.
Слияние — `pipeline/merge_duplicate_deals_batch.py` по файлу спецификаций.

Запуск:
    python3 pipeline/find_duplicate_deal_candidates.py         # печатает пары
"""
import json
import re
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / 'static' / 'data' / 'deals_promoted.json'

# Пары, прочитанные глазами и признанные РАЗНЫМИ сделками (порядок id не важен).
NOT_DUPLICATES = {
    frozenset({'gf9932079', 'gd3ba954d'}): 'две покупки по 25% «Просвещения» в 2025 году: у «Сбера» (март) и у «Инвест ПРО» (август)',
    frozenset({'g942865d3', 'g88304d3a'}): 'УК «Первая»: 1 млрд ₽ в «Интерскол» и 1 млрд ₽ в MVS — разные предметы и даты',
    frozenset({'gff35947d', 'g47844a63'}): '«ТилТех Капитал»: 200 млн ₽ в Noun и 200 млн ₽ в DocMed — разные предметы',
    frozenset({'g5eb6ff22', 'g6a4b0a2a'}): '«Дело»: «русская рулетка» Росатома и более ранний меморандум Шишкарёва с «Ростехом» (см. CLAUDE.md)',
    frozenset({'g139db8c2', 'g26608f96'}): '«Аквариус»: S8 Capital/«МТ-Интеграция» и версия про Махмудова — не слиты намеренно (см. CLAUDE.md)',
    frozenset({'g76f31c63', 'gb31c796f'}): '«Ла дача Астрахань»: продажа Дубовицкой и её же перепродажа «Акашевской» через три недели',
    frozenset({'g87234072', 'gd1130c05'}): 'завод Volkswagen в Калуге: несостоявшийся интерес АФК «Система»/Allur и продажа бизнеса VW другому покупателю',
    frozenset({'g0410fde2', 'g68a112bd'}): '«Медскан»: Сбербанк Инвестиции в «Медскан лаб» и Русатом Хэлскеа в самой группе — разные покупатели и предметы',
    frozenset({'g38ce6e22', 'ga7232033'}): '«Деметра-Холдинг»: выход Marathon Group и продажа 45% ВТБ — разные продавцы',
    frozenset({'g12370211', 'ga133cd89'}): '«Кассир.ру»: 25% АБ Холдинга и 10% VK — разные покупатели и даты',
    frozenset({'g7533d350', 'gdaf7fdda'}): '«Мой девайс»: два раунда 2021 года от разных инвесторов',
    frozenset({'g576de71f', 'gcef50cb7'}): '«Моторика»: раунд 900 млн ₽ (июнь 2024) и вход Газпромбанка (декабрь 2024)',
    frozenset({'g3875e8f5', 'g4444b396'}): 'ТВК «Тишинка»: 83,4% и 16,6% — два пакета у Capital Group',
    frozenset({'g22000f22', 'g50c555a0'}): '«Детский мир»: покупка 29,9% консорциумом Зуева и вся программа выкупа акций',
    frozenset({'g22000f22', 'g76159e00'}): '«Детский мир»: консорциум Зуева и продажа 10% Кленовым — разные продавцы',
    frozenset({'g50c555a0', 'g76159e00'}): '«Детский мир»: программа выкупа и продажа 10% Кленовым',
    frozenset({'g2197ed53', 'gc9461b5c'}): '«Медскан»: неизвестный инвестор и выход Сбербанк Инвестиций — разные стороны',
    frozenset({'g7b4be1c4', 'gc9461b5c'}): '«Медскан»: предложение Харитонина и выход Сбербанк Инвестиций',
    frozenset({'g2197ed53', 'g7b4be1c4'}): '«Медскан»: неизвестный инвестор (допэмиссия) и предложение Харитонина выкупить долю Туголукова',
    frozenset({'ga46c5b15', 'gcf05509a'}): 'АФК «Система»: структурная сделка с ВТБ и IPO Cosmos/«Медси»',
    frozenset({'g46cc9712', 'g64831887'}): 'банк «Точка» и ГК «Зеленая точка» — разные компании (предмет второй карточки исправлен)',
    frozenset({'g54879bcb', 'gec65b08d'}): 'HeadHunter: SPO акционеров и инвестиция в YouDo',
    frozenset({'g150f6855', 'g64141daa'}): '«Клиентский сервис» («Самолет») и «Домиленд» (Яндекс)',
    frozenset({'g0591604d', 'gdd45b5d5'}): 'фонд «Восход»: учреждение фонда «Интерросом» (2022) и продажа его УК менеджменту (2023)',
    frozenset({'g81a766ac', 'g97d9fa60'}): '«Агро-Белогорье»: 25% по решению суда за номинал (сентябрь 2024) и 100% по мировому соглашению (ноябрь) — два юридически разных шага',
    frozenset({'g46cc9712', 'gcd2b0954'}): 'банк «Точка»: продажа 90,01% «Трастом» консорциуму (август 2023) и отдельная покупка 25% VK у участников консорциума (ноябрь)',
}

PLACEHOLDER = re.compile(r'^\s*(—|-|не раскрыт[а-яё]*|публично не сообщалось|нет данных)?\s*\.?\s*$', re.I)


def norm_sum(value):
    if not value or PLACEHOLDER.match(str(value)):
        return None
    return re.sub(r'[^0-9a-zа-яё₽$€]+', '', str(value).lower())


def year_of(value):
    m = re.match(r'(\d{4})', str(value or ''))
    return m.group(1) if m else None


def candidates(deals):
    by_asset, by_buyer = defaultdict(list), defaultdict(list)
    for d in deals:
        asset = d.get('target') or d.get('asset_id')
        if asset:
            by_asset[asset].append(d)
        if d.get('buyer'):
            by_buyer[d['buyer']].append(d)
    found = {}
    for group in by_asset.values():
        for a, b in combinations(group, 2):
            same_year = year_of(a.get('date')) and year_of(a.get('date')) == year_of(b.get('date'))
            same_sum = norm_sum(a.get('sum')) and norm_sum(a.get('sum')) == norm_sum(b.get('sum'))
            if same_year or same_sum:
                found[frozenset({a['id'], b['id']})] = 'один предмет, ' + ('один год' if same_year else 'одна сумма')
    for group in by_buyer.values():
        for a, b in combinations(group, 2):
            same_year = year_of(a.get('date')) and year_of(a.get('date')) == year_of(b.get('date'))
            same_sum = norm_sum(a.get('sum')) and norm_sum(a.get('sum')) == norm_sum(b.get('sum'))
            if same_year and same_sum:
                found.setdefault(frozenset({a['id'], b['id']}), 'один покупатель, один год, одна сумма')
    return found


def fingerprint(d):
    """Что считается существенным изменением карточки после чтения: заголовок,
    дата, сумма, стороны и предмет. Изменилось — пара читается заново
    (замечание рецензента, 6 сентября 2026: разобранные не-дубли перепроверять
    при существенном изменении карточек)."""
    return (d.get('title'), d.get('date'), d.get('sum'), d.get('buyer'), d.get('buyer_name'),
            d.get('seller_id'), d.get('seller'), d.get('target'), d.get('asset_id'))


def load_read_state():
    path = Path(__file__).resolve().parent / 'gold' / 'non_duplicates_seen.json'
    return path, (json.load(open(path, encoding='utf-8')) if path.exists() else {})


def main():
    data = json.load(open(DATA, encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    found = candidates(list(deals.values()))
    seen_path, seen = load_read_state()
    changed = {}
    for pair in NOT_DUPLICATES:
        key = '|'.join(sorted(pair))
        now = {i: list(fingerprint(deals[i])) for i in sorted(pair) if i in deals}
        if key in seen and seen[key] != now:
            changed[pair] = 'карточка изменилась после чтения — пару перечитать'
        seen.setdefault(key, now)
    json.dump(seen, open(seen_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    fresh = {pair: why for pair, why in found.items() if pair not in NOT_DUPLICATES}
    fresh.update({pair: why for pair, why in changed.items() if pair in found})
    stale = [pair for pair in NOT_DUPLICATES if not pair <= set(deals)]
    for pair, why in sorted(fresh.items(), key=lambda kv: sorted(kv[0])):
        a, b = sorted(pair)
        print(f'{a} / {b} — {why}')
        for i in (a, b):
            d = deals[i]
            print(f'    {i}: {d.get("date")} · {d.get("sum") or "—"} · {d["title"][:90]}')
    print(f'\nКандидатов: {len(fresh)} (ещё {len(found) - len(fresh)} прочитаны и признаны разными сделками)')
    if stale:
        print('В NOT_DUPLICATES есть id, которых нет в базе:', [sorted(p) for p in stale])
    return 0


if __name__ == '__main__':
    sys.exit(main())
