# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gbac532cf` («"Авито работа" купила контрольный пакет HR Messenger»,
2023, Закрыта) — точная доля (62,75%) когда-то стояла в `eco.rationale`
(видна в старом значении записи FIXES), но правка вычитки заменила
это поле на описание продукта, а доля никуда не переехала — на экране
«Предмет / доля» стоит пустой прочерк.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты kommersant.ru/doc/5695608,
источник, который уже нашёл саб-агент, но не я лично):
- «Доля Авито в компании составит 62,75%.»
- «Сделка осуществлена через холдинговую структуру группы Авито — ООО
  "Авито Холдинг".»
- Сумма сделки в статье не названа.
- Мурат Абдрахманов (упомянутый саб-агентом со ссылкой на forbes.kz)
  в этой статье не встречается — не вносится без отдельной проверки.

НЕ ВНЕСЕНО: (1) Мурат Абдрахманов и Chocofamily как прежние инвесторы
— только по WebSearch-пересказу форбс.kz, саб-агент не прочитал
источник целиком, дословной цитаты нет; (2) «выкуп оставшихся долей
инвесторов в 2023 году» — саб-агент прямо пометил как неподтверждённое
(только агрегированная поисковая сводка, первоисточник не найден); ни
то ни другое не вносится без отдельной проверки.

Запуск: python3 pipeline/fix_avito_hr_messenger_share.py
        python3 pipeline/fix_avito_hr_messenger_share.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gbac532cf'

OLD_ECO_SHARE = '—'
NEW_ECO_SHARE = (
    'Доля Авито в HR Messenger составит 62,75%. Сделка осуществлена '
    'через холдинговую структуру группы — ООО «Авито Холдинг».'
)

OLD_LAW_STRUCT = '—'
NEW_LAW_STRUCT = (
    'Сделка проведена через ООО «Авито Холдинг» — холдинговую '
    'структуру группы «Авито».'
)

OLD_SRC = [['VC.ru', 'https://vc.ru/services/552174-avito-rabota-kupila-kontrolnyy-paket-v-kazahstanskom-servise-chat-botov-hr-messenger']]
NEW_SRC = OLD_SRC + [['Коммерсантъ', 'https://www.kommersant.ru/doc/5695608']]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['share'] == OLD_ECO_SHARE
    assert deal['law']['struct'] == OLD_LAW_STRUCT
    assert deal['src'] == OLD_SRC

    print('=== eco.share: станет ===')
    print(NEW_ECO_SHARE)
    print('\n=== law.struct: станет ===')
    print(NEW_LAW_STRUCT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['eco']['share'] = NEW_ECO_SHARE
        deal['law']['struct'] = NEW_LAW_STRUCT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
