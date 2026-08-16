# -*- coding: utf-8 -*-
"""Откат ошибки из `fix_yuzhgazenerdzhi_target_profile.py`: профиль
«Росимущество» (`g9fd82fee`) удалён напрасно.

ЧТО СЛОМАНО. Прошлый скрипт проверил, что `g9fd82fee` не используется как
`buyer`/`target` НИ ОДНОЙ другой сделкой, и на этом основании удалил его —
но не проверил поле `seller_id` (отдельная от текстового `seller` ссылка на
профиль продавца) и `match_keys`. На деле профиль «Росимущество» —
ЗАКОННЫЙ, переиспользуемый профиль продавца для приватизационных сделок:
на него ссылаются через `seller_id` 8 других сделок, и тест
`test_company_refs_resolve`/`test_match_keys_point_to_existing_profiles`
поймал разрыв сразу после записи. Ошибочным был только `target` карточки
g097e34b2 (уже починен на верный лотовый профиль в прошлом скрипте) — сам
профиль «Росимущество» ошибочным не был.

ЧТО ДЕЛАЕТСЯ. Возвращает профиль `g9fd82fee` в `companies` ровно с тем же
содержимым, с которым он был до удаления. `target` карточки g097e34b2
НЕ трогается — он уже указывает на верный профиль
`g097e34b2-target` («Южгазэнерджи»/«Кейтеринг-Юг»), и это остаётся так.

Запуск:
    python3 pipeline/fix_restore_rosimushchestvo_profile.py            # сухой прогон
    python3 pipeline/fix_restore_rosimushchestvo_profile.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

PROFILE_ID = 'g9fd82fee'
PROFILE = {
    'name': 'Росимущество',
    'ind': 'Профессиональные услуги',
    'desc': 'Федеральное агентство по управлению государственным '
            'имуществом: приватизация и продажа активов с торгов.',
    'kpi': ['Профиль', 'Автоматический'],
}


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']

    assert PROFILE_ID not in comps, '%s уже в базе — нечего восстанавливать' % PROFILE_ID
    users = [d['id'] for d in data['deals'] if d.get('seller_id') == PROFILE_ID]
    assert users, 'ни одна сделка не ссылается на %s через seller_id — восстанавливать незачем' % PROFILE_ID
    print('Восстанавливается профиль %s ("%s"), на него ссылаются %d сделок через seller_id.'
          % (PROFILE_ID, PROFILE['name'], len(users)))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    comps[PROFILE_ID] = PROFILE
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
