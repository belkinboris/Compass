# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка g741672ac (Kama Flow/
Platformeco): дельта-поиск (mergers.ru) нашёл ещё несколько фактов сверх
уже известного — кто был первым инвестором до Kama Flow, приоритеты
самого фонда и мнение независимого эксперта о размере инвестиции
относительно обычного профиля Kama Flow. Не через review.py: старое
значение eco.context — про структуру владения, отдельная часть статьи,
не образует непрерывный кусок с этими цитатами.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
Mergers.ru (03.10.2025), уже добавлен в src.
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g741672ac'

OLD_CONTEXT = (
    'По данным «СПАРК-Интерфакса», 65,04% ООО «Платформеко» (юрлицо '
    'Platformeco) принадлежит Сергею Шелухину, 18,4% – Александру '
    'Бондарику, 11,04% – Аркадию Юсупову. Также 5,52% компании у ООО '
    '«Портофино Кэпитал».'
)
ADDITION = (
    'На старте в Platformeco инвестировала Portofino Capital, созданная '
    'бывшим исполнительным директором J.P. Morgan Дмитрием Водянниковым. '
    'Детали процесса выхода «Леруа Мерлен» из Platformeco стороны не '
    'раскрывают. Kama Flow рассматривает инвестиции в инфраструктурный '
    'софт как одно из приоритетных направлений, сообщил инвестиционный '
    'директор компании Сергей Гайворонский. Обычно Kama Flow '
    'инвестирует в более зрелые компании с оборотом от 300 млн руб., но '
    'динамика Platformeco, вероятно, сделала проект интересным, говорит '
    'партнёр Startech.vc Елизавета Тихер. По её мнению, фонд может '
    'рассматривать возможность участия и в следующем инвестиционном '
    'раунде.'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} eco.context: += первый инвестор, приоритеты Kama Flow, оценка Startech.vc")
    deal['eco']['context'] = NEW_CONTEXT

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
