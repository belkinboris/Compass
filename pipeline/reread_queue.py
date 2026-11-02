# -*- coding: utf-8 -*-
"""Вычитка базы: каждая опубликованная карточка — по всем правилам и по статье.

ЗАЧЕМ. 2 ноября 2026 десять первых карточек базы прочитали против статей:
пять с серьезными ошибками (выдуманная цель сделки, неверный продавец,
согласование чужой сделки, версия прокурора как факт, «могла составить» →
«составила»), четыре с мелочами, чистая одна. Ошибки старше октябрьского
пересказа: 1344 карточки из 1533 (88%) собраны до того, как появилась приемка,
и ни разу ее не проходили; второе чтение было у 96. Пересказ эти ошибки не
исправил, потому что сверялся с текстом самой карточки. Владелец: «наладим
рутину, которая будет проходиться по всем карточкам, начиная с самой первой,
и вычитывать её на все наши правила… и будет сверять с источником»; темп —
50 карточек в день.

ОЧЕРЕДЬ. Сначала карточки, чей текст изменился после последней проверки
(`readiness.changed_after_check`: правка опубликованной карточки возвращает
ее на проверку), потом — еще не вычитанные, с самой первой (по дню
добавления, затем по месту в базе).

    python3 pipeline/reread_queue.py --stats
    python3 pipeline/reread_queue.py --next 5            # досье: карточка, находки приемки, вопросы
    python3 pipeline/reread_queue.py --stamp answers.json [--write]

Порядок работы — routines/reread.md. Ответ на карточку (список в answers.json):

    {"id": "g…", "sources_opened": ["https://…"], "fixes": "pipeline/ingest/fixes/<файл>.py" | "",
     "fields": {"<поле>": "ok", …}, "general": {"<вопрос>": "ok", …}, "verdict": "ok",
     "ok_findings": {"<код находки>": "<почему это не ошибка>"}, "note": "…"}

Отметка `reread` (дата) и `reread_hash` (отпечаток вычитанного текста)
ставится, только когда правки из `fixes` уже записаны (`review.py --write`),
на каждый вопрос ответ «ok», и не осталось находок приемки из
`BLOCKING` без причины. Ни одна статья не открылась — `note` от 40 знаков,
где искали; карточка тогда вычитана только по правилам, и отметка это пишет.
"""
import json
import os
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (os.path.join(HERE, 'ingest'), HERE, ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

import readiness  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
STAMP = 'reread'
PER_DAY = 50
SITE = 'https://projectcompass.ru/#/deal/'

# Вопросы, которых нет во втором чтении: оно смотрит карточку саму по себе,
# вычитка — карточку против статьи.
SOURCE_QUESTIONS = {
    'source_support': 'Каждое утверждение карточки есть хотя бы в одной открытой статье? Чего нет нигде — снято, '
                      'а не оставлено «на всякий случай» (пустое поле честнее).',
    'motive': 'Цель сделки (eco.rationale) названа в статье самими сторонами или с автором оценки? Наш вывод, '
              'рассуждение третьего лица без имени — замечание.',
    'seller': 'Продавец — тот, чья доля уменьшилась, по статье или реестру? Не прежний владелец, вышедший раньше, '
              'и не «владельцы компании», если статья называет имена.',
    'industry': 'Отрасль — по предмету сделки, а не по покупателю (docs/card_parties.md#Отрасль)?',
    'numbers': 'Все числа (доли, суммы, оценки, финансы, даты) совпадают со статьей, и при оценке назван, кто оценивал?',
    'other_deal': 'В карточке нет фактов другой сделки — согласования, цены или участников предыдущей продажи актива?',
}
# Находки приемки, с которыми отметка не ставится без причины в `ok_findings`:
# смысловые и те, что видны читателю. Формальные (ИНН, профиль стороны,
# строка поста) правятся своими шагами и отметку не держат.
BLOCKING = ('stale_statement', 'date_unbased', 'adviser_not_deal', 'sum_fields_differ', 'industry_undefined',
            'why_fragment', 'truncated', 'bare_surname', 'title_style', 'parties_missing', 'jv_participants')


def load():
    return json.load(open(DATA, encoding='utf-8'))


def order(data):
    deals = data['deals']
    return sorted(range(len(deals)), key=lambda i: (deals[i].get('added') or '9999', i))


def queue(data):
    comps = data.get('companies') or {}
    deals = data['deals']
    idx = order(data)
    changed = [deals[i] for i in idx if readiness.changed_after_check(deals[i], comps)]
    seen = {c['id'] for c in changed}
    rest = [deals[i] for i in idx if not deals[i].get(STAMP) and deals[i]['id'] not in seen]
    return [(c, 'изменена после проверки') for c in changed] + [(c, 'по порядку') for c in rest]


def signals(card, data):
    """Подсказки читателю, не находки: отрасль карточки не совпадает с
    отраслью профиля покупаемой компании (Аэрофлот/«Директ Стар»: отрасль
    покупателя вместо предмета) — не всегда ошибка, но повод проверить."""
    comps = data.get('companies') or {}
    out = []
    subj = comps.get(card.get('target') or card.get('asset_id') or '') or {}
    if subj.get('ind') and card.get('ind') and subj['ind'] != card['ind']:
        out.append('отрасль карточки «%s», у профиля предмета «%s» — по предмету ли поставлена?'
                   % (card['ind'], subj['ind']))
    return out


def _findings(card, data):
    import accept_card
    return accept_card.findings(card, data)


def dossier(card, why, data):
    import second_reading
    lines = ['#' * 78, '%s  %s%s  (%s)' % (card['id'], SITE, card['id'], why),
             'добавлена %s · проверки: приемка %s, второе чтение %s, вычитка %s'
             % (card.get('added'), card.get('accepted') or '—', card.get('second_read') or '—', card.get(STAMP) or '—')]
    f = _findings(card, data)
    lines.append('НАХОДКИ ПРИЕМКИ (%d):' % len(f))
    lines += ['  %s %s %s' % ('!' if c.split(':')[0] in BLOCKING else '-', c, t) for c, t in f]
    for s in signals(card, data):
        lines.append('ПОДСКАЗКА: ' + s)
    lines.append(second_reading.questionnaire(card, data))
    lines.append('ВОПРОСЫ ПО СТАТЬЕ')
    lines += ['[%s] %s' % (k, q) for k, q in SOURCE_QUESTIONS.items()]
    return '\n'.join(lines)


def check(ans, card, data):
    import second_reading
    general_q = dict(second_reading.GENERAL_QUESTIONS, **SOURCE_QUESTIONS)
    bad = []
    fields, general = ans.get('fields') or {}, ans.get('general') or {}
    bad += ['нет ответа по полю %s' % f for f in second_reading.filled_fields(card) if f not in fields]
    bad += ['нет ответа на вопрос %s' % k for k in general_q if k not in general]
    left = [k for k, v in list(fields.items()) + list(general.items()) if str(v).strip().lower() != 'ok']
    if left:
        bad.append('замечания не исправлены (ответ не «ok»): %s' % ', '.join(left))
    if ans.get('verdict') != 'ok':
        bad.append('verdict — «ok», когда карточка исправлена; иначе отметка не ставится')
    opened = [u for u in ans.get('sources_opened') or [] if str(u).startswith('http')]
    if not opened and len(str(ans.get('note') or '')) < 40:
        bad.append('ни одной открытой статьи и нет note от 40 знаков: где искали')
    fx = ans.get('fixes') or ''
    if fx:
        import review
        mine = [r for r in review.load_fixes() if r.get('id') == card['id']]
        pending = [r for r in mine if not review.already_applied(r, card)] if hasattr(review, 'already_applied') else []
        if not mine:
            bad.append('в %s нет записей на эту карточку' % fx)
        elif pending:
            bad.append('правки не записаны (review.py --write): %s' % ', '.join(r['field'] for r in pending))
    ok = ans.get('ok_findings') or {}
    for c, _t in _findings(card, data):
        if c.split(':')[0] in BLOCKING and not (len(str(ok.get(c) or '')) >= 15):
            bad.append('находка приемки без причины: %s' % c)
    return bad


def stamp(card, ans, comps, day=None):
    card[STAMP] = day or date.today().isoformat()
    card[STAMP + '_hash'] = readiness.fingerprint(card, comps)
    opened = [u for u in ans.get('sources_opened') or [] if str(u).startswith('http')]
    card[STAMP + '_note'] = ('статьи: %d' % len(opened)) if opened else ('без статьи: ' + str(ans.get('note')))


def stats(data):
    deals = data['deals']
    done = sum(1 for d in deals if d.get(STAMP))
    q = queue(data)
    changed = sum(1 for _c, w in q if w != 'по порядку')
    print('Карточек в базе: %d · вычитано: %d · изменены после проверки: %d · осталось по порядку: %d'
          % (len(deals), done, changed, len(q) - changed))
    print('При %d в день — еще %d дн.' % (PER_DAY, -(-len(q) // PER_DAY)))
    if q:
        print('Следующая: %s %s%s' % (q[0][0]['id'], SITE, q[0][0]['id']))


def _self_check():
    data = {'companies': {'t': {'name': 'Т', 'ind': 'Лесопром'}},
            'deals': [{'id': 'g2', 'added': '2026-07-15', 'title': 'b'},
                      {'id': 'g1', 'added': '2026-07-15', 'title': 'a', 'ind': 'Ритейл', 'target': 't'},
                      {'id': 'g0', 'added': '2026-08-01', 'title': 'c'}]}
    assert [c['id'] for c, _w in queue(data)] == ['g2', 'g1', 'g0']
    data['deals'][2]['gate_baseline_hash'] = readiness.fingerprint(data['deals'][2], data['companies'])
    data['deals'][2]['title'] = 'c изменен'
    data['deals'][0][STAMP] = '2026-11-02'
    assert [(c['id'], w) for c, w in queue(data)] == [('g0', 'изменена после проверки'), ('g1', 'по порядку')]
    assert signals(data['deals'][1], data)


def main(argv):
    _self_check()
    data = load()
    if '--stats' in argv or not argv:
        stats(data)
        return 0
    if '--next' in argv:
        n = int(argv[argv.index('--next') + 1])
        for c, why in queue(data)[:n]:
            print(dossier(c, why, data))
        return 0
    if '--stamp' in argv:
        answers = json.load(open(argv[argv.index('--stamp') + 1], encoding='utf-8'))
        cards = {d['id']: d for d in data['deals']}
        good, refused = [], 0
        for ans in answers:
            card = cards.get(str(ans.get('id')))
            bad = ['карточки нет в базе'] if card is None else check(ans, card, data)
            if bad:
                refused += 1
                print('  ОТКАЗ  %s:' % ans.get('id'))
                for b in bad:
                    print('         - %s' % b)
            else:
                good.append(ans)
                print('  ГОДНА  %s' % card['id'])
        print('ответов %d, отказов %d' % (len(answers), refused))
        if good and '--write' in argv:
            # Перечитать файл прямо перед записью (docs/card_editing.md): другие
            # рутины могли запушить свое, пока шла вычитка.
            fresh = load()
            comps = fresh.get('companies') or {}
            by_id = {d['id']: d for d in fresh['deals']}
            for ans in good:
                stamp(by_id[ans['id']], ans, comps)
            json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
            print('Записано отметок: %d' % len(good))
        elif good:
            print('Сухой прогон. Запись — с ключом --write.')
        return 1 if refused else 0
    print(__doc__)
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
