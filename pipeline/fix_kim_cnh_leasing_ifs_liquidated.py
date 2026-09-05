# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g020432e9` («Игорь Ким приобретает лизинговую и факторинговую дочки
CNH Industrial», февраль 2023, Закрыта) — судьба активов и дальнейшие
сделки Кима того же типа не прослеживались.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- audit-it.ru/contragent/1037709021283_ooo-ifs-lizing: лизинговая
  «дочка» переименована в «ИФС ЛИЗИНГ»; «Ликвидирована 18.09.2025» —
  «прекращение деятельности юридического лица путем реорганизации в
  форме присоединения»; прежний учредитель — «ПУБЛИЧНАЯ КОМПАНИЯ
  "СИЭНЭЙЧ ИНДАСТРИАЛ Н.В."» (Нидерланды, до 08.02.2023), текущий (с
  14.08.2023) — «ООО "ЭКСПОКАПИТАЛ ЛИЗ."»;
- vedomosti.ru/business/news/2024/02/02/1018209 (02.02.2024):
  «Новосибирская компания "ЦК", связанная с бизнесменом Игорем Кимом,
  приобрела российские лизинговую и факторинговую компании
  Volkswagen» — та же схема, что и с активами CNH, повторена год
  спустя с другим уходящим автоконцерном.

НЕ ВНЕСЕНО: (1) правопреемник ООО «ИФС Лизинг» после присоединения в
сентябре 2025 года — не найден ни в одном проверенном источнике;
(2) финансовые показатели за 2023-2025 годы и судьба факторинговой
«дочки» (переименование, финансы) — известны только по агрегированным
сниппетам без прямой цитаты, не проверены личным чтением; (3) отдельная
сделка CNH Industrial того же дня (продажа ОСНОВНОГО дилерского бизнеса
гендиректору Михаилу Мураховскому за $60 млн) — это ДРУГОЙ актив и
другая сделка, не предмет этой карточки, не вносится.

Запуск: python3 pipeline/fix_kim_cnh_leasing_ifs_liquidated.py
        python3 pipeline/fix_kim_cnh_leasing_ifs_liquidated.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g020432e9'

OLD_ECO_CONTEXT = (
    'Сделка закрыта в феврале 2023 года: подконтрольное Игорю Киму ООО '
    '«Экспокап» приобрело лизинговую и факторинговую дочерние компании '
    'CNH Industrial в России.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Лизинговая компания переименована в «ИФС '
    'Лизинг» и 18 сентября 2025 года прекратила существование как '
    'отдельное юрлицо, присоединившись к другой структуре (к какой —'
    ' источники не называют). Через год после этой сделки, в феврале '
    '2024 года, связанная с Кимом новосибирская компания «ЦК» повторила '
    'ту же схему — купила лизинговый и факторинговый бизнес Volkswagen '
    'в России.'
)

OLD_SRC = [
    ['Интерфакс', 'https://www.interfax.ru/business/885719'],
    ['Интерфакс', 'https://www.interfax.ru/business/898224'],
]
NEW_SRC = OLD_SRC + [
    ['audit-it.ru', 'https://www.audit-it.ru/contragent/1037709021283_ooo-ifs-lizing'],
    ['Ведомости', 'https://www.vedomosti.ru/business/news/2024/02/02/1018209-kompaniya-igorya-kima-priobrela'],
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
