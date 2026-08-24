# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g23cad370 («Полиметалл»/Новая охотская
рудная компания): дельта-поиск нашёл, что «Полиметалл»-продавец в этой
карточке — это НЕ международная Polymetal International (та ушла с
российского рынка), а российское АО «Полиметалл», с февраля 2024 года
принадлежащее группе «Мангазея» Сергея Янчукова. Не через `review.py`:
факт из того же источника (Коммерсантъ, doc/8025397), что уже дал
текущий `eco.context`, но не образует с ним непрерывный кусок текста
(WebFetch подтвердил: сведения в разных абзацах статьи).

Источники — читал напрямую (WebFetch, дословные цитаты подтверждены):
https://www.kommersant.ru/doc/8025397
https://ria.ru/20240219/polymetal-1928152416.html

Запуск: python3 pipeline/fix_norc_okhotskaya_seller_identity.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g23cad370'

OLD_CONTEXT = (
    'НОРК создана в 2021 году как совместное предприятие (СП) '
    '«Полиметалла» и Новой рудной компании (НРК; сегодня называется '
    '«Восток»), подразделения корпорации «Энергия» экс-главы '
    'Минэнерго Игоря Юсуфова. Как сообщал «Интерфакс», НРК внесет в СП '
    'участок Высокий, ресурсы которого по классификации РФ оцениваются '
    'в 37,2 тонны золота, «Полиметалл» — Ветвистый, Охотская ГГК — '
    'Пуркикит. В 2023 году «Полиметалл» консолидировал НОРК.'
)
CONTEXT_ADDITION = (
    ' Сергей Янчуков, выкупивший российский бизнес золотодобытчика '
    '«Полиметалл» (MOEX: POLY), оптимизирует портфель этой компании '
    '(Коммерсантъ). Золотодобывающая компания Polymetal International '
    'продала российский бизнес структуре компании «Мангазея», исходя '
    'из оценки в 3,69 миллиарда долларов, в феврале 2024 года (РИА '
    'Новости) — то есть к моменту сделки с Охотской ГГК «Полиметалл» '
    'уже больше года как российское юрлицо под контролем группы '
    '«Мангазея», а не часть международной Polymetal International.'
)
NEW_CONTEXT = OLD_CONTEXT + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f'{CARD_ID} eco.context: += кто такой продавец «Полиметалл» '
          f'(АО под контролем Мангазеи/Янчукова, не Polymetal International)')

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
