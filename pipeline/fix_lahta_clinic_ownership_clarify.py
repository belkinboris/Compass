# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g054eba01` («Фонд Газпромбанка приобрел долю в сети клиник Lahta
Clinic», 2022-12-03, Закрыта) — `law.struct` и `eco.share` на первый
взгляд противоречили друг другу: «72,5%... перешли к ООО "Глобал МК"»
(law.struct) против «на 58,12% принадлежит Игорю Краснолуцкому и на
41,88% — структуре Газпромбанка» (eco.share). Это НЕ противоречие, а
два уровня одной цепочки владения — `law.struct` не объяснял этого.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты)
newprospect.ru/news/articles/klinika-na-payakh-set-medtsentrov-v-peterburge-privlekla-neobychnogo-investora/:
- «у Александра Изака теперь 5%, у Дмитрия Волкова — 1,5%, у Кирилла
  Краснолуцкого по-прежнему 21%»; новый совладелец — «ООО "Глобал МК"
  с долей в 72,5%»;
- «ООО "Глобал МК", им владеют Игорь Краснолуцкий (58,12%) и ЗПИФ
  "Яшма" (41,8%)»;
- управляющая компания ЗПИФ «Яшма» — «АО "ААА Управление капиталом"...
  часть бизнеса доверительного управления группы Газпромбанка».

Итог: 72,5% «Лахта Клиники» принадлежат ООО «Глобал МК» НАПРЯМУЮ, а
уже ВНУТРИ «Глобал МК» доли делятся 58,12% (Краснолуцкий) / 41,88%
(ЗПИФ «Яшма», Газпромбанк) — оба числа верны одновременно, просто на
разных уровнях владения.

НЕ ВНЕСЕНО: (1) была ли сделка денежной — источник прямо пишет, что
информации об этом нет, редакция направляла запрос без ответа; (2)
финансовые показатели сети GMS+Lahta Clinic за 2023-2024 годы — саб-
агент нашёл их только через WebSearch-пересказ без точной ссылки на
конкретную статью, не проверено мной лично дословно; (3) консультанты
и согласование ФАС — не найдены ни в одном источнике.

Запуск: python3 pipeline/fix_lahta_clinic_ownership_clarify.py
        python3 pipeline/fix_lahta_clinic_ownership_clarify.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g054eba01'

OLD_LAW_STRUCT = (
    '13 декабря 2022 года 72,5% юрлица сети — ООО «Лахта Клиника» — '
    'перешли к ООО «Глобал МК».'
)
NEW_LAW_STRUCT = (
    OLD_LAW_STRUCT + ' Само «Глобал МК» на 58,12% принадлежит Игорю '
    'Краснолуцкому и на 41,88% — ЗПИФ «Яшма», управляющая компания '
    'которого («ААА Управление капиталом») входит в бизнес '
    'доверительного управления группы Газпромбанка: это два уровня '
    'одной цепочки, а не расхождение цифр.'
)

OLD_SRC = [['Vademecum', 'https://vademec.ru/news/2023/02/13/dochka-gazprombanka-stala-sovladeltsem-peterburgskoy-seti-lahta-clinic/']]
NEW_SRC = OLD_SRC + [['New Prospect', 'https://newprospect.ru/news/articles/klinika-na-payakh-set-medtsentrov-v-peterburge-privlekla-neobychnogo-investora/']]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['law']['struct'] == OLD_LAW_STRUCT
    assert deal['src'] == OLD_SRC

    print('=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
