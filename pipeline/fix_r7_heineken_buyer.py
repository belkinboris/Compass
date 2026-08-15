# -*- coding: utf-8 -*-
"""g6168731b (Heineken): заголовок карточки называет покупателя
«неразглашаемым», хотя источник (Ведомости, 25.08.2023) прямо его
называет — группа «Арнест». Сделка также уже закрыта, а не «обсуждается».
Партия 5 агентов, раунд 7, 15 августа 2026.

Один скрипт вместо записи в FIXES, потому что правок много и разнородно:
buyer_name (сейчас пусто), sum и eco.sum (сейчас «Не раскрыта» — по
образцу OBI из раунда 6, €1 символической суммой), law.terms (сейчас
«—» — два условия), status. law.appr не трогаем: фраза «сделка получила
все необходимые одобрения» не называет орган узнаваемо (APPROVING_BODY),
поэтому факт идёт в law.terms, а не в law.appr — тот же приём, что уже
применялся в раунде 4 и раунде 6 для похожих случаев.

ЗАГОЛОВОК карточки («…неразглашаемому покупателю») это НЕ чинит — он
не соответствует фактам, но переименование старых карточек осознанно
не автоматизировано (см. CLAUDE.md); нужно решение владельца.

ЗАПУСК:
    python3 pipeline/fix_r7_heineken_buyer.py            # сухой прогон
    python3 pipeline/fix_r7_heineken_buyer.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CID = 'g6168731b'
BUYER_NAME = 'Группа «Арнест»'
SUM_NEW = '€1 (символическая сумма)'
TERMS_NEW = (
    'По условиям соглашения покупатель должен погасить задолженность '
    'российского бизнеса перед иностранным производителем в размере '
    'около 100 млн евро. Соглашение не предусматривает опциона на '
    'обратный выкуп активов, утверждается в сообщении компании. Пиво под '
    'товарным знаком Amstel, по условиям соглашения, в России перестанут '
    'выпускать через шесть месяцев. Сделка получила все необходимые '
    'одобрения, говорится в сообщении пивоваренного концерна.'
)
SRC = ('Ведомости', 'https://www.vedomosti.ru/business/articles/2023/08/25/991930-heineken-prodala-rossiiskii-biznes')
SRC2 = ('Интерфакс', 'https://www.interfax.ru/business/917760')


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    deal = by_id[CID]

    assert deal.get('buyer_name') is None, 'buyer_name уже не пуст: %r' % deal.get('buyer_name')
    assert deal.get('buyer') is None, 'buyer уже занят профилем: %r' % deal.get('buyer')
    assert deal.get('sum') == 'Не раскрыта', 'sum уже другой: %r' % deal.get('sum')
    assert deal['eco'].get('sum') == 'Не раскрыта', 'eco.sum уже другой: %r' % deal['eco'].get('sum')
    assert deal['law'].get('terms') == '—', 'law.terms уже не пуст: %r' % deal['law'].get('terms')
    assert deal.get('status') == 'Обсуждается', 'status уже другой: %r' % deal.get('status')

    print('ПРАВИМ %s:' % CID)
    print('  buyer_name: None -> %r' % BUYER_NAME)
    print('  sum/eco.sum: «Не раскрыта» -> %r' % SUM_NEW)
    print('  law.terms: «—» -> (условия сделки)')
    print('  status: «Обсуждается» -> «Закрыта»')

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    deal['buyer_name'] = BUYER_NAME
    deal['sum'] = SUM_NEW
    deal['eco']['sum'] = SUM_NEW
    deal['law']['terms'] = TERMS_NEW
    deal['status'] = 'Закрыта'
    existing_urls = {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}
    for label, url in (SRC, SRC2):
        if url not in existing_urls:
            deal.setdefault('src', []).append([label, url])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
