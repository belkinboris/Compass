"""Второе чтение gb5456bba: в title буква «ё» ("продаёт") — правило владельца
26-27 октября 2026 требует «е» везде в текстах для людей. Точечная правка
только этой карточки (pending.json), не общий pipeline/strip_yo.py, чтобы не
трогать файлы других карточек/агентов в этом же дереве.

    python3 pipeline/fix_gb5456bba_title_yo_2026_10_30.py          # сухой прогон
    python3 pipeline/fix_gb5456bba_title_yo_2026_10_30.py --write
"""
import json
import sys

PATH = 'static/data/pending.json'
DID = 'gb5456bba'
OLD = '«Иртыш Ривьера» повторно продаёт базу отдыха «Иртышская Ривьера» под Омском'
NEW = '«Иртыш Ривьера» повторно продает базу отдыха «Иртышская Ривьера» под Омском'


def main():
    write = '--write' in sys.argv
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    card = next((c for c in data['cards'] if c.get('id') == DID), None)
    assert card is not None, 'карточка %s не в pending.json' % DID
    assert card.get('title') == OLD, ('title изменился с момента чтения', card.get('title'))
    print('%s: title ->' % DID, NEW)
    if write:
        card['title'] = NEW
        with open(PATH, encoding='utf-8') as f:
            fresh = json.load(f)
        fresh_card = next((c for c in fresh['cards'] if c.get('id') == DID), None)
        assert fresh_card is not None and fresh_card.get('title') == OLD, 'pending.json изменился под ногами'
        fresh_card['title'] = NEW
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(fresh, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('записано')
    else:
        print('сухой прогон — добавьте --write')


if __name__ == '__main__':
    main()
