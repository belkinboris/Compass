# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка gd71753e0
(Яндекс купил рекламную платформу eLama). Уже стоявшая оценка суммы
(«10-15 млрд руб., полагают аналитики») была безымянной; нашлась партия
именных, более низких оценок того же порядка сделки. Проверено лично
прямым WebFetch.

`eco.val` — дополнено. ADPASS, дословно: Дмитрий Туркевич (основатель
MediaSniper) — «В моем представлении «Яндекс», скорее, оценивал бы
eLama по чистой прибыли с мультипликатором в районе 4-5, что дало бы
стоимость всей компании в 6-7,5 млрд рублей»; Сергей Либин (старший
аналитик Газпромбанка) — «Придерживаясь консервативной оценки, получим
10 млрд рублей»; Илья Хоффман (старший партнёр VDI Group) — «текущая
оценка компании, вероятно, находится в интервале 3-4,5 EBITDA или в
денежном выражении в диапазоне 6-8,5 млрд рублей»; сами эксперты ADPASS
подводят итог — «общая оценка компании в коридоре 6-10 млрд рублей».
Это заметно ниже уже стоявшей безымянной оценки (10-15 млрд ₽) — обе
оценки сохранены рядом, ни одна не вытесняет другую.
Источник: https://adpass.ru/yandeks-prerval-elamnuyu-pauzu-pochem-prodali-platformu-avtomatizatsii-zakupok-kontekstnoj-reklamy-elama/

НЕ ВКЛЮЧЕНО: кто именно продавал (Impulse VC или Довжиков) — не
прояснилось ни в одном источнике 2025-2026 годов, обе стороны
по-прежнему отказываются называть продавца; финансовый консультант
(отдельный от юридического) — не найден; судьба eLama после сделки —
бренд и команда сохранены («eLama стала частью Яндекса. Мы продолжим
работать под брендом eLama той же командой», сама компания), но это не
меняет содержания карточки существенно.

Запуск: python3 pipeline/fix_yandex_elama_valuation_range.py
        python3 pipeline/fix_yandex_elama_valuation_range.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gd71753e0'

OLD_VAL = (
    'Сумма сделки по покупке технологической рекламной платформы eLama '
    '«Яндексом» составит в 10−15 млрд руб., полагают аналитики.'
)
NEW_VAL = OLD_VAL + (
    ' Более низкие именные оценки (ADPASS): Дмитрий Туркевич (основатель '
    'MediaSniper) — «стоимость всей компании в 6-7,5 млрд рублей»; '
    'Сергей Либин (старший аналитик Газпромбанка) — «Придерживаясь '
    'консервативной оценки, получим 10 млрд рублей»; Илья Хоффман '
    '(старший партнёр VDI Group) — «в денежном выражении в диапазоне '
    '6-8,5 млрд рублей»; сами эксперты ADPASS — «общая оценка компании в '
    'коридоре 6-10 млрд рублей».'
)

NEW_SRC = [
    ['ADPASS', 'https://adpass.ru/yandeks-prerval-elamnuyu-pauzu-pochem-prodali-platformu-avtomatizatsii-zakupok-kontekstnoj-reklamy-elama/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['val'] == OLD_VAL
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.val: станет ===')
    print(NEW_VAL)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['val'] = NEW_VAL
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
