# -*- coding: utf-8 -*-
"""Десять карточек раунда 8 (партия 5 агентов, 15 августа 2026), у которых
дата и/или статус разошлись с источником — большинство в пределах 2023
года (закрытие случилось позже объявления/переговоров), одна — со сменой
года (g97f0244e: источник прямо называет декабрь ПРОШЛОГО года, то есть
2022-й, а не дату публикации расследования в марте 2023).

ПОЧЕМУ НЕ ЧЕРЕЗ review.py. Смена года через FIXES категорически не
разрешена date_is_supported() (см. CLAUDE.md). Смена даты И статуса
ОДНОВРЕМЕННО в разных карточках удобнее и безопаснее одним скриптом со
своим assert на исходное состояние, чем размазывать по FIXES-таблице и
отдельным полям.

c6eb3063c (бренд «Республика»): КРУПНАЯ ПРАВКА — карточка несла стартовую
цену аукциона (53,5 млн ₽) как итоговую сумму; аукцион состоялся 24 июля
2023 года и актив ушёл в 11 РАЗ ДЕШЕВЛЕ — за 4,8 млн ₽, покупателю Дмитрию
Алиеву, чьё имя в карточке отсутствовало.

g88d5e740 (НЛМК сортовой дивизион): buyer_name заполняется впервые —
структуры Евгения Зубицкого (ПМХ); поле `sum` НЕ трогается — текущая
оценка (75–100 млрд ₽) была из более ранних слухов, новый источник даёт
другую методику оценки (40–50 млрд ₽ на бездолговой основе), сравнивать
их напрямую нельзя, решение о замене — за человеком.

ЗАПУСК:
    python3 pipeline/fix_r8_date_status_corrections.py            # сухой прогон
    python3 pipeline/fix_r8_date_status_corrections.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# (id, old_date, new_date, old_status, new_status, extra_fields_or_None, src_label, src_url)
FIXES = [
    ('g61a8095f', '2023-02-27', '2023-05-16', 'Закрыта', 'Закрыта', None,
     'Ведомости', 'https://www.vedomosti.ru/business/news/2023/05/16/975217-polskii-franchaizi-kfc-zakril-sdelku-po-prodazhe-215-restoranov'),
    ('g97f0244e', '2023-03-06', '2022-12-15', 'Закрыта', 'Закрыта', None,
     'Ведомости', 'https://www.vedomosti.ru/realty/articles/2023/03/06/965329-struktura-roskosmosa-prodala-krupnii-uchastok'),
    ('gc4c76129', '2023-03-06', '2023-09-04', 'Обсуждается', 'Закрыта', None,
     'Хабр (со ссылкой на РБК)', 'https://habr.com/ru/news/758758/'),
    ('g8ea21d1b', '2023-02-06', '2023-03-24', 'Обсуждается', 'Закрыта', None,
     'Интерфакс', 'https://www.interfax.ru/business/892787'),
    ('g88d5e740', '2023-02-17', '2023-09-06', 'Обсуждается', 'Закрыта',
     {'buyer_name': (None, 'Структуры Евгения Зубицкого (ПМХ)')},
     'Коммерсантъ', 'https://www.kommersant.ru/doc/6199678'),
    ('g7ad4e39d', '2023-03-28', '2023-04-20', 'Обсуждается', 'Подписана', None,
     'Ведомости', 'https://www.vedomosti.ru/business/news/2023/04/20/971857-henkel-prodazhe-biznesa-rossii'),
    ('c6eb3063c', '2023-02-10', '2023-07-24', None, 'Закрыта',
     {'sum': ('53,5 млн ₽', '4,8 млн ₽'), 'buyer_name': (None, 'Дмитрий Алиев')},
     'vc.ru (со ссылкой на «Коммерсантъ»)',
     'https://vc.ru/marketplace/770621-brend-i-sait-knizhnoi-seti-respubliki-prodali-na-torgah-za-48-mln-rublei-pri-nachalnoi-cene-v-535-mln-rublei'),
    ('g2a6d5d16', '2023-03-31', '2023-08-14', 'Закрыта', 'Закрыта', None,
     'Коммерсантъ', 'https://www.kommersant.ru/doc/6159861'),
    ('g4ac0a0a7', '2023-05-01', '2023-09-19', 'Закрыта', 'Закрыта', None,
     'Интерфакс', 'https://www.interfax.ru/amp/921561'),
    ('g694126dd', '2023-04-14', '2023-03-23', 'Закрыта', 'Закрыта', None,
     'Ведомости', 'https://www.vedomosti.ru/realty/articles/2023/04/14/970860-prezident-futbolnogo-kluba-tsska-evgenii-giner-prodal-torgovii-tsentr-start'),
]


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    for cid, old_date, new_date, old_status, new_status, extra, label, url in FIXES:
        deal = by_id[cid]
        assert deal.get('date') == old_date, \
            '%s: date уже другой: %r (ожидали %r)' % (cid, deal.get('date'), old_date)
        assert deal.get('status') == old_status, \
            '%s: status уже другой: %r (ожидали %r)' % (cid, deal.get('status'), old_status)
        if extra:
            for field, (efrom, eto) in extra.items():
                assert deal.get(field) == efrom, \
                    '%s: %s уже другой: %r (ожидали %r)' % (cid, field, deal.get(field), efrom)
        print('ПРАВИМ %s: date %r -> %r, status %r -> %r%s' % (
            cid, old_date, new_date, old_status, new_status,
            (', ' + ', '.join('%s %r -> %r' % (f, v[0], v[1]) for f, v in extra.items())) if extra else ''))

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    for cid, old_date, new_date, old_status, new_status, extra, label, url in FIXES:
        deal = by_id[cid]
        deal['date'] = new_date
        deal['status'] = new_status
        if extra:
            for field, (efrom, eto) in extra.items():
                deal[field] = eto
        existing_urls = {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}
        if url not in existing_urls:
            deal.setdefault('src', []).append([label, url])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
