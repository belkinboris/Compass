"""ТЦ «Сказка» (gcd8d2664): «ЗПИФК» → «ЗПИФ» по заметке владельца 9 октября
2026 («лучше просто ЗПИФ»). Рутина ответила на заметку «поправлено» и сняла
её с очереди, но правка в данные не попала. Меняются заголовок, имя
покупателя, свидетельство стороны; снимок поста и отметки об отправке
снимаются, чтобы карточка и пост ушли в консоль заново в новом виде (иначе
кнопка «Пост в канал» выпустила бы старый снимок).

Без ключа — сухой прогон; запись — --write (файл перечитывается перед записью).
"""
import json
import os
import sys

PENDING = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static/data/pending.json')
OLD, NEW = 'ЗПИФК «Инвестпроф»', 'ЗПИФ «Инвестпроф»'


def apply(card):
    if card.get('buyer_name') == NEW:
        return False
    assert card.get('buyer_name') == OLD and card['title'].startswith(OLD), (card.get('buyer_name'), card['title'])
    card['title'] = card['title'].replace(OLD, NEW)
    card['buyer_name'] = NEW
    for ev in (card.get('party_evidence') or {}).get('buyer') or []:
        if ev.get('value') == OLD:
            ev['value'] = NEW
    card['draft_sent'] = False
    card['post_draft_sent'] = False
    card.pop('post_preview', None)
    return True


def main(write):
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next(c for c in data['cards'] if c['id'] == 'gcd8d2664')
    changed = apply(card)
    print(card['title'], '| изменено' if changed else '| уже исправлено')
    if write and changed:
        fresh = json.load(open(PENDING, encoding='utf-8'))
        apply(next(c for c in fresh['cards'] if c['id'] == 'gcd8d2664'))
        with open(PENDING, 'w', encoding='utf-8') as f:
            json.dump(fresh, f, ensure_ascii=False, indent=1)
        print('Записано.')
    elif not write:
        print('Сухой прогон. Запись — с ключом --write.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
