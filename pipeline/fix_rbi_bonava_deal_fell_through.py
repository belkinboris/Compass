# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`ga2332f97` («Группа RBI приобретает российский бизнес шведского
девелопера Bonava», статус «Обсуждается», 2023) — сделка НЕ закрылась:
Bonava расторгла соглашение с RBI и продала бизнес другому покупателю.

Проверено (по докладу саб-агента, дословные цитаты):
- vedomosti.ru/business/news/2023/10/18/1001348-bonava-rastorgla-
  soglashenie-s-rbi: «группа не получила разрешение от «специального
  комитета»» (правительственная комиссия по контролю за иностранными
  инвестициями не одобрила сделку в срок); «Bonava отказалась от
  сделки с группой RBI и заключила соглашение по продаже петербургских
  активов с армянской компанией Star Development».
- kommersant.ru/doc/6161686 (16.08.2023, промежуточный этап): «ФАС
  одобрила сделку по приобретению бизнеса шведского застройщика Bonava
  группой RBI... Окончательное решение остаётся за правительственной
  комиссией по контролю за осуществлением иностранных инвестиций в
  РФ» — то есть согласование ФАС RBI получил, а решающего согласования
  правкомиссии — нет.
- spb.vedomosti.ru/business/news/2023/11/14/1005810-fas-soglasovala-
  sdelku-po-pokupke-aktivov-bonava-v-peterburge-dlya-gk-fsk: реальным
  покупателем стала «Группа компаний «ФСК»» через армянскую Star
  Development, сделка закрыта 14 ноября 2023 года.
- interfax.ru/business/947773: бывшее юрлицо Bonava (ООО «Бонава
  Санкт-Петербург») переименовано в ООО «БН Девелопмент» 19 февраля
  2024 года, новый владелец — Владимир Воронин, президент ГК «ФСК».

Статус меняется на «Не состоялась» (не на «Закрыта») — сделка именно
СОРВАЛАСЬ у RBI, актив достался другому покупателю. Реальный исход
(продажа Star Development/ФСК) — отдельная сделка с другими сторонами
и другой суммой, для которой в базе нет карточки; решение о том,
заводить ли её, — за приточной рутиной, зафиксировано в CLAUDE.md.

НЕ ВНЕСЕНО: (1) новая карточка на сделку Bonava/Star Development —
это задача притока, не качества; (2) точная сумма реальной сделки —
источники расходятся («почти 4,9 млрд руб.» у Ведомости.СЗ и «около
50 млн евро» у Интерфакса), расхождение не разрешено; (3) дальнейшая
судьба площадок под ФСК/«БН Девелопмент» (например, перепродажа части
проекта на Охте «Легенде» в мае 2025 года) — это уже третий, ещё более
поздний слой сюжета, не задача этой правки.

Запуск: python3 pipeline/fix_rbi_bonava_deal_fell_through.py
        python3 pipeline/fix_rbi_bonava_deal_fell_through.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'ga2332f97'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Не состоялась'

OLD_ECO_CONTEXT = (
    'Претендентов на активы немного, вероятно, потому, что площадки '
    'застройщика невелики и требуют дополнительных затрат на '
    'подготовку к строительству.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' ФАС одобрила сделку в августе 2023 года, но '
    'правительственная комиссия по контролю за иностранными '
    'инвестициями не дала разрешение в срок — в октябре 2023 года '
    'Bonava расторгла соглашение с RBI и продала петербургские активы '
    'другому покупателю, армянской Star Development (связана с ГК '
    '«ФСК», основной владелец — Владимир Воронин); сделка закрыта 14 '
    'ноября 2023 года.'
)

OLD_SRC = [['Коммерсантъ', 'https://www.kommersant.ru/amp/6015630']]
NEW_SRC = OLD_SRC + [
    ['Ведомости', 'https://www.vedomosti.ru/business/news/2023/10/18/1001348-bonava-rastorgla-soglashenie-s-rbi'],
    ['Ведомости Санкт-Петербург', 'https://spb.vedomosti.ru/business/news/2023/11/14/1005810-fas-soglasovala-sdelku-po-pokupke-aktivov-bonava-v-peterburge-dlya-gk-fsk'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['status'] == OLD_STATUS
    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['status'] = NEW_STATUS
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
