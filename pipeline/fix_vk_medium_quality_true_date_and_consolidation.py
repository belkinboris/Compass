# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g630a6fbb («VK приобрела 51% ООО «Медиум Кволити Продакшн»», карточка
несла дату 29 сентября 2023) — дата закрытия ошибочна на целый год,
VK с тех пор консолидировала 100%, а флагманское шоу сделки потеряло
поддержку VK Видео из-за конфликта об эксклюзивности.

Проверено лично прямым WebFetch (LEVEL Legal Services,
https://www.level-legal.com/news/sdelki-goda): страница со списком
сделок озаглавлена периодом «февраль 2022 — сентябрь 2023» — это
ОТЧЁТНЫЙ ПЕРИОД страницы, а не дата закрытия конкретной сделки; сама
запись о сделке VK/«Медиум Кволити Продакшн» даты не несёт вовсе.
Похоже, что при разборе источника конец отчётного периода страницы
(«сентябрь 2023») был принят за дату сделки — тот же класс дефекта,
что уже описан в CLAUDE.md («Дата новости — не дата сделки»), только
здесь дата взята не из соседней новости, а из рамки отчётного периода
источника.

Настоящая дата подтверждена лично прямым WebFetch (VC.ru,
https://vc.ru/media/593013-vk-uvedomila-fas-o-namerenii-poluchit-100-studii-kotoraya-vypuskaet-youtube-shou-chto-bylo-dalshe):
«По данным "Контур.Фокуса", группа получила 51% 20 декабря 2022 года,
49% остались у Вячеслава Дусмухаметова» — и независимо подтверждена
Ведомостями (https://www.vedomosti.ru/media/articles/2025/02/28/1095121-vyacheslav-dusmuhametov-vpervie):
«В декабре 2022 г. VK приобрела у Дусмухаметова контрольную долю (51%)
в продакшене».

Та же статья Ведомостей: «В феврале 2024 г. VK довела свою долю в
продакшене до 67,3%», «в декабре того же года приобрела и оставшиеся у
Дусмухаметова 32,7% компании» — VK стала единственным владельцем;
Дусмухаметов вышел из капитала полностью, но сохранил пост
генпродюсера и место в совете директоров. Выручка выросла с 1,2 млрд ₽
(2021) до 4,4 млрд ₽ (2023, РСБУ), прибыль осталась на том же уровне
(132,4 млн ₽).

Проверено лично прямым WebFetch (Click-or-die.ru,
https://click-or-die.ru/2026/05/iz-vk-video-sbezhali-eshhe-odni-zvezdnye-komiki-oni-vernulis-na-youtube-kak-chto-bylo-dalshe/):
«шоу «Что было дальше?» после завершения контракта с «ВК» фактически
потеряло поддержку соцсети — именно из-за запуска нового ютуб-канала и
дублирования выпусков» — в VK Видео строго относятся к параллельной
публикации контента студии на других платформах.

НЕ ВКЛЮЧЕНО: официальная сумма сделки — по-прежнему не раскрыта нигде
(структура сделки предполагала оплату по KPI просмотров в течение
нескольких лет, а не единовременный платёж, по данным Habr со ссылкой
на Коммерсантъ); финансы компании за 2024-2025 годы — не найдены.

Запуск: python3 pipeline/fix_vk_medium_quality_true_date_and_consolidation.py
        python3 pipeline/fix_vk_medium_quality_true_date_and_consolidation.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g630a6fbb'

OLD_DATE = '2023-09-29'
NEW_DATE = '2022-12-20'

OLD_EXTRA = (
    'LEVEL Legal Services консультировала VK при приобретении 51% '
    'долей ООО «Медиум Кволити Продакшн», производителя контента (шоу '
    '«Что было дальше?», Roast Battle, «Я себя знаю», Big Russian Boss '
    'Show и др.).'
)
NEW_EXTRA = OLD_EXTRA + (
    ' Дата сделки была ошибочно взята из конца отчётного периода '
    'источника (LEVEL Legal Services, «февраль 2022 — сентябрь 2023») '
    'вместо настоящей даты закрытия — 20 декабря 2022 года (по данным '
    'ЕГРЮЛ/Контур.Фокус). VK с тех пор консолидировала пакет полностью: '
    'в феврале 2024 доля выросла до 67,3%, в декабре 2024 — до 100%. '
    'Дусмухаметов вышел из капитала, но остался генпродюсером и в '
    'совете директоров. Выручка выросла с 1,2 до 4,4 млрд ₽ (2021→2023). '
    'Флагманское шоу сделки, «Что было дальше?», к 2026 году потеряло '
    'активную поддержку VK Видео из-за конфликта о параллельной '
    'публикации на YouTube.'
)

NEW_SRC = [
    ['VC.ru', 'https://vc.ru/media/593013-vk-uvedomila-fas-o-namerenii-poluchit-100-studii-kotoraya-vypuskaet-youtube-shou-chto-bylo-dalshe'],
    ['Ведомости', 'https://www.vedomosti.ru/media/articles/2025/02/28/1095121-vyacheslav-dusmuhametov-vpervie'],
    ['Click-or-die.ru', 'https://click-or-die.ru/2026/05/iz-vk-video-sbezhali-eshhe-odni-zvezdnye-komiki-oni-vernulis-na-youtube-kak-chto-bylo-dalshe/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert deal['extra'] == OLD_EXTRA

    new_src = deal['src'] + NEW_SRC

    print('=== date: станет ===')
    print(NEW_DATE)
    print('\n=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['date'] = NEW_DATE
        deal['extra'] = NEW_EXTRA
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
