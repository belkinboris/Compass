"""«ЗПИФ «Аталанта» купил 7,8% «Бифоркома»» (gc1037ea9): без поста — решение владельца
в чате 26 ноября 2026 («По Аталанту не отправляем пост»). Карточка на сайте остается.

    python3 pipeline/archive/2026-11/gc1037ea9_no_post.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))      # читается прямо перед записью
    deal = next(d for d in data['deals'] if d['id'] == 'gc1037ea9')
    assert 'gc1037ea9' not in data.get('telegram_posts', {}), 'пост уже вышел'
    assert not deal.get('post_approved'), 'пост уже одобрен'
    print(deal['title'], '— было no_post:', deal.get('no_post'))
    deal['no_post'] = True
    deal.pop('post_held', None)
    if not write:
        print('сухой прогон')
        return
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('записано')


if __name__ == '__main__':
    main('--write' in sys.argv)
