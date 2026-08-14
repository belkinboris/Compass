# -*- coding: utf-8 -*-
"""Консультанты из дополнительного consultant-only прохода ChatGPT
(14 августа 2026): отдельный поиск по сайтам юрфирм/инвестбанков и по
рейтингу Mergers.ru, поверх основной партии round1. Тот же класс правки,
что `enrich_from_lawfirms_batchN.py` — `law.adv` не проверяется `review.py`
(поле поверх дословных цитат не строится: пересказ роли, а не сама цитата),
поэтому правка идёт отдельным скриптом с `assert` на исходное состояние.

ЧТО ПРОВЕРЕНО, А ЧТО НЕТ.
- g51cff34c: ChatGPT подал это как «прямое подтверждение» (MVP — консультант
  покупателя Brio Capital), но единственный указанный источник — рейтинг
  Mergers.ru (https://mergers.ru/rankings/2025-12/381/), а там у MVP в списке
  клиентов стоит САМ ПРЕДМЕТ («Платёжный сервис А3»), а не «Brio Capital».
  Записано честно — сторона не установлена, роль звучит осторожнее, чем в
  черновике ChatGPT.
- rosatom-mali: Advance Capital на своём сайте называет долю 80%, а в нашей
  карточке (`eco.share`, `law.struct`) уже стоит 75% с отдельным источником.
  Расхождение НЕ разрешается этим скриптом — консультант добавлен, а доля не
  трогается; сверка вынесена в примечание для будущего чтения.

Запуск: python3 pipeline/enrich_consultants_r1.py            # сухой прогон
        python3 pipeline/enrich_consultants_r1.py --write    # запись
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# (id, роль, фирма, пояснение, url, заглушка_для_снятия_или_None,
#  ожидаемые роли ДО правки)
PLAN = [
    ('g51cff34c',
     'Юридический консультант («Платёжный сервис А3»)',
     'Melling, Voitishkin & Partners (MVP)',
     'В рейтинге консультантов Mergers.ru за 2025 год у MVP в списке клиентов '
     'значится «Платёжный сервис А3» — предмет этой сделки (Brio Capital '
     'приобрела 80% сервиса). Сторона (покупатель или сама компания) '
     'рейтингом не уточняется. Источник: https://mergers.ru/rankings/2025-12/381/',
     'https://mergers.ru/rankings/2025-12/381/',
     'Стороны сделки',
     ['Стороны сделки']),

    ('gfe21a083',
     'Финансовый консультант покупателя (Алексей Маврин)',
     'Advance Capital',
     'В перечне сделок на своём сайте Advance Capital называет проект '
     '«Выкуп финансовых инвесторов в сети домов престарелых СГЦ Опека» '
     '(июль 2024, сумма не раскрывается), роль — финансовый консультант '
     'покупателя. Источник: https://advancecapital.ru/sdelki/',
     'https://advancecapital.ru/sdelki/',
     'Стороны сделки',
     ['Стороны сделки']),

    ('rosatom-mali',
     'Финансовый консультант покупателя (структура Росатома)',
     'Advance Capital',
     'В перечне сделок на своём сайте Advance Capital называет проект '
     '«Приобретение УУГ (Росатом) 80% долей литиевого актива в Республике '
     'Мали» (октябрь 2024), роль — финансовый консультант покупателя. Доля '
     '(80%) расходится с уже стоящей в карточке (75%, eco.share/law.struct, '
     'источник — Интерфакс) — расхождение не разрешено, доля не трогается. '
     'Источник: https://advancecapital.ru/sdelki/',
     'https://advancecapital.ru/sdelki/',
     'Стороны проекта',
     ['Стороны проекта']),

    ('g300d56ed',
     'Финансовый консультант продавца',
     'Advance Capital',
     'В перечне сделок на своём сайте Advance Capital называет проект '
     '«Продажа 100% долей торговой сети Молния Ленте» (июнь 2025), роль — '
     'финансовый консультант продавца. Источник: https://advancecapital.ru/sdelki/',
     'https://advancecapital.ru/sdelki/',
     None,
     ['Юридический консультант покупателя (Группа «Лента»)',
      'Юридический консультант продавцов (предположительно)']),

    ('c985468d2',
     'Финансовый консультант продавца',
     'Advance Capital',
     'В перечне сделок на своём сайте Advance Capital называет проект '
     '«Продажа 100% компании Молл Ленте» (июнь 2025), роль — финансовый '
     'консультант продавца. Источник: https://advancecapital.ru/sdelki/',
     'https://advancecapital.ru/sdelki/',
     None,
     ['Юридический консультант']),

    ('ga7e96633',
     'Юридический консультант эмитента и банков-организаторов',
     'Better Chance (бывш. АБ «Проспект»)',
     'Better Chance на своём сайте прямо подтверждает: практика рынков '
     'капитала консультировала B2B-РТС и банков-организаторов (Т-Банк, '
     'Совкомбанк) по структуре размещения, договорам с организаторами и '
     'розничными брокерами, lock-up, стабилизации и legal opinion. '
     'Источник: https://www.betterchance.ru/media_center/news/'
     'better-chance-soprovodila-pervoe-ipo-na-rossiyskom-rynke-v-2026-godu-'
     'publichnoe-predlozhenie-aktsiy-/',
     'https://www.betterchance.ru/media_center/news/better-chance-soprovodila-pervoe-ipo-na-rossiyskom-rynke-v-2026-godu-publichnoe-predlozhenie-aktsiy-/',
     'Стороны сделки',
     ['Стороны сделки']),
]

SRC_LABEL = {
    'g51cff34c': 'Mergers.ru (рейтинг консультантов)',
    'gfe21a083': 'Advance Capital',
    'rosatom-mali': 'Advance Capital',
    'g300d56ed': 'Advance Capital',
    'c985468d2': 'Advance Capital',
    'ga7e96633': 'Better Chance',
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for did, role, firm, note, url, drop, before in PLAN:
        deal = by_id.get(did)
        assert deal is not None, 'карточки %s нет в базе' % did
        adv = (deal.get('law') or {}).get('adv') or []
        names = ' | '.join(str(a[1]) for a in adv if len(a) > 1).lower()
        assert firm.split(' (')[0].lower() not in names, \
            '%s: %s уже записан — перепроверьте, не двойной ли это прогон' % (did, firm)
        assert [str(a[0]) for a in adv if a] == before, \
            '%s: роли в «Консультантах» другие (%r), чем ожидалось (%r)' % (
                did, [str(a[0]) for a in adv if a], before)
        if drop:
            assert drop in before, '%s: заглушки «%s» нет — состояние другое' % (did, drop)
        existing_urls = {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}
        assert url not in existing_urls, '%s: источник уже стоит' % did

        print('%s  %s' % (did, (deal.get('title') or '')[:60]))
        if drop:
            print('    убрать заглушку: %s' % drop)
        print('    + %s — %s' % (role, firm))

    print('\nкарточек к правке: %d' % len(PLAN))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0

    for did, role, firm, note, url, drop, before in PLAN:
        deal = by_id[did]
        law = deal.setdefault('law', {})
        adv = [a for a in (law.get('adv') or []) if not (drop and str(a[0]) == drop)]
        adv.append([role, firm, note])
        law['adv'] = adv
        deal.setdefault('src', []).append([SRC_LABEL[did], url])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
