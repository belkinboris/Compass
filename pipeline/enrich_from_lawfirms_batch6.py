# -*- coding: utf-8 -*-
"""Партия 6 @LawFirms: объявления, которые правило не видело из-за формулировки.

ЗАЧЕМ. После разбора всех 91 объявления остались 468 постов канала, похожих
на сделку. Читать их подряд дорого и почти всё — мимо (вебинары, назначения,
рейтинги, зарубежные новости). Но среди них нашлись объявления о
сопровождении, которые правило `advisors.lead_advisor` пропускало не по
смыслу, а по формулировке: «обеспечила юридическое сопровождение»,
«осуществила комплексное сопровождение», «сообщает о консультировании».
Первый список глаголов собирался по одной партии из десяти постов — и
оказался списком ТЕХ формулировок, а не всех.

ЗАМЕР ПОСЛЕ РАСШИРЕНИЯ ПРАВИЛА: срабатываний было 115, стало 128. Все 13
добавившихся — настоящие объявления фирм, ложных ноль, потерянных ноль.

ЧТО ЗДЕСЬ ПРАВИТСЯ. Из этих 13 шесть сделок уже стояли в базе с тем же
консультантом (ВТБ/АФК «Система», Ситибанк, SPO «Эталон», Wildberries/
«Ситимобил», IPO «Займера», Sk Capital/Softline — у последней консультант
был только со стороны покупателя). Две карточки получают факт, пять сделок
заводятся отдельным прогоном.

ЗАГЛУШКА У IPO «ИНКАБ ХОЛДИНГА»: «Эмитент — Не раскрывался». Объявление
Better Chance её опровергает, поэтому строка заменяется, а не дополняется.

Запуск:
    python3 pipeline/enrich_from_lawfirms_batch6.py            # сухой прогон
    python3 pipeline/enrich_from_lawfirms_batch6.py --write    # записать
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SRC_LABEL = 'РУЛЬФЫ, ИЛЬФЫ И ИНХАУСЫ (@LawFirms)'

ADVISORS = [
    ('inkab-ipo',
     'Юридический консультант эмитента («Инкаб Холдинг»)',
     'Better Chance',
     'Полное юридическое сопровождение публичного размещения акций: структура холдинга со '
     '«сквозным» корпоративным управлением в соответствии со Стандартами IPO Московской '
     'биржи. Сопровождение силами практики рынков капитала. '
     'Источник: https://t.me/LawFirms/11090',
     'https://t.me/LawFirms/11090',
     'Эмитент — «Инкаб Холдинг»',
     ['Эмитент — «Инкаб Холдинг»']),
    ('ge9937266',
     'Юридический консультант продающей стороны (группа компаний Softline)',
     'White Square',
     'Сопровождение группы компаний Softline в связи с продажей более 10% акций '
     'инвестиционной компании Sk Capital. Источник: https://t.me/LawFirms/9569',
     'https://t.me/LawFirms/9569',
     None,
     ['Юридический консультант']),
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for did, role, firm, note, url, drop, before in ADVISORS:
        deal = by_id.get(did)
        assert deal is not None, 'карточки %s нет в базе' % did
        adv = (deal.get('law') or {}).get('adv') or []
        assert firm.lower() not in ' | '.join(str(a[1]) for a in adv if len(a) > 1).lower(), \
            '%s: %s уже записан' % (did, firm)
        assert [str(a[0]) for a in adv if a] == before, \
            '%s: роли другие (%r)' % (did, [str(a[0]) for a in adv if a])
        assert url not in {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}, \
            '%s: объявление уже стоит в источниках' % did
        print('%s  %s' % (did, (deal.get('title') or '')[:58]))
        if drop:
            print('    убрать заглушку: %s' % drop)
        print('    + %s — %s' % (role, firm))

    print('\nкарточек к правке: %d' % len(ADVISORS))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    for did, role, firm, note, url, drop, before in ADVISORS:
        deal = by_id[did]
        law = deal.setdefault('law', {})
        law['adv'] = [a for a in (law.get('adv') or []) if not (drop and str(a[0]) == drop)]
        law['adv'].append([role, firm, note])
        deal.setdefault('src', []).append([SRC_LABEL, url])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО в %s' % os.path.relpath(DATA, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
