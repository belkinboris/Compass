# -*- coding: utf-8 -*-
"""Слияние близнеца, найденного НЕ по падежу и НЕ по общему стеблю, а по
систематическому промеру всей базы (см. журнал прогона G2-30: «стоит
подумать, не завести ли одноразовый скрипт-замер»). Плюс 8 описаний
профилей той же партии G2.

ЗАМЕР. `test_no_company_twins` ловит падежные/фонетические варианты
приведением к латинице (`c/k`, `ph/f`, удвоенные буквы…), но не ловит
ГЛАСНЫЕ, которые меняются при русской фонетической транскрипции
английского слова: «Cloud» /klaʊd/ передаётся по-русски как «Клауд»
(через «ау», это стандартная передача дифтонга), а обратная
транслитерация «Клауд» → «klaud», не «kloud» — гласная не
восстанавливается, потому что кириллица передавала ЗВУЧАНИЕ, а не
написание. Отдельный сплошной промер (сравнение стема имени профиля со
стемами заголовков ЕГО ЖЕ сделок, с допуском на падеж через 5-значный
префикс) нашёл 36 кандидатов из 1709 профилей с 2+ сделками; из пяти
профилей, где НИ ОДНА сделка не содержит имени профиля (сильнейший
сигнал), четыре оказались ложными срабатываниями (уже проверенные и
описанные в прошлых партиях — «Лента», Augment Investments, «Стинн»,
«АЛД Автомотив» — совпадения по роли, не по словам заголовка), а пятый
— настоящий близнец:

ДЕФЕКТ. `g61cf2aaf` «ООО «ТИКЕТСКЛАУД»» (сделка `gedc0eb10`, сентябрь
2023, «МТС купила 85% TicketsCloud») и `g4b69137f` «TicketsCloud»
(сделка `gc4c76129`, март 2023, «МТС приобретает TicketsCloud») — одна
и та же компания под двумя профилями: сначала стадия переговоров
(латиница, как в источнике), потом закрытие (кириллица — юрлицо из
ЕГРЮЛ). Ни один id не встречается больше нигде в базе (проверено
полнотекстовым поиском), псевдонимов в match_keys не было. Выживший —
`g4b69137f` «TicketsCloud» (более узнаваемое написание бренда), `target`
сделки `gedc0eb10` перенаправлен, дубль удалён с записью в
`merged_companies` — по образцу `merge_case_variant_company_twins_batch4.py`.

ЧТО ДЕЛАЕТ. 1 слияние профилей, 8 описаний (включая выжившего после
слияния).

Запуск:
    python3 pipeline/merge_ticketscloud_twin_and_describe_batch31.py            # сухой прогон
    python3 pipeline/merge_ticketscloud_twin_and_describe_batch31.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

DUP_ID = 'g61cf2aaf'
SURVIVOR_ID = 'g4b69137f'
DUP_NAME = 'ООО «ТИКЕТСКЛАУД»'
SURVIVOR_NAME = 'TicketsCloud'
MERGE_DEAL_IDS = ['gedc0eb10']

DESCRIPTIONS = {
    'g4b69137f': 'Сервис продажи билетов; в 2023 году МТС Entertainment '
                 'выкупила контрольную долю (85%) у основателя Егора '
                 'Егерева.',
    'gf19b3163': 'Разработчик IoT и телематических решений для '
                 'транспорта (группа СКАУТ); в 2022–2023 годах МТС '
                 'последовательно нарастила долю до контрольной.',
    'gfaa7f73a': 'Инвестиционный фонд группы «Тилтех» (совладельцы — '
                 'Андрей Кривенко и партнёры), вкладывается в '
                 'потребительские бренды — мебель VMMGame, Shinsale.',
    'g093e9633': 'Сервис аренды бытовой техники и гаджетов по подписке; '
                 'среди инвесторов — Kontinuum Group, AngelsDeck, TMT '
                 'Investments.',
    'gprostobarista': 'Сеть кофеен самообслуживания (более 1000 точек в '
                       'России и СНГ); в 2026 году поглощена сетью '
                       '«Точка Черного».',
    'gfffc5ddd': 'Структура Мусы Бажаева; купила у Kopy Goldfields '
                 'золотодобывающую компанию «Амур Золото».',
    'gff01c2ae': 'Сеть детских тематических парков; в 2023 году финский '
                 'фонд CapMan продал 40% долю основателям и гендиректору.',
    'gfe425e93': 'Инвестиционный фонд; купил 20% в производителе '
                 'спешелти-кофе Tasty Coffee у его основателей.',
    'gfda9fe6c': 'Завод минеральной воды «Чистозерье» в Новосибирской '
                 'области; в 2024 году продан IDS Borjomi Russia.',
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    deals = data['deals']

    assert comps[DUP_ID]['name'] == DUP_NAME, 'дубль %s уже не тот' % DUP_ID
    assert comps[SURVIVOR_ID]['name'] == SURVIVOR_NAME, 'выживший %s уже не тот' % SURVIVOR_ID
    full_text_refs = sorted(d['id'] for d in deals if DUP_ID in json.dumps(d, ensure_ascii=False))
    assert full_text_refs == sorted(MERGE_DEAL_IDS), (
        'дубль %s встречается не только в учтённых сделках: %r' % (DUP_ID, full_text_refs))

    print('СЛИВАЕМ  %s -> %s (%s)' % (DUP_ID, SURVIVOR_ID, SURVIVOR_NAME))
    print('ПЕРЕНАПРАВЛЯЕМ  сделки', MERGE_DEAL_IDS)

    if write:
        for d in deals:
            if d.get('id') in MERGE_DEAL_IDS:
                for field in ('buyer', 'target', 'seller_id', 'asset_id'):
                    if d.get(field) == DUP_ID:
                        d[field] = SURVIVOR_ID
        survivor_aliases = set(data['match_keys'].get(SURVIVOR_ID, []))
        survivor_aliases.update(data['match_keys'].pop(DUP_ID, []))
        if survivor_aliases:
            data['match_keys'][SURVIVOR_ID] = sorted(survivor_aliases)
        data.setdefault('merged_companies', {})[DUP_ID] = SURVIVOR_ID
        del comps[DUP_ID]

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
        print('  ОПИСАНИЕ %-14s %-30s %s' % (cid, str(c.get('name'))[:30], text[:50]))
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
