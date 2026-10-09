"""Второе чтение принятой карточки — другой сессией, с вопросом к каждому полю.

Зачем. 8 октября 2026 карточка «Яндекс»/VK прошла сборку и приёмку одной и
той же сессией и дошла до владельца с полями, списанными у CNews, обрывком
в «Цели сделки» и описанием компании в «Форме расчётов». Сборщик знает, что
имел в виду, и не видит, как это читается. Второе чтение делает читатель,
который карточку не собирал (саб-агент с чистым контекстом,
SECOND_READING_BRIEF.md): на каждое заполненное поле — вопрос, на который
поле обязано отвечать; на всё вместе — четыре общих вопроса. Любой ответ,
кроме «ok», возвращает карточку на правку.

    python3 pipeline/ingest/second_reading.py --queue [id …]   # вопросы читателю
    python3 pipeline/ingest/second_reading.py --apply ответ.json [--write]

Штамп `second_read` обязателен для карточек, принятых с SINCE и позже
(`send_drafts.needs_second_reading`); принятые раньше идут по-старому.
"""
import json
import os
import re
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'publish'))
sys.path.insert(0, os.path.join(HERE, '..', '..'))

import accept_card                     # noqa: E402
import format_post                     # noqa: E402

STAMP = 'second_read'
SINCE = '2026-10-09'                   # принятые с этого дня без второго чтения в консоль не идут

FIELD_QUESTIONS = {
    'title': 'Можно сказать вслух партнёру — кто, что сделал, с чем? Без обрывка формулировки издания и прямых кавычек? '
             'Люди названы по имени и фамилии, а не одной фамилией?',
    'asset': 'Это предмет сделки (что покупают, продают или объединяют) в именительном падеже, а не описание компании?',
    'eco.share': 'Это размер доли или сам предмет (какой пакет, у кого)?',
    'eco.sum': 'Это цена сделки — число, а не рассказ?',
    'eco.val': 'Это оценка компании или мультипликатор?',
    'eco.target_fin': 'Это числа о покупаемой компании (у СП — об обоих вносимых бизнесах), а не описание рода занятий?',
    'eco.fin': 'Это о том, чем и как платят (деньги, рассрочка, обмен акциями), а не о бизнесе и не отчётность?',
    'eco.rationale': 'Первое предложение — мотив сделки, самостоятельная фраза без «такой/это», понятная без источника?',
    'eco.context': 'История и окружение сделки, которых нет в других полях, своими словами?',
    'eco.finadv': 'Это финансовые консультанты сделки?',
    'law.struct': 'Механика сделки — формат, структура владения, этапы, сроки, — а не история переговоров и не кто сообщил?',
    'law.appr': 'Кто согласует или согласовал сделку (ФАС, правкомиссия, президент, министерство), а не кто сообщил новость?',
    'law.terms': 'Условия сделки — заверения, опционы, earn-out, обязательства сторон?',
    'extra': 'Дополнение, которого нет в других полях, а не их повтор?',
}
GENERAL_QUESTIONS = {
    'verbatim': 'Есть ли предложение, которое читается как текст журналиста (сверьте с источником)? '
                'Дословно допустимо только в «ёлочках» с указанием, кто сообщает.',
    'parties': 'Роли сторон верны для этого типа сделки? У СП оба участника — учредители, не вносимые бизнесы; '
               'у раунда нет продавца; у торгов продавец назван.',
    'status_date': 'Статус и дата — о событии, которое описано (объявление ≠ закрытие)?',
    'post': 'Пост читается подписчиком без карточки: ни одна строка не обрывается, не повторяет заголовок, '
            'не называет предмет описанием?',
}


def _get(card, field):
    a, _, b = field.partition('.')
    v = card.get(a) if not b else (card.get(a) or {}).get(b)
    return v if isinstance(v, str) else None


def filled_fields(card):
    return [f for f in FIELD_QUESTIONS if accept_card.has(_get(card, f))]


def needs_second_reading(card):
    """Принята с SINCE и позже и ещё не прочитана второй раз. У старых
    фикстур `accepted: True` — не дата, они идут по-старому."""
    acc = card.get(accept_card.STAMP)
    return isinstance(acc, str) and acc >= SINCE and not card.get(STAMP)


