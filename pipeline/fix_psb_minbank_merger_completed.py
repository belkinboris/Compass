# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gadd949cc` («Промсвязьбанк стал собственником Московского
индустриального банка», январь 2023, Закрыта) — что случилось с
МИнБанком дальше (присоединение или отдельная работа) не было
отражено.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- interfax.ru/business/898856: «Промсвязьбанк (ПСБ) 1 мая завершил
  присоединение Московского индустриального банка»; «Все клиенты
  МИнБанка будут переведены на обслуживание в ПСБ».

НЕ ВНЕСЕНО: точная дата аннулирования записи о регистрации МИнБанка как
отдельного юрлица (встретилась только в сниппете banki.ru, не в
дословно прочитанной странице — TASS отдал 403, banki.ru не
отрендерился); отдельно найденная, явно устаревшая или ошибочная
страница bankodrom.ru, утверждающая, что банк «действующий» по
состоянию на июль 2026 года, — прямо противоречит надёжно
подтверждённому присоединению 2023 года и не используется.

Запуск: python3 pipeline/fix_psb_minbank_merger_completed.py
        python3 pipeline/fix_psb_minbank_merger_completed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gadd949cc'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    '1 мая 2023 года ПСБ завершил присоединение МИнБанка: банк '
    'прекратил существование как отдельное юрлицо, все клиенты '
    'переведены на обслуживание в ПСБ.'
)

OLD_SRC = [
    ['Интерфакс', 'https://www.interfax.ru/business/881350'],
]
NEW_SRC = OLD_SRC + [
    ['Интерфакс', 'https://www.interfax.ru/business/898856'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
