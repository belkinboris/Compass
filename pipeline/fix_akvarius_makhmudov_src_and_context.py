# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g26608f96 (Искандер Махмудов покупает
контроль в ГК «Аквариус»): дельта-поиск нашёл, что два из трёх
источников карточки (Sostav.ru и Ведомости) НЕ ПОДТВЕРЖДАЮТ факты этой
карточки вовсе — оба целиком про сделку S8 Capital/«МТ-Интеграция»
(уже отдельная карточка `g139db8c2`, с записанным в CLAUDE.md
опровержением МТ-Интеграции). Судя по третьей статье того же CNews
(22.08.2025), это последовательные версии ОДНОГО сюжета продажи доли
«Аквариуса» с РАЗНЫМИ названными претендентами: сперва (июнь 2025)
источники CNews называли структуры Махмудова (УГМК/ТМХ), затем
(август 2025) — S8 Capital/«МТ-Интеграция». Ни один источник не
подтверждает, что Махмудов реально закрыл сделку или что он связан с
S8 Capital. Родня уже записанного класса «Стороной сделки может быть
записан профиль совсем другой сущности», только здесь испорчена не
сама сторона, а ДВА ИСТОЧНИКА, прикреплённых, видимо, автоматически
по совпадению названия компании «Аквариус», а не потому, что там
реально идёт речь об этой карточке.

Не через `review.py`: снятие источников (`src`) в обратную сторону —
операция, которую `review.py` не поддерживает (там `src` только
аддитивен), плюс замена по существу (`extra`) на основе контекста
всей истории.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
https://www.cnews.ru/news/top/2025-08-22_na_rynke_poyavilas_novaya

Запуск: python3 pipeline/fix_akvarius_makhmudov_src_and_context.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g26608f96'

OLD_SRC = [
    ['CNews', 'https://www.cnews.ru/news/top/2025-06-03_na_rynke_gotovitsya_krupnaya'],
    ['Sostav.ru', 'https://www.sostav.ru/publication/s8-capital-priobrel-kontrolnyj-paket-kompanii-akvarius-77557.html'],
    ['Ведомости', 'https://www.vedomosti.ru/technology/news/2025/08/22/1133615-maksima-ne-voidet'],
]
NEW_SRC = [
    ['CNews', 'https://www.cnews.ru/news/top/2025-06-03_na_rynke_gotovitsya_krupnaya'],
    ['CNews', 'https://www.cnews.ru/news/top/2025-08-22_na_rynke_poyavilas_novaya'],
]

OLD_CONTEXT = (
    'В ноябре 2024 г. «СберИнвест», входящий в блок '
    'корпоративно-инвестиционного бизнеса Сбербанка, получил 12% долю '
    'в капитале «Аквариуса». Позже, как сообщили собеседники CNews, '
    'близкие к Сбербанку, «СберИнвест» приобрела еще 12%. Таким '
    'образом, теперь у «СберИнвеста» есть 24% доля «Аквариуса». Помимо '
    '«СберИнвеста» крупными долями «Аквариуса» владеют Алексей Калинин '
    'и президент одноименной группы Владимир Степанов.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' О том, что доля «Аквариуса» может быть продана, CNews писал в '
    'июне 2025 г., но тогда назывались другие потенциальные инвесторы '
    '— промышленные компании Уральская горно-металлургическая компания '
    '(УГМК) и Трансмашхолдинг (ТМХ). В число владельцев как УГМК, так '
    'и ТМХ входит Искандер Махмудов. К августу 2025 года в прессе '
    'вместо Махмудова стал фигурировать другой покупатель — S8 Capital '
    'и ГК «МТ-Интеграция» (карточка отдельной сделки: `g139db8c2`) — '
    'связь между двумя версиями ни разу не подтверждена ни одним '
    'источником.'
)


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['src'] == OLD_SRC, f"src: {deal['src']!r}"
    assert deal['eco']['context'] == OLD_CONTEXT, f"eco.context: {deal['eco']['context']!r}"

    print(f'{CARD_ID} src: сняты два источника, не относящихся к '
          f'этой карточке (Sostav.ru, Ведомости — оба про S8 Capital), '
          f'добавлен второй материал CNews')
    print(f'{CARD_ID} eco.context: += смена названного претендента '
          f'(Махмудов -> S8 Capital/МТ-Интеграция), связь не '
          f'подтверждена')

    if write:
        deal['src'] = NEW_SRC
        deal['eco']['context'] = NEW_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('Сухой прогон. Запись — с --write.')


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
