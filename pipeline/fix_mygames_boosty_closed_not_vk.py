# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gc6322659` («My.Games выставила платформу Boosty на продажу», статус
«Обсуждается», 2023-08-21) — сделка закрылась, но не с тем покупателем,
которого предполагала карточка.

Проверено (по докладу саб-агента, дословные цитаты):
- kommersant.ru/doc/6863712 (уже в `src`): «My.Games... продает эти
  активы структурам кипрского бизнесмена Павла Харанеки», Харанеки —
  «основатель Broadsmart Group»; «Стоимость сделки не раскрывается»;
  «Аналитики оценивали актив в $5–10 млн»; решение позволит My.Games
  «полностью сосредоточиться на своем приоритетном бизнесе: разработке и
  публикации игр».
- mergers.ru/news/MyGames-prodal-Boosty-i-Donation-Alerts-...: «My.Games
  через нидерландскую CEBC B.V. владеет сервисами монетизации контента
  Boosty и Donation Alerts» — то есть предметом были ДВА сервиса, не
  только Boosty.
- about.my.games/ru/news/300-my-games-completes-sale-of-...: «MY.GAMES
  Completes Sale of DonationAlerts and Boosty Platforms» — пресс-релиз
  датирован 11 декабря 2024 года, «the deal, originally announced in
  July 2024 and initiated as part of a restructuring process in 2023».

Гипотеза карточки («по неофициальным данным, сервис может достаться
VK») НЕ подтвердилась — VK ни разу не упоминается как участник сделки ни
в одном из проверенных материалов о её закрытии, только как прежний,
2022 года, владелец самой My.Games.

Статус меняется на «Закрыта» — сделка прямо названа закрытой и завершённой
собственным пресс-релизом My.Games. `buyer_name` заполняется текстом
(профиль под структуру Харанеки заводить не стоит — единственная сделка
в базе).

НЕ ВНЕСЕНО: текущее состояние платформы Boosty на 2025-2026 год — саб-агент
не проверял отдельно, оставлено на будущий заход, если появится повод.

Запуск: python3 pipeline/fix_mygames_boosty_closed_not_vk.py
        python3 pipeline/fix_mygames_boosty_closed_not_vk.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gc6322659'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_BUYER_NAME = None
NEW_BUYER_NAME = 'Структуры Павла Харанеки (Broadsmart Group)'

OLD_RATIONALE = (
    'По неофициальным данным, сервис может достаться VK: это позволило'
    ' бы холдингу объединить платформу с VK Donut и привлечь новых'
    ' авторов и создателей контента'
)
NEW_RATIONALE = (
    'Актив достался не VK, как предполагалось, а структурам кипрского'
    ' бизнесмена Павла Харанеки (Broadsmart Group); сделка вместе с'
    ' сервисом Donation Alerts закрылась в декабре 2024 года. По словам'
    ' продавца, решение позволит My.Games сосредоточиться на приоритетном'
    ' бизнесе — разработке и издании игр.'
)

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'Предметом сделки были сразу два сервиса — Boosty и Donation Alerts,'
    ' которыми My.Games владела через нидерландскую CEBC B.V. Сумма'
    ' сделки не раскрывалась.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal.get('buyer_name') == OLD_BUYER_NAME
    assert deal['eco']['rationale'] == OLD_RATIONALE
    assert deal['law']['struct'] == OLD_LAW_STRUCT

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== buyer_name: станет ===')
    print(NEW_BUYER_NAME)
    print('\n=== eco.rationale: станет ===')
    print(NEW_RATIONALE)
    print('\n=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)

    if write:
        deal['status'] = NEW_STATUS
        deal['buyer_name'] = NEW_BUYER_NAME
        deal['eco']['rationale'] = NEW_RATIONALE
        deal['law']['struct'] = NEW_LAW_STRUCT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
