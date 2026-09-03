# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка `g85b8634d`
(««Медскан» приобрел лаборатории NovaScreen», закрыта 27.04.2023) —
продавец назван только юрлицом, без бенефициаров; финансы самого
NovaScreen (не покупателя KDL) не были в `eco.target_fin`; `eco.val`
пустовал; `law.terms` не объяснял, почему условия неизвестны.

Проверено лично прямым WebFetch:
- Medvestnik.ru, https://medvestnik.ru/content/news/Medskan-kupil-stolichnye-laboratorii-Novascreen.html,
  27.04.2023: «"Огмент Инвестмент Лимитед" Виктора Харитонина и Егора
  Кулькова»; «Чистый убыток АО "Биоскрин", которое управляет
  лабораториями этой сети, в 2021 году составлял 68,7 млн руб., в
  2022-м сократился до 24,4 млн руб.»; «Рыночную стоимость NovaScreen
  аналитики оценили в 300–350 млн руб.»; «Представители сторон раскрыть
  структуру и условия сделки отказались».
- Vademec.ru, https://vademec.ru/news/2023/04/27/medskan-priobrel-laboratorii-novascreen/,
  27.04.2023: «По итогам 2021 года сеть заняла 36-е место в рейтинге
  Vademecum "ТОП50 крупнейших лабораторных сетей" с выручкой 360 млн
  рублей».

`eco.target_fin` уже нёс финансы KDL-тест/KDL Домодедово-тест —
это финансы ПОКУПАТЕЛЯ (сети KDL), а не самого предмета сделки
(NovaScreen/«Биоскрин»); новые данные ДОБАВЛЕНЫ отдельным предложением
с явным указанием, что это финансы именно NovaScreen — прежний текст
не трогаю и не переклассифицирую (это отдельная, более крупная задача).

НЕ ВНЕСЕНО: утверждение «бренд NovaScreen не сохраняется отдельно» —
при повторном прямом чтении medvestnik.ru такой формулировки в статье
не нашлось, только нейтральный факт вхождения в сеть KDL (уже отражён
в `extra`). `law.struct`/`law.appr` — ФАС и структура сделки (покупка
юрлица vs активов) ни в одном источнике не названы; замена этих полей
на предположение аналитиков «пока не проверено дословно» не делаю.

Запуск: python3 pipeline/fix_medskan_novascreen_seller_and_target_fin.py
        python3 pipeline/fix_medskan_novascreen_seller_and_target_fin.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g85b8634d'

OLD_SELLER = '«Огмент инвестментс лимитед»'
NEW_SELLER = '«Огмент инвестментс лимитед» (владельцы — Виктор Харитонин и Егор Кульков)'

OLD_LAW_TERMS = '—'
NEW_LAW_TERMS = 'Представители сторон раскрыть структуру и условия сделки отказались.'

OLD_ECO_TARGET_FIN = (
    'В 2021 г. совокупная выручка операционных структур сети – ООО '
    '«КДЛ-тест» и ООО «КДЛ Домодедово – тест» – составила 13,6 млрд '
    'руб., чистая прибыль – 2,2 млрд руб.'
)
NEW_ECO_TARGET_FIN = (
    OLD_ECO_TARGET_FIN + ' Показатели самого предмета сделки, АО '
    '«Биоскрин» (управляет лабораториями NovaScreen): чистый убыток в '
    '2021 году — 68,7 млн ₽, в 2022 году сократился до 24,4 млн ₽; по '
    'итогам 2021 года сеть заняла 36-е место в рейтинге Vademecum '
    '«ТОП50 крупнейших лабораторных сетей» с выручкой 360 млн ₽.'
)

OLD_ECO_VAL = '—'
NEW_ECO_VAL = (
    'Аналитики оценивали рыночную стоимость NovaScreen в 300–350 млн ₽ '
    '(Medvestnik.ru) — оценка близка к уже указанной сумме сделки '
    '(≈360 млн ₽, по оценке).'
)

NEW_SRC = [
    ['Vademec', 'https://vademec.ru/news/2023/04/27/medskan-priobrel-laboratorii-novascreen/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['seller'] == OLD_SELLER
    assert deal['law']['terms'] == OLD_LAW_TERMS
    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN
    assert deal['eco']['val'] == OLD_ECO_VAL

    existing_urls = {s[1] for s in deal['src']}
    add_src = [s for s in NEW_SRC if s[1] not in existing_urls]
    new_src = deal['src'] + add_src

    print('=== seller: станет ===')
    print(NEW_SELLER)
    print('\n=== law.terms: станет ===')
    print(NEW_LAW_TERMS)
    print('\n=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    print('\n=== eco.val: станет ===')
    print(NEW_ECO_VAL)
    if add_src:
        print('\n=== src: добавится ===')
        for s in add_src:
            print(s)

    if write:
        deal['seller'] = NEW_SELLER
        deal['law']['terms'] = NEW_LAW_TERMS
        deal['eco']['target_fin'] = NEW_ECO_TARGET_FIN
        deal['eco']['val'] = NEW_ECO_VAL
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
