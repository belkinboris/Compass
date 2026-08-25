# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF), карточка gcdd2b6de («Севергрупп
может выкупить сеть магазинов OBI у Синдики»): дельта-поиск нашёл, что
сделка ДАВНО закрыта — 13 января 2026 года группа «Лента» объявила о
покупке всей сети OBI в России (25 магазинов, 263 тыс. кв. м), с
ребрендингом в «DOM Лента» к маю 2026 года. Прямым покупателем выступило
ООО «Гермес» (получило 24,99% в апреле 2025, довело долю до 65% после
одобрения ФАС в июне 2025 и затем до 90%) — и уже от «Гермеса» актив
перешёл к «Ленте», входящей в холдинг «Севергрупп» Алексея Мордашова.
Статус карточки («Обсуждается») и время в заголовке («может выкупить»)
были неверны почти год.

Правки: status → «Закрыта»; заголовок — глагол в прошедшем времени
(правило CLAUDE.md «время в заголовке должно соответствовать статусу»);
buyer — конкретное юрлицо-приобретатель (профиль «Группа Лента», уже
существующий), а не только холдинг верхнего уровня «Севергрупп»
(родственный принцип, что для УГМК-Инвест/УГМК); law.appr — согласование
ФАС (было прозой лежать нельзя, см. test_approval_is_not_left_in_prose);
eco.context/eco.val расширены итоговыми фактами закрытия и оценками
января 2026 года. Не через review.py: цитаты из ПЯТИ разных новых
источников, комбинируемых в разных полях.

Запуск: python3 pipeline/fix_obi_lenta_severgrupp_closed.py
        python3 pipeline/fix_obi_lenta_severgrupp_closed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gcdd2b6de'

OLD_TITLE = 'Севергрупп может выкупить сеть магазинов OBI у Синдики'
NEW_TITLE = 'Севергрупп выкупил сеть магазинов OBI у Синдики'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

OLD_BUYER = 'g7ffb3b7a'
NEW_BUYER = 'gcca31da7'  # Группа Лента — прямой приобретатель по объявлению

OLD_CONTEXT = '—'
NEW_CONTEXT = (
    '13 января 2026 года группа «Лента» объявила о покупке сети OBI в '
    'России — в сделку вошли 25 магазинов общей площадью 263 тыс. кв. м, '
    'интеграция запланирована поэтапно до мая 2026 года, сеть меняет '
    'название на «DOM Лента». Прямым покупателем выступило ООО «Гермес» '
    '(бенефициар Владимир Захватошин), которое в апреле 2025 года '
    'получило 24,99% в трёх из пяти юрлиц OBI, летом 2025 года после '
    'одобрения ФАС довело долю до 65%, а затем до 90% — и уже от '
    '«Гермеса» актив перешёл к «Ленте», входящей в холдинг «Севергрупп» '
    'Алексея Мордашова. Сумму сделки «Лента» не назвала; ребрендинг и '
    'интеграция могут обойтись в 0,2–1 млрд руб., по оценке аналитика '
    'Freedom Finance Global.'
)

OLD_VAL = (
    'За продажу OBI «Синдика» планировала выручить 7–8 млрд руб., но '
    'рыночная цена актива, скорее всего, меньше из-за «околонулевого '
    'показателя EBIDTA», отмечает источник «Ъ» на рынке торговой '
    'недвижимости. Гендиректор «Infoline-Аналитики» Михаил Бурмистров '
    'сомневается, что стоимость сделки по покупке OBI составила более 5 '
    'млрд руб. Руководитель департамента M&A BGP Capital Иван Пешков '
    'склоняется к тому, что цена актива вовсе была символической: '
    '«Бизнес давно глубоко убыточный, за прошлый год убыток от продаж '
    'достиг 3 млрд руб.».'
)
VAL_ADDITION = (
    ' В январе 2026 года источник «Ъ» оценивал полную стоимость бизнеса '
    'OBI в России примерно в 6 млрд руб., а опрошенные эксперты — сумму '
    'самой сделки в 5 млрд руб.; гендиректор Atomic Capital Александр '
    'Зайцев допускал, что цена могла быть меньше или вовсе символической '
    'из-за убыточности актива.'
)
NEW_VAL = OLD_VAL + VAL_ADDITION

OLD_APPR = 'Публично не сообщалось'
NEW_APPR = (
    'ФАС России одобрила сделку по приобретению ООО «Гермес» контрольного '
    'пакета акций сети строительных гипермаркетов Obi.'
)

NEW_SRC = [
    ['meduza.io', 'https://meduza.io/news/2026/01/13/lenta-ob-yavila-o-pokupke-obi-set-gipermarketov-smenit-nazvanie-na-dom-lenta'],
    ['kommersant.ru', 'https://www.kommersant.ru/doc/8340567'],
    ['realnoevremya.ru', 'https://realnoevremya.ru/news/338081-fas-odobrila-prodazhu-seti-gipermarketov-obi-kompanii-germes'],
    ['interfax.ru', 'https://www.interfax.ru/business/1036100'],
    ['sostav.ru', 'https://www.sostav.ru/publication/germes-uvelichil-dolyu-v-obi-76602.html'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['title'] == OLD_TITLE
    assert deal['status'] == OLD_STATUS
    assert deal['buyer'] == OLD_BUYER
    assert deal['eco']['context'] == OLD_CONTEXT
    assert deal['eco']['val'] == OLD_VAL
    assert deal['law']['appr'] == OLD_APPR
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'
    assert 'gcca31da7' in data['companies'], 'профиль «Группа Лента» не найден'

    print('=== title ===')
    print(NEW_TITLE)
    print('=== status ===', NEW_STATUS)
    print('=== buyer ===', NEW_BUYER, '(', data['companies']['gcca31da7']['name'], ')')
    print('=== eco.context ===')
    print(NEW_CONTEXT)
    print('=== eco.val ===')
    print(NEW_VAL)
    print('=== law.appr ===')
    print(NEW_APPR)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['title'] = NEW_TITLE
        deal['status'] = NEW_STATUS
        deal['buyer'] = NEW_BUYER
        deal['eco']['context'] = NEW_CONTEXT
        deal['eco']['val'] = NEW_VAL
        deal['law']['appr'] = NEW_APPR
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
