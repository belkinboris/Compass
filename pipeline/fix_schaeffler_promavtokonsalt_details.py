# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g5fb64cd9` («Продажа завода Schaeffler в Ульяновске компании
ПромАвтоКонсалт», статус «Закрыта») — три находки: неверная дата,
пустые `law.struct`/`eco.target_fin`.

Проверено лично прямым WebFetch:
- Единственный источник самой карточки, business-magazine.online/fn_1411754.html
  (Бизнес-журнал), сам датирован 27 ноября 2023 года и описывает
  распоряжение президента — а не дату 2023-02-02, стоявшую в
  карточке (эта дата, похоже, не соответствует ни одному известному
  событию сделки — ни распоряжению, ни закрытию, ни подписанию
  договора).
- Коммерсантъ, https://www.kommersant.ru/doc/6410800: «с 15 декабря
  2023 года 100% ульяновского завода автокомпонентов ООО «Шэффлер
  Рус» перешло в собственность «Промавтоконсалта»» (дата — по ЕГРЮЛ);
  покупатель получил 100% долей в ДВУХ дочерних структурах — ООО
  «Шэффлер Рус» (Ульяновск, производство) и ООО «Шэффлер Руссланд»
  (Москва, торговля); бенефициар — Александр Горлов.
- Vedomosti (со ссылкой на Reuters и отчётность Schaeffler),
  https://www.vedomosti.ru/business/news/2023/12/18/1011628-schaeffler:
  «Выручка снизилась в 1,5 раза до 734 млн руб. Убыток 300 млн руб.
  (против прибыли 76 млн руб. в 2021 г.)» (ООО «Шэффлер Рус» за 2022
  год); «Шэффлер Руссланд»: оборот 2 млрд руб., убыток 262 млн руб.

Дата сделки исправлена на 2023-12-15 (дата перехода права
собственности по ЕГРЮЛ, совпадает со статусом «Закрыта») — тот же
год, что и раньше, замена в пределах известного года.

НЕ ВНЕСЕНО: нарратив о связи бенефициара Александра Горлова с
холдингом «Русские машины» (Дерипаска) и версия о причине продажи
(предложение использовать детали Schaeffler в автомобилях ГАЗ,
находящегося под санкциями) — по докладу саб-агента, эти сведения
взяты из агрегированной поисковой выдачи (pravo.ru, lenta.ru), не
подтверждены прямым чтением ни одной из этих страниц; учитывая
серьёзность утверждения (санкционная связь), не вносится без личной
проверки. Более поздние приобретения «ПромАвтоКонсалт» (завод Benteler
в Калуге, бывший завод Nemak) — отдельные, не относящиеся к этой
карточке сделки; данные 2025-2026 годов о заводе — из непроверенных
агрегаторов (403 при прямой проверке), не вносятся.

Запуск: python3 pipeline/fix_schaeffler_promavtokonsalt_details.py
        python3 pipeline/fix_schaeffler_promavtokonsalt_details.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g5fb64cd9'

OLD_DATE = '2023-02-02'
NEW_DATE = '2023-12-15'

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    '«ПромАвтоКонсалт» получил 100% долей в двух дочерних структурах'
    ' Schaeffler — ООО «Шэффлер Рус» (Ульяновск, производство) и ООО'
    ' «Шэффлер Руссланд» (Москва, торговля). Бенефициар покупателя —'
    ' Александр Горлов. Переход права собственности зарегистрирован в'
    ' ЕГРЮЛ 15 декабря 2023 года.'
)

OLD_ECO_TARGET_FIN = '—'
NEW_ECO_TARGET_FIN = (
    'ООО «Шэффлер Рус» за 2022 год: выручка снизилась в 1,5 раза до'
    ' 734 млн ₽, убыток — 300 млн ₽ (против прибыли 76 млн ₽ в 2021'
    ' году). ООО «Шэффлер Руссланд»: оборот 2 млрд ₽, убыток 262 млн ₽.'
)

NEW_SRC = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/6410800'],
    ['Ведомости', 'https://www.vedomosti.ru/business/news/2023/12/18/1011628-schaeffler'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['date'] == OLD_DATE
    assert deal['law']['struct'] == OLD_LAW_STRUCT
    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== date: станет ===')
    print(NEW_DATE)
    print('\n=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    print('\n=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['date'] = NEW_DATE
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['eco']['target_fin'] = NEW_ECO_TARGET_FIN
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
