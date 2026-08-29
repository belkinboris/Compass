# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g77e91362
(Технониколь приобрела завод Termoclip). Проверено лично прямым WebFetch
(основной источник ворот, Plastinfo, в этой сессии не читается — сеть
отдаёт повреждённую кодировку/403; факты взяты из независимых
источников, republish пресс-релиза ТЕХНОНИКОЛЬ и агрегатора СПАРК).

1) `eco.rationale` (новое поле) — причина сделки: вертикальная интеграция
давнего поставщика, а не разовая покупка. Пресс-релиз ТЕХНОНИКОЛЬ
(republish cheminsight.ru), дословно: «Мы сотрудничаем с заводом
последние 10 лет»; «Приобретение завода Termoclip стало планомерным
шагом в ходе создания единого технологического процесса».
Источник: https://cheminsight.ru/tpost/lmf7ln9d21-tehnonikol-priobrela-proizvoditelya-stro

2) `eco.context` (новое поле) — инвестиционный план, объявленный при
сделке: «в ближайший год «Технониколь» намерена инвестировать в завод
«ПК-Термоснаб»... порядка 250 млн руб.» (приобретение оборудования,
автоматизация производства, адаптация к стандартам компании).

3) `eco.target_fin` (новое поле) — финансы предмета за 2023 год
(агрегатор СПАРК/Контур, tenchat.ru), дословно: ООО «ПК-ТЕРМОСНАБ» —
«Выручка – 1,9 млрд руб.», «Прибыль от продаж – 496 млн руб.», «ЧП – 393
млн руб.»; ООО «ТЕРМОКЛИП» — «Выручка – 232 млн руб.», «Прибыль от
продаж – 3,5 млн руб.», «ЧП – 1,1 млн руб.»
Источник: https://tenchat.ru/media/2404893-tekhnonikol-priobrelo-zavod-proizvodyaschiy-montazhnyye-i-krepezhnyye-sistemy-termoclip

НЕ включены: продавец — три независимых реестровых агрегатора (RBC,
datanewton, audit-it) называют текущими участниками ПК-ТЕРМОСНАБ
Прохорова И.В. (с 2005) и Фонарева О.В. (с 14.06.2024, за 12 дней до
объявления сделки), но ни один источник прямо не называет их продавцами,
а главное — спустя два года в реестре по-прежнему числятся физлица, а
не структура Технониколь, что противоречит ожиданию завершённой M&A-
сделки; это наблюдение для будущей проверки человеком (см. «Известные
проблемы» в CLAUDE.md), а не факт для записи в `seller`. Независимая
оценка суммы и консультанты сделки — не найдены ни в одном источнике.

Запуск: python3 pipeline/fix_technonikol_termoclip_rationale_and_finances.py
        python3 pipeline/fix_technonikol_termoclip_rationale_and_finances.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g77e91362'

NEW_RATIONALE = (
    '«Мы сотрудничаем с заводом последние 10 лет»; «Приобретение завода '
    'Termoclip стало планомерным шагом в ходе создания единого '
    'технологического процесса» (пресс-релиз ТЕХНОНИКОЛЬ).'
)

OLD_CONTEXT = (
    'Владеет – 70 производственными площадками. Оборот «Технониколь» в '
    '2023 году достиг 211 млрд руб. Основные владельцы — Игорь Рыбаков '
    'и Сергей Колесников.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' «В ближайший год «Технониколь» намерена инвестировать в завод '
    '«ПК-Термоснаб»... порядка 250 млн руб.» на приобретение '
    'оборудования, автоматизацию производства и адаптацию к стандартам '
    'компании.'
)

NEW_TARGET_FIN = (
    'За 2023 год: ООО «ПК-ТЕРМОСНАБ» — «Выручка – 1,9 млрд руб.», '
    '«Прибыль от продаж – 496 млн руб.», «ЧП – 393 млн руб.»; ООО '
    '«ТЕРМОКЛИП» — «Выручка – 232 млн руб.», «Прибыль от продаж – 3,5 '
    'млн руб.», «ЧП – 1,1 млн руб.» (СПАРК/tenchat.ru).'
)

NEW_SRC = [
    ['cheminsight.ru', 'https://cheminsight.ru/tpost/lmf7ln9d21-tehnonikol-priobrela-proizvoditelya-stro'],
    ['tenchat.ru', 'https://tenchat.ru/media/2404893-tekhnonikol-priobrelo-zavod-proizvodyaschiy-montazhnyye-i-krepezhnyye-sistemy-termoclip'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert not deal['eco'].get('rationale')
    assert deal['eco']['context'] == OLD_CONTEXT
    assert deal['eco']['target_fin'] == '—'
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.rationale (новое поле): станет ===')
    print(NEW_RATIONALE)
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== eco.target_fin (новое поле): станет ===')
    print(NEW_TARGET_FIN)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['rationale'] = NEW_RATIONALE
        deal['eco']['context'] = NEW_CONTEXT
        deal['eco']['target_fin'] = NEW_TARGET_FIN
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
