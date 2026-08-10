# -*- coding: utf-8 -*-
"""20 карточек 2022 года несут в `eco.rationale` протёкшую служебную пометку
роли стороны в двойных скобках на конце текста: «...Сделка закрыта 1 марта
2022 года. (АО «Кредит Европа банк» (покупатель))», «...Сумма: 240 млн евро.
(Сбербанк (продавец))». Это тот же класс дефекта, что уже точечно чинили
через `review.py` FIXES (g718e3d0e, gafe121ae, g2d90c4d5, g20d4cc38 — везде
внутренняя разметка стороны для сортировки просочилась в текст, который
показывается читателю), но здесь — массовый след компактного импорта 2022
года: паттерн (одно и то же имя стороны, уже названной в тексте предложением
раньше, плюс слово роли в скобках внутри скобок) не совпадает случайно ни с
чем содержательным — «(по оценке)», «(оценка эксперта)» и подобные пометки
одноуровневые, без вложенной пары скобок.

Почему не через review.py: снимается не новый факт, а уже присутствующий в
базе служебный шум; цитаты источника для остающегося текста в большинстве
случаев не существует вовсе — часть источников этих карточек не открывается
(forbes.ru, rbc.ru отдают пустой текст или 401/403). Резать шум безопасно
без цитаты: остающийся текст не меняется ни на символ, снимается только
контрольный хвост.

Область: только карточки с датой, начинающейся на «2022» — это моя часть
очереди дочитывания; карточки 2023–2025 годов принадлежат параллельным
потокам и не трогаются, даже если несут тот же дефект.

Запуск: python3 pipeline/strip_leaked_role_tags_2022.py           # проверка
        python3 pipeline/strip_leaked_role_tags_2022.py --write   # запись
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(os.path.dirname(ROOT), 'static', 'data', 'deals_promoted.json')

TAG_RX = re.compile(
    r'\s*\([^()]{2,60}\((?:продавец|покупатель|цель|таргет)\)\)\s*$', re.I)

EXPECTED_COUNT = 20


def main(write=False):
    data = json.load(open(BASE, encoding='utf-8'))
    todo = {}
    for d in data['deals']:
        if not str(d.get('date', '')).startswith('2022'):
            continue
        val = d.get('eco', {}).get('rationale')
        if isinstance(val, str) and TAG_RX.search(val):
            todo[d['id']] = TAG_RX.sub('', val).rstrip()

    assert len(todo) == EXPECTED_COUNT, (
        'ожидалось %d карточек с протёкшей пометкой роли, найдено %d — '
        'состояние базы изменилось, проверьте список заново'
        % (EXPECTED_COUNT, len(todo)))

    cards = {d['id']: d for d in data['deals']}
    for cid, new in todo.items():
        print('ПРАВИМ  %s eco.rationale: снята протёкшая пометка роли' % cid)
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    for cid, new in todo.items():
        cards[cid]['eco']['rationale'] = new
    json.dump(data, open(BASE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Записано: %d карточек.' % len(todo))


if __name__ == '__main__':
    main(write='--write' in sys.argv)
