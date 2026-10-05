# -*- coding: utf-8 -*-
"""Качество, 5 октября 2026 — отмена ошибочной правки того же прогона.

Подтверждение фактов (`facts_confirm.py`) сегодня дало читателям A и B
только 2 источника карточки `technored` (Коммерсантъ, рэнкинг «Ъ» —
пакет 51%; technored.ru — процент не называет), и оба сошлись на 51%,
разойдясь с текстом карточки (49%, «контрольного пакета у «Вартона» нет»)
— я исправил карточку на 51% через `review.py`.

Это было ОШИБКОЙ. `pipeline/ingest/fixes/batch_a_2025.py` уже
документирует: именно эта же цифра 51% из рэнкинга «Ъ» была найдена и
ОТВЕРГНУТА 14 августа 2026 года («партия 5 агентов, раунд 2») — прямая
цитата гендиректора Technored Артёма Лукина в comnews.ru прямо опровергла
51%: «"Вартон" не владеет контрольным пакетом акций, размер выкупа
составляет 49%». Рэнкинг «Ъ» получает цифру от консультанта стороны
(ASB Consulting Group), а не от самих сторон — это и увидели сегодняшние
читатели (attribution=adviser), но без comnews.ru в списке источников
задания не нашли более авторитетную прямую цитату, которая эту цифру уже
опровергала. comnews.ru при этом не входит в текущий `src` карточки —
это отдельный, более старый гэп (ссылка раньше была, а потом пропала),
разбирать его — отдельная задача, не сегодня.

Возвращает `eco.share`, `stake_acquired` и `facts.stake` к состоянию до
сегодняшней правки. `facts.stake` правится здесь явно, а не оставляется
на `facts_derive.py --write`: once `basis` стал `stale`, слой фактов
сознательно НЕ пересчитывает его автоматически обратно в `rule` (защита
от бага 21 сентября — «проверенный факт тихо превращается в rule») — это
верно для настоящего «карточка изменилась, нужно перечитать», но здесь
не тот случай: сама правда не менялась, менялась только моя ошибочная
запись в рамках этого же прогона, поэтому откатываю руками.

Запуск:
    python3 pipeline/fix_technored_revert_stake_51_2026_10_05.py            # сухой прогон
    python3 pipeline/fix_technored_revert_stake_51_2026_10_05.py --write    # запись
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'

OLD_SHARE = 'Формат сделки: купля-продажа акций Размер пакета акций/долей: 51%'
RESTORED_SHARE = 'Размер выкупа — 49%, контрольного пакета у «Вартона» нет.'


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals'] if isinstance(data, dict) else data
    target = [d for d in deals if d.get('id') == 'technored']
    assert len(target) == 1, target
    card = target[0]
    assert card['eco']['share'] == OLD_SHARE, card['eco']['share']
    assert card.get('stake_acquired') == 51.0, card.get('stake_acquired')

    card['eco']['share'] = RESTORED_SHARE
    card['stake_acquired'] = None

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('eco.share и stake_acquired карточки technored возвращены к 49%. ЗАПИСАНО.')
    else:
        print('Сухой прогон: вернул бы eco.share/stake_acquired к 49%. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
