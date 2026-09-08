# -*- coding: utf-8 -*-
"""Месячная очередь, 8 сентября 2026 — карточка `c6fd3a848` («Передача
авиагрузовой группы «Волга-Днепр» государству», август 2025) описывала
намерение основателя Алексея Исайкина безвозмездно передать активы
государству. Личный WebFetch (vedomosti.ru/business/news/2025/09/17/
1139840, 17.09.2025) подтвердил дословно: «Минтранс отказался от
предложения, сославшись на нецелесообразность в условиях санкций» — то
есть само предложение ОТКЛОНЕНО адресатом, а не просто повисло без
ответа. Статус меняется с «Обсуждается» на «Не состоялась».

Отдельно (НЕ вносится в структурные поля этой карточки — другой сюжет,
другие стороны, кандидат на свою карточку, записан в «Известные
проблемы» CLAUDE.md): вместо передачи государству группа продана
коммерческому покупателю — «ЕАС Групп» (структура Евгения Солодилина,
экс-главы аэропорта Жуковский и авиакомпании Red Wings). Личный WebFetch
(akm.ru, 12.01.2026): «К «ЕАС Групп» отошли: ООО «Волга-Днепр-Москва»,
ООО «Атран» и ООО «АК ЭйрБриджКарго»»; «Сделка ещё не завершена, доли
находятся в залоге у прежних владельцев» — то есть на дату этой заметки
сделка в процессе, а не закрыта окончательно.

Поля `eco.context`/`law.struct` уже прошли вычитку — правка не трогает
их, только `status`.

Запуск:
    python3 pipeline/fix_volga_dnepr_state_transfer_rejected.py            # сухой прогон
    python3 pipeline/fix_volga_dnepr_state_transfer_rejected.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
CARD_ID = 'c6fd3a848'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Не состоялась'


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}
    card = by_id[CARD_ID]

    assert card.get('status') == OLD_STATUS, \
        'status уже другой: %r' % (card.get('status'),)

    print('status: %r -> %r (Минфин/Минтранс отклонил предложение, '
          'vedomosti.ru 17.09.2025)' % (OLD_STATUS, NEW_STATUS))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    card['status'] = NEW_STATUS

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
