# -*- coding: utf-8 -*-
"""Заметка владельца 11 сентября 2026 (id решения 606, карточка gbd3416b4,
«Холдинг «Автобан» приобретает «Уренгойдорстрой»»): «пусть останется одна
сделка, в разделе дополнительная информация можно написать, что Автобан
вышел. в разделе "цель сделки" написано "У «Уренгойдорстроя» есть
эксклюзивные подряды на дорожное строительство по всему Ямало-Ненецкому
автономному округу." это надо убрать, нет подтверждения точного, что это
цель.»

Карточка НЕ разделяется (владелец прямо сказал «одна сделка»). Два
изменения: (1) `eco.rationale` — снята непроверенная догадка о мотиве
покупки (источник не называет эксклюзивность подрядов ПРИЧИНОЙ сделки,
это отдельный факт о цели, ошибочно поданный как мотив); (2) `extra`
дополнен фактом о выходе «Автобана» — он уже подробно изложен в
`eco.context`, но на главной вкладке читатель его не видел.

Запуск: python3 pipeline/fix_avtoban_urengoidorstroy_rationale_extra.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'gbd3416b4'
OLD_RATIONALE = ('У «Уренгойдорстроя» есть эксклюзивные подряды на дорожное '
                  'строительство по всему Ямало-Ненецкому автономному округу.')
OLD_EXTRA = ''
NEW_EXTRA = ('К лету 2026 года холдинг «Автобан» полностью вышел из состава '
             'учредителей «Уренгойдорстроя» на фоне финансовых проблем '
             'компании: её включили в реестр недобросовестных поставщиков, '
             'а один из кредиторов требует признать её банкротом.')


def main(write=False):
    with open(BASE_PATH, encoding='utf-8') as f:
        base = json.load(f)

    card = next((c for c in base['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, 'карточка %s не найдена' % CARD_ID
    assert card['eco']['rationale'] == OLD_RATIONALE, 'eco.rationale уже другой'
    assert card['extra'] == OLD_EXTRA, 'extra уже другой'

    card['eco']['rationale'] = '—'
    card['extra'] = NEW_EXTRA

    print('Правка %s: eco.rationale очищен, extra дополнен фактом о выходе '
          '«Автобана».' % CARD_ID)

    if write:
        with open(BASE_PATH, 'w', encoding='utf-8') as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('(сухой прогон, для записи — --write)')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
