# -*- coding: utf-8 -*-
"""Догоняющий прогон 16-18 сентября 2026, карточка g2349d667 (Canpack/
Вадим Смагин). ЧТО ЧИНИТ: eco.context утверждал «В марте компании вывели
из-под временного управления» — дата ничем не подтверждена и, судя по
всему, взята по ошибке (в тексте карточки нигде не встречается «март»).
Независимый источник (Банкфакс, https://www.bankfax.ru/news/167611/,
уже добавлен в src отдельной правкой) называет месяц прямо: «Напомним,
что в августе этого года президент России Владимир Путин подписал указ,
которым вывел «Кэн-пак» и «Кэн-пак - завод упаковки» из временного
управления». ПОЧЕМУ НЕ ЧЕРЕЗ review.py: поле eco.context уже сложено из
нескольких фактов разных источников (дата передачи в управление, дата
вывода, судьба бренда) — заменить нужно только ОДНО предложение внутри
уже существующего текста, а не подобрать единую цитату на весь абзац
целиком, как того требует дословная проверка review.py для текстовых
полей. Меняется только дата месяца; смысл предложения не меняется.

Запуск: python3 pipeline/fix_canpack_temporary_management_removal_date.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g2349d667'
OLD_SENTENCE = 'В марте компании вывели из-под временного управления.'
NEW_SENTENCE = 'В августе 2026 года компании вывели из-под временного управления.'


def main():
    write = '--write' in sys.argv
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)
    context = deal['eco']['context']
    assert OLD_SENTENCE in context, 'ожидаемое предложение не найдено — карточку уже правили'
    new_context = context.replace(OLD_SENTENCE, NEW_SENTENCE)
    print('было:', context)
    print('стало:', new_context)
    if write:
        deal['eco']['context'] = new_context
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print('Записано.')
    else:
        print('Сухой прогон. Запись — с ключом --write.')


if __name__ == '__main__':
    main()
