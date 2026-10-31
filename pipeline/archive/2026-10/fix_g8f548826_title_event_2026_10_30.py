# -*- coding: utf-8 -*-
"""Карточка g8f548826 (ВТБ/«Росгосстрах Жизнь», очередь, в pending.json):
заголовок и текст единственного события оказались ДОСЛОВНОЙ копией
исходной записи притока (`from_raw`-подобный снимок RBC в
data/inbox/raw/2026-10-30.jsonl): title слово в слово повторял заголовок
источника, а events[0].note на 27 слов подряд совпадал с его кратким
анонсом («Госбанк вместе с новым партнером планирует развивать своего
страховщика жизни и расширять линейку продуктов компании. Сделка принесла
группе ВТБ 24,3 млрд руб. чистой прибыли в сентябре») — `accept_card.py
--queue` поймал оба («заголовок повторяет заголовок источника»,
«27 слов подряд как в источнике в events[0].note»).

ЗАГОЛОВОК переписан другой конструкцией (docs/card_parties.md): назван тот
же факт (ВТБ продал часть доли, покупателя не назвал), но другими словами
и в другом порядке — пересечение слов с заголовками RBC/Ведомостей/ПРАЙМ/
Mail.ru из `src` ниже порога `title_copied_from` (0,75).

EVENTS[0]. `date`/`note` пересказаны своими словами по тем же фактам, что
легли в `eco.val`/`eco.share`/`law.struct` (shag 9, review.py --write):
дата события — 30 сентября (а не 30 октября, дата публикации звонка
Пьянова, — docs/card_status_dates.md), текст — без 27-словного повтора
анонса. Правка идет СВОИМ скриптом, а не `review.py`: вложенные
`events[].note`/`events[].date` таблица FIXES не поддерживает (только
верхнеуровневые поля карточки).

Запуск:
    python3 pipeline/fix_g8f548826_title_event_2026_10_30.py            # сухой
    python3 pipeline/fix_g8f548826_title_event_2026_10_30.py --write    # записать
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PENDING = os.path.join(HERE, '..', 'static', 'data', 'pending.json')
DEAL_ID = 'g8f548826'

OLD_TITLE = 'ВТБ продал долю в «Росгосстрах Жизни» неназванному партнеру'
NEW_TITLE = 'ВТБ продал часть доли в «Росгосстрах Жизни», не назвав покупателя'

OLD_EVENT_DATE = '2026-10-30'
NEW_EVENT_DATE = '2026-09-30'

OLD_EVENT_NOTE = ('Госбанк вместе с новым партнером планирует развивать своего страховщика жизни и '
                  'расширять линейку продуктов компании. Сделка принесла группе ВТБ 24,3 млрд руб. '
                  'чистой прибыли в сентябре')
NEW_EVENT_NOTE = ('ВТБ нашел партнера для «Росгосстрах Жизни» и продал ему часть пакета акций: '
                  'компания вышла из числа дочерних структур банка и с 30 сентября работает как '
                  'совместное предприятие. Цену и доли сторон ВТБ не раскрыл. Переоценка доли по '
                  'справедливой стоимости принесла группе 24,3 млрд ₽ чистой прибыли за третий '
                  'квартал — это бухгалтерский эффект сделки, а не ее цена.')


def main(argv):
    p = json.load(open(PENDING, encoding='utf-8'))
    c = next((x for x in p['cards'] if x['id'] == DEAL_ID), None)
    assert c is not None, 'карточки %s нет в очереди' % DEAL_ID
    assert c.get('title') == OLD_TITLE, 'title уже другой: %r' % c.get('title')
    assert c.get('events') and len(c['events']) == 1, 'events[] устроен иначе, перечитайте карточку'
    ev = c['events'][0]
    assert ev.get('date') == OLD_EVENT_DATE, 'events[0].date уже другой: %r' % ev.get('date')
    assert ev.get('note') == OLD_EVENT_NOTE, 'events[0].note уже другой: %r' % ev.get('note')

    print('%s: title ->\n  %r' % (DEAL_ID, NEW_TITLE))
    print('%s: events[0].date %r -> %r' % (DEAL_ID, OLD_EVENT_DATE, NEW_EVENT_DATE))
    print('%s: events[0].note -> переписан своими словами (без 27-словного повтора анонса RBC)'
          % DEAL_ID)

    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    c['title'] = NEW_TITLE
    ev['date'] = NEW_EVENT_DATE
    ev['note'] = NEW_EVENT_NOTE
    assert c['title'] == NEW_TITLE and ev['date'] == NEW_EVENT_DATE and ev['note'] == NEW_EVENT_NOTE

    json.dump(p, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
