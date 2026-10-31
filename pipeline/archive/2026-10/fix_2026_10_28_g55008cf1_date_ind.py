"""«Ломбард 888» / «Ломбардный дом» (g55008cf1, очередь): дата и отрасль (28 октября 2026).

Пресс-релиз покупателя на lombard888.ru датирован 26 октября 2026 и говорит
«закрыла сделку»; карточка стояла с датой 27 октября (день заметки Mergers.ru,
по которой сделку нашли) и отраслью «Не определена». Ломбарды — «Финансовые
услуги».

    python3 pipeline/fix_2026_10_28_g55008cf1_date_ind.py --write
"""
import json
import os
import sys

PENDING = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'data', 'pending.json')
SRC = ['Lombard888.ru (пресс-релиз покупателя)', 'https://lombard888.ru/news/lombard-888-sovershil-krupneyshuyu-sdelku-na-lombardnom-rynke-rossii-v-2026-godu-i-priobrel-set-iz-3/']


def main(argv):
    p = json.load(open(PENDING, encoding='utf-8'))
    c = next(x for x in p['cards'] if x['id'] == 'g55008cf1')
    assert c.get('date') == '2026-10-27' and c.get('ind') == 'Не определена', (c.get('date'), c.get('ind'))
    print('g55008cf1: дата 2026-10-27 → 2026-10-26 (пресс-релиз покупателя), отрасль → «Финансовые услуги»')
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    c['date'] = '2026-10-26'
    c['ind'] = 'Финансовые услуги'
    for e in c.get('events') or []:
        if e.get('kind') == 'closed' and e.get('date') == '2026-10-27':
            e['date'] = '2026-10-26'
            e['source'] = SRC
    json.dump(p, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
