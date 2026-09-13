# -*- coding: utf-8 -*-
"""G6 — превосходная степень без меры у профиля «ООО «Стинн»» (`g3817a50b`).

Замер 13 сентября 2026: из 85 профилей со словом «крупнейший»/«ведущий» в
`desc` только у одного меры не было вовсе — «Холдинг Григория Садояна,
контролирующий крупнейшее рекламное агентство Russ и Russ Outdoor» (нет ни
страны, ни доли рынка, ни выручки — просто «крупнейшее»). Мера при этом уже
лежит в БАЗЕ, просто в другом поле: карточка сделки `gf424fa11` (Wildberries/
СП с Russ) несёт в `extra` дословно «ООО «Стинн» владеет крупнейшим
российским рекламным агентством Russ (выручка 28 млрд ₽ в 2023 году)» —
и страна, и цифра. Перенос факта из уже прочитанного поля в описание
профиля, а не новое исследование (тот же приём, что и G8-связки `holding`
18 августа/13 сентября).

Запуск:
    python3 pipeline/fix_stinn_russ_superlative_measure.py            # сухой прогон
    python3 pipeline/fix_stinn_russ_superlative_measure.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
COMPANY_ID = 'g3817a50b'

OLD_DESC = ('Холдинг Григория Садояна, контролирующий крупнейшее рекламное '
            'агентство Russ и Russ Outdoor; в 2023 году купил через Russ '
            'Outdoor агентство Gallery (Медиа-1 Аутдор).')
NEW_DESC = ('Холдинг Григория Садояна, контролирующий крупнейшее российское '
            'рекламное агентство Russ (выручка 28 млрд ₽ в 2023 году) и '
            'Russ Outdoor; в 2023 году купил через Russ Outdoor агентство '
            'Gallery (Медиа-1 Аутдор).')


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    company = data['companies'][COMPANY_ID]

    current = company.get('desc')
    if current == NEW_DESC:
        print('Уже применено — нечего делать.')
        return
    assert current == OLD_DESC, 'desc изменился с момента находки: %r' % current

    print('Профиль:', company['name'])
    print('Было: ', OLD_DESC)
    print('Станет:', NEW_DESC)

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    company['desc'] = NEW_DESC
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
