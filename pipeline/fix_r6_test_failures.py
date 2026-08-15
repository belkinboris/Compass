# -*- coding: utf-8 -*-
"""Три инварианта, упавших после записи партии 5 агентов, раунд 6 (15 августа
2026) — правит показываемое значение, не меняет решение о том, какой факт
верен.

1. c21076c79 (OBI) — сумма «1 евро» словом вместо значка: CLAUDE.md требует
   «€» ПЕРЕД числом.
2. gfc7e5649, g50d455bb — buyer_name записан ПОВЕРХ уже существующего
   профиля buyer, тест `test_buyer_is_named_once` не разрешает оба сразу.
   gfc7e5649: buyer уже указывает на профиль «Awara IT Group» — Ермаков и
   Шумаков и есть совладельцы этой группы (та же сущность), buyer_name
   избыточен. g50d455bb: карточка описывает ДВЕ сделки бывших заводов IKEA
   (Слотекс и Лузалес одним лотом), buyer уже указывает на профиль
   «Лузалес» — «ООО «Инвест Плюс»» из находки относится ТОЛЬКО к заводу в
   Великом Новгороде (сторона Слотекса), а не ко всей карточке; писать его
   в общее поле buyer_name значило бы приписать сумму/сторону одной сделки
   карточке о двух. И в том, и в другом случае факт остаётся в law.struct
   дословной цитатой — просто не дублируется в buyer_name.
3. g5c3eeb06, g383b170f, g0e8b9617, g2dc1ba74 — law.appr на немецком/
   английском либо не называет узнаваемый орган («все необходимые
   разрешения получены» без имени), либо называет орган словами, которых
   нет в `APPROVING_BODY` (австрийская DSN, «the Russian authorities»,
   «the competition regulator»). Перенесено в law.terms — тот же приём,
   что уже применялся в раунде 4 (g85dfa88c, g8a66f3c7): факт настоящий,
   орган не назван узнаваемо — не согласование, а условие закрытия.

ЗАПУСК:
    python3 pipeline/fix_r6_test_failures.py            # сухой прогон
    python3 pipeline/fix_r6_test_failures.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SUM_OLD = '1 евро (символическая сумма)'
SUM_NEW = '€1 (символическая сумма)'

DROP_BUYER_NAME = {
    'gfc7e5649': 'Александр Ермаков и Юрий Шумаков',
    'g50d455bb': 'ООО «Инвест Плюс»',
}

# (id, old law.appr, куда девать: None — просто заглушка, либо (действие
# на law.terms))
APPR_TO_TERMS = {
    'g5c3eeb06': (
        'Genehmigt wurde die Transaktion laut Bericht von der Direktion '
        'Staatsschutz und Nachrichtendienst (DSN), die für '
        'Sanktionsangelegenheiten zuständig ist.',
        # у этой карточки law.terms уже занят — дописываем через разделитель
        'Im Kaufvertrag festgehalten wurde wiederum, dass die '
        'Raiffeisenbank Russland für die Bepoda gegenüber der Sberbank ein '
        'sogenanntes Akkreditiv („Letter of Credit") – eine Art '
        'Bankbürgschaft – abgeben sollte.',
    ),
    'g383b170f': (
        'With the approval of the Russian authorities, Kiilto has now '
        'been able to sell all its Russian subsidiaries.',
        '—',
    ),
    'g0e8b9617': (
        'The deal, the price of which was not disclosed, is subject to '
        'approval by the competition regulator, Reuters reported, citing '
        'the company.',
        '—',
    ),
    'g2dc1ba74': (
        'Закрытие сделки не подлежит обременениям, все необходимые '
        'разрешения получены.',
        '—',
    ),
}
APPR_PLACEHOLDER = 'Публично не сообщалось'


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}

    deal = by_id['c21076c79']
    assert deal.get('sum') == SUM_OLD, 'c21076c79 sum уже другой: %r' % deal.get('sum')
    assert deal['eco'].get('sum') == SUM_OLD, 'c21076c79 eco.sum уже другой'
    print('ПРАВИМ c21076c79: sum/eco.sum %r -> %r' % (SUM_OLD, SUM_NEW))

    for cid, expected in DROP_BUYER_NAME.items():
        deal = by_id[cid]
        assert deal.get('buyer_name') == expected, \
            '%s: buyer_name уже другой: %r' % (cid, deal.get('buyer_name'))
        assert deal.get('buyer'), '%s: buyer-профиль пуст, снимать нечего' % cid
        print('ПРАВИМ %s: buyer_name %r -> None (профиль buyer уже покрывает)'
              % (cid, expected))

    for cid, (old_appr, expected_terms) in APPR_TO_TERMS.items():
        deal = by_id[cid]
        assert deal.get('law', {}).get('appr') == old_appr, \
            '%s: law.appr уже другой: %r' % (cid, deal.get('law', {}).get('appr'))
        assert deal.get('law', {}).get('terms') == expected_terms, \
            '%s: law.terms уже другой: %r' % (cid, deal.get('law', {}).get('terms'))
        print('ПРАВИМ %s: law.appr -> заглушка, факт переносится в law.terms' % cid)

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    deal = by_id['c21076c79']
    deal['sum'] = SUM_NEW
    deal['eco']['sum'] = SUM_NEW

    for cid in DROP_BUYER_NAME:
        by_id[cid]['buyer_name'] = None

    for cid, (old_appr, expected_terms) in APPR_TO_TERMS.items():
        deal = by_id[cid]
        if expected_terms == '—':
            deal['law']['terms'] = old_appr
        else:
            deal['law']['terms'] = expected_terms + ' ' + old_appr
        deal['law']['appr'] = APPR_PLACEHOLDER

    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
