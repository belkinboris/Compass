# -*- coding: utf-8 -*-
"""Месячная очередь, 8 сентября 2026 — карточка `cea87de0a` (Selgros
продал 100% группы «Зельгрос Россия» компании «Ароса-Логистика», ноябрь
2024) несла оптимистичный прогноз («продолжат работать под собственными
брендами»), который не подтвердился. Личный WebFetch
(kommersant.ru/doc/8815346, 15.07.2026): «выручка сети сократилась на
92%, до 667 млн руб., чистый убыток составил 1,1 млрд руб.» (2025 год);
«Последний торговый объект сети был закрыт в мае 2025 года» — то есть
розничная сеть «Зельгрос Cash & Carry» прекратила работу целиком;
«Консалтинговая компания Molga подала заявление о признании ООО
«Зельгрос» банкротом».

Поле `eco.context` не проходило вычитку — правка обычная.

Запуск:
    python3 pipeline/fix_selgros_zelgros_closure_followup.py            # сухой прогон
    python3 pipeline/fix_selgros_zelgros_closure_followup.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
CARD_ID = 'cea87de0a'

OLD_CONTEXT = (
    '«Зельгрос Cash & Carry» и «Глобал Фудс», входящие в группу '
    '«Зельгрос Россия», продолжат работать под собственными брендами, '
    'несмотря на смену собственника.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' Прогноз не подтвердился: последний магазин сети закрылся в мае '
    '2025 года, выручка ООО «Зельгрос» за 2025 год упала на 92% до 667 '
    'млн ₽ при чистом убытке 1,1 млрд ₽, и консалтинговая компания Molga '
    'подала заявление о признании ООО «Зельгрос» банкротом.'
)


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}
    card = by_id[CARD_ID]

    assert card['eco']['context'] == OLD_CONTEXT, \
        'eco.context уже другой: %r' % (card['eco']['context'],)

    print('eco.context: добавляется факт о закрытии сети и заявлении о '
          'банкротстве (Коммерсантъ, 15.07.2026)')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    card['eco']['context'] = NEW_CONTEXT

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
