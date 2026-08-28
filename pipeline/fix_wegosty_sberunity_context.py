# -*- coding: utf-8 -*-
"""Недельная очередь (REVISION_BRIEF), карточка g8b03762d (ИИ-платформа
Wegosty привлекла 23 млн ₽ от бизнес-ангелов, 13 августа 2026): дельта-поиск
нашёл НОВЫЙ источник (CNews), которого в карточке ещё не было, с двумя фактами
за пределами уже известного: раунд закрыт через венчурную платформу SberUnity,
и прямая цитата основателя Романа Тяна о планах использования средств. Не
через review.py: добавляется НОВЫЙ источник вместе с текстом из него — та же
комбинация, что уже применялась для похожих находок (сначала новый src, потом
расширение поля цитатой из него).

Запуск: python3 pipeline/fix_wegosty_sberunity_context.py
        python3 pipeline/fix_wegosty_sberunity_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g8b03762d'

OLD_RATIONALE = (
    'Стартап разработал ИИ-платформу для ресторанов, отелей и туристической '
    'отрасли. Решение автоматизирует весь путь гостя: от первого обращения до '
    'бронирования и оплаты. Платформа объединяет ИИ-ресепшн, систему '
    'онлайн-бронирования и оплаты, инструменты привлечения гостей через '
    'партнёрские каналы и мобильный гастронавигатор. Продукт интегрируется с '
    'ключевыми отраслевыми системами, включая iiko и Bnovo. Задача компании — '
    'помочь объектам HoReCa получать больше бронирований при меньших '
    'операционных затратах и создать единую независимую ИИ-инфраструктуру для '
    'российского рынка.'
)
RATIONALE_ADDITION = (
    ' Стартап нашел инвесторов на платформе венчурных инвестиций SberUnity, '
    'которая связывает стартапы с инвесторами и крупным бизнесом напрямую. '
    'Основатель Wegosty Роман Тян: «Привлеченные средства позволят нам '
    'масштабировать технологии и построить федеральную сеть продаж. Мы '
    'направим инвестиции на дальнейшее развитие ИИ-ресепшена, расширение '
    'списка отраслевых интеграций, автоматизацию обработки более 100 новых '
    'B2B-лидов ежемесячно и запуск федеральной агентской сети».'
)
NEW_RATIONALE = OLD_RATIONALE + RATIONALE_ADDITION

NEW_SRC = [
    ['CNews', 'https://www.cnews.ru/news/line/2026-08-13_rossijskaya_ii-platforma'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['rationale'] == OLD_RATIONALE
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.rationale: станет ===')
    print(NEW_RATIONALE)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['rationale'] = NEW_RATIONALE
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
