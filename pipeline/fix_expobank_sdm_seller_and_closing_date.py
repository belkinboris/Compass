# -*- coding: utf-8 -*-
"""Недельная очередь 18.09.2026: карточка `gbeb0dfe8` (Экспобанк
приобрёл контрольный пакет акций СДМ-банка) — дельта-поиск нашёл два
новых факта в источниках, УЖЕ стоящих в `src` карточки (Mergers.ru,
Коммерсантъ), и один в новом источнике (Абирег):

  1. Точная дата закрытия — 10 сентября 2026 года (Абирег; в карточке
     был только месяц).
  2. Mergers.ru (со ссылкой на Frank Media) НАЗЫВАЕТ продавцов пакета:
     Анатолий Ландсман (>15,5%) и ООО «Милавер рус» (53%) — этого не
     было использовано при первом обыске, хотя предложение лежит
     дословно в уже сохранённом источнике.
  3. ОДНАКО Абирег, тем же днём (14.09.2026), пишет прямо противоположное:
     «Информация о продавцах пакета в рамках завершенной сделки не
     раскрыта» — источники расходятся, поэтому оба утверждения внесены
     честно, а не выбрано одно.

Отдельно: Абирег (как и сам Mergers.ru/Frank Media) устойчиво пишет
«Анатолий Ландсман», в то время как уже стоящая в карточке цитата из
Коммерсанта — «Анатолий Ландеман» (со ссылкой на телеграм-канал
MarketOverview). Это расхождение написания оставлено КАК ЕСТЬ — уже
существующая цитата Коммерсанта не трогается, чтобы не исказить то,
что реально написал источник; факт зафиксирован для будущего чтения,
не решён односторонне.

Правится ОДНОРАЗОВЫМ СКРИПТОМ (не через `review.py`): поле `eco.context`
уже заполнено, а новые предложения — из тех же и из нового источника;
дописывание проверяется ПОПРЕДЛОЖЕНЧАТО.

Источники:
  https://mergers.ru/news/Jekspobank-priobrjol-kontrolnyj-paket-akcij-SDM-Banka-87507 (уже в src)
  https://www.kommersant.ru/doc/8953009 (уже в src)
  https://abireg.ru/newsitem/117331/ (новый)

Запуск: python3 pipeline/fix_expobank_sdm_seller_and_closing_date.py [--write]
"""
import argparse
import json
import re
from pathlib import Path

DATA = Path('/home/user/static/data/deals_promoted.json')
DEAL_ID = 'gbeb0dfe8'

OLD_CONTEXT = (
    'По данным «СПАРК-Интерфакса», до сделки Экспобанку принадлежало '
    '23,5% акций, по её итогам доля выросла до 86%. Экспобанк выкупил '
    '15% СДМ-банка у ЕБРР в ноябре 2018 года и увеличил пакет до 23,57% '
    'в январе 2021-го; крупнейшим акционером СДМ-банка после этого и до '
    'конца 2021 года, по данным телеграм-канала MarketOverview, '
    'оставался Анатолий Ландеман. Кто именно продал контрольный пакет '
    'сейчас, источники не называют.'
)

ADD_DATE = 'Сделка была закрыта 10 сентября.'
QUOTE_DATE = (
    'Экспобанк увеличил долю в капитале СДМ-банка с 23,5% до 86% и стал '
    'контролирующим акционером кредитной организации. Сделка была '
    'закрыта 10 сентября, ее согласовали Федеральная антимонопольная '
    'служба и Банк России.'
)

ADD_SELLER = (
    'Свою долю более чем в 15,5% продал один из его основателей '
    'основных владельцев банка Анатолий Ландсман, а также компания '
    '«Милавер рус», владевшая 53% акций, указывает Frank Media.'
)
QUOTE_SELLER = (
    'Из материалов СДМ-банка следует, что свою долю более чем в 15,5% '
    'продал один из его основателей основных владельцев банка Анатолий '
    'Ландсман, а также компания «Милавер рус», владевшая 53% акций, '
    'указывает Frank Media.'
)

ADD_ABIREG_DENIAL_CORE = (
    'Информация о продавцах пакета в рамках завершенной сделки не '
    'раскрыта'
)
ADD_ABIREG_DENIAL = 'Абирег в тот же день писал: «%s».' % ADD_ABIREG_DENIAL_CORE
QUOTE_ABIREG_DENIAL = ADD_ABIREG_DENIAL_CORE + '.'

ABIREG_URL = 'https://abireg.ru/newsitem/117331/'


def flat(s):
    return re.sub(r'[^0-9a-zа-яё]+', '', str(s or '').lower().replace('ё', 'е'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--write', action='store_true')
    args = ap.parse_args()

    data = json.load(open(DATA, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, 'eco.context уже другой: %r' % deal['eco']['context']

    for add, quote in ((ADD_DATE, QUOTE_DATE), (ADD_SELLER, QUOTE_SELLER),
                        (ADD_ABIREG_DENIAL_CORE, QUOTE_ABIREG_DENIAL)):
        assert flat(add) in flat(quote), 'не лежит дословно в цитате: %r' % add

    base = OLD_CONTEXT.replace(
        ' Кто именно продал контрольный пакет сейчас, источники не называют.',
        '')
    new_context = base + ' ' + ADD_DATE + ' ' + ADD_SELLER + ' ' + ADD_ABIREG_DENIAL

    print('НОВОЕ eco.context:')
    print(new_context)
    print()

    if args.write:
        deal['eco']['context'] = new_context
        urls = {s[1] for s in (deal.get('src') or []) if isinstance(s, list) and len(s) > 1}
        if ABIREG_URL not in urls:
            deal.setdefault('src', []).append(['Абирег', ABIREG_URL])
        json.dump(data, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main()
