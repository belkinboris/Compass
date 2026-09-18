# -*- coding: utf-8 -*-
"""Карточка g5599430f (CPF/«Новомясово»): в events[0].note просочилась
служебная вики-разметка TAdviser («История 2026: ...» — заголовок раздела
статьи, не текст), а сам текст обрублен многоточием на середине фразы —
жёсткий лимит разбора, уже описанный в CLAUDE.md («Нашли жёсткий лимит —
почините его там, где он режет»). review.py не может адресовать элемент
списка events[], поэтому правка — отдельным скриптом с assert на исходное
состояние (тот же приём, что fix_g21795ec9_truncated_note.py). Дата этапа
поправлена на подтверждённую дату сделки (2026-04-15), как и у самой
карточки.

Запуск: python3 pipeline/fix_novomyasovo_event_note.py [--write]
"""
import json
import sys

PENDING_PATH = 'static/data/pending.json'

OLD_NOTE = (
    'История 2026: Таиландская CPF купила «Новомясово» за 2,05 млрд рублей В компании '
    '«Новомясово», управляющей свиноводческими активами новгородской группы «Адепт», '
    'сменился владелец. Им стала компания СПФО — российская «дочка» тайского '
    'агропромышленного гиганта…'
)
NEW_NOTE = (
    'В компании «Новомясово», управляющей свиноводческими активами новгородской группы '
    '«Адепт», сменился владелец. Им стала компания СПФО — российская «дочка» тайского '
    'агропромышленного гиганта Charoen Pokphand Foods (CPF).'
)


def main(write):
    data = json.load(open(PENDING_PATH, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == 'g5599430f')
    assert card['events'][0]['note'] == OLD_NOTE, card['events'][0]['note']
    assert card['events'][0]['date'] == '2026-09-18'
    card['events'][0]['note'] = NEW_NOTE
    card['events'][0]['date'] = '2026-04-15'

    if write:
        json.dump(data, open(PENDING_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('g5599430f: events[0] дописан и датирован. ЗАПИСАНО.')
    else:
        print('Сухой прогон: поправил бы events[0].note и дату g5599430f.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
