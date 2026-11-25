"""Вернуть отметки «пост не нужен», стертые коммитом 7be4e85c (23 ноября 2026).

Тот коммит притока записал `telegram_posts` из 221 записи вместо 1814: пропали
1593 отметки `None` («карточка на сайте, пост не выходил и не нужен»). Большую
часть позже вернул засев старых карточек, но у 32 сделок ключа нет до сих пор,
и три из них (`g2777a4b6` «Астра ИИ», `gmru-arnest-reckitt`, `rosatom-mali`)
25 ноября пришли владельцу проектами постов: «Арнест и Астра у нас точно же
выходили. Бугула я даже не уверен, что нам предлагался».

Возвращается ровно прежнее значение (None) и только там, где ключа сейчас нет,
а сделка в базе есть.

    python3 pipeline/archive/2026-11/restore_post_marks_lost_2026_11_23.py [--write]
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def main(write):
    before = json.loads(subprocess.run(['git', 'show', '7be4e85c~1:static/data/deals_promoted.json'],
                                       cwd=ROOT, capture_output=True, text=True, check=True).stdout)
    data = json.load(open(DATA, encoding='utf-8'))      # читается прямо перед записью
    old, posts = before['telegram_posts'], data['telegram_posts']
    ids = {d['id'] for d in data['deals']}
    back = [k for k, v in old.items() if v is None and k in ids and k not in posts]
    assert len(back) <= 40, len(back)
    for k in back:
        posts[k] = None
    print('возвращено отметок «пост не нужен»: %d — %s' % (len(back), ', '.join(back)))
    if write and back:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    elif not write:
        print('сухой прогон')


if __name__ == '__main__':
    main('--write' in sys.argv)
