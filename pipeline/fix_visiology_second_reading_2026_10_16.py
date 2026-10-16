# -*- coding: utf-8 -*-
"""Карточка g7bff6e5c (Visiology/«Поток») — находки второго чтения:

1. `title` почти побуквенно совпадал с заголовком Ведомостей — переписан.
2. `date`/`events[0].date` несли дату ПУБЛИКАЦИИ статьи (16 октября), а не
   дату закрытия раунда — в тексте статьи нет ни одного временного маркера
   закрытия (проверено WebFetch вторым чтением). Снижено до года (правило
   «нет дня — только год», docs/card_status_dates.md).
3. `party_evidence.buyer` указывал источником Ведомости, хотя деталь про
   платформу «Поток» и организатора BITL — из ComNews; url исправлен.

Запуск:
    python3 pipeline/fix_visiology_second_reading_2026_10_16.py            # сухой прогон
    python3 pipeline/fix_visiology_second_reading_2026_10_16.py --write    # применить
"""
import json
import sys

PENDING = '/home/user/Compass/static/data/pending.json'
CARD_ID = 'g7bff6e5c'

COMNEWS_URL = 'https://www.comnews.ru/content/240377/2025-07-25/2025-w30/1010/visiology-uskorit-razrabotku-platformy-opirayas-sredstva-vneshnikh-investorov'

OLD_TITLE = 'Visiology завершил инвестиционный раунд объёмом 200 млн рублей'
NEW_TITLE = 'Visiology привлекла 200 млн рублей через краудинвестинговую платформу «Поток»'

OLD_DATE = '2026-10-16'
NEW_DATE = '2026'

OLD_EVENT_NOTE = ('Раунд объявлен в июле 2025 года на инвестиционной платформе «Поток» '
                   '(организатор — компания BITL); закрыт 16 октября 2026 года.')
NEW_EVENT_NOTE = ('Раунд объявлен в июле 2025 года на инвестиционной платформе «Поток» '
                   '(организатор — компания BITL); о закрытии стало известно 16 октября '
                   '2026 года, точный день закрытия источник не называет.')


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = {c['id']: c for c in data['cards']}[CARD_ID]
    assert card['title'] == OLD_TITLE, 'title уже не тот: %r' % card['title']
    assert card['date'] == OLD_DATE, 'date уже не тот: %r' % card['date']
    assert card['events'][0]['date'] == OLD_DATE, 'events[0].date уже не тот'
    assert card['events'][0]['note'] == OLD_EVENT_NOTE, 'events[0].note уже не та'
    assert card['party_evidence']['buyer'][0]['url'].startswith('https://www.vedomosti.ru'), \
        'party_evidence.buyer.url уже не Ведомости'
    print('title: %r -> %r' % (OLD_TITLE, NEW_TITLE))
    print('date: %r -> %r' % (OLD_DATE, NEW_DATE))
    print('events[0].date: %r -> %r' % (OLD_DATE, NEW_DATE))
    print('events[0].note переписывается')
    print('party_evidence.buyer.url -> ComNews')
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    fresh = json.load(open(PENDING, encoding='utf-8'))
    fc = {c['id']: c for c in fresh['cards']}[CARD_ID]
    assert fc['title'] == OLD_TITLE, 'title поменяли параллельно — перечитайте'
    fc['title'] = NEW_TITLE
    fc['date'] = NEW_DATE
    fc['events'][0]['date'] = NEW_DATE
    fc['events'][0]['note'] = NEW_EVENT_NOTE
    fc['party_evidence']['buyer'][0]['url'] = COMNEWS_URL
    fc['party_evidence']['buyer'][0]['method'] = 'research'
    json.dump(fresh, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
