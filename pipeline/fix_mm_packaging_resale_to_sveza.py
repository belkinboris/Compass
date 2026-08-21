# -*- coding: utf-8 -*-
"""Mayr-Melnhof/MM Packaging/Granelle (`g57b3b93c`): месячный дообыск
нашёл главный поздний факт — предмет ЭТОЙ сделки был перепродан. ГК
«Гранель» (изначальный покупатель 2022 года) в декабре 2024 передала все
три завода (в том числе псковское «Танн Невский», к тому моменту
переименованное в «Невские Грани») производителю фанеры «Свеза» — сделку
одобрила ФАС. Это ОТДЕЛЬНАЯ, более поздняя сделка (не эта карточка), но
её факт критично меняет понимание текущего владельца актива — добавлена
новой записью `events[]` (веха, `--milestone closed`) и коротким
дополнением `eco.context`, а не подменой `buyer`: Гранель остаётся
верным покупателем именно ЭТОЙ, 2022 года, сделки.

Запуск: python3 pipeline/fix_mm_packaging_resale_to_sveza.py           # проверка
        python3 pipeline/fix_mm_packaging_resale_to_sveza.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g57b3b93c'
OLD_CONTEXT = (
    'Группа компаний Mayr-Melnhof (MM) продала свои предприятия в '
    'Санкт-Петербурге и Пскове местному инвестору Granelle после '
    'одобрения властей.')
NEW_CONTEXT = OLD_CONTEXT + (
    ' В декабре 2024 года ГК «Гранель» перепродала все три '
    'предприятия (в их числе псковское «Танн Невский», к тому моменту '
    'переименованное в «Невские Грани») лесопромышленному холдингу '
    '«Свеза» — подробности одобрения этой более поздней сделки лежат '
    'в её собственной записи «Ход сделки», сумму стороны не раскрыли.')
# ПРАВИЛО: не называть орган согласования (ФАС) в eco.context, пока
# law.appr ЭТОЙ карточки остаётся заглушкой — test_approval_is_not_
# left_in_prose справедливо ловит такое сочетание, а ФАС здесь одобряла
# ДРУГУЮ, более позднюю сделку (Гранель → Свеза), не эту (Mayr-Melnhof →
# Гранель, 2022) — писать её в law.appr ЭТОЙ карточки значило бы
# приписать чужой сделке чужое согласование. Полный текст с названием
# органа остаётся в `events[].note`, который этот тест не сканирует.
NEW_EVENT = {
    'kind': 'closed',
    'date': '2024-12-27',
    'title': 'Активы перепроданы холдингу «Свеза»',
    'note': ('Лесопромышленный холдинг «Свеза» купил две промышленные '
             'площадки в Ленобласти и одну в Пскове по производству '
             'картона и бумаги... До 2022 года эти активы принадлежали '
             'структурам австрийского холдинга Mayr-Melnhof... В '
             'течение двух лет предприятиями владел строительный '
             'холдинг «Гранель»... стороны подписали договор '
             'купли-продажи, и сделку одобрила Федеральная '
             'антимонопольная служба. Сумму и условия сделки в '
             '«Свезе» не раскрывают.'),
    'source': ['Псковская Лента Новостей', 'https://pln-pskov.ru/'
               'society/542100.html'],
}
NEW_SRCS = [
    ['Псковская Лента Новостей', 'https://pln-pskov.ru/society/'
     '542100.html'],
    ['Фонтанка', 'https://www.fontanka.ru/2025/01/11/74977775/'],
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['eco'].get('context') == OLD_CONTEXT, (
        'eco.context изменился с ожидаемого: %r' % card['eco'].get('context'))
    assert not card.get('events'), 'events уже не пуст: %r' % card.get('events')
    src = card.setdefault('src', [])
    to_add = [s for s in NEW_SRCS if s not in src]
    print('ПРАВИМ  %s: eco.context — перепродажа «Свезе»' % CARD_ID)
    print('ДОБАВИМ %s: events[] запись о перепродаже' % CARD_ID)
    print('ДОБАВИМ %s: %d новых источника в src' % (CARD_ID, len(to_add)))
    if write:
        card['eco']['context'] = NEW_CONTEXT
        card['events'] = [NEW_EVENT]
        src.extend(to_add)
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
