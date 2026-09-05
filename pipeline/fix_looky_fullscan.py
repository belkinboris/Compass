# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g3fce1b7d` («Looky привлекла 300 млн руб. от частных инвесторов»,
закрыта, 2023) — предмет сделки не был описан вовсе (eco.share/
target_fin — заглушки), хотя источники рассказывают о продукте и о
дальнейшей судьбе компании достаточно подробно.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- cnews.ru/news/top/2023-04-11_investory_vlozhilis_po-krupnomu:
  «представители Looky отвечать отказались, заявив лишь, что это
  "частные российские инвесторы с опытом инвестирования в ИТ-стартапы"»;
  «Looky принадлежит компании CSDevelopment LLC, зарегистрированной в
  Тбилиси (Грузия)»;
- vc.ru/money/661810-...: «Раунд в размере 300 млн рублей Looky
  привлекла при поддержке инвестфирмы "Восход Капитал", основанной
  Михаилом Афониным»;
- sostav.ru/publication/sotsset-59943.html: функционал — «посты,
  сторис, фото- и видеоредактор, фильтры, хештеги, комментарии и
  директ»; цель — привлечь «не менее 10% российских пользователей
  Instagram к 2024 году»;
- vc.ru/theedinorogblog/3075124 (2026, обзор компании спустя годы):
  «В 2024-м половиной поделилась с АО УК "Апрель Капитал". И сейчас
  владеют почти поровну — 57% и 43%»; «компания привлекла более 500
  млн рублей инвестиций» [с 2022 года]; «у них 7 млн зарегистрированных
  пользователей»; финансы по годам — 2022: выручка 80 тыс. ₽, убыток
  9,4 млн ₽; 2023: выручка 729 тыс. ₽, убыток 95,3 млн ₽; 2024:
  выручка 1,2 млн ₽, убыток 110 млн ₽; 2025: выручка 4,5 млн ₽, убыток
  98 млн ₽.

НЕ ВНЕСЕНО: (1) Егор Яковлев как основатель/руководитель — статья
vc.ru/theedinorogblog сама признаёт: «автор не нашёл документального
подтверждения его связи с юрлицом компании», молву без подтверждения в
карточку не переносим; (2) валюация компании при раунде — ноль по всем
семи проверенным источникам; (3) связь фонда «Восход Капитал» (2023) с
УК «Апрель Капитал» (совладелец с 2024) — источники не устанавливают
её напрямую, это могут быть разные, сменившие друг друга инвесторы;
(4) планы запуска собственного мессенджера (2026, ответ на уход VK
MAX/Telegram из сторов) — отдельное, более позднее событие вне рамок
самой сделки 2023 года, не факт об инвестиции; (5) консультанты — ноль.

Запуск: python3 pipeline/fix_looky_fullscan.py
        python3 pipeline/fix_looky_fullscan.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g3fce1b7d'

OLD_ECO_SHARE = '—'
NEW_ECO_SHARE = (
    'Looky — российский аналог Instagram: посты, сторис, фото- и '
    'видеоредактор, фильтры, хештеги, комментарии и директ; заявленная '
    'цель — привлечь не менее 10% российских пользователей Instagram к '
    '2024 году. Приложением владеет зарегистрированная в Тбилиси '
    'компания CSDevelopment LLC.'
)

OLD_ECO_TARGET_FIN = '—'
NEW_ECO_TARGET_FIN = (
    'Выручка ООО «Мотивационные решения» росла с 80 тыс. ₽ в 2022 году '
    'до 4,5 млн ₽ в 2025-м, но при этом компания ежегодно убыточна: '
    'убыток составил 9,4 млн ₽ (2022), 95,3 млн ₽ (2023), 110 млн ₽ '
    '(2024) и 98 млн ₽ (2025). У сервиса 7 млн зарегистрированных '
    'пользователей, активную аудиторию компания не раскрывает.'
)

OLD_ECO_CONTEXT = (
    'Это второй раунд за четыре месяца с официального запуска Looky — '
    'в первом сервис привлёк 160 млн ₽.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Кто именно вложился, компания не раскрыла, '
    'назвав инвесторов «частными российскими инвесторами с опытом '
    'инвестирования в ИТ-стартапы» — по данным vc.ru, раунд прошёл при '
    'поддержке инвестфирмы «Восход Капитал» Михаила Афонина. К 2024 '
    'году совладельцем компании (57%) стала УК «Апрель Капитал», '
    'сохранив за прежним владельцем 43%; с 2022 года в проект вложено '
    'более 500 млн ₽.'
)

OLD_SRC = [['RB.ru', 'https://rb.ru/news/looky-deal/']]
NEW_SRC = OLD_SRC + [
    ['CNews', 'https://www.cnews.ru/news/top/2023-04-11_investory_vlozhilis_po-krupnomu'],
    ['VC.ru', 'https://vc.ru/money/661810-socset-looky-rossiiskii-analog-instagram-privlekla-300-mln-rublei-ot-chastnyh-investorov'],
    ['VC.ru', 'https://vc.ru/theedinorogblog/3075124'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['share'] == OLD_ECO_SHARE
    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== eco.share: станет ===')
    print(NEW_ECO_SHARE)
    print('\n=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['eco']['share'] = NEW_ECO_SHARE
        deal['eco']['target_fin'] = NEW_ECO_TARGET_FIN
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
