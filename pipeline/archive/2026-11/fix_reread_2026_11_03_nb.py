# -*- coding: utf-8 -*-
"""Вычитка базы, партия nb (3 ноября 2026, ночь): то, что таблица FIXES не умеет.
Пара к pipeline/ingest/fixes/reread_2026_11_03_nb.py.

- g8e9d37ba (ТРЦ «Авиапарк»): сумма «100 млрд ₽» → «Не раскрыта». Это не цена сделки,
  а нижняя граница того, что владельцы надеются получить (Ведомости 24.07.2025: «рассчитывают
  выручить за него 100–120 млрд руб.», со слов одного консультанта); сделки нет, обязывающих
  документов нет и в декабре 2025 года (InvestFuture по ТАСС). docs/card_money.md, «Что не
  цена»: цена при выставлении на продажу — в eco.val (там она теперь и стоит), снятое — в
  retracted.sum. Стороны: покупателя еще нет, продавец — владельцы АО «ТВК «Авиапарк»», которых
  статьи не называют (на декабрь 2022 года — кипрская Darkforest Holding Company, нынешние
  бенефициары неизвестны) — причина в no_parties и accepted_notes.no_profile. legal_short
  предмета — по реестру (АО ТВК «Авиапарк», ИНН 7707298722); party_legal_names.py его не
  предложил.
- g3cd0f85e («Пансионат Камелия»): описание профиля предмета пересказывало сделку (находка
  приемки «post»: «Пансионат Камелия — отель…; в 2025 году ВТБ продал…») — теперь «кто это».

    python3 pipeline/archive/2026-11/fix_reread_2026_11_03_nb.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def set_val(obj, key, old, new):
    assert obj.get(key) == old, (key, obj.get(key), old)
    obj[key] = new


def retract(card, field, value):
    lst = card.setdefault('retracted', {}).setdefault(field, [])
    if value not in lst:
        lst.append(value)


def main(argv):
    raw = open(BASE, encoding='utf-8').read()                  # перечитываем прямо перед записью
    data = json.loads(raw)
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']

    # g8e9d37ba
    c = deals['g8e9d37ba']
    set_val(c, 'sum', '100 млрд ₽', 'Не раскрыта')
    set_val(c['eco'], 'sum', '100 млрд ₽', 'Не раскрыта')
    retract(c, 'sum', '100 млрд ₽')
    assert c.get('buyer') is None and not c.get('seller') and not c.get('seller_id')
    assert not c.get('no_parties')
    c['no_parties'] = ('Объект только выставлен на продажу: покупателя нет, обязывающих документов не '
                       'подписано (Ведомости, 24.07.2025; в декабре 2025 года — тоже); владельцы '
                       'АО «ТВК «Авиапарк»» в статьях не названы.')
    notes = c.setdefault('accepted_notes', {}).setdefault('no_profile', {})
    assert 'seller' not in notes and 'buyer' not in notes
    notes['seller'] = ('Владельцы АО «ТВК «Авиапарк»» не названы: на декабрь 2022 года — кипрская Darkforest '
                       'Holding Company, нынешние бенефициары неизвестны (Ведомости, The Moscow Times, '
                       'Lenta.ru, 24.07.2025); у АО история участников ЕГРЮЛ акционеров не показывает '
                       '(на сайте ФНС участником значится только ОАО «ТД ЦУМ»).')
    notes['buyer'] = ('Покупателя нет: объект выставлен на продажу, предложение разослано холдингам, '
                      'обязывающих документов ни с кем не подписано (Ведомости 24.07.2025, InvestFuture '
                      'по ТАСС 05.12.2025).')
    t = comps['g82bd57f9']
    assert t['name'] == 'Авиапарк' and t.get('legal_short') is None
    t['legal_short'] = 'АО «ТВК «Авиапарк»»'

    # g3cd0f85e — описание профиля предмета
    p = comps['ge64430f4']
    set_val(p, 'desc',
            'Отель Swissotel Resort Сочи Камелия; в 2025 году ВТБ продал 100% долей компании «Правильные '
            'решения» на торгах за 10 млрд ₽.',
            'Компания, которой принадлежит пятизвездочный отель Swissotel Resort Сочи Камелия; ей же '
            'принадлежат 99% ООО «УК Камелия», управляющего отелем.')

    if '--write' in argv:
        out = json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else '')
        with open(BASE, 'w', encoding='utf-8') as f:
            f.write(out)
        print('записано')
    else:
        print('сухой прогон; запись — с ключом --write')


if __name__ == '__main__':
    main(sys.argv[1:])
