# -*- coding: utf-8 -*-
"""Разовая правка g097e34b2 (Избрехт/«Южгазэнерджи»): `target` указывал на
профиль совсем другой сущности.

ЧТО СЛОМАНО. `target` карточки — `g9fd82fee`, а его `name` — «Росимущество».
Родня уже описанного в CLAUDE.md урока (ЛСР/Domina Пулково, «Стороной сделки
может быть записан профиль совсем другой сущности»): предмет сделки —
газодобывающая компания «Южгазэнерджи», а не продавец-регулятор. Профиль
`g9fd82fee` не используется больше НИ ОДНОЙ сделкой (проверено прямым
поиском по базе) — это чистая ошибка привязки, не переиспользуемый профиль,
который нужно было бы сохранить.

ПОЧЕМУ НАШЛОСЬ ИМЕННО СЕЙЧАС. Правка регистра `seller`
(«Росимущества» → «Росимущество», партия 3 REVISION_BRIEF) впервые сделала
`seller` дословно совпадающим с именем профиля `target` — до этого
`test_asset_is_not_a_party` (точнее, его сестринская проверка на дубль имени
стороны и предмета) не видела совпадения из-за разных падежей. Профиль был
сломан и раньше, просто тест не мог этого поймать.

ЧТО ДЕЛАЕТСЯ. Как и в прецеденте ЛСР/Domina Пулково: профиль не
переименовывается (нечем доказать, что старый профиль вообще должен был
существовать), а создаётся новый, верный — лот из двух юрлиц, купленных
одним лотом по тексту самой карточки (`eco.share`/`extra`: «100% уставного
капитала ООО «Южгазэнерджи»... 100% ООО «Кейтеринг-Юг»»), с признаком `lot`
(тот же класс, что и другие лотовые профили базы, например
`g7bbe19c2-target`). `target` карточки перенаправляется на новый профиль,
старый ошибочный удаляется — на него не было ни одной другой ссылки.

Запуск:
    python3 pipeline/fix_yuzhgazenerdzhi_target_profile.py            # сухой прогон
    python3 pipeline/fix_yuzhgazenerdzhi_target_profile.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g097e34b2'
OLD_TARGET = 'g9fd82fee'
NEW_TARGET = 'g097e34b2-target'

NEW_PROFILE = {
    'name': 'ООО «Южгазэнерджи» и ООО «Кейтеринг-Юг»',
    'ind': 'Нефть и газ',
    'desc': 'Единственное крупное газодобывающее предприятие и основной '
            'поставщик газа в Республике Адыгея, лицензия на разведку и '
            'добычу углеводородов на Кошехабльском ГКМ; проданы одним '
            'лотом на приватизационном аукционе Росимущества в 2026 году.',
    'kpi': ['Профиль', 'Автоматический'],
    'lot': True,
}


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)
    comps = data['companies']

    assert deal.get('target') == OLD_TARGET, \
        '%s: target уже не %r' % (DEAL_ID, OLD_TARGET)
    assert comps.get(OLD_TARGET, {}).get('name') == 'Росимущество', \
        'профиль %s больше не «Росимущество» — проверить вручную' % OLD_TARGET
    assert not any(d.get('target') == OLD_TARGET or d.get('buyer') == OLD_TARGET
                   for d in data['deals'] if d['id'] != DEAL_ID), \
        'профиль %s используется другой сделкой — удалять нельзя' % OLD_TARGET
    assert NEW_TARGET not in comps, '%s уже существует' % NEW_TARGET

    print('БЫЛО: target=%s (%r)' % (OLD_TARGET, comps[OLD_TARGET]['name']))
    print('СТАНЕТ: target=%s (%r)' % (NEW_TARGET, NEW_PROFILE['name']))
    print('Удаляется ошибочный профиль %s.' % OLD_TARGET)

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    comps[NEW_TARGET] = NEW_PROFILE
    deal['target'] = NEW_TARGET
    del comps[OLD_TARGET]

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
