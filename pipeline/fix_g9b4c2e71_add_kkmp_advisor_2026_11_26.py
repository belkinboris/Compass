# -*- coding: utf-8 -*-
"""ККМП — юридический консультант покупателя в карточке `g9b4c2e71`
(«Т-Технологии» собираются купить до 100% «Циана»).

ЧТО СЛОМАНО. `law.adv` карточки пуст: до 26 ноября 2026 консультантов не
называл ни один источник. 26 ноября фирма сама сообщила о мандате; партнер
(Артем) переслал это сообщение в тему «Клод» (message_id=4129).

ОТКУДА ФАКТ. Сайт фирмы, новость от 26.11.2026 (адрес — в SRC): «Команда ККМП
выступает юридическим консультантом МКПАО «Т-Технологии» … в связи с
добровольным предложением о приобретении до 100% акций МКПАО «Циан»».
Клиент назван дословно, роль не выводится догадкой. Факты сообщения (оферта
направлена «Циану» 24 ноября 2026, до этого — в Банк России, закрытие в
I квартале 2027) совпадают с уже записанными в карточке — источник о той же
сделке.

ЧЕГО НЕ ДЕЛАЕМ. Сумму не трогаем: «более 77 млрд рублей» у ККМП — это та же
цена 100% по 993,05 ₽ за акцию, что уже стоит верхней границей
(«38,6–77,1 млрд ₽ (по оценке)»); сколько акций предъявят, неизвестно.
Не через review.py: `law.adv` — элемент списка (docs/card_editing_scripts.md),
цитата пишется в `fact_log` (`fact_edit_guard.log`).

Запуск:
    python3 pipeline/fix_g9b4c2e71_add_kkmp_advisor_2026_11_26.py            # сухой прогон
    python3 pipeline/fix_g9b4c2e71_add_kkmp_advisor_2026_11_26.py --write    # запись
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
PATH = os.path.join(HERE, '..', 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g9b4c2e71'
URL = ('https://kkmp.legal/news/novosti/kkmp-konsultiruet-t-tekhnologii-v-svyazi-s-'
       'dobrovolnym-predlozheniem-o-pokupke-tsian/')
SRC = ['ККМП', URL]
QUOTE = ('Команда ККМП выступает юридическим консультантом МКПАО «Т-Технологии» (MOEX: Т), '
         'технологической компании, развивающей финансовую и транзакционную экосистему, в связи '
         'с добровольным предложением о приобретении до 100% акций МКПАО «Циан»')
ROW = ['Юридический консультант покупателя («Т-Технологии»)', 'ККМП',
       'Консультирует «Т-Технологии» в связи с добровольным предложением о покупке до 100% '
       'акций «Циана». Транзакционная часть: управляющий партнер Максим Кулешов, советник '
       'Тамара Кулык, помощники юристов Алина Даринская, Владислав Сливаев и Георгий Винокуров; '
       'регуляторная часть: партнер Анна Максименко, старший юрист Илья Кожевников, юристы '
       'Ирина Бойко и Егор Азизов (по данным сайта фирмы). Источник: ' + URL]


def main(write):
    # Файл читается прямо перед записью: чужой пуш не затираем (docs/card_editing.md).
    data = json.load(open(PATH, encoding='utf-8'))
    old = copy.deepcopy(data)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)
    adv = deal.setdefault('law', {}).setdefault('adv', [])
    if ROW in adv:
        print('%s: уже применено' % DEAL_ID)
        return 0
    assert adv == [], 'law.adv изменился, перепроверьте: %r' % adv
    assert 'Т-Технологии' in deal['title'] and 'Циан' in deal['title'], deal['title']
    src_new = not any(len(s) > 1 and s[1] == URL for s in deal['src'])
    print('%s — %s' % (DEAL_ID, deal['title']))
    print('law.adv [] -> %r' % ROW)
    print('src: %s' % ('добавляем ' + repr(SRC) if src_new else 'уже есть'))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    import fact_edit_guard
    import mass_edit_guard
    adv.append(ROW)
    if src_new:
        deal['src'].append(SRC)
    fact_edit_guard.log(deal, 'law.adv', deal['law']['adv'], QUOTE, URL,
                        'fix_g9b4c2e71_add_kkmp_advisor_2026_11_26')
    mass_edit_guard.check(old, data)
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')  # файл в git кончается переводом строки
    print('ЗАПИСАНО:', PATH)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
