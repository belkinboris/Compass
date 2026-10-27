# -*- coding: utf-8 -*-
"""Качество, 11 октября 2026 — месячная очередь (кластеры 2, 4, 5):
семь карточек дополнены новыми фактами сверх уже известного.

Сознательно не внесено (решает владелец, вопрос в консоли):
`ga4d82b1c` — личность и санкционный статус гендиректора «Логики
молока» и характеристика Алисултанова как «номинального» владельца.

Запуск:
    python3 pipeline/fix_2026_10_11_monthly_cluster2345.py            # сухой прогон
    python3 pipeline/fix_2026_10_11_monthly_cluster2345.py --write    # запись
"""
import json
import sys

sys.path.insert(0, '.')
from pipeline.ingest.review import fix_fingerprint

DATA_PATH = 'static/data/deals_promoted.json'

EDITS = [
    # 1. g3ecb7b86 — S8 Capital/Meteor Lift: мощность завода, фон «Лифтконнект».
    dict(
        id='g3ecb7b86', field='eco.context', old='—',
        new=('Завод в Петербурге под брендом Meteor Lift рассчитан на выпуск до '
             '7 тыс. лифтов в год. В сервисный портфель АО «Лифтконнект» (ранее '
             'бизнес Kone, выкупленный S8 Capital в октябре 2023 года) вошли '
             '7 тыс. единиц обслуживаемого оборудования, включая '
             'высокоскоростные лифты в шести регионах; по данным «Контур.Фокуса», '
             'выручка «Лифтконнект» на конец 2022 года составила 4,2 млрд ₽ '
             '(-35% год к году), чистая прибыль — 62,6 млн ₽, сохранено '
             '300 рабочих мест.'),
        src=[['The Moscow Times', 'https://ru.themoscowtimes.com/2026/09/09/bank-domrf-stal-vladeltsem-rossiyskogo-biznesa-gruppy-otis-a205634'],
             ['vc.ru', 'https://vc.ru/money/889378']],
    ),
    # 2. g2349d667 — Canpack: точные даты временного управления, характер убытка.
    dict(
        id='g2349d667', field='eco.context',
        old=('В январе 2026 года Владимир Путин передал активы Canpack во '
             'временное управление «Стальэлемента». В августе 2026 года '
             'компании вывели из-под временного управления. После завершения '
             'сделки предприятия прекратят использовать бренд Canpack.'),
        append=(' По собственному сообщению Canpack, временное управление ввели '
                'указом 31 декабря 2025 года, а отменили 24 августа 2026 года — '
                'именно для того, чтобы сделку можно было закрыть.'),
        src=[['Canpack', 'https://www.canpack.com/news/canpack-completes-exit-from-russia/'],
             ['Canpack', 'https://www.canpack.com/news/canpack-group-reports-q2-2026-results/']],
        absorb_fingerprint_of=('eco.context',
            'В январе 2026 года Владимир Путин передал активы Canpack во '
            'временное управление «Стальэлемента». В августе 2026 года '
            'компании вывели из-под временного управления. После завершения '
            'сделки предприятия прекратят использовать бренд Canpack.'),
    ),
    dict(
        id='g2349d667', field='eco.val',
        old='Польский производитель продал оставшиеся доли в российских подразделениях за $122 млн, зафиксировав убыток $354,7 млн.',
        append=(' Canpack сама называет этот убыток бухгалтерским (US GAAP) и '
                'отмечает, что сумма «намного ниже» ее собственной оценки '
                'справедливой стоимости бизнеса на тот момент; часть убытка '
                'будет частично восстановлена после продажи.'),
        src=[['Canpack', 'https://www.canpack.com/news/canpack-completes-exit-from-russia/']],
        absorb_fingerprint_of=('eco.val',
            'Польский производитель продал оставшиеся доли в российских '
            'подразделениях за $122 млн, зафиксировав убыток $354,7 млн.'),
    ),
    # 3. gb2bed44c — ЛСР/«Геометрия»: мотив Кравцова.
    dict(
        id='gb2bed44c', field='eco.context', old='—',
        new=('Александр Кравцов объяснил создание «Геометрии» так: «Пришла '
             'пора переходить на следующий уровень, открывать и развивать '
             'новые бизнесы в сфере строительства. Поэтому я создаю '
             'застройщика "Геометрия" и становлюсь его единоличным '
             'владельцем». Важно не путать это юрлицо с одноименными '
             'компаниями «Геометрия 1» и «Геометрия 2», которые Кравцов '
             'зарегистрировал еще в марте 2026 года вместе с Николаем '
             'Урусовым для проектов коммерческой недвижимости — это другие '
             'юрлица и другой сегмент.'),
        src=[['dp.ru', 'https://www.dp.ru/a/2026/06/10/soosnovatel-zastrojshhika-jelitnogo']],
    ),
    # 4. g18bb9694 — «Инсайт»/«РНЛ Лизинг»: одобрение правкомиссии, номинал.
    dict(
        id='g18bb9694', field='law.appr', old='—',
        new='Сделку одобрила правительственная комиссия по контролю за иностранными инвестициями.',
        src=[['insightgroup.ru', 'https://insightgroup.ru/en/news/rnl-leasing-rebrands-as-fleet-autoleasing/']],
    ),
    dict(
        id='g18bb9694', field='eco.context',
        old=('Покупку «Инсайт» оплатил собственными средствами. Вместе с «РНЛ '
             'Лизинг» ему досталась и ее дочерняя компания «РНЛ Финанс», '
             'принадлежавшая ей на 100%. 8 ноября 2023 года «РНЛ Лизинг» '
             'переименовали во «Флит Автолизинг». Раньше Renault собирался '
             'продать эту же компанию АвтоВАЗу, но сделка не состоялась.'),
        append=(' По данным ЕГРЮЛ, номинальная стоимость «РНЛ Лизинг» составляла '
                '35 млн ₽. Сама RCI Banque называла продажу завершающим шагом '
                'выхода из России: решение об уходе группа Renault приняла еще '
                'в 2022 году.'),
        src=[['Коммерсантъ', 'https://www.kommersant.ru/doc/6159210'],
             ['insightgroup.ru', 'https://insightgroup.ru/en/news/rnl-leasing-rebrands-as-fleet-autoleasing/']],
    ),
    # 5. gce803e3f — палаты Кожевенной слободы: цель покупки «Кростом».
    #    Полный old/new — ниже, в main() (длинный текст).
    # 6. gbeb0dfe8 — Экспобанк/СДМ-Банк: капитал, ROE, вторая оценка цены, рынок.
    dict(
        id='gbeb0dfe8', field='eco.val',
        old='Аналитик IPM Consulting Анастасия Владимирова оценивала справедливый диапазон для пакета в 0,8–1,0 P/BV, то есть 6–8,5 млрд ₽ без учета премии за контроль (по оценке).',
        append=(' По ее словам, капитал СДМ-Банка оценивается в 12–14 млрд ₽ при '
                'рентабельности капитала около 15,6% — это и определяет такой '
                'мультипликатор; кроме того, Экспобанк не покупал контроль с '
                'нуля, а докупал до полного контроля, что снижает премию. '
                'Независимо от нее аналитик Freedom Global Наталья Мильчакова '
                'оценила сделку в 6–8 млрд ₽.'),
        src=[['atnow.ru', 'https://atnow.ru/deals/expobank-sdm'],
             ['Fomag.ru', 'https://fomag.ru/news/konsolidatsiya-bankovskogo-rynka-prodolzhaetsya-ekspobank-stal-vladeltsem-sdm-banka/']],
    ),
    # gbeb0dfe8.eco.context — полный old/new — ниже, в main() (длинный текст).
    # 7. ga4d82b1c — Danone/«Вамин Р»: переименование в «Логику молока»,
    #    инвестпрограмма. Санкционный статус гендиректора и характеристика
    #    Алисултанова как «номинального» владельца — не вносится, вопрос
    #    отправлен владельцу через send_open_questions.py.
    dict(
        id='ga4d82b1c', field='law.struct',
        old=('Руслан Алисултанов стал владельцем ООО "Юнимилк" (бывшее '
             '"Вамин-Татарстан"), которое контролирует (через "Вамин-Р") '
             'компанию "Эйч энд Эн" (объединяет бывшие активы Danone в '
             'России). Соответствующие изменения отражены в ЕГРЮЛ 6 декабря '
             '2024 года. Ранее ему принадлежал 1% компании.'),
        append=(' С октября 2025 года компания публично называется «Логика '
                'молока» (юрлицо не переименовано) — сама компания объясняет '
                'это завершением «локализации и укрепления статуса компании '
                'как лидера молочной индустрии».'),
        src=[['Meduza', 'https://meduza.io/news/2025/10/08/rossiyskiy-danone-stal-logikoy-moloka']],
    ),
    dict(
        id='ga4d82b1c', field='eco.context',
        old='Общий убыток от ухода из России Danone отразила в своей отчетности — 1,2 млрд €.',
        append=(' Новые владельцы бизнес не заморозили: в 2026 году компания '
                'объявила об увеличении инвестиционной программы до 2030 года '
                'с 100 млрд до более чем 120 млрд ₽ — модернизация затронет '
                'все 13 производственных площадок.'),
        src=[['New Retail', 'https://new-retail.ru/novosti/retail/logika_moloka_investiruet_v_proizvodstvo_bolee_120_mlrd_rubley_do_2030_goda/']],
    ),
]

