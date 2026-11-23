# -*- coding: utf-8 -*-
"""Приемка карточки g9b852635 («Эталон»/Нагатинская пойма, независимый читатель,
docs/card_acceptance.md): механическая находка `party_unlinked:target` — предмет
назван текстом («Участки в Нагатинской пойме»), без профиля. Предмет — два
земельных участка, не юрлицо, профиль им не положен (тот же случай, что
g69c83a3f, g17362840, g9f2d671d и другие участки в базе). Записываем причину в
accepted_notes.no_profile.target, как требует docs/card_acceptance.md
(«Профиля нет — только после поиска в базе, отказ — не причина»).

Запуск:
    python3 pipeline/fix_etalon_card_2026_11_23_no_profile_target.py            # сухой прогон
    python3 pipeline/fix_etalon_card_2026_11_23_no_profile_target.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PENDING = os.path.join(ROOT, '..', 'static', 'data', 'pending.json')

CARD_ID = 'g9b852635'
OLD_NOTE = 'Покупателя пока нет — участки только выставлены на продажу.'
NEW_TARGET_NOTE = ('Два земельных участка в Нагатинской пойме — не юрлицо, профиля быть не может '
                    '(тот же случай, что g69c83a3f, g17362840, g9f2d671d); РИА Недвижимость '
                    '23.11.2026 называет лоты по номеру очереди «Нагатино Ай-Лэнда» и программе КРТ, '
                    'без кадастровых номеров и без общества-владельца конкретно этих участков.')


def main(write):
    pending = json.load(open(PENDING, encoding='utf-8'))
    by_id = {c['id']: c for c in pending['cards']}
    assert CARD_ID in by_id, 'карточка %s не нашлась' % CARD_ID
    card = by_id[CARD_ID]
    notes = card.get('accepted_notes') or {}
    no_profile = notes.get('no_profile') or {}
    assert no_profile.get('buyer') == OLD_NOTE, 'no_profile.buyer уже другой: %r' % no_profile.get('buyer')
    assert 'target' not in no_profile, 'no_profile.target уже записан: %r' % no_profile.get('target')

    print('Карточка: %s' % CARD_ID)
    print('  accepted_notes.no_profile.target -> %s' % NEW_TARGET_NOTE)

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    pending = json.load(open(PENDING, encoding='utf-8'))  # перечитать прямо перед записью
    cur_by_id = {c['id']: c for c in pending['cards']}
    assert CARD_ID in cur_by_id, 'карточка пропала при повторном чтении'
    cur_card = cur_by_id[CARD_ID]
    cur_notes = cur_card.get('accepted_notes') or {}
    cur_no_profile = cur_notes.get('no_profile') or {}
    assert cur_no_profile.get('buyer') == OLD_NOTE, 'значение изменилось параллельно — остановитесь'
    assert 'target' not in cur_no_profile, 'no_profile.target уже записан параллельно'
    cur_no_profile['target'] = NEW_TARGET_NOTE
    cur_notes['no_profile'] = cur_no_profile
    cur_card['accepted_notes'] = cur_notes
    pending['cards'] = [cur_card if c['id'] == CARD_ID else c for c in pending['cards']]
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: accepted_notes.no_profile.target добавлен в pending.json')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
