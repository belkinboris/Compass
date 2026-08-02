# -*- coding: utf-8 -*-
"""Служебная пометка о сторонах, утёкшая в конец «Цели сделки».

ЧТО СЛОМАНО. У 17 карточек `eco.rationale` (и продублированное в `extra` —
те же 17, слово в слово, см. правило «одинаковый текст лежит в двух полях»)
заканчивается техническим хвостом вида «(Продавец: ГК «Михайлов и
Партнеры»)», «(покупатель En+ Group / ООО «Парк-отель Бурдугуз»)»,
«(продавец ЕБРР / покупатель Александр Рязанов)» — похоже на разметку,
которой помечали стороны при разборе источника, и которую забыли убрать
перед тем, как текст попал на карточку. Сторона в каждом случае уже названа
явно чуть выше по тексту (проверено на всех 17 вручную) — хвост не добавляет
факта, только повторяет его канцелярским фрагментом.

ЧТО ДЕЛАЕМ. Отрезаем ровно этот хвост — последнюю скобку в конце строки,
если внутри неё есть слово «продав»/«покупател»/«инвестор»/«эмитент»/
«получател» (регистронезависимо). Скобки ВНУТРИ текста (не в конце) не
трогаем — у сделки может быть несколько скобочных вставок подряд, и только
самая последняя — служебный хвост (пример: g5809b7a2, «...(официально не
раскрывается). (Покупатель: ООО «Деметра-Холдинг»)» — стрижём только
вторую). Меняем оба поля, `eco.rationale` и `extra`, если хвост есть в обоих.

ЧЕГО НЕ ДЕЛАЕМ. Не сочиняем замену — если после стрижки в конце не осталось
знака препинания, ничего не дописываем: то, что было до хвоста, уже
самостоятельное предложение с точкой.

Запуск:
    python3 pipeline/fix_leaked_party_tags.py            # сухой прогон
    python3 pipeline/fix_leaked_party_tags.py --write    # записать
"""
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'
TAG = re.compile(
    r'\s*\([^()]*(?:продав|покупател|инвестор|эмитент|получател)[^()]*\)\s*$', re.I)

# 17 карточек, найденные прогоном 1 августа — если после стрижки список не
# совпадёт (карточка исчезла/появилась новая), скрипт остановится вместо
# того, чтобы молча захватить лишнее.
EXPECTED_IDS = {
    'g6ccd4122', 'gd4c470d0', 'g15b9d8e2', 'g1d003324', 'g7596ae81',
    'g97a4c417', 'ge292671d', 'gfeb4e569', 'g1e73548b', 'ge578141f',
    'g5809b7a2', 'gecede2fc', 'g36386bcf', 'g37066bfe', 'g184477ed',
    'gf0b712ef', 'g1f43265d',
}


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)

    touched_ids = set()
    changes = []
    for d in data['deals']:
        eco = d.get('eco') or {}
        for label, obj, key in (('eco.rationale', eco, 'rationale'), ('extra', d, 'extra')):
            old = obj.get(key)
            if not old or not TAG.search(old):
                continue
            new = TAG.sub('', old)
            assert new != old and len(new) < len(old)
            touched_ids.add(d['id'])
            changes.append((d['id'], label, old, new))
            if write:
                obj[key] = new

    unexpected = touched_ids - EXPECTED_IDS
    missing = EXPECTED_IDS - touched_ids
    assert not unexpected, f'нашлись новые карточки с хвостом, не в списке ожидаемых: {unexpected}'
    assert not missing, f'ожидаемые карточки не задеты — хвост пропал раньше скрипта: {missing}'

    print(f'карточек затронуто: {len(touched_ids)}, правок полей: {len(changes)}')
    for did, label, old, new in changes:
        print(f'  {did} [{label}]')
        print(f'    было:  …{old[-90:]!r}')
        print(f'    стало: …{new[-90:]!r}')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в', PATH)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