# Длинные old/new без сокращения (отдельно от списка выше для читаемости).
OLD_KOZH = (
    'Памятник архитектуры можно приспособить под ресторан, офис или другое '
    'коммерческое использование. В лот входит аренда земельного участка '
    '0,18 гектара. Палаты — старейшая сохранившаяся постройка Кожевенной '
    'слободы: изначально здание использовалось для хранения товаров и '
    'администрирования торговли, п'
)
OLD_SDM_CONTEXT = (
    'Экспобанк выкупил 15% СДМ-банка у ЕБРР в ноябре 2018 года и увеличил '
    'пакет до 23,57% в январе 2021-го; крупнейшим акционером СДМ-банка после '
    'этого и до конца 2021 года, по данным телеграм-канала MarketOverview, '
    'оставался Анатолий Ландеман. Сделка была закрыта 10 сентября. Данные о '
    'продавцах расходятся: одни источники называют продавцами Анатолия '
    'Ландсмана (продал долю более 15,5%) и компанию «Милавер рус» (владела '
    '53% акций), другие сообщают, что информация о продавцах пакета не '
    'раскрыта.'
)
ADD_SDM_CONTEXT = (
    ' Независимый анализ рынка (Fomag.ru) ожидает, что после сделки доля '
    'объединенного Экспобанка на рынке кредитования физлиц вырастет примерно '
    'вдвое, до 0,5–0,6%, а на рынке корпоративного кредитования — в 1,5–1,6 '
    'раза, до 0,7–1%.'
)


