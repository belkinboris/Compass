"""g25a6766d (Baggins Coffee): заголовок переписан своими словами (28 октября 2026).

Карточка родилась с заголовком новости «Коммерсанта» дословно и так ушла в
консоль (партнер: «Заголовок буквально копирует заголовок из Коммерсанта»;
владелец: «мы же пересказываем и переделываем»). Заголовок — не поле переноса,
review.py требует для него дословной цитаты, поэтому правка разовым скриптом.
Факты — из статьи: 50% выкупил фонд «Бумеранг Капитал», 50% перешли Антону
Петрову, ранее компанию контролировал сооснователь Андрей Павлов.

    python3 pipeline/fix_2026_10_28_g25a6766d_title.py --write
"""
import json
import os
import sys

PENDING = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'data', 'pending.json')
OLD = 'Фонд «Бумеранг Капитал» стал совладельцем Baggins Coffee'
NEW = 'Фонд «Бумеранг Капитал» и Антон Петров выкупили сеть кофеен Baggins Coffee у ее сооснователя Андрея Павлова'


def main(argv):
    p = json.load(open(PENDING, encoding='utf-8'))
    c = next(x for x in p['cards'] if x['id'] == 'g25a6766d')
    assert c.get('title') == OLD, c.get('title')
    print('g25a6766d: заголовок → ' + NEW)
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    p = json.load(open(PENDING, encoding='utf-8'))
    c = next(x for x in p['cards'] if x['id'] == 'g25a6766d')
    assert c.get('title') == OLD
    c['title'] = NEW
    json.dump(p, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
