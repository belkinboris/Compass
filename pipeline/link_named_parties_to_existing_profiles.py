# -*- coding: utf-8 -*-
"""Связывает `seller`/`buyer_name`, записанные ТЕКСТОМ, с уже существующим
профилем компании — если он уже есть в базе, просто под другой ролью в
другой сделке. Не путать с `link_orphan_profiles.py`: тот ищет первую
сделку профилям БЕЗ единой сделки; здесь профиль обычно уже занят другими
сделками (Банк «Траст» продал десятки активов), просто эта конкретная
сторона в этой конкретной карточке осталась текстом, хотя ссылку можно было
поставить сразу.

НАШЛОСЬ 18 августа при разборе жалобы владельца на карточку ПСБ/«Атом»:
«Кама» и «ПСБ» не кликались, хотя оба профиля уже существовали в базе.
Измерил класс целиком (точное совпадение нормализованного имени поля со
`seller`/`buyer_name` и именем существующего профиля, без `seller_id`/
`buyer`) — 21 карточка, не одна.

ГРАНИЦА — ТА ЖЕ, ЧТО В `link_orphan_profiles.py`, И НЕ ОСЛАБЛЯЕТСЯ: только
точное совпадение имени после снятия правовой формы и пунктуации, никакого
вхождения подстрокой. Та же причина: «Продавец — Морган Стэнли» и профиль
«Morgan Stanley (ТРЦ «Галерея»)» — по подстроке связались бы, а по смыслу
это профиль ПРЕДМЕТА, не стороны сделки. Проверено, что предмета в кандидате
не оказалось — все 21 профиля сверены глазами: описание профиля тематически
совпадает со сделкой (Михаил Бобров — «Балтийский берег», рыбопереработка;
Александр Клячин — недвижимость; Банк «Траст» — банк непрофильных активов,
уже известный многократный продавец, см. CLAUDE.md).

`buyer_name` удаляется при связывании (тест `test_buyer_is_named_once` не
даёt заполнить оба поля разом); `seller` текстом остаётся РЯДОМ с `seller_id`
— так уже устроено (интерфейс предпочитает профиль, текст не мешает).

Запуск:
    python3 pipeline/link_named_parties_to_existing_profiles.py            # проверка
    python3 pipeline/link_named_parties_to_existing_profiles.py --write    # запись
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

_OPF = re.compile(r'\b(ооо|ао|пао|оао|зао|нко|банк|акционерное общество|'
                   r'общество с ограниченной ответственностью)\b', re.I)
_PUNCT = re.compile(r'[^0-9a-zа-яё]+', re.I)


def norm(s):
    s = str(s or '').lower().replace('ё', 'е')
    s = _OPF.sub(' ', s)
    return ' '.join(_PUNCT.sub(' ', s).split())


# (id карточки, поле-текст, поле-ссылка, ожидаемый текст, id профиля) —
# проверка исходного состояния перед записью, найдено замером 18 августа.
LINKS = [
    ('g097e34b2', 'seller', 'seller_id', 'Росимущество', 'g9fd82fee'),
    ('g711eb87e', 'seller', 'seller_id', 'Банк «Траст»', 'gdc4235da'),
    ('gb5ac2288', 'seller', 'seller_id', 'Банк «Траст»', 'gdc4235da'),
    ('g05ca1a94', 'seller', 'seller_id', 'Банк «ФК Открытие»', 'g7ac0b3cc'),
    ('g37619a9e', 'buyer_name', 'buyer', 'Игорь Рыбаков', 'g601bcc88'),
    ('g7d64b437', 'seller', 'seller_id', '«Газпром Тех»', 'g6261c82c'),
    ('g9876feaa', 'seller', 'seller_id', 'Банк «Траст»', 'gdc4235da'),
    ('g506ea8c4', 'seller', 'seller_id', 'Михаил Бобров', 'g09bfb452'),
    ('g34cab70b', 'seller', 'seller_id', 'Александр Рязанов', 'ga09351d2'),
    ('g7b4be1c4', 'seller', 'seller_id', 'Евгений Туголуков', 'g66c1d4b8'),
    ('gd38acdec', 'seller', 'seller_id', 'ООО «Формат Инвест»', 'g14d905f4'),
    ('g26b319ff', 'seller', 'seller_id', 'Банк «Траст»', 'gdc4235da'),
    ('g5e4677da', 'seller', 'seller_id', 'Александр Клячин', 'gb9c8945c'),
    ('g7d5f252d', 'seller', 'seller_id', 'Банк «Траст»', 'gdc4235da'),
    ('g5f0d5d18', 'seller', 'seller_id', 'Банк «Траст»', 'gdc4235da'),
    ('g256dd345', 'seller', 'seller_id', 'Банк «Траст»', 'gdc4235da'),
    ('gff984390', 'seller', 'seller_id', 'Банк «Траст»', 'gdc4235da'),
    ('g16a70078', 'seller', 'seller_id', 'Банк «Траст»', 'gdc4235da'),
    ('ce7b84bec', 'buyer_name', 'buyer', 'АО «Управление активами»', 'gf0a760bf'),
    ('ca754c77a', 'seller', 'seller_id', 'Банк «Траст»', 'gdc4235da'),
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    cards = {d['id']: d for d in data['deals']}
    companies = data['companies']

    for cid, text_field, id_field, expected_text, profile_id in LINKS:
        card = cards[cid]
        assert card.get(text_field) == expected_text, (
            '%s.%s: ожидали %r, сейчас %r — состояние изменилось'
            % (cid, text_field, expected_text, card.get(text_field)))
        assert not card.get(id_field), (
            '%s.%s уже заполнено (%r) — состояние изменилось'
            % (cid, id_field, card.get(id_field)))
        assert profile_id in companies, '%r должен уже существовать' % profile_id
        assert norm(expected_text) == norm(companies[profile_id]['name']), (
            '%s: имя %r и профиль %r разошлись после нормализации — проверьте вручную'
            % (cid, expected_text, companies[profile_id]['name']))

    print('Связок: %d' % len(LINKS))
    for cid, text_field, id_field, expected_text, profile_id in LINKS:
        print('  %s.%s (%r) -> %s.%s = %r'
              % (cid, text_field, expected_text, cid, id_field, profile_id))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    for cid, text_field, id_field, _expected_text, profile_id in LINKS:
        card = cards[cid]
        card[id_field] = profile_id
        if id_field == 'buyer':
            # buyer/buyer_name взаимоисключающие — держит test_buyer_is_named_once.
            del card['buyer_name']

    json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
