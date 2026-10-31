"""Профиль «Первая нерудная компания» (gbcf3f414): чем занимается (28 октября 2026).

Профиль заведен приемкой с описанием «род деятельности источник не
называет». Сайт компании 1pnk.ru и реестры: крупнейший производитель
нерудных материалов, основной поставщик путевого щебня для ОАО «РЖД»
(щебеночные заводы — Орский, Сибирцевский и другие).

    python3 pipeline/fix_2026_10_28_pnk_profile.py --write
"""
import json
import os
import sys

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'data', 'deals_promoted.json')
OLD = ('Акционерное общество, 25% плюс 1 акция которого принадлежали ОАО «РЖД» и теперь '
       'продаются на открытом аукционе; род деятельности источник не называет.')
NEW = ('Крупнейший в России производитель нерудных материалов и основной поставщик путевого '
       'щебня для ОАО «РЖД»: сеть щебеночных заводов от Поволжья до Приморья. 25% плюс 1 акцию '
       'общества РЖД выставили на открытый аукцион в октябре 2026 года.')


def main(argv):
    d = json.load(open(BASE, encoding='utf-8'))
    c = d['companies']['gbcf3f414']
    assert c.get('desc') == OLD, c.get('desc')
    print('gbcf3f414: описание профиля → ' + NEW)
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    d = json.load(open(BASE, encoding='utf-8'))  # перечитать прямо перед записью
    assert d['companies']['gbcf3f414'].get('desc') == OLD
    d['companies']['gbcf3f414']['desc'] = NEW
    json.dump(d, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
