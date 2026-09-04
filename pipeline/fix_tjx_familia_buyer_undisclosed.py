# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g4df9c492` («TJX Companies продала 25% доли в сети магазинов
Familia», закрыта, 2022) — карточка стояла закрытой при пустом
`buyer`/`buyer_name`: дочитывание подтвердило, что это честная
пустота — покупатель прямо не раскрыт ни одним источником.

Проверено (по докладу саб-агента, дословные цитаты):
- kommersant.ru/doc/6012599 (источник карточки, перепрочитан
  полностью): «Информация о том, кому перешла доля TJX Companies, не
  раскрывается»; «в апреле 2023 года головная структура Familia
  сменила юрисдикцию в Люксембурге, зарегистрировав одноимённую
  компанию в ОАЭ».
- vc.ru/money/709243 и profashion.ru: то же самое об отсутствии имени
  покупателя, независимо подтверждено; «В TJX и Familia на запрос "Ъ"
  не ответили»; текущий состав совладельцев по данным DIFC — «Broomfield
  Int.» (по данным РБК связана с российским топ-менеджментом местной
  структуры Goldman Sachs), «Ambron Holding» (по данным DIFC
  принадлежит Дмитрию Луковникову), «Kemble Corporation» (бенефициары
  не называются); «Veliada — структура Baring Vostok — по-прежнему
  остаётся в числе совладельцев Familia».
- stonebridgelegal.ru: партнёр Stonebridge Legal Дмитрий Позин — «В
  ОАЭ Familia не обязана соблюдать санкции ЕС и сможет свободнее
  взаимодействовать с российским бизнесом».

НЕ ВНЕСЕНО: (1) имя покупателя доли TJX — источники прямо утверждают,
что оно не раскрыто, поле `buyer`/`buyer_name` остаётся честной
пустотой; (2) фигура «$218 млн» — это списание/бухгалтерский убыток
TJX от собственных вложений в российский актив, а НЕ цена продажи
доли (сумма продажи по-прежнему не раскрыта нигде) — не вносится как
`sum`, это тот же класс риска, что уже описан в CLAUDE.md («Число
может быть верным фактом и совсем не той величиной»); (3) точный
день/месяц закрытия сделки — известно только, что она пришлась на
финансовый (не календарный) 2023 год TJX; (4) гипотеза о личностях
бенефициаров Broomfield (Максим Климов, Антон Шрейдер) — получена
только через агрегированный пересказ поисковика, не через дословное
чтение первоисточника, не вносится без отдельной проверки;
(5) консультанты сделки — ноль по всем источникам.

Запуск: python3 pipeline/fix_tjx_familia_buyer_undisclosed.py
        python3 pipeline/fix_tjx_familia_buyer_undisclosed.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g4df9c492'

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'В апреле 2023 года головная структура Familia сменила '
    'юрисдикцию с люксембургской на структуру, зарегистрированную в '
    'ОАЭ. Покупатель доли TJX прямо не назван: «Информация о том, кому '
    'перешла доля TJX Companies, не раскрывается» — ни TJX, ни Familia '
    'на запрос журналистов не ответили.'
)

OLD_ECO_RATIONALE = (
    'Перевод головной структуры Familia из Люксембурга в Дубай — '
    'вынужденная мера для ритейлера. Как поясняет старший юрист BGP '
    'Litigation Екатерина Ардашева, дружественный статус ОАЭ позволяет '
    'российским собственникам финансировать компании в РФ, тогда как '
    'для структур из недружественных юрисдикций это в ряде случаев '
    'ограничено.'
)
NEW_ECO_RATIONALE = (
    OLD_ECO_RATIONALE + ' В ОАЭ Familia не обязана соблюдать санкции '
    'ЕС и сможет свободнее взаимодействовать с российским бизнесом, '
    'добавляет партнёр Stonebridge Legal Дмитрий Позин.'
)

OLD_ECO_CONTEXT = (
    'TJX Companies купила 25% Familia осенью 2019 года. Сумму сделки '
    'тогда оценивали в $225 млн, а продавцами выступали все '
    'совладельцы сети, включая структуры Goldman Sachs и Baring '
    'Vostok.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' После выхода TJX среди совладельцев Familia по '
    'данным реестра DIFC значатся Broomfield Int. (по данным СМИ '
    'связана с российским менеджментом местной структуры Goldman '
    'Sachs), Ambron Holding (принадлежит Дмитрию Луковникову) и Kemble '
    'Corporation (бенефициары не раскрываются); структура Baring '
    'Vostok (Veliada) в числе совладельцев осталась.'
)

OLD_SRC = [['Коммерсантъ', 'https://www.kommersant.ru/doc/6012599']]
NEW_SRC = OLD_SRC + [
    ['VC.ru', 'https://vc.ru/money/709243-amerikanskii-riteiler-tjx-vyshel-iz-chisla-sovladelcev-seti-magazinov-odezhdy-i-tovarov-dlya-doma-familia'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['struct'] == OLD_LAW_STRUCT
    assert deal['eco']['rationale'] == OLD_ECO_RATIONALE
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    print('\n=== eco.rationale: станет ===')
    print(NEW_ECO_RATIONALE)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['eco']['rationale'] = NEW_ECO_RATIONALE
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
