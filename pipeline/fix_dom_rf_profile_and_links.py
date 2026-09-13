# -*- coding: utf-8 -*-
"""Единый профиль «АО «ДОМ.РФ»» — сквозной паттерн из аудита адреса фактов
(13 сентября 2026, отчёт `pipeline/audit_field_placement/2026-09-13-report.md`,
пункт 9 сквозных паттернов): «Дом.РФ» упоминалась стороной сделки текстом,
без единого профиля, минимум в четырёх разных партиях аудита — измерено по
всей базе: 6 карточек называют «Дом.РФ» продавцом или покупателем (`seller`/
`buyer_name`) без привязки к профилю (класс UNLINKED_PARTY).

Кто это: финансовый институт развития в жилищной сфере (поддержка ипотеки,
инфраструктурные облигации, аренда жилья, управление земельными ресурсами
для застройки, торги недвижимостью) — образован в 1997 году, переименован
в АО «ДОМ.РФ» в 2018 году. Факты подтверждены живым поиском (Википедия,
finance.mail.ru, gazprombank.investments), а не выдуманы; точный ИНН
публичный поиск ЕГРЮЛ по краткому имени не разрешает (юрлицо зарегистрировано
под другим полным наименованием) — оставлен пустым, как и у уже существующего
профиля «Росимущество» (тоже без ИНН).

Пишет: новый профиль в `companies`, `match_keys` для него, и привязывает
шесть уже названных карточек (`buyer`/`seller_id`) без придумывания новых
фактов — сама сделка не меняется, только появляется кликабельная сторона.
Assert на исходном состоянии — обычная защита от повторного запуска.
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit(os.sep + 'pipeline', 1)[0]
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

NEW_ID = 'gb2b066c3'
NEW_PROFILE = {
    'name': 'АО «ДОМ.РФ»',
    'ind': 'Профессиональные услуги',
    'desc': ('Финансовый институт развития в жилищной сфере: поддержка ипотечного '
             'кредитования, инфраструктурные облигации, развитие рынка арендного '
             'жилья, управление земельными ресурсами для застройки и продажа '
             'непрофильной недвижимости с торгов. Образован в 1997 году как АИЖК, '
             'переименован в АО «ДОМ.РФ» в 2018 году.'),
    'kpi': ['Профиль', 'Автоматический'],
}
MATCH_KEYS = ['дом.рф', 'дом рф']

# (id карточки, роль, текстовое поле, значение) — сверка перед записью.
LINKS = [
    ('gdfce7e3d', 'buyer', 'buyer_name', '«Дом.РФ»'),
    ('g9254527a', 'seller', 'seller', 'Дом.РФ'),
    ('g8827d795', 'seller', 'seller', 'Дом.РФ'),
    ('g7ea48d66', 'seller', 'seller', '«Дом.РФ»'),
    ('g3ecb7b86', 'buyer', 'buyer_name', '«Дом.РФ»'),
    ('gce803e3f', 'seller', 'seller', '«Дом.РФ»'),
]


def main(write):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    comps = data['companies']
    assert NEW_ID not in comps, 'id профиля уже занят'
    by_id = {c['id']: c for c in data['deals']}

    for cid, role, text_field, expected_text in LINKS:
        card = by_id[cid]
        assert card.get(text_field) == expected_text, (cid, text_field, card.get(text_field))
        if role == 'buyer':
            assert not card.get('buyer'), (cid, 'buyer уже привязан')
        else:
            assert not card.get('seller_id'), (cid, 'seller_id уже привязан')

    comps[NEW_ID] = NEW_PROFILE
    data.setdefault('match_keys', {})[NEW_ID] = MATCH_KEYS
    print('Новый профиль:', NEW_ID, NEW_PROFILE['name'])

    for cid, role, text_field, _expected_text in LINKS:
        card = by_id[cid]
        if role == 'buyer':
            card['buyer'] = NEW_ID
            card.pop('buyer_name', None)
        else:
            card['seller_id'] = NEW_ID
        print('  %s: %s -> %s' % (cid, role, NEW_ID))

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('Сухой прогон — для записи передайте --write')


if __name__ == '__main__':
    import sys
    main('--write' in sys.argv)
