# -*- coding: utf-8 -*-
"""Качество, 7 октября 2026 — месячная дельта карточки `g95370469`
(«Базис» купил 70% Proto).

ComNews (comnews.ru/content/247266, 08.09.2026) не входит в текущий `src`
карточки и даёт прямые цитаты обеих сторон, которых в `eco.rationale` и
`law.terms` нет. Поля уже заполнены другими источниками (Коммерсантъ,
Ведомости) — через `review.py` дописать цитату из НОВОГО источника в УЖЕ
занятое поле нельзя (таблица требует, чтобы `new` был чистой подстрокой
`quote` ОДНОГО источника), поэтому — отдельным скриптом, который
ДОПОЛНЯЕТ поле, а не заменяет (routines/quality.md, «Факт из другого
источника в цитату той же записи не дописать»).

Запуск:
    python3 pipeline/fix_g95370469_comnews_quotes_2026_10_07.py            # сухой прогон
    python3 pipeline/fix_g95370469_comnews_quotes_2026_10_07.py --write    # запись
"""
import json
import sys

DATA_PATH = 'static/data/deals_promoted.json'

OLD_RATIONALE = (
    'Сделка поможет «Базису» улучшить собственное предложение в области '
    'серверной виртуализации благодаря технологиям и экспертизе Proto. '
    'Покупка доли в компании позволила сократить цикл самостоятельной '
    'разработки технологий. По оценке «Базиса», создание собственного '
    'продукта обошлось бы компании в 3-4 раза дороже.'
)
ADD_RATIONALE = (
    ' Гендиректор «Базиса» Давид Мартиросов отметил, что приобретение '
    'Proto также позволило компании «на полтора года сократить сроки '
    'внедрения решений наблюдаемости в экосистеме компании по сравнению '
    'с самостоятельной разработкой аналогичного ПО с нуля» (ComNews).'
)

OLD_TERMS = (
    'Разработчик войдет в группу «Базис» как дочерняя компания. Его '
    'команду сохранят и усилят, чтобы ускорить развитие платформы и '
    'других решений, а клиентская база, экспертиза и каналы продаж '
    'нового акционера помогут вывести продукт на более широкий рынок. '
    'Сделка не повлияет на исполнение действующих договоров: Proto '
    'сохраняет все обязательства перед текущими клиентами и продолжит '
    'выполнять их в полном объеме.'
)
ADD_TERMS = (
    ' Гендиректор и сооснователь Proto Денис Безкоровайный: «Партнерство '
    'с таким игроком позволяет нам быстрее реализовать наше видение '
    'развития Proto и масштабировать продукт вместе с одной из ведущих '
    'российских ИТ-компаний» (ComNews).'
)

NEW_SRC = ['ComNews', 'https://www.comnews.ru/content/247266']


def main(write):
    data = json.load(open(DATA_PATH, encoding='utf-8'))
    deals = data['deals'] if isinstance(data, dict) else data
    target = [d for d in deals if d.get('id') == 'g95370469']
    assert len(target) == 1, target
    card = target[0]
    assert card['eco']['rationale'] == OLD_RATIONALE, card['eco']['rationale']
    assert card['law']['terms'] == OLD_TERMS, card['law']['terms']
    assert NEW_SRC not in (card.get('src') or [])

    card['eco']['rationale'] = OLD_RATIONALE + ADD_RATIONALE
    card['law']['terms'] = OLD_TERMS + ADD_TERMS
    card.setdefault('src', []).append(NEW_SRC)

    # Поля дописаны мимо таблицы FIXES — записи, которые изначально ставили
    # эти поля (batch_2026_09_07_bazis_proto.py, `new` == OLD_RATIONALE /
    # OLD_TERMS), иначе разойдутся с базой и review.py откажет «поле уже
    # другое». Синхронизация — отпечаток старого `new` в
    # `proofread_absorbed` (тот же механизм, что у proofread.py), не правка
    # самой записи (new перестал бы быть подстрокой quote).
    from pipeline.ingest.review import fix_fingerprint
    absorbed = card.setdefault('proofread_absorbed', {})
    for field, old_value in (('eco.rationale', OLD_RATIONALE), ('law.terms', OLD_TERMS)):
        fp = fix_fingerprint(old_value)
        lst = absorbed.setdefault(field, [])
        if fp not in lst:
            lst.append(fp)

    if write:
        json.dump(data, open(DATA_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('g95370469: цитаты ComNews дописаны в eco.rationale и law.terms, src дополнен, '
              'proofread_absorbed синхронизирован. ЗАПИСАНО.')
    else:
        print('Сухой прогон: дописал бы цитаты ComNews. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
