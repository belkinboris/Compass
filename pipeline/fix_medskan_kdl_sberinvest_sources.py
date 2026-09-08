# -*- coding: utf-8 -*-
"""Месячная очередь, 8 сентября 2026 — карточка `c54966856» (Медскан
выкупил долю Сбербанка Инвестиций в KDL, октябрь 2025) держалась только
на двух телеграм-ссылках — слабое подтверждение для сделки почти на
5 млрд ₽. Найдены и лично проверены прямым WebFetch два независимых
СМИ, дословно подтверждающих уже стоящие в карточке факты и добавляющих
новый:

- Vademecum (vademec.ru/news/2025/10/28/…, 28.10.2025): «Сделка
  направлена на завершение приобретения сети KDL и снижение долговой
  нагрузки ГК «Медскан» перед планируемым выходом на IPO»; «ООО
  «Сбербанк Инвестиции» передало 39% долей головной компании АО
  «Медскан»»; сумма — «4,767 млрд рублей»; соглашение подписано 17
  октября 2025 года, сделка закрыта 24 октября 2025 года.
- AKM (akm.ru/news/sberbank_investitsii_vyshli_iz_sostava_uchrediteley_
  medskan_lab/): «ООО «Сбербанк Инвестиции» передало принадлежащие ему
  39% ООО «Медскан Лаб»»; «Тогда размер инвестиций оценивался в 2.49
  млрд руб.» (2023 год) — НОВЫЙ факт, которого в карточке не было:
  «Доля Медскан Лаб в ООО «Диагностика» стоимостью 7.6 млрд руб.
  заложена в ООО «Сбербанк Инвестиции» и в ПАО «Сбербанк»».

Поле `eco.context` не проходило вычитку — правка обычная.

Запуск:
    python3 pipeline/fix_medskan_kdl_sberinvest_sources.py            # сухой прогон
    python3 pipeline/fix_medskan_kdl_sberinvest_sources.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'
CARD_ID = 'c54966856'

OLD_CONTEXT = (
    'После закрытия сделки Медскан полностью контролирует сеть '
    'лабораторий KDL, пут-опцион аннулирован — это улучшает финансовую '
    'структуру перед IPO.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' Доля «Медскан Лаб» в ООО «Диагностика» (головном юрлице сети KDL) '
    'стоимостью 7,6 млрд ₽ остаётся в залоге у ООО «Сбербанк Инвестиции» '
    'и ПАО «Сбербанк». Соглашение о сделке подписано 17 октября 2025 '
    'года, закрыта она 24 октября.'
)

NEW_SRCS = [
    ['Vademecum', 'https://vademec.ru/news/2025/10/28/'
     'v-medskane-nazvali-prichinu-sdelki-po-vykhodu-struktury-sberbanka-'
     'iz-kholdingovoy-kompanii-gruppy-kd/'],
    ['AKM.RU', 'https://www.akm.ru/news/'
     'sberbank_investitsii_vyshli_iz_sostava_uchrediteley_medskan_lab/'],
]


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}
    card = by_id[CARD_ID]

    assert card['eco']['context'] == OLD_CONTEXT, \
        'eco.context уже другой: %r' % (card['eco']['context'],)

    print('eco.context: добавляется факт о залоге доли в «Диагностике» '
          'и точных датах подписания/закрытия')
    existing_urls = {s[1] for s in card['src']}
    for s in NEW_SRCS:
        if s[1] not in existing_urls:
            print('src: добавляется', s)

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    card['eco']['context'] = NEW_CONTEXT
    for s in NEW_SRCS:
        if s[1] not in existing_urls:
            card['src'].append(s)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
