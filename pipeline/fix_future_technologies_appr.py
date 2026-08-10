# -*- coding: utf-8 -*-
"""У карточки `ge945a8e1` («Росатом планирует купить 50% в производителе
телеком-оборудования Future Technologies») статус уже стоит «Не состоялась»,
но `law.appr` всё ещё несёт устаревшее «Сделка находится на согласовании
ФАС.» — прямое противоречие внутри карточки. Источник (TAdviser, уже в src)
подтверждает срыв сделки («сделки по продаже доли в компании «Росатому» не
произошло»), но эта дословная цитата не называет согласующий орган и не
проходит `test_approval_names_a_body`, если положить её в `law.appr` как
есть (проверено на параллельном потоке rev10 в ту же ночь — там тем же
пришлось оставить поле нетронутым по этой же причине). Никакой источник не
подтверждает, что ФАС вообще вынесла решение по этой сделке (ни отказ, ни
одобрение) — сделка сорвалась ДО завершения рассмотрения, о самом решении
ФАС публично не сообщалось.

Правильное поле — честный плейсхолдер, а не текст о срыве сделки (это уже
есть в `eco.rationale`/`status`/`extra`). Не через `review.py`: снимается
факт без органа, а не добавляется новый — та же логика, что у скриптов
снятия протёкшей пометки роли (assert на исходное состояние вместо цитаты).

Запуск: python3 pipeline/fix_future_technologies_appr.py
        python3 pipeline/fix_future_technologies_appr.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

CARD_ID = 'ge945a8e1'
OLD_APPR = 'Сделка находится на согласовании ФАС.'
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
