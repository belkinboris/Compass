# -*- coding: utf-8 -*-
"""Месячная очередь, карточка g1d1ac507 (Сбер продал 45% доли в
«Еаптеке» структурам Алексея Репика, сентябрь 2025): дельта-поиск нашёл
дальнейшую судьбу актива — Репик владел им недолго. В июле 2025 года
(тот же месяц, что и сделка со Сбером) оставшиеся 10% основателя Антона
Буздалина тоже перешли структуре Репика, а 1 июля 2026 года группа RWB
(Wildberries & Russ) объявила о получении контроля над «Еаптекой» —
независимая оценка (RNC Pharma) даёт 7–12 млрд руб. без учёта долгов,
условия сделки не раскрыты.

Это НОВАЯ, отдельная сделка (Репик → RWB/Wildberries), а не факт внутри
текущей — своей карточки под неё в базе пока нет (заведение новой
карточки — задача притока/promote.py, не этого прогона). Здесь
фиксируется только история ПРЕДМЕТА текущей карточки: чем закончилось
владение Репика, купленное у Сбера. Не через review.py: eco.context уже
несёт содержание, а новый источник (vademec.ru) не образует с ним
непрерывный кусок текста.

Источник — читал напрямую (fetch_article_texts.py, закэширован):
https://www.vademec.ru/news/2026/07/01/rvb-poluchila-kontrol-nad-eaptekoy/
Независимая оценка суммы — https://www.cnews.ru/news/top/2026-07-01_wildberries_prevrashchaetsya_v_apteku

Запуск: python3 pipeline/fix_sber_eapteka_resale_to_rwb_context.py [--write]
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g1d1ac507'

OLD_CONTEXT = (
    'В 2020–2021 гг. «Сбер» и структуры «Р-фарм» приобрели по 45% в '
    '«Еаптеке» через ООО «Цифровые активы» и кипрскую Amsele Limited '
    'соответственно. В их совместном пресс-релизе говорилось, что сумма '
    'инвестиций со стороны банка в рамках сделки составила 5,7 млрд руб. '
    'Еще 10% тогда сохранил за собой основатель и гендиректор Антон '
    'Буздалин.'
)
CONTEXT_ADDITION = (
    'В июле 2025 года, тогда же, когда 90% компании консолидировала '
    'МКООО «Амсел» (структура Репика), оставшиеся 10% основателя Антона '
    'Буздалина тоже перешли самому Репику — он стал 100% владельцем. '
    'Владение оказалось недолгим: 1 июля 2026 года группа RWB '
    '(объединяющая Wildberries и Russ) объявила о получении контроля над '
    '«Еаптекой» для развития направления «RWB Здоровье»; условия сделки '
    'не раскрыты, независимая оценка (директор по развитию RNC Pharma '
    'Николай Беспалов) — 7–12 млрд руб. без учёта долгов. Своей карточки '
    'у этой, более поздней сделки в базе пока нет.'
)
NEW_CONTEXT = OLD_CONTEXT + ' ' + CONTEXT_ADDITION


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deal = next(d for d in data['deals'] if d['id'] == CARD_ID)

    assert deal['eco']['context'] == OLD_CONTEXT, \
        f"eco.context: неожиданное значение {deal['eco']['context']!r}"

    print(f"{CARD_ID} eco.context: += дальнейшая судьба актива "
          f"(перепродажа RWB/Wildberries, июль 2026)")
    deal['eco']['context'] = NEW_CONTEXT

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
