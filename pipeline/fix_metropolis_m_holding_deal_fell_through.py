# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`g56342584` («М Холдинг Лтд (Capital Partners) приобретает торговый
центр Метрополис у Morgan Stanley и Hines», «Обсуждается») — сделка с
этим покупателем НЕ состоялась, ТЦ реально купила другая структура.
Единственным источником карточки была ссылка на телеграм-репост, без
единой полноценной статьи.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты):
- cre.ru/news/89539 (26.12.2022, 13:26) — «ФАС одобрила покупку ТРЦ
  «Метрополис» входящей в Capital Partners казахстанской компанией
  «М Холдинг Лтд.»» — это ПЕРВЫЙ полноценный источник карточки, добавлен
  в `src` (ранее там была только ссылка на телеграм-пост).
- adpass.ru/amerikantsy-sdali-metropolis-novymi-vladeltsami-molla-stal-
  armyanskij-investfond/ (06.04.2023, 11:54): «Сделка по неизвестным
  причинам не состоялась»; «Ранее покупка была одобрена правительственной
  комиссией по контролю за осуществлением иностранных инвестиций» — то
  есть одобрение получили ОБА органа (ФАС и правкомиссия), но сделка всё
  равно сорвалась.
- adindex.ru/news/marketing/2023/04/6/311771.phtml (06.04.2023, 13:34):
  «Новым владельцем торгово-развлекательного центра «Метрополис»...
  стал армянский инвестфонд Balchug Capital»; «Сумму сделки представитель
  Balchug Capital раскрывать отказался, сообщив лишь, что цена была
  «привлекательной»» — эксперты оценили ТЦ в 60–65 млрд ₽.

НЕ ВНЕСЕНО: факт про переход управления ТЦ к «ТПС недвижимость» (июль
2024 года, malls.ru) — найден только сабагентом через WebSearch, не
перепроверен мной лично прямым WebFetch, и это уже отдельное, третье
по счёту событие после самой смены собственника.

`buyer`/`title`/`status` карточки НЕ тронуты — реальный покупатель не
М Холдинг/Capital Partners, а Balchug Capital, и решение, как
переформулировать карточку (переписать под реального покупателя,
завести отдельную карточку, или оставить с пояснением), — за человеком.
Вопрос вынесен в «Известные проблемы» CLAUDE.md.

Запуск: python3 pipeline/fix_metropolis_m_holding_deal_fell_through.py
        python3 pipeline/fix_metropolis_m_holding_deal_fell_through.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g56342584'

OLD_ECO_CONTEXT = '—'
NEW_ECO_CONTEXT = (
    'Сделка с этим покупателем не состоялась: несмотря на одобрение ФАС '
    '(декабрь 2022) и правительственной комиссии по контролю за '
    'иностранными инвестициями, «по неизвестным причинам» она не была '
    'закрыта. Реальным владельцем ТЦ «Метрополис» с апреля 2023 года стал '
    'армянский инвестфонд Balchug Capital, купивший его у Morgan Stanley и '
    'Hines напрямую; сумма сделки не раскрыта, эксперты оценивали ТЦ в '
    '60–65 млрд ₽.'
)

OLD_SRC = [
    ['@dealsma (Telegram)', 'https://t.me/dealsma/3473'],
]
NEW_SRC = [
    ['CRE.ru', 'https://www.cre.ru/news/89539'],
] + OLD_SRC


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_ECO_CONTEXT
    assert deal['src'] == OLD_SRC

    print('=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)
    print('\n=== src: станет ===')
    print(NEW_SRC)

    if write:
        deal['eco']['context'] = NEW_ECO_CONTEXT
        deal['src'] = NEW_SRC
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
