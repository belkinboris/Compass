"""g0b187624 — первоисточник о консультанте: новость на сайте АЛРУД, 23 октября 2026.

Владелец спросил, стоит ли в источниках сайт АЛРУД. Не стоял: была только
ссылка на пересказ в @LawFirms (агрегатор, лежит в discovery_src). Новость
нашлась на сайте фирмы — www.alrud.ru/publications/2080 от 22 октября 2026,
текст тот же. Добавляем её в src и ставим ссылкой в записи консультанта.
Без ключа — сухой прогон.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
URL = 'https://www.alrud.ru/publications/2080'
OLD = 'Источник: t.me/LawFirms/11566'
NEW = 'Источник: alrud.ru/publications/2080'


def apply(data):
    d = next(x for x in data['deals'] if x['id'] == 'g0b187624')
    if URL in {s[1] for s in d.get('src') or []}:
        return False
    adv = d['law']['adv']
    assert len(adv) == 1 and adv[0][1] == 'АЛРУД' and adv[0][2].endswith(OLD), adv
    adv[0][2] = adv[0][2][:-len(OLD)] + NEW
    d['src'].append(['АЛРУД', URL])
    return True


def main(write):
    if not apply(json.load(open(DATA, encoding='utf-8'))):
        print('уже есть'); return
    print('g0b187624: в источниках сайт АЛРУД (%s)' % URL)
    if write:
        data = json.load(open(DATA, encoding='utf-8'))  # перечитать прямо перед записью
        assert apply(data)
        with open(DATA, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
            f.write('\n')


if __name__ == '__main__':
    main('--write' in sys.argv)
