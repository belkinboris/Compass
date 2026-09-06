# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`ga9be07b2` («Сабуровский комбинат хлебопродуктов» приобрёл 100% акций
«Ленинградского мельничного комбината им. Кирова», Закрыта, конец 2022
года) — линза «Экономист» пустовала в поле «Контекст», хотя у сделки
есть заметное продолжение: судьба актива и продавца после сделки.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- interfax.ru/pressreleases/896849 (пресс-релиз, 21.04.2023): «холдингом
  было принято решение о закупке 200 вагонов для нужд ЛКХП Кирова» —
  комбинат вошёл в состав агрохолдинга «Агрополис «Сабурово»; продукция
  поставляется в страны Западной Африки, Ближнего Востока и Юго-Восточной
  Азии (Вьетнам, Южная Корея, Филиппины, Бенин, Сомали, Израиль, ОАЭ);
  «В феврале 2023 года в составе Агрополиса ЛКХП Кирова принял участие в
  крупнейшей международной выставке продуктов питания — Gulfood (Дубай,
  ОАЭ)».
- nsp.ru/35369-aladuskin-grupp-stala-novym-vladelcem-darnicy: «АО
  «Аладушкин групп», в свою очередь, по данным Интерфакс, в конце 2022
  года продало ОАО «Ленинградский комбинат хлебопродуктов им. С. М.
  Кирова» холдингу «Агрополис Сабурово»» — подтверждает саму сделку
  независимо от `agroinvestor.ru`; «Сделку по покупке 100% долей ООО
  «Группа компаний «Дарница» закрыли в конце января 2023 года» —
  продавец («Аладушкин групп») сам стал покупателем другого актива
  («Дарница», у гендиректора Виктории Устименко) вскоре после этой
  продажи.

НЕ ВНЕСЕНО: точный день закрытия сделки (ни один источник его не
называет — только «конец 2022 года»); дальнейшая судьба «Дарницы» (слух
о перепродаже «Коломенскому» встретился только в сниппете поисковой
выдачи, без подтверждения прямым чтением).

`buyer`/`seller`/`status`/`title`/`date` карточки НЕ тронуты — поле было
пустым (`eco.context: '—'`), правка только дополняет.

Запуск: python3 pipeline/fix_saburovo_lkhp_kirov_aftermath.py
        python3 pipeline/fix_saburovo_lkhp_kirov_aftermath.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ga9be07b2'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'После сделки комбинат вошёл в агрохолдинг «Агрополис «Сабурово»: '
    'холдинг закупил 200 вагонов для нужд предприятия, продукция '
    'поставляется в страны Западной Африки, Ближнего Востока и '
    'Юго-Восточной Азии, а в феврале 2023 года завод участвовал в '
    'международной выставке Gulfood в Дубае. Продавец, «Аладушкин '
    'групп», вскоре после этой продажи сам купил другой актив — 100% '
    'группы компаний «Дарница» (сделка закрыта в конце января 2023 '
    'года).'
)

OLD_SRC = [
    ['Агроинвестор', 'https://www.agroinvestor.ru/transaction/news/39341-saburovskiy-kombinat-khleboproduktov-priobrel-leningradskiy-melnichnyy-kombinat-im-kirova/'],
]
NEW_SRC = OLD_SRC + [
    ['Интерфакс', 'https://www.interfax.ru/pressreleases/896849'],
    ['НСП', 'https://nsp.ru/35369-aladuskin-grupp-stala-novym-vladelcem-darnicy'],
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
