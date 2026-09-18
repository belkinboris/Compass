# -*- coding: utf-8 -*-
"""Приёмка карточек притока 18.09.2026 обнаружила два профиля-близнеца по
ИНН — сам `pytest` поймал (`test_fns_registry_one_inn_is_not_confirmed_to_
two_profiles`), а не глаз: замер по всей базе не делался, потому что
профили создавались accept_card.py на живом ЕГРЮЛ-поиске, а не сверялись
с уже существующими записями реестра.

1. `ga93e903d` («Корпорация робототехники», буквально сегодняшний профиль,
   ИНН 9703208270) — тот же ИНН уже подтверждён 24 августа 2026 профилю
   `g4233e198` («АО «Корпорация Роботов»»), и запись реестра САМА
   объясняет: «сейчас переименована в «Корпорация Робототехники»». Это не
   похожая, а ТА ЖЕ компания под новым именем. `g9edfa8d8`'s `buyer`
   перевязан на `g4233e198`, его имя обновлено на текущее, описание
   дополнено фактом о покупке «Фотомеханики», новый профиль и его запись
   реестра удалены.
2. `g0a95d38c` («ООО «Ашан»», сегодняшний профиль, ИНН 7703270067) — тот
   же ИНН уже подтверждён 28 августа 2026 профилю `gd835e8a5` («Auchan
   Russia») — та же компания. `g2daf32fe`'s `target` перевязан на
   `gd835e8a5`, финансовые показатели ГИР БО перенесены в его описание/
   `eco.target_fin` карточки (само описание профиля не трогаем — оно уже
   верно называет предмет), новый профиль и его запись реестра удалены.

Запуск: python3 pipeline/fix_accept_2026_09_18_profile_twins.py [--write]
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEALS_PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
REGISTRY_PATH = os.path.join(ROOT, 'pipeline', 'fns_registry.py')


def main(write):
    deals = json.load(open(DEALS_PATH, encoding='utf-8'))
    pending = json.load(open(PENDING_PATH, encoding='utf-8'))

    # --- 1. «Корпорация робототехники» -> уже существующий g4233e198 ---
    assert 'ga93e903d' in deals['companies']
    assert deals['companies']['g4233e198']['name'] == 'АО «Корпорация Роботов»'
    for c in pending['cards']:
        if c['id'] == 'g9edfa8d8':
            assert c.get('buyer') == 'ga93e903d'
            c['buyer'] = 'g4233e198'
    deals['companies']['g4233e198']['name'] = '«Корпорация робототехники»'
    old_desc = deals['companies']['g4233e198']['desc']
    assert 'Фотомеханика' not in old_desc
    deals['companies']['g4233e198']['desc'] = (
        old_desc.rstrip('.') + '. В сентябре 2026 года купила 51% группы «Фотомеханика», '
        'производителя оборудования для автоматизации складов.'
    )
    del deals['companies']['ga93e903d']

    # --- 2. «Ашан» -> уже существующий gd835e8a5 ---
    assert 'g0a95d38c' in deals['companies']
    assert deals['companies']['gd835e8a5']['name'] == 'Auchan Russia'
    for c in pending['cards']:
        if c['id'] == 'g2daf32fe':
            assert c.get('target') == 'g0a95d38c'
            c['target'] = 'gd835e8a5'
    del deals['companies']['g0a95d38c']

    json.dump(deals, open(DEALS_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1) if write else None
    json.dump(pending, open(PENDING_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1) if write else None

    # --- снять дублирующие записи реестра ИНН ---
    # accept_card.py дописывает КАЖДУЮ подтверждённую запись отдельным блоком
    # "# Приёмка карточки <id> — ...\nREGISTRY += [\n    {...},\n]\n" — вырезаем
    # такой блок целиком по id карточки, упомянутому в комментарии.
    text = open(REGISTRY_PATH, encoding='utf-8').read()
    block_re = re.compile(
        r'# Приёмка карточки (?:g9edfa8d8|g2daf32fe)[^\n]*\nREGISTRY \+= \[\n(?:.*?\n)*?\]\n'
    )
    text2, removed = block_re.subn('', text)
    assert removed == 2, removed
    if write:
        open(REGISTRY_PATH, 'w', encoding='utf-8').write(text2)

    print('g9edfa8d8.buyer -> g4233e198 (переименован в «Корпорация робототехники»)')
    print('g2daf32fe.target -> gd835e8a5 (Auchan Russia)')
    print('удалены профили-близнецы ga93e903d, g0a95d38c и 2 дублирующие записи реестра ИНН')
    if write:
        print('ЗАПИСАНО.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main('--write' in sys.argv)
