# -*- coding: utf-8 -*-
"""Приток 19.09.2026, часовой прогон 10:20 МСК — ответ на заметку владельца
№700: «Карту объедини, а с постами мы сами разберемся». g6743f902 и
g7a96dda2 описывают одну и ту же сделку («Трамплин Холдинг» купил 51%
ООО «Мальт Систем» у Сергея Елизарова) — обе уже вышли отдельными постами
в канале (message_id 116 и 122 соответственно), и владелец прямо разрешил
слить КАРТОЧКИ, оставив разбор постов людям отдельно (telegram_posts не
трогаем). Выживает g6743f902 (первая по времени añadida, 2026-09-11,
дочитана дважды: deep + weekly) — в неё переносятся источники и факт из
g7a96dda2, которых там ещё нет: телеграм-канал «Сделки M&A» и АБН как
источники, и абзац о структуре группы «Трамплин» (учредитель Святослав
Капустин, «Трамплин Электроникс» — разработчик «Иртыша» внутри группы,
её финансовые показатели за 2025 год и заём холдинга на 1,30 млрд ₽).
g7a96dda2 удаляется с редиректом на g6743f902.
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'

SURVIVOR_ID = 'g6743f902'
MERGED_ID = 'g7a96dda2'

ADDED_CONTEXT = (
    ' АО «Трамплин Холдинг» входит в группу компаний «Трамплин», основателем '
    'и руководителем которой является Святослав Капустин. Группа развивает '
    'проекты в высоких технологиях, строительстве, образовании и культуре. '
    'В микроэлектронике её ключевой актив — «Трамплин Электроникс», '
    'разработчик процессоров «Иртыш». Консолидированная выручка группы не '
    'раскрывается; выручка «Трамплин Электроникс» за 2025 год составила '
    '0 руб., чистый убыток — 36,3 млн руб. В 2025 году АО «Трамплин Холдинг» '
    'предоставил займы на 1,30 млрд руб., при этом его собственная выручка '
    'отсутствовала — это инвестиционная структура.'
)

NEW_SOURCES = [
    ['Телеграм-канал: Сделки M&A', 'https://t.me/dealsma/7383'],
    ['АБН', 'https://abn.agency/2026/09/14/razrabotchik-proczessora-irtysh-vykupil-kontrolnyj-paket-dizajn-czentra-malt-system/'],
]


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals']
    survivor = next(d for d in deals if d['id'] == SURVIVOR_ID)
    merged_card = next(d for d in deals if d['id'] == MERGED_ID)

    assert survivor['title'] == '«Трамплин Холдинг» купил 51% дизайн-центра «Мальт Систем»'
    assert merged_card['title'] == '«Трамплин Холдинг» приобрел 51% разработчика процессоров Malt System'
    assert 'Святослав Капустин' not in survivor['eco']['context']

    survivor['eco']['context'] = survivor['eco']['context'] + ADDED_CONTEXT

    existing_urls = {u for _, u in survivor['src']}
    for label, url in NEW_SOURCES:
        if url not in existing_urls:
            survivor['src'].append([label, url])

    data['deals'] = [d for d in deals if d['id'] != MERGED_ID]
    data.setdefault('merged', {})[MERGED_ID] = SURVIVOR_ID

    tp = data.get('telegram_posts', {})
    assert tp.get(SURVIVOR_ID) == 116
    assert tp.get(MERGED_ID) == 122

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f'{MERGED_ID} слита в {SURVIVOR_ID}, посты (116, 122) не тронуты. ЗАПИСАНО.')
    else:
        print('Сухой прогон. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