def queue(base, pending):
    return [c for c in list(pending.get('cards') or []) + list(base.get('deals') or [])
            if needs_second_reading(c)]


def questionnaire(card, base):
    comps = base.get('companies') or {}
    seller, asset, buyer = format_post.party_names(card, comps)
    lines = ['=== %s ===' % card['id'],
             'Тип: %s · статус: %s · дата: %s' % (card.get('type'), card.get('status'), card.get('date')),
             'Стороны: покупатель/участник — %s; продавец — %s; предмет — %s' % (buyer, seller, asset), '']
    for f in filled_fields(card):
        lines.append('[%s] %s' % (f, FIELD_QUESTIONS[f]))
        lines.append('    %s' % _get(card, f))
    lines.append('')
    for k, q in GENERAL_QUESTIONS.items():
        lines.append('[%s] %s' % (k, q))
    lines.append('')
    lines.append('Источники: ' + '; '.join('%s — %s' % (s[0], s[1]) for s in card.get('src') or [] if len(s) > 1))
    lines.append('')
    try:
        post = format_post.render(card, comps)
        post = re.sub(r'<a href="([^"]*)">([^<]*)</a>', r'\2 (\1)', post)
        lines.append('Пост, как уйдёт в канал:\n' + re.sub(r'<[^>]+>', '', post))
    except Exception as e:                                     # noqa: BLE001
        lines.append('Пост не собирается: %s' % e)
    return '\n'.join(lines)


def check(ans, card):
    """Причины, по которым ответ принять нельзя: ответ обязан покрыть каждое
    заполненное поле и каждый общий вопрос."""
    bad = []
    fields = ans.get('fields') or {}
    for f in filled_fields(card):
        if f not in fields:
            bad.append('нет ответа по полю %s' % f)
    general = ans.get('general') or {}
    for k in GENERAL_QUESTIONS:
        if k not in general:
            bad.append('нет ответа на общий вопрос %s' % k)
    problems = [(k, v) for k, v in list(fields.items()) + list(general.items())
                if str(v).strip().lower() != 'ok']
    if ans.get('verdict') not in ('ok', 'fix'):
        bad.append('verdict — ok или fix')
    elif ans.get('verdict') == 'ok' and problems:
        bad.append('verdict ok при замечаниях: %s' % ', '.join(k for k, _ in problems))
    elif ans.get('verdict') == 'fix' and not problems:
        bad.append('verdict fix без единого замечания')
    return bad, problems


def apply(ans, card, day=None):
    bad, problems = check(ans, card)
    if bad:
        return 'refused', bad
    if problems:
        return 'fix', ['%s: %s' % (k, v) for k, v in problems]
    card[STAMP] = day or date.today().isoformat()
    return 'stamped', []


def main(argv):
    base, pending = accept_card.load()
    if '--queue' in argv:
        ids = [a for a in argv if a not in ('--queue',)]
        cards = queue(base, pending)
        if ids:
            cards = [c for c in cards if c['id'] in ids]
        print('Ждут второго чтения: %d' % len(cards))
        for c in cards:
            print(questionnaire(c, base))
            print()
        return 0
    path = next((a for a in argv if a.endswith('.json')), None)
    if not path:
        print(__doc__)
        return 1
    answers = json.load(open(path, encoding='utf-8'))
    write = '--write' in argv
    stamped = 0
    for ans in answers if isinstance(answers, list) else [answers]:
        card, _where = accept_card.find_card(str(ans.get('id')), base, pending)
        if not card:
            print('  ОТКАЗ  %s: карточки нет' % ans.get('id'))
            continue
        state, notes = apply(ans, card)
        if state == 'refused':
            print('  ОТКАЗ  %s: %s' % (card['id'], '; '.join(notes)))
        elif state == 'fix':
            print('  НА ПРАВКУ %s:\n    %s' % (card['id'], '\n    '.join(notes)))
        else:
            stamped += 1
            print('  ПРОЧИТАНА %s (%s)' % (card['id'], card[STAMP]))
    if stamped and write:
        accept_card.save(base, pending)
        print('Записано: %d' % stamped)
    elif stamped:
        print('Сухой прогон. Запись — с ключом --write.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
