# -*- coding: utf-8 -*-
"""21 августа, следствие двух независимых сбоев подряд:
`/api/moderation/decisions` несколько часов отвечал 500, решения копились
непрочитанными; когда эндпоинт ожил, `approve.py` применил накопившийся
бэклог разом — и обнаружился отдельный, ранее не найденный баг: черновик
`d59961733` (Wegosty/tadviser, «Российская платформа для отелей и
ресторанов Wegosty привлекла 23 млн рублей инвестиций») лежал сразу в ТРЁХ
дневных hold-файлах (18, 19, 21 августа — сырьё без решения переносится
вперёд каждый день). `approve.py` объединял все hold-файлы в один список
БЕЗ дедупликации по draft_id, и единственное решение «в работу» встретило
один и тот же черновик трижды — родились три карточки-близнеца с тремя
разными id (g855e50b1, gf544dd13, g5cba276f), каждая — голый скелет без
чтения источника.

Первопричина починена в approve.py (дедуп hold-файлов по draft_id + защита
`plan_raw` от повторного применения уже решённого draft_id) — этот скрипт
чистит уже случившееся следствие. Все три карточки описывают ту же сделку,
что уже полностью собрана и прочитана как `g8b03762d`
(pipeline/fix_wegosty_lost_take_decision.py, 21 августа, чтением
первоисточника) — три пустых близнеца не несут ни одного факта, которого
там нет, удаляются целиком, а не сливаются.

Запуск: python3 pipeline/fix_wegosty_triplicate_cards.py           # проверка
        python3 pipeline/fix_wegosty_triplicate_cards.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import promote  # noqa: E402

PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

DUPLICATE_IDS = ('g855e50b1', 'gf544dd13', 'g5cba276f')
KEPT_ID = 'g8b03762d'
DUPLICATE_TITLE = ('Российская платформа для отелей и ресторанов Wegosty '
                    'привлекла 23 млн рублей инвестиций')


def main(write=False):
    data = json.load(open(PENDING, encoding='utf-8'))
    by_id = {c['id']: c for c in data['cards']}
    assert KEPT_ID in by_id, '%r (полная карточка) не найдена в pending.json' % KEPT_ID
    for cid in DUPLICATE_IDS:
        assert cid in by_id, '%r не найдена — уже почищена?' % cid
        assert by_id[cid]['title'] == DUPLICATE_TITLE, (
            '%r несёт неожиданный заголовок %r — не трогаю' % (cid, by_id[cid]['title']))
        assert not by_id[cid].get('reviewed'), (
            '%r уже помечена reviewed — возможно, её успели дочитать, не трогаю' % cid)

    print('УДАЛЯЮ %d карточек-близнецов (%s) — та же сделка уже полностью '
          'собрана в %s' % (len(DUPLICATE_IDS), ', '.join(DUPLICATE_IDS), KEPT_ID))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    data['cards'] = [c for c in data['cards'] if c['id'] not in DUPLICATE_IDS]
    json.dump(data, open(PENDING, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # Мимо send_drafts.py эти id не пройдут снова: draft_id-новых решений по
    # ним не осталось (три близнеца родились из ОДНОГО решения на ОДИН
    # draft_id, уже отмеченного 'take' в decided_raw/raw_titles ранее
    # сегодня) — записывать их отдельно не нужно, дубликат был на уровне
    # to_card(), а не на уровне решения.
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
