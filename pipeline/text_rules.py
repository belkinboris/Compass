# -*- coding: utf-8 -*-
"""Правила текста для людей — одна проверка на любой путь записи.

ЗАЧЕМ (22 октября 2026). Правила владельца жили там, где их однажды записали:
«собеседник издания» — в `prose_gate` (его проходит только `review.py`), жаргон
и пресс-атрибуция — в `proofread.check` (только вычитка), «вложился» — в
приёмке. Разовый скрипт, которым агент правит базу напрямую, не проходил ни
одной из этих проверок, и «другой собеседник издания говорит» вышло на сайт.
Владелец: «нужно сделать так, чтобы ошибок не возникало — вычитывать любой
новый текст на те правила, которые мы установили».

Здесь собраны правила, которым не нужна статья-источник: их можно проверить
на готовом тексте в базе. `problems(text, field)` — список (код, пояснение).
Держит их `test_data.py::test_card_text_follows_the_house_rules` по ВСЕЙ базе —
то есть по любому пути записи: `review.py`, вычитка, приёмка, разовый скрипт.
Правила, которым нужна статья (числа и дословность против цитаты), остаются в
`prose_gate`/`proofread` — без источника их не проверить.

Новое правило владельца про текст — сюда, с датой и словами владельца, и
сразу замер по базе: что нашлось — исправить в том же коммите.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import proofread  # noqa: E402

# Поля прозы карточки сделки, которые читает человек.
PROSE_FIELDS = ('extra', 'eco.share', 'eco.val', 'eco.target_fin', 'eco.fin', 'eco.rationale',
                'eco.context', 'eco.sum', 'law.struct', 'law.terms', 'law.appr')

INSIDER_VOICE = re.compile(
    r"собеседник|по\s+словам\s+(?:двух\s+|нескольких\s+)?источник|источник\w*\s+(?:РБК|«|издания|газеты|агентства)"
    r"|(?:уточнил|сообщил|рассказал)\w*\s+(?:один\s+из\s+)?источник", re.I)
INVESTED_COLLOQUIAL = re.compile(r'\bвложил(?:ся|ась|ось|ись|а|и)?\b', re.I)
STIFF = re.compile(r'на\s+момент\s+(?:записи|написания|подготовки)|\bэто\s+и\s+привело\b', re.I)
SERVICE_NOTE = re.compile(r'расхождени\w*\s+(?:источников\s+)?не\s+разрешен|не\s+сходится\s+—\s+источник', re.I)
YELLOW = re.compile(r'истори\w*\s+скандал|скандал\w*\s+вокруг|должн\w*\s+беспоко', re.I)


def problems(text, field=''):
    """[(код, пояснение)] — пусто, если текст чист."""
    t = str(text or '')
    if not t.strip() or proofread.PLACEHOLDER.match(t.strip()):
        return []
    out = []

    def add(code, why):
        out.append((code, why))
    m = INSIDER_VOICE.search(t)
    if m:
        add('insider', '«%s» — голос газеты, не наш: «по данным РБК» или «по неофициальным данным» '
            '(владелец, 22.10.2026)' % m.group(0))
    for rule, frag in proofread.source_note(t):
        # «По данным РБК» — законная атрибуция чужих сведений (владелец,
        # 22.10.2026: так и надо вместо «собеседника издания»). Запрещены
        # пометки о том, где МЫ это прочитали: «(Коммерсантъ)», «Источник:».
        if rule in ('издание в скобках', '«Источник:» в тексте') or rule == 'пометка о нашей работе':
            add('source_note', 'пометка о происхождении «%s» — %s: назовите издание в тексте '
                '(«по данным РБК») или уберите' % (frag[:40], rule))
    for rx in proofread.JARGON:
        m = rx.search(t)
        if m:
            add('jargon', 'наш диалект в тексте для людей: «%s»' % m.group(0))
    m = proofread.BAD_TOKEN.search(t)
    if m:
        add('bad_token', 'служебное значение в тексте: %s' % m.group(0))
    m = STIFF.search(t)
    if m:
        add('stiff', 'казённый оборот «%s» — скажите, как сказал бы человек' % m.group(0))
    m = SERVICE_NOTE.search(t)
    if m:
        add('service_note', 'служебная пометка разбора: «%s»' % m.group(0))
    m = YELLOW.search(t)
    if m:
        add('yellow', 'тон жёлтой прессы: «%s»' % m.group(0))
    if '...' in re.sub(r'«(?:[^«»]|«[^«»]*»)*»', ' ', t):     # в чужой цитате «…» — законный пропуск
        add('dots', 'троеточие из точек — знак обрыва')
    m = proofread.HYPHEN_AS_DASH.search(t)
    if m:
        add('hyphen', '« - » вместо тире « — »: «%s»' % m.group(0))
    if not proofread.quotes_balanced(t):
        add('quotes', 'кавычки « » / „ “ не сбалансированы')
    if field == 'title':
        m = INVESTED_COLLOQUIAL.search(t)
        if m:
            add('invested', '«%s» — пишем «проинвестировал(а)» (владелец, 21.10.2026)' % m.group(0))
    return out


def card_texts(deal):
    """[(поле, текст)] — всё, что человек читает в карточке сделки."""
    out = [('title', deal.get('title'))]
    for f in PROSE_FIELDS:
        out.append((f, proofread.get_field(deal, f)))
    for i, e in enumerate(deal.get('events') or []):
        if isinstance(e, dict):
            out.append(('events.%d.note' % i, e.get('note')))
    return [(f, v) for f, v in out if isinstance(v, str) and v.strip()]


def deal_problems(deal):
    return [(f, code, why) for f, v in card_texts(deal) for code, why in problems(v, f)]


BASELINE = os.path.join(HERE, 'text_rules_baseline.json')


def fingerprint(deal_id, field, code, text):
    import hashlib
    return '%s|%s|%s|%s' % (deal_id, field, code, hashlib.sha1(str(text).encode('utf-8')).hexdigest()[:10])


def all_findings(data):
    out = []
    for d in data['deals']:
        texts = dict(card_texts(d))
        for f, code, why in deal_problems(d):
            out.append((fingerprint(d['id'], f, code, texts[f]), d['id'], f, code, why))
    return out


def main(argv):
    """Без ключей — вся база; `--changed` — только поля, которые отличаются от HEAD."""
    import json
    import subprocess
    root = os.path.dirname(HERE)
    data = json.load(open(os.path.join(root, 'static', 'data', 'deals_promoted.json'), encoding='utf-8'))
    old = {}
    if '--changed' in argv:
        raw = subprocess.run(['git', 'show', 'HEAD:static/data/deals_promoted.json'], cwd=root,
                             capture_output=True, text=True).stdout
        old = {d['id']: dict(card_texts(d)) for d in json.loads(raw)['deals']}
    if '--rebaseline' in argv:
        # Только сокращает список: убирает исправленное, нового не добавляет.
        known = json.load(open(BASELINE, encoding='utf-8'))
        now = {f[0] for f in all_findings(data)}
        left = sorted(fp for fp in known['known'] if fp in now)
        print('Было %d, осталось %d.' % (len(known['known']), len(left)))
        known['known'] = left
        with open(BASELINE, 'w', encoding='utf-8') as fh:
            json.dump(known, fh, ensure_ascii=False, indent=1)
        return 0
    n = 0
    for d in data['deals']:
        before = old.get(d['id'], {})
        for f, code, why in deal_problems(d):
            if '--changed' in argv and before.get(f) == dict(card_texts(d)).get(f):
                continue
            n += 1
            print('%s %s [%s] %s' % (d['id'], f, code, why))
    print('Нарушений: %d' % n)
    return 1 if n else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
