# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g9d09dc7c
(ТМК продала Ярцевский металлургический завод ООО «Фрунзе»/МеталлСервис)
— сумма сделки стояла заглушкой «Не раскрыта», хотя сама ТМК раскрыла её
в отчётности МСФО. Проверено лично прямым WebFetch двух независимых
источников, оба ссылаются на ту же отчётность.

1) `sum`/`eco.sum` — Ведомости, дословно: «компания продала за 8,6 млрд
руб. предприятие, купленное в 2020 г. за 15 млрд руб.»; «Убыток от
продажи этого актива компания оценила в 5,5 млрд руб.» Mashnews
(со ссылкой на ту же отчётность за 1 полугодие 2024), точнее: «продала
за 8,65 млрд рублей (плюс денежное вознаграждение за продажу доли в
размере 2,3 млрд рублей)... ТМК оценивает убыток от продажи актива в
5,45 млрд рублей». Это раскрытая самой ТМК цифра, а не сторонняя
оценка — пометка «(по оценке)» не нужна.
Источники: https://www.vedomosti.ru/business/articles/2024/08/13/1055574-tmk-poluchila,
https://mashnews.ru/prodazha-yarczevskogo-metkombinata-prinesla-tmk-ubyitok-v-545-mlrd-rublej.html

2) `eco.context` (дополнено) — судьба завода под новым владельцем.
AEMP (Ассоциация электрометаллургических предприятий), дословно: «Завод
находится под управлением Металлсервиса с июня 2024 года»; оснащён
«экологически эффективными системами газоочистки и замкнутого
водоснабжения»; предприятие вошло в состав ассоциации 9 апреля 2025
года.
Источник: https://aemprus.ru/2025/04/09/predpriyatie-yartsevskij-metallurgicheskij-zavod-voshlo-v-sostav-aemp/

НЕ ВКЛЮЧЕНО: цитата про «сосредоточиться на профильном для компании
бизнесе» из пресс-релиза ТМК — она уже дословно стоит в `eco.rationale`,
повторный перенос в `extra` дублировал бы то же самое (родня уроку
CLAUDE.md «Одно поле — одна линза»); консультанты — не найдены; строящийся
литейно-прокатный комплекс на заводе — упоминания есть, но оба
первоисточника (metalinfo.ru, minpromtorg.gov.ru) отдавали 503 при
нескольких попытках, а вторичный пересказ противоречил сам себе —
дословную цитату добыть не удалось, факт не включён; связь «денежного
вознаграждения за продажу доли» (2,3 млрд ₽) с этой же сделкой не
пояснена ни одним источником — не включена как отдельная цифра, чтобы
не гадать о её значении.

Запуск: python3 pipeline/fix_tmk_yartsevsky_sum_and_progress.py
        python3 pipeline/fix_tmk_yartsevsky_sum_and_progress.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g9d09dc7c'

OLD_SUM = 'Не раскрыта'
NEW_SUM = '8,65 млрд ₽'

OLD_CONTEXT = (
    'ТМК приобрела Ярцевский элекрометаллургический завод в 2020 году за '
    '15 млрд рублей. Производственная мощность предприятия составляла '
    'тогда более 300 тыс. тонн сортового проката в год. На момент продажи '
    'мощности завода были увеличены до 350 тыс. тонн в год. До 2019 года '
    'владельцем ярцевского завода был «Евраз НТМК» (входит в группу '
    'Evraz), в 2019 году ЯМЗ интересовался также Загорский трубный завод '
    'Дениса Сафина.'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' По отчётности за 1 полугодие 2024 года ТМК «продала за 8,65 млрд '
    'рублей (плюс денежное вознаграждение за продажу доли в размере 2,3 '
    'млрд рублей)... ТМК оценивает убыток от продажи актива в 5,45 млрд '
    'рублей» (Mashnews). «Завод находится под управлением Металлсервиса '
    'с июня 2024 года», оснащён «экологически эффективными системами '
    'газоочистки и замкнутого водоснабжения»; 9 апреля 2025 года '
    'предприятие вошло в состав Ассоциации электрометаллургических '
    'предприятий (AEMP).'
)

NEW_SRC = [
    ['Ведомости', 'https://www.vedomosti.ru/business/articles/2024/08/13/1055574-tmk-poluchila'],
    ['Mashnews', 'https://mashnews.ru/prodazha-yarczevskogo-metkombinata-prinesla-tmk-ubyitok-v-545-mlrd-rublej.html'],
    ['AEMP', 'https://aemprus.ru/2025/04/09/predpriyatie-yartsevskij-metallurgicheskij-zavod-voshlo-v-sostav-aemp/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['sum'] == OLD_SUM
    assert deal['eco']['sum'] == OLD_SUM
    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print(f'=== sum/eco.sum: {OLD_SUM!r} -> {NEW_SUM!r} ===')
    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['sum'] = NEW_SUM
        deal['eco']['sum'] = NEW_SUM
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
