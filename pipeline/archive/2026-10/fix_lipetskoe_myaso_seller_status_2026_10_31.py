# -*- coding: utf-8 -*-
"""Карточка `g39fc7468` («Липецкое мясо» / «Телтекс Системс»), очередь
`pending.json` — два поля, которые `review.py` не проводит сам:

1. **Продавец.** Статья Абирега (https://abireg.ru/newsitem/118951-…) не
   называет, у кого именно «Телтекс Системс» выкупила 70%: только что
   «стала владельцем» и что гендиректором остаётся Сергей Медведев.
   Правило владельца 14 октября 2026 (`docs/card_parties.md`, «Продавец не
   назван в статье — искать в реестре»): история участников ООО открыта
   без ключа на datanewton.ru. Запрос по ОГРН «Липецкого мяса»
   (1214800015022) показал ПОЛНУЮ историю:
   - 2026-07-13: Медведев Сергей Юрьевич (ИНН 773603114328) снизил долю с
     65% до 50%, Оганов Сергей Георгиевич — с 32,5% до 27,5%; одновременно
     появился новый участник — ООО «Телтекс Системс» (ОГРН 1267700094705),
     20%. (Сумма снижений 15%+5%=20% равна новой доле «Телтекс Системс» —
     это и был её вход в капитал.)
   - 2026-10-27: доля Медведева (50%) исчезла из реестра, доля «Телтекс
     Системс» выросла с 20% до 70%. Разница (50 п.п.) и есть тот самый
     переход, который Абирег описал как «получил 70%» — это СУММА прежней
     доли покупателя (20%) и доли, купленной у Медведева (50%), а не одна
     покупка 70% у единственного продавца.
   Медведев при этом остаётся гендиректором (это и указано в самой статье,
   и подтверждено Т-Банк Бизнес/rusprofile: «Медведев Сергей Юрьевич,
   генеральный директор с 05.03.26») — то есть это тот же человек, что и
   участник реестра с совпадающей фамилией/именем/отчеством. Второй
   совладелец, Оганов С. Г. (27,5%), в сделке 27 октября не участвует —
   его доля не менялась.
   Доказательство — не цитата из статьи (её там нет), а сама запись
   реестра; тот же класс, что `pipeline/fix_sellers_from_registry_2026_10_14.py`
   уже вносил прямым скриптом, минуя `review.py` (цитаты для сверки по
   `data/inbox/raw/*-articles.jsonl` там и не могло быть).

2. **Статус.** «Изменения в составе участников зарегистрированы 27
   октября» — смена владельца в ЕГРЮЛ, один из независимых признаков
   «Закрыта» без слова из `STATUS_WORDS` (`docs/card_status_dates.md`,
   «„Закрыта" — и без слова „закрыла", если независимые признаки
   однозначны»). Слово в самой статье — «стала владельцем» (женский род,
   «Телтекс Системс» как существительное женского рода), а в словаре
   `review.STATUS_WORDS['Закрыта']` стоит только «стал владельцем» —
   буквально это разные подстроки, `review.py` отказал бы
   («в цитате нет слова, подтверждающего статус»). Решение — тот же путь,
   что `fix_rnl_leasing_avtovaz_deal_fell_through.py`: статус меняется
   прямым скриптом с `assert` на старое значение, а не обходом словаря.
   Дата сделки меняется ОБЫЧНОЙ правкой `review.py` (день и месяц «27
   октября» названы в статье прописью) — это в отдельном файле
   `pipeline/ingest/fixes/structural_g39fc7468_2026_10_31.py`.

Карточка лежит в очереди (`static/data/pending.json`), не в
`static/data/deals_promoted.json`: приток и забор новостей пишут тот же
файл несколько раз в час, поэтому читаем его заново прямо перед записью
(`docs/intake_run.md`, «Запись, пока идёт публикация»).

Запуск: python3 pipeline/fix_lipetskoe_myaso_seller_status_2026_10_31.py
        python3 pipeline/fix_lipetskoe_myaso_seller_status_2026_10_31.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')

DEAL_ID = 'g39fc7468'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'

SELLER = 'Сергей Медведев'
SELLER_EVIDENCE_URL = ('https://datanewton.ru/api/v2/history?ogrn=1214800015022'
                        '&startDate=2000-01-01&attributes=OWNERS')
SRC_ROW = ['ЕГРЮЛ — история участников «Липецкого мяса» (datanewton)', SELLER_EVIDENCE_URL]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    card = next(c for c in data['cards'] if c['id'] == DEAL_ID)

    assert card['status'] == OLD_STATUS, card['status']
    assert not card.get('seller') and not card.get('seller_id'), card.get('seller')
    assert SRC_ROW not in (card.get('src') or [])

    print('=== seller: станет ===')
    print(SELLER)
    print('\n=== status: станет ===')
    print(NEW_STATUS)
    print('\n=== src: добавится ===')
    print(SRC_ROW)

    if write:
        card['seller'] = SELLER
        card.setdefault('party_evidence', {})['seller'] = [{
            'value': SELLER,
            'method': 'registry_owner_history',
            'url': SELLER_EVIDENCE_URL,
        }]
        card.setdefault('src', []).append(SRC_ROW)
        card['status'] = NEW_STATUS
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