def get(card, field):
    obj = card
    for part in field.split('.')[:-1]:
        obj = obj[part]
    return obj[field.split('.')[-1]]


def set_(card, field, value):
    obj = card
    parts = field.split('.')
    for part in parts[:-1]:
        obj = obj[part]
    obj[parts[-1]] = value


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals'] if isinstance(data, dict) else data
    by_id = {d['id']: d for d in deals}

    for edit in EDITS:
        if edit.get('append_hint'):
            continue
        card = by_id[edit['id']]
        current = get(card, edit['field'])
        if 'new' in edit:
            expected_old = edit['old']
            new_value = edit['new']
        else:
            expected_old = edit['old']
            new_value = edit['old'] + edit['append']
        if current != expected_old:
            raise SystemExit('%s.%s: в базе %r, ожидали %r' % (
                edit['id'], edit['field'], current, expected_old))
        set_(card, edit['field'], new_value)
        existing_src = card.setdefault('src', [])
        for pair in edit['src']:
            if pair not in existing_src:
                existing_src.append(pair)
        if 'absorb_fingerprint_of' in edit:
            afield, atext = edit['absorb_fingerprint_of']
            absorbed = card.setdefault('proofread_absorbed', {})
            fp = fix_fingerprint(atext)
            lst = absorbed.setdefault(afield, [])
            if fp not in lst:
                lst.append(fp)

    # gce803e3f.eco.context — полный текст (old длинный, храним целиком тут).
    card = by_id['gce803e3f']
    full_old = card['eco']['context']
    if not full_old.startswith(OLD_KOZH):
        raise SystemExit('gce803e3f.eco.context: не совпадает ожидаемое начало — %r' % full_old[:80])
    add_kozh = (' Концерн «Крост» планирует включить палаты в масштабный проект '
                'развития территории между Кожевнической улицей и Шлюзовой '
                'набережной — ранее «Крост» уже приобрел соседние объекты, в '
                'том числе бывшие Кожевнические бани и административное '
                'здание.')
    card['eco']['context'] = full_old + add_kozh
    src = card.setdefault('src', [])
    pair = ['Москвич Mag', 'https://moskvichmag.ru/?p=523342']
    if pair not in src:
        src.append(pair)

    # gbeb0dfe8.eco.context — полный текст.
    card = by_id['gbeb0dfe8']
    if card['eco']['context'] != OLD_SDM_CONTEXT:
        raise SystemExit('gbeb0dfe8.eco.context: в базе %r' % card['eco']['context'][:80])
    card['eco']['context'] = OLD_SDM_CONTEXT + ADD_SDM_CONTEXT
    src = card.setdefault('src', [])
    pair = ['Fomag.ru', 'https://fomag.ru/news/konsolidatsiya-bankovskogo-rynka-prodolzhaetsya-ekspobank-stal-vladeltsem-sdm-banka/']
    if pair not in src:
        src.append(pair)

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано: g3ecb7b86, g2349d667 (x2), gb2bed44c, g18bb9694 (x2), gce803e3f, gbeb0dfe8.')
    else:
        print('Сухой прогон. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
