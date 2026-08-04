# -*- coding: utf-8 -*-
"""Согласования в тексте новых карточек — перенести в «Согласования».

ЗАЧЕМ. 142 карточки, пришедшие из компактных записей при слиянии базы, несут
исходную заметку в «Дополнительной информации». У шести из них там описано
согласование («сделка ожидала одобрения ФАС», «Совет директоров ОАО «РЖД»
предварительно одобрил», «разрешение Президента РФ»), а поле «Согласования»
пусто — и линза «Юрист» сказала бы, что согласований не называли, на той же
карточке, где они названы. Ровно этот дефект держит
`test_approval_is_not_left_in_prose`.

ГРАНИЦА. Ничего не сочиняется и не пересказывается: в `law.appr` кладётся
ДОСЛОВНОЕ предложение из той же карточки. Проверка — `assert`, что результат
является подстрокой исходного текста; попытка «слегка переформулировать»
уронит скрипт. Это главная проверка здесь, а не украшение.

ПОЧЕМУ НЕ `extract_approvals.py`. Тот скрипт разовый и несёт таблицу из 82
прочитанных вручную карточек прошлой партии; повторный запуск падает на
проверке исходного состояния. Здесь другая партия и другой список.

Запуск:
    python3 pipeline/extract_approvals_after_merge.py            # сухой прогон
    python3 pipeline/extract_approvals_after_merge.py --write    # записать
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

# Точка не значит конец предложения («18,8 млрд руб.», «SRV Group B.V.»):
# режем только по «точка + пробел + заглавная» — ошибается в безопасную
# сторону, склеивая два предложения вместо того чтобы разрезать одно.
SENTENCE = re.compile(r'(?<=[.!?])\s+(?=(?-i:[А-ЯЁA-Z]))')

BODY = re.compile(
    r'ФАС\b|антимонопольн|правительственн[а-яё]*\s+(?:под)?комисси|правкомисси'
    r'|Банк[а-яё]*\s+России|ЦБ\s+РФ|Центробанк|президент[а-яё]*|правительств[а-яё]*|премьер'
    r'|совет[а-яё]*\s+директоров|собрани[а-яё]*\s+акционеров|суд\b|указ|распоряжени', re.I)
ACT = re.compile(r'одобр|разреш|согласова|утверд|аннулирова|предписани', re.I)

TARGETS = ('cf9e8af73', 'c6b5fb9f3', 'cfdc0e962', 'cf9ca3b8f', 'cd175a614', 'c2455b014')


def normalize(text):
    return re.sub(r'\s+', ' ', str(text or '')).strip()


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    picked = []

    for did in TARGETS:
        deal = by_id.get(did)
        assert deal is not None, 'карточки %s нет в базе' % did
        current = str((deal.get('law') or {}).get('appr') or '').strip()
        assert current in ('', '—'), \
            '%s: поле «Согласования» уже заполнено (%r) — перепроверьте' % (did, current[:40])
        source = str(deal.get('extra') or '')
        found = None
        for sent in SENTENCE.split(source):
            if BODY.search(sent) and ACT.search(sent):
                found = sent.strip()
                break
        assert found, '%s: предложение о согласовании не найдено' % did
        # Главная проверка: результат обязан дословно лежать в исходном тексте.
        assert normalize(found) in normalize(source), \
            '%s: результат не является дословным куском карточки' % did
        picked.append((did, found))

    for did, sent in picked:
        print('  %s' % did)
        print('     %s' % sent[:150])

    # Проверка правила на себе: заведомо чужой текст не должен «находиться».
    assert normalize('ФАС одобрила эту сделку в июне') not in normalize(
        by_id[TARGETS[0]].get('extra') or ''), 'проверка подстроки не работает'

    print('\nпереносов: %d' % len(picked))
    if write:
        for did, sent in picked:
            by_id[did].setdefault('law', {})['appr'] = sent
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО в %s' % os.path.relpath(DATA, ROOT))
    else:
        print('Сухой прогон. Запись — с ключом --write.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
