"""«Вложился» → «проинвестировал» в заголовках, 21 октября 2026.

Владелец: «Не пиши больше „вложился“, пиши „проинвестировал“». Шесть
заголовков базы. Снимок вышедших постов (`telegram_post_state`) правится тем
же словом, чтобы смена заголовка не вызвала «⟳ Обновлено» старых постов.
Без ключа — сухой прогон; --write перечитывает базу прямо перед записью.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
WORDS = (('вложился', 'проинвестировал'), ('вложилась', 'проинвестировала'), ('вложила', 'проинвестировала'),
         ('вложили', 'проинвестировали'), ('вложил', 'проинвестировал'))


def fix(title):
    for old, new in WORDS:
        title = re.sub(r'\b%s\b' % old, new, title)
    return title


def main(write):
    data = json.load(open(DATA, encoding='utf-8'))
    state = data.get('telegram_post_state') or {}
    n = 0
    for d in data['deals']:
        new = fix(d.get('title') or '')
        if new != d.get('title'):
            print('%s: %s\n   -> %s' % (d['id'], d['title'], new))
            d['title'] = new
            if isinstance(state.get(d['id']), dict) and state[d['id']].get('title'):
                state[d['id']]['title'] = fix(state[d['id']]['title'])
            n += 1
    print('заголовков:', n)
    if write and n:
        with open(DATA, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
            f.write('\n')


if __name__ == '__main__':
    main('--write' in sys.argv)
