# -*- coding: utf-8 -*-
"""У карточки `ge945a8e1` («Росатом планирует купить 50% в производителе
телеком-оборудования Future Technologies») поле `law.appr` несло факт о том,
что сделка не состоялась («Как сообщили TAdviser... сделки... не произошло»)
— дословная правка через `review.py`, снявшая устаревшее «Сделка находится
на согласовании ФАС» (статус карточки уже стоял «Не состоялась», текст поля
ему противоречил). Но `test_approval_names_a_body` справедливо потребовал,
чтобы непустое `law.appr` называло согласующий орган — а факт о срыве сделки
сам по себе органа не называет (TAdviser лишь передаёт слова самой компании,
без ФАС). Никакой источник не подтверждает, что ФАС вообще вынесла решение
по этой сделке (ни отказ, ни одобрение) — сделка сорвалась ДО завершения
рассмотрения, о самом решении ФАС публично не сообщалось.

Правильное поле — честный плейсхолдер, а не текст о срыве сделки (это уже
есть в `eco.rationale`/`status`). Не через `review.py`: снимается факт без
органа, а не добавляется новый — та же логика, что у скриптов снятия
протёкшей пометки роли (assert на исходное состояние вместо цитаты).

Запуск: python3 pipeline/fix_future_technologies_appr.py
        python3 pipeline/fix_future_technologies_appr.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'ge945a8e1'
OLD_APPR = ('Как сообщили TAdviser в компании Future Technologies в начале '
            'июня 2026 года, сделки по продаже доли в компании «Росатому» '
            'не произошло.')
NEW_APPR = 'Публично не сообщалось'


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    cards = {d['id']: d for d in data['deals']}
    card = cards[CARD_ID]
    assert card['law']['appr'] == OLD_APPR, (
        'law.appr уже другое — проверьте карточку заново')
    print('ПРАВИМ  %s law.appr: снят факт без согласующего органа, '
          'поставлен честный плейсхолдер' % CARD_ID)
    print('        (решение ФАС по этой сделке нигде не публиковалось — '
          'сделка сорвалась до его вынесения)')
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['law']['appr'] = NEW_APPR
    json.dump(data, open(BASE, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv[1:])
