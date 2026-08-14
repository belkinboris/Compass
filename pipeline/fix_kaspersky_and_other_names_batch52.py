# -*- coding: utf-8 -*-
"""Пятьдесят вторая партия: дублирующий профиль + три обрезанных имени
+ 8 описаний.

НАЙДЕНО.
  - `g2700fefa` «сама компания» — у сделки gf174262b («Лаборатория
    Касперского» выкупила долю сооснователя Алексея Де-Мондерика) поле
    `buyer` указывало на профиль-заглушку «сама компания» (буквально
    вырезано из текста «покупатель — сама компания»), хотя это ТА ЖЕ
    «Лаборатория Касперского», которая уже правильно стоит в `target`
    (`g623b934f`) — классический дубль под мусорным именем. ПЕРВАЯ
    ПОПЫТКА перенести `buyer` на сам профиль «Лаборатория Касперского»
    провалила `test_one_company_holds_one_role_in_a_deal` — компания не
    может быть одновременно `buyer` и `target` одной сделки. Проверил
    два похожих байбэка уже в базе (`geb18dcad` ТМК, `g499ed10e` Банк
    «Санкт-Петербург») — в обоих заполнена ТОЛЬКО ОДНА сторона (или
    `buyer`, или `target`), вторая оставлена `None`. Тот же приём здесь:
    `buyer` очищен (`None`), `target` остаётся «Лаборатория Касперского»
    — сделка и так однозначно про эту компанию, дублирующий буквальный
    `buyer` был избыточен. Профиль-заглушка удалён (единственная ссылка
    на него была эта же сделка).
  - `gf0644c08` «PIPE-инвестиция» — предмет сделки g688f1f79 (PIPE-
    инвестиция $50 млн в Nexters при слиянии со SPAC Kismet Acquisition
    One, выход на Nasdaq под тикером GDEV); имя обрезано до типа
    инвестиции. Переименован в «Nexters (GDEV)».
  - `ga7a23344` «Туристический» — предмет сделки g82d1f224 («Туристический
    стартап Finalprice привлёк $1 млн...»); имя обрезано до
    прилагательного. Переименован в «Finalprice».
  - `g152f9c1d` «Сахалине-2» — предмет сделки g6d74bc39 (продажа доли
    Shell в «Сахалине-2»); имя в предложном падеже, вырезано без
    согласования. Переименован в именительный «Сахалин-2» (отдельно от
    уже существующего в базе профиля оператора проекта «Сахалинская
    энергия», `g21a1f3ce»).

Все переименования — на месте (тот же id, та же единственная сделка),
не смена личности профиля; удаление касается только явного дубля с
единственной ссылкой.

Плюс 8 описаний обычным G2-кандидатам.

Запуск:
    python3 pipeline/fix_kaspersky_and_other_names_batch52.py            # сухой прогон
    python3 pipeline/fix_kaspersky_and_other_names_batch52.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

KASPERSKY_DEAL_ID = 'gf174262b'
DUP_ID = 'g2700fefa'
DUP_NAME = 'сама компания'
KASPERSKY_ID = 'g623b934f'

RENAMES = {
    'gf0644c08': ('PIPE-инвестиция', 'Nexters (GDEV)'),
    'ga7a23344': ('Туристический', 'Finalprice'),
    'g152f9c1d': ('Сахалине-2', 'Сахалин-2'),
}
NEW_ALIASES = {
    'gf0644c08': ['nexters', 'gdev'],
    'ga7a23344': ['finalprice'],
    'g152f9c1d': ['сахалин-2'],
}

DESCRIPTIONS = {
    'g5dcb62e3': 'Петербургская УК; в 2024 году купила 15 российских и '
                 'постсоветских предприятий литовской Vičiūnų grupė '
                 '(бренд Vici) за более 100 млн €.',
    'gdd6f9260': 'Сеть салонов красоты, совладелец Денис Цыпулев '
                 'выступил бизнес-ангелом; в 2019 году участвовал в '
                 'раунде Amlab.me на 27,5 млн ₽.',
    'g62dd02d2': 'СП Т-Технологий и Интерроса; в 2025 году купило 25% '
                 'акций Selectel у структур Мирилашвили и Вермишяна.',
    'g9cdc6760': 'Нефтегазовый проект на мелководном шельфе Мексиканского '
                 'залива; в 2021 году 50% операторской доли купил '
                 'ЛУКОЙЛ у обанкротившейся Fieldwood Energy.',
    'g73f27a32': 'Нефтесервисный стартап; в 2021 году привлёк $9,3 млн '
                 'во втором раунде от Runtech Ventures и Phystech '
                 'Ventures.',
    'g5f515899': 'Венчурный фонд Артёма Инютина и Германа Каплуна; в '
                 '2021 году возглавил раунд на $1,5 млн в эстонский '
                 'SaaS-стартап Postoplan.',
    'g870d935d': 'Владеет никелево-медно-сульфидным проектом Кун-Манье; '
                 'в 2023 году структура Владислава Свиблова купила его '
                 'у Amur Minerals Corporation за $35 млн.',
    'gc9913f2a': 'Московская компания, бенефициар с 2025 года — Марат '
                 'Тякин; в 2025 году купила у ТМК 96% Челябинского '
                 'завода металлоконструкций за 5,2 млрд ₽.',
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    mk = data['match_keys']
    by_id = {d['id']: d for d in data['deals']}

    # --- 1. дубль Kaspersky ---
    # Первый прогон уже удалил профиль-дубль g2700fefa и (ошибочно)
    # перенаправил buyer на g623b934f — тот же id, что и target, что
    # завалило test_one_company_holds_one_role_in_a_deal. Довершаем
    # исправление идемпотентно: если дубль ещё жив — тот же путь, что
    # раньше; если уже удалён (как сейчас) — просто чистим buyer.
    deal = by_id[KASPERSKY_DEAL_ID]
    assert comps[KASPERSKY_ID]['name'] == 'Лаборатория Касперского'
    assert deal['target'] == KASPERSKY_ID, 'target сделки не Лаборатория Касперского'
    dup_alive = DUP_ID in comps
    if dup_alive:
        assert comps[DUP_ID]['name'] == DUP_NAME
        refs = [d['id'] for d in data['deals']
                if d.get('buyer') == DUP_ID or d.get('target') == DUP_ID
                or d.get('seller_id') == DUP_ID]
        assert refs == [KASPERSKY_DEAL_ID], 'на дубль есть другие ссылки: %s' % refs
    else:
        assert deal['buyer'] == KASPERSKY_ID, 'buyer сделки в неожиданном состоянии: %r' % deal['buyer']
    print('ОЧИСТКА BUYER  %s: -> None (target уже верно указывает на Лабораторию Касперского)' % KASPERSKY_DEAL_ID)
    print('УДАЛЕНИЕ  %-12s %r (%s)' % (DUP_ID, DUP_NAME, 'ещё жив, удаляю' if dup_alive else 'уже удалён ранее'))
    if write:
        deal['buyer'] = None
        if dup_alive:
            del comps[DUP_ID]
            mk.pop(DUP_ID, None)

    # --- 2. переименования (идемпотентно: первый прогон их уже применил) ---
    for cid, (old, new) in RENAMES.items():
        current = comps[cid]['name']
        if current == new:
            print('ПЕРЕИМЕНОВАНИЕ  %-12s уже применено (%r)' % (cid, new))
            continue
        assert current == old, 'профиль %s в неожиданном состоянии: %r' % (cid, current)
        existing_names = {c.get('name') for c in comps.values()}
        assert new not in existing_names, 'имя %r уже занято' % new
        print('ПЕРЕИМЕНОВАНИЕ  %-12s %r -> %r' % (cid, old, new))
        if write:
            comps[cid]['name'] = new
            mk[cid] = NEW_ALIASES[cid]

    # --- 3. описания ---
    wrote, skipped = 0, []
    for cid, text in DESCRIPTIONS.items():
        c = comps.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert 15 <= len(text) <= 220, 'описание %s вне 1–2 строк: %d' % (cid, len(text))
        old = str(c.get('desc') or '')
        if old.strip() == text:
            continue
        if old and not PLACEHOLDER.match(old):
            skipped.append((cid, c.get('name'), old[:60]))
            continue
        print('  ОПИСАНИЕ %-12s %-40s %s' % (cid, str(c.get('name'))[:40], text[:50]))
        if write:
            c['desc'] = text
        wrote += 1

    print('\nОписаний записано: %d' % wrote)
    if skipped:
        print('Пропущено (уже есть своё описание): %d' % len(skipped))
        for cid, name, old in skipped[:5]:
            print('   %s %s — %r' % (cid, name, old))

    real = sum(1 for v in comps.values()
               if (v.get('desc') or '').strip() and not PLACEHOLDER.match(str(v.get('desc'))))
    print('Всего профилей с описанием: %d из %d (%d%%)'
          % (real, len(comps), round(100 * real / len(comps))))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
