# -*- coding: utf-8 -*-
"""Недельная очередь 18.09.2026: карточка `g1536c7fc` (Райффайзенбанк
вошёл в капитал разработчика ПО «Точный код») — дельта-поиск нашёл два
новых факта в уже известном источнике (finance.mail.ru) и в новом —
вики-карточке компании на TAdviser (отдельная от уже известной статьи
tadviser.ru/a/966210):

  1. Уставный капитал нового юрлица — 1,5 млн ₽ (только формальный
     размер капитала при регистрации, не сумма инвестиции Райффайзенбанка
     — она нигде не раскрыта, проверено отдельно).
  2. Уточнение о совладельцах — бывшие сотрудники банка среди
     учредителей БОЛЬШЕ НЕ РАБОТАЮТ в Райффайзенбанке (важно для
     понимания структуры: это не действующие сотрудники со сторонним
     бизнесом).
  3. Расширенная формулировка мотива банка (в дополнение к уже
     известному «требования законодательства о КИИ»): отраслевой опыт
     партнёра, надёжность, информационная безопасность, отказоустойчивость.

Источники:
  https://finance.mail.ru/article/rajffajzenbank-priobrel-dolyu-v-razrabotchike-softa-dlya-finsektora-69227387/ (уже в src)
  https://www.tadviser.ru/index.php/Компания:Точный_код (новый)

Запуск: python3 pipeline/fix_tochny_kod_capital_and_founders.py [--write]
"""
import argparse
import json
import re
from pathlib import Path

DATA = Path('/home/user/static/data/deals_promoted.json')
DEAL_ID = 'g1536c7fc'

OLD_CONTEXT = (
    'Компания зарегистрирована 9 сентября 2026 года. Остальные 51% '
    'поделили между собой пять основателей: Наталья Меньшикова — 18%, '
    'Эльвира Емец, Андрей Кабанов, Андрей Почеснев и Шухрат Собиров — '
    'по 8,25% каждому.'
)
OLD_RATIONALE = (
    'Участие в компании позволит Райффайзенбанку выполнить требования '
    'законодательства об использовании отечественного программного '
    'обеспечения на значимых объектах критической информационной '
    'инфраструктуры.'
)

ADD_CAPITAL = 'уставным капиталом 1,5 млн рублей'
QUOTE_CAPITAL = (
    'В банке уточнили, что компания «Точный код» создана 9 сентября '
    '2026 года с уставным капиталом 1,5 млн рублей.'
)

ADD_FOUNDERS = (
    'Некоторые из них ранее работали в Райффайзенбанке, но более не '
    'участвуют в его деятельности'
)
QUOTE_FOUNDERS = (
    'Среди соучредителей — независимые российские инвесторы с '
    'экспертизой в финансовой отрасли. Некоторые из них ранее работали '
    'в Райффайзенбанке, но более не участвуют в его деятельности.'
)

ADD_RATIONALE = (
    'Банку важен отраслевой опыт партнера, надежность, информационная '
    'безопасность и отказоустойчивость систем'
)
QUOTE_RATIONALE = (
    'В банке также пояснили, что сотрудничество с «Точным кодом» '
    'позволит выполнить требование законодательства об использовании '
    'российского ПО на значимых объектах критической информационной '
    'инфраструктуры (КИИ). Банку важен отраслевой опыт партнера, '
    'надежность, информационная безопасность и отказоустойчивость '
    'систем.'
)

TADVISER_URL = 'https://www.tadviser.ru/index.php/Компания:Точный_код'


def flat(s):
    return re.sub(r'[^0-9a-zа-яё]+', '', str(s or '').lower().replace('ё', 'е'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()

    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, 'eco.context уже другой: %r' % deal['eco']['context']
    assert deal['eco']['rationale'] == OLD_RATIONALE, 'eco.rationale уже другой: %r' % deal['eco']['rationale']

    for add, quote in ((ADD_CAPITAL, QUOTE_CAPITAL), (ADD_FOUNDERS, QUOTE_FOUNDERS),
                        (ADD_RATIONALE, QUOTE_RATIONALE)):
        assert flat(add) in flat(quote), 'не лежит дословно в цитате: %r' % add

    new_context = OLD_CONTEXT + (' Компания создана с %s. %s.' % (ADD_CAPITAL, ADD_FOUNDERS))
    new_rationale = OLD_RATIONALE + ' ' + ADD_RATIONALE + '.'

    print('НОВОЕ eco.context:')
    print(new_context)
    print()
    print('НОВОЕ eco.rationale:')
    print(new_rationale)

    if args.write:
        deal['eco']['context'] = new_context
        deal['eco']['rationale'] = new_rationale
        urls = {s[1] for s in (deal.get('src') or []) if isinstance(s, list) and len(s) > 1}
        if TADVISER_URL not in urls:
            deal.setdefault('src', []).append(['TAdviser', TADVISER_URL])
        json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main()
