# -*- coding: utf-8 -*-
"""Карточка g654a1ce5 (особняк в Тюмени, объявление о продаже): `no_parties`
— пояснение читателю, почему у сделки M&A нет ни покупателя, ни продавца, а
не перенос цитаты источника. `review.py` отказывает на этом поле (значение
не лежит ни в одной дословной цитате целиком — тот же класс, что `no_parties`
у g17a522dc, docs/card_editing_scripts.md, «Когда review.py не подходит»),
поэтому пишется прямой правкой JSON, с проверкой старого значения.
Запись синхронизирована с fixes/g654a1ce5_mansion_2026_11_19.py (там та же
пара old/new — для истории и чтобы review.py не нашел рассинхрона).

Запуск: python3 pipeline/archive/2026-11/fix_g654a1ce5_no_parties_2026_11_19.py --write
"""
import json
import sys

PENDING = 'static/data/pending.json'

NEW = ('Продавец и покупатель не раскрыты: частное риелторское объявление о продаже на сайте '
       'недвижимости не называет собственника, сделка не заключена — покупателя еще нет.')


def main():
    write = '--write' in sys.argv
    data = json.load(open(PENDING, encoding='utf-8'))
    card = next((c for c in data['cards'] if c.get('id') == 'g654a1ce5'), None)
    if card is None:
        raise SystemExit('карточка g654a1ce5 не найдена в pending.json')
    assert card.get('no_parties') is None, 'no_parties уже заполнено: %r' % card.get('no_parties')
    if write:
        # Перечитываем файл прямо перед записью — не затереть чужой пуш.
        data = json.load(open(PENDING, encoding='utf-8'))
        card = next((c for c in data['cards'] if c.get('id') == 'g654a1ce5'), None)
        assert card is not None and card.get('no_parties') is None
        card['no_parties'] = NEW
        json.dump(data, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('Записано: g654a1ce5.no_parties')
    else:
        print('Сухой прогон: g654a1ce5.no_parties -> %r' % NEW)


if __name__ == '__main__':
    main()
