# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
g60fedbfd («"36,6" + Горздрав приобрели аптечную сеть "Фармакон"»,
закрыта 2023) — второе внимательное чтение уже привязанного источника
(Ведомости) нашло цель сделки и комментарий эксперта, не перенесённые
при первом чтении; отдельно нашлось продолжение экспансии сети в том
же районе.

Проверено лично прямым WebFetch (Ведомости, тот же адрес, что уже стоит
в `src` карточки,
https://www.vedomosti.ru/business/articles/2023/08/31/992880-366-kupila-ramenskuyu-aptechnuyu-set):
«Чистая прибыль компании за прошлый год составила 38,8 млн руб.»,
«"36,6", согласно своей стратегии, выбирает регионы, где еще не была
широко представлена и где у нее есть перспективы роста, как в
Раменском», «При этом на данный момент активность сделок на фармрынке
очень низкая» (Николай Беспалов, RNC Pharma), «75% долей в компании
принадлежали Татьяне Коваленко» (по данным СПАРК за 2019 год).

Проверено лично прямым WebFetch (Фармвестник,
https://pharmvestnik.ru/content/news/Aptechnaya-set-36-6-kupila-apteki-v-Podmoskove.html):
13 июня 2024 года «Аптечная сеть 36,6» (бренд «Горздрав») купила ещё
четыре точки в Раменском (бренды «Эксфарм» и «Витафарм»), продавец не
назван, сумма не раскрыта — «Сделка логично дополнила покупку группой
аптечной сети "Фармакон" в том же Раменском, завершенную в 2023 году».

НЕ ВКЛЮЧЕНО: связь Татьяны Коваленко с юрлицом-продавцом после 2023
года и причина продажи — ни один источник не называет; юридический
консультант сделки — не назван нигде; переименование самих 18 точек
«Фармакона» под бренд «Горздрав» — подтверждено только общей фразой
Vademecum без дословной цитаты о ребрендинге конкретно этих точек, не
переношу как факт.

Запуск: python3 pipeline/fix_366_farmakon_expansion_and_finances.py
        python3 pipeline/fix_366_farmakon_expansion_and_finances.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g60fedbfd'

OLD_ECO_TARGET_FIN = (
    'Фармакон» создана в 1999 году и управляет 18 аптеками в Московской '
    'области. Издание сообщает, что выручка компании в 2022 году '
    'увеличилась на 4% — до 771 млн руб.'
)
NEW_ECO_TARGET_FIN = OLD_ECO_TARGET_FIN + (
    ' Чистая прибыль за 2022 год составила 38,8 млн ₽. По данным СПАРК '
    'за 2019 год, 75% долей в компании принадлежали Татьяне Коваленко.'
)

NEW_ECO_RATIONALE = (
    '«36,6», согласно своей стратегии, выбирает регионы, где ещё не '
    'была широко представлена и где у неё есть перспективы роста, — '
    'таким регионом стало Раменское.'
)

OLD_ECO_CONTEXT = (
    'Последний раз «36,6» покупала точки год назад — в августе 2022 '
    'года сеть приобрела подмосковную аптечную сеть «Кит-Фарма». Уже '
    'тогда в сети заявляли о намерении укрепить свои позиции в '
    'Московском регионе.'
)
NEW_ECO_CONTEXT = OLD_ECO_CONTEXT + (
    ' По оценке эксперта RNC Pharma Николая Беспалова, «на данный '
    'момент активность сделок на фармрынке очень низкая»: крупные сети '
    'если и приобретают активы, то небольшие, точечно наращивая '
    'присутствие в конкретных местах, чтобы минимизировать риски. В '
    'июне 2024 года «36,6»/Горздрав купила в том же Раменском ещё '
    'четыре аптеки (бренды «Эксфарм» и «Витафарм») — продавец и сумма '
    'не раскрыты, это отдельная сделка, для которой пока нет своей '
    'карточки в базе.'
)

NEW_SRC = [
    ['Фармвестник', 'https://pharmvestnik.ru/content/news/Aptechnaya-set-36-6-kupila-apteki-v-Podmoskove.html'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN
    assert 'rationale' not in deal['eco']
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    new_src = deal['src'] + NEW_SRC

    print('=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    print('\n=== eco.rationale: новое поле ===')
    print(NEW_ECO_RATIONALE)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['target_fin'] = NEW_ECO_TARGET_FIN
        deal['eco']['rationale'] = NEW_ECO_RATIONALE
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
