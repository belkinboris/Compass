# -*- coding: utf-8 -*-
"""18 сентября 2026 — пересчитать `post_preview` для карточек временного
управления Nestlé/«Ашан» после починки данных и рендера поста.

`send_telegram.py` при публикации ОТДАЁТ ПРИОРИТЕТ сохранённому
`post_preview` перед автоформатом (см. докстроку у `_post_text_for` в
send_telegram.py: «post_preview не используется для правок уже вышедшего...
но используется для ПЕРВОЙ публикации»). Обе карточки уже прошли
`send_drafts.py` ДО того, как нашлись и были починены дефекты
(`eco.finadv`, `kind`, метка «Покупатель», обрыв «Л.Е.В.» в `_sentences()`)
— их `post_preview` несёт СТАРЫЙ, гарантированно неверный текст. Не
перезаписать его — значит опубликовать в канал ровно то, что владелец
назвал абсурдом, несмотря на то, что все данные под ним уже исправлены.

Запуск: python3 pipeline/regenerate_custody_post_previews.py [--write]
"""
import json
import sys

sys.path.insert(0, 'pipeline/publish')
import format_post  # noqa: E402

PENDING_PATH = 'static/data/pending.json'
BASE_PATH = 'static/data/deals_promoted.json'
CARDS = ['g64462179', 'g2daf32fe']


def main(write):
    pending = json.load(open(PENDING_PATH, encoding='utf-8'))
    base = json.load(open(BASE_PATH, encoding='utf-8'))
    companies = base['companies']
    by_id = {c['id']: c for c in pending['cards']}

    for cid in CARDS:
        assert cid in by_id, 'карточки %r нет в pending.json' % cid
        card = by_id[cid]
        assert card.get('kind') == 'custody', \
            '%s: kind не custody — сначала fix_auchan_nestle_custody_cards.py' % cid
        old_preview = card.get('post_preview')
        new_preview = format_post.render(card, companies)
        assert old_preview != new_preview, \
            '%s: пересчитанный текст не отличается — нечего чинить' % cid
        assert 'Покупатель' not in new_preview, \
            '%s: метка «Покупатель» всё ещё в тексте — _buyer_label не сработал' % cid
        card['post_preview'] = new_preview
        print('%s: post_preview пересчитан' % cid)
        print(new_preview)
        print('-' * 80)

    if write:
        json.dump(pending, open(PENDING_PATH, 'w', encoding='utf-8'),
                   ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('сухой прогон — для записи передайте --write')


if __name__ == '__main__':
    main('--write' in sys.argv)
