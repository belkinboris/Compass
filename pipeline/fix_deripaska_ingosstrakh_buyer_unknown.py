# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gf0b712ef` («Олег Дерипаска продал 10% акций «Ингосстраха»», август
2022, Закрыта) — покупатель не назван нигде, и это не пробел
дочитывания: сама компания ОТКАЗАЛАСЬ его называть, а раскрытие
структуры акционеров позже вообще приостановлено ЦБ.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- ingos.ru/company/disclosure-info/structure-shareholders: «Информация
  о структуре и составе акционеров СПАО "Ингосстрах" временно не
  публикуется на основании Решения Совета директоров Банка России от
  24 декабря 2024 года» — с этой даты узнать текущего владельца доли
  Дерипаски в принципе не из чего;
- ria.ru/20250110/ssha-1993174049.html: «США ввели санкции против
  российских страховых компаний "Ингосстрах" и "АльфаСтрахование"»
  (10 января 2025 года), «Санкции связаны с деятельностью компаний в
  сфере морского страхования».

НЕ ВНЕСЕНО: (1) имя покупателя доли Дерипаски — не установлено ни в
одном источнике, включая более поздние (2023-2026); (2) финансовые
показатели «Ингосстраха» за 2025 год (активы 312,1 млрд ₽, капитал
165,5 млрд ₽) — найдены только в агрегированной сводке WebSearch, не
подтверждены личным чтением первоисточника; (3) санкции ЕС —
обсуждались в 14-м пакете (май 2024), но формально не введены, не
вносятся как факт; (4) новый совладелец «Бекар-Сервис» (Коновалов/
Панов, 2018 год) — не связан с долей Дерипаски, к этой карточке не
относится.

Запуск: python3 pipeline/fix_deripaska_ingosstrakh_buyer_unknown.py
        python3 pipeline/fix_deripaska_ingosstrakh_buyer_unknown.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gf0b712ef'

OLD_ECO_CONTEXT = (
    'С 2018 года «Ингосстрах» не раскрывает состав акционеров, но доля '
    'Дерипаски указывалась в ежеквартальном отчёте компании.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Покупателя доли компания отказалась называть и '
    'в момент сделки, и позже; с 24 декабря 2024 года по решению совета '
    'директоров Банка России структура и состав акционеров «Ингосстраха» '
    'вообще не публикуются — узнать нынешнего владельца доли Дерипаски '
    'не из чего. 10 января 2025 года США ввели санкции против '
    '«Ингосстраха» (и «АльфаСтрахования») за морское страхование.'
)

OLD_SRC = [['Коммерсантъ', 'https://www.kommersant.ru/doc/5953554']]
NEW_SRC = OLD_SRC + [
    ['Ingos.ru', 'https://www.ingos.ru/company/disclosure-info/structure-shareholders'],
    ['РИА Новости', 'https://ria.ru/20250110/ssha-1993174049.html'],
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
