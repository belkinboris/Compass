# -*- coding: utf-8 -*-
"""Карточка `g5eb6ff22` («Росатом» завершил выкуп у Шишкарева 51% в ГК
«Дело»): источники ЭТАПА «Сделка завершена» и три новые публикации о
закрытии.

ЗАЧЕМ. Владелец 7 октября 2026: «в посте про Росатом указал только
источник Прайм, хотя в консоли написал, что Коммерсантъ подтвердил
финальную цену 77 млрд ₽». Прогон притока 12:20 МСК дописал «Коммерсантъ» и
РБК в `src` карточки (`fixes/fix_rosatom_delo_closed.py`), но у самого
этапа остался один `source` — ПРАЙМ, а пост этапа берёт источники этапа.
Здесь этап получает `sources`: первым — ПРАЙМ (первым сообщил о закрытии),
дальше подтверждения. `review.py` источники этапа не правит, поэтому —
разовый скрипт с проверкой старого значения.

Новые публикации 7 октября (прочитаны, цитаты дословно):
- Reuters / The Moscow Times: «Российская госкорпорация Росатом завершила
  выкуп доли Сергея Шишкарева в одном из крупнейших логистических холдингов
  РФ, группе компаний Дело» (цены нет; со ссылкой на заявление Лихачева).
- Infranews.ru, 12:17: «„Росатом“ завершил выкуп 51% доли Сергея Шишкарева
  в группе компаний „Дело“ и стал владельцем 100% холдинга, сообщил глава
  госкорпорации Алексей Лихачев» («Стоимость сделки не раскрывается, однако
  ранее была озвучена сумма 77 млрд рублей»).
- Абирег, 12:11: «Госкорпорация „Росатом“ завершила выкуп 51%-ной доли
  Сергея Шишкарева в группе компаний „Дело“» (77 млрд — объявленная цена
  выкупа пакета).
Alta.ru пересказывает РБК — перепечатка, не источник; MirTesen, www1,
business-magazine — агрегаторы.

    python3 pipeline/fix_g5eb6ff22_closing_sources.py           # показать
    python3 pipeline/fix_g5eb6ff22_closing_sources.py --write   # записать
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL = 'g5eb6ff22'
PRIME = ['ПРАЙМ', 'https://1prime.ru/20261007/likhachev-874021694.html']
KOMMERSANT = ['Коммерсантъ', 'https://www.kommersant.ru/doc/9008037']
RBC = ['РБК', 'https://www.rbc.ru/business/07/10/2026/6ac604919a79474bd4a62c9e']
MT = ['Reuters / The Moscow Times',
      'https://ru.themoscowtimes.com/2026/10/07/rosatom-kupil-dolyu-sergeya-shishkareva-v-logisticheskoy-gruppe-delo-a207974']
INFRANEWS = ['Infranews.ru', 'https://www.infranews.ru/novosti/71593-rosatom-zavershil-vykup-51-gruppy-delo-u-shishkareva/']
ABIREG = ['Абирег', 'https://abireg.ru/newsitem/117978']

STAGE_SOURCES = [PRIME, KOMMERSANT, RBC, MT, INFRANEWS, ABIREG]
NEW_CARD_SOURCES = [MT, INFRANEWS, ABIREG]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))   # перечитано прямо перед записью
    deal = next(d for d in data['deals'] if d['id'] == DEAL)
    stage = next(e for e in deal.get('events') or [] if e.get('kind') == 'closed')
    assert stage.get('date') == '2026-10-07', stage.get('date')
    assert stage.get('source') == PRIME, stage.get('source')
    assert 'sources' not in stage, stage.get('sources')
    urls = {s[1] for s in deal.get('src') or [] if len(s) > 1}
    assert {KOMMERSANT[1], RBC[1], PRIME[1]} <= urls, 'ждали Коммерсантъ, РБК и ПРАЙМ в src'

    stage['sources'] = [list(s) for s in STAGE_SOURCES]
    added = [list(s) for s in NEW_CARD_SOURCES if s[1] not in urls]
    deal['src'] = list(deal.get('src') or []) + added
    print('Этап %s: источников было 1, стало %d' % (stage['id'], len(stage['sources'])))
    for s in stage['sources']:
        print('   %s — %s' % (s[0], s[1]))
    print('В src карточки добавлено: %d' % len(added))
    for s in added:
        print('   %s — %s' % (s[0], s[1]))
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('записано')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
