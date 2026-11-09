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
    'registry': 'У покупаемого ООО продавец, доля и дата перехода сверены с историей участников из реестра '
                '(pipeline/party_legal_names.py <id>)? Вход через увеличение уставного капитала — не покупка у владельца.',
    'placement': 'Каждый факт в своем поле: цель — только мотив, названный сторонами; финансы сторон вокруг сделки '
                 '(долги, убытки продавца) — eco.fin_context; род занятий компании — в контекст, не в финансы; '
                 '«Как устроена сделка» — механика, а не дата записи в ЕГРЮЛ и не очевидное «стал единственным участником»?',
    'reader': 'Прочитайте карточку глазами читателя: у каждого предложения есть подлежащее, нет разговорного '
              '(«в минусе», «сам»), оценочного («теряет деньги») и пустого; разные темы контекста — отдельными абзацами?',
    'other_deal': 'В карточке нет фактов другой сделки — согласования, цены или участников предыдущей продажи актива?',
}
# Находки приемки, с которыми отметка не ставится без причины в `ok_findings`:
# смысловые и те, что видны читателю. Формальные (ИНН, профиль стороны,
# строка поста) правятся своими шагами и отметку не держат.
BLOCKING = ('title_standard', 'share_form', 'party_legal_form', 'plain_words', 'stale_statement', 'date_unbased', 'adviser_not_deal', 'sum_fields_differ', 'industry_undefined',
            'why_fragment', 'truncated', 'bare_surname', 'title_style', 'parties_missing', 'jv_participants')


# Короткая проверка (владелец, 9 ноября 2026: «пройдись короткой проверкой по 273
# картам после 3 октября»). Карточки, созданные после 3 октября, прошли приемку по
# статье при создании; на 17 вычитанных из них неверных покупателей не нашлось,
# правки были в дате, доле и продавце. Поэтому сверяется только каркас сделки:
# стороны, дата и статус, сумма и доля, консультанты, заголовок. Отметка та же
# (`reread`), с `reread_scope: short` — полная вычитка такие карточки не берет.
SHORT_FROM = '2026-10-03'
SHORT_FIELDS = ('title', 'eco.sum', 'eco.share')
SHORT_GENERAL = ('parties', 'status_date', 'seller', 'numbers', 'registry', 'other_deal', 'advisers')
SHORT_BLOCKING = ('title_standard', 'share_form', 'date_unbased', 'adviser_not_deal', 'sum_fields_differ',
                  'parties_missing', 'jv_participants', 'party_legal_form')
SHORT_ADVISERS_Q = ('Консультанты (law.adv, eco.finadv): каждый подтвержден источником, у роли назван клиент '
                    '(или «одной из сторон», если ни один источник и устройство сделки его не дают)?')


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


def registry_lines(card, data, fetch=None):
    """Стороны по реестру — в досье само, без напоминания (2 ноября 2026:
    знание о продавце по истории участников ООО, записанное 14 октября,
    в новой рутине потерялось). Правовая форма сторон и история участников
    покупаемого общества: продавец, доля, дата перехода."""
    import party_legal_names as pln
    fetch = fetch or pln.fetch
    comps = data.get('companies') or {}
    out = ['РЕЕСТР (сайт /api/companies/<id>/fns):']
    for role in pln.ROLES:
        cid = card.get(role)
        if not cid or cid not in comps:
            continue
        try:
            info = fetch(cid)
        except Exception as e:  # сеть недоступна — читающий ищет сам (READING_BRIEF.md, datanewton по ОГРН)
            out.append('  %s %s: реестр недоступен (%s)' % (role, comps[cid].get('name'), e))
            continue
        ents = info.get('entities') or []
        if not info.get('available') or not ents:
            out.append('  %s %s: %s — искать по ОГРН (READING_BRIEF.md)'
                       % (role, comps[cid].get('name'), info.get('reason') or 'нет в реестре'))
            continue
        ent = ents[0]['entity']
        out.append('  %s %s: %s, ИНН %s' % (role, comps[cid].get('name'), ent.get('short_name'), ent.get('inn')))
        if role in ('target', 'asset_id'):
            out += pln.owners_text(ents[0])[:14]
    return out if len(out) > 1 else []


def _findings(card, data):
    """Находки приемки плюс стандарт заголовка. Приемка у опубликованной
    карточки заголовок не проверяет (переписывать вышедшее — не ее дело), а
    вычитка — проверяет: заголовок переписывается в том же проходе, что и
    остальные поля, а не отдельной партией (владелец, 6 ноября 2026: «добавь
    изменение названия в глубокую проверку… двойная работа не нужна»)."""
    import accept_card
    out = [f for f in accept_card.findings(card, data) if f[0] != 'title_standard']
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import title_standard
    if title_standard.verb_ok(card) is False:
        out.append(('title_standard', 'заголовок не по стандарту для «%s», статус «%s»: %s (pipeline/title_standard.py)'
                    % (card.get('type'), card.get('status'), title_standard.hint(card))))
    return out


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
    lines += registry_lines(card, data)
    lines.append(second_reading.questionnaire(card, data))
    lines.append('ВОПРОСЫ ПО СТАТЬЕ')
    lines += ['[%s] %s' % (k, q) for k, q in SOURCE_QUESTIONS.items()]
    return '\n'.join(lines)


def short_dossier(card, data):
    """Досье короткой проверки: карточка, находки, вопросы только о каркасе сделки."""
    import second_reading
    keys = ('title', 'type', 'status', 'date', 'buyer', 'buyer_name', 'seller', 'seller_name', 'target', 'asset',
            'sum')
    lines = ['#' * 78, '%s  %s%s  (короткая проверка, добавлена %s)' % (card['id'], SITE, card['id'], card.get('added'))]
    lines += ['  %s: %s' % (k, card.get(k)) for k in keys if card.get(k) not in (None, '', [])]
    eco, law = card.get('eco') or {}, card.get('law') or {}
    for k in ('sum', 'share', 'finadv'):
        if eco.get(k):
            lines.append('  eco.%s: %s' % (k, eco[k]))
    for a in law.get('adv') or []:
        lines.append('  law.adv: %s' % ' | '.join(str(x) for x in a))
    lines += ['  src: %s' % ' '.join(str(x) for x in s) for s in card.get('src') or []]
    f = [x for x in _findings(card, data) if x[0].split(':')[0] in SHORT_BLOCKING]
    lines += ['  ! %s %s' % (c, t) for c, t in f]
    lines += registry_lines(card, data)
    q = dict(second_reading.GENERAL_QUESTIONS, **SOURCE_QUESTIONS, advisers=SHORT_ADVISERS_Q)
    lines += ['[%s] %s' % (k, q[k]) for k in SHORT_GENERAL]
    return '\n'.join(lines)


def check(ans, card, data):
    import second_reading
    short = ans.get('scope') == 'short'
    general_q = dict(second_reading.GENERAL_QUESTIONS, **SOURCE_QUESTIONS)
    bad = []
    fields, general = ans.get('fields') or {}, ans.get('general') or {}
    if short:
        if (card.get('added') or '') < SHORT_FROM:
            bad.append('короткая проверка — только для карточек, добавленных с %s' % SHORT_FROM)
        bad += ['нет ответа по полю %s' % f for f in SHORT_FIELDS
                if f in second_reading.filled_fields(card) and f not in fields]
        bad += ['нет ответа на вопрос %s' % k for k in SHORT_GENERAL if k not in general]
    else:
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
        pending = [r for r in mine if not review.already_applied(r, card, data.get('companies'))]
        if not mine:
            bad.append('в %s нет записей на эту карточку' % fx)
        elif pending:
            bad.append('правки не записаны (review.py --write): %s' % ', '.join(r['field'] for r in pending))
    ok = ans.get('ok_findings') or {}
    for c, _t in _findings(card, data):
        if c.split(':')[0] in (SHORT_BLOCKING if short else BLOCKING) and not (len(str(ok.get(c) or '')) >= 15):
            bad.append('находка приемки без причины: %s' % c)
    return bad


def keep_post_title(data, card):
    """Вычитка не переписывает пост в канале (см. «Чего не делать» в routines/reread.md):
    заголовок, исправленный в вычитке по стандарту, остается на сайте, а вышедший пост — каким
    был. Публикация правит пост «молча», когда заголовок карточки расходится со снимком поста
    (send_telegram.card_changes_since_post), — поэтому снимок получает новый заголовок
    (6 ноября 2026: стандарт заголовков — для карточек, посты свободнее)."""
    snap = (data.get('telegram_post_state') or {}).get(card['id'])
    if snap and snap.get('title') is not None and snap.get('title') != card.get('title'):
        snap['title'] = card.get('title')
        return True
    return False


def stamp(card, ans, comps, day=None):
    card[STAMP] = day or date.today().isoformat()
    card[STAMP + '_hash'] = readiness.fingerprint(card, comps)
    if ans.get('scope') == 'short':
        card[STAMP + '_scope'] = 'short'
    else:
        card.pop(STAMP + '_scope', None)
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
    fake = lambda cid: {'available': True, 'entities': [{'entity': {'short_name': 'ООО "Т"', 'inn': '1'},
                        'ownership': {'history': [{'date': '2026-06-01', 'kind': 'left', 'owner': {'name': 'ООО "Л"'},
                                                   'before_share': 100.0, 'after_share': None}]}}]}
    reg = registry_lines(data['deals'][1], data, fetch=fake)
    assert any('left: ООО "Л"' in l for l in reg), reg


def main(argv):
    _self_check()
    data = load()
    if '--stats' in argv or not argv:
        stats(data)
        return 0
    if '--ids' in argv:
        # Досье на выбранные карточки вне очереди (владелец, 9 ноября 2026: вычитать
        # все карточки, где консультанты — организаторы форума M&A).
        want = [x.strip() for x in argv[argv.index('--ids') + 1].split(',') if x.strip()]
        by_id = {d['id']: d for d in data['deals']}
        for cid in want:
            print(dossier(by_id[cid], 'вне очереди', data))
        return 0
    if '--short' in argv:
        # Карточки для короткой проверки: не вычитаны, добавлены с SHORT_FROM.
        n = int(argv[argv.index('--short') + 1])
        todo = [c for c, _why in queue(data) if not c.get(STAMP) and (c.get('added') or '') >= SHORT_FROM]
        if '--list' in argv:
            print('\n'.join(c['id'] for c in todo[:n]))
            return 0
        for c in todo[:n]:
            print(short_dossier(c, data))
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
                keep_post_title(fresh, by_id[ans['id']])
            json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
            print('Записано отметок: %d' % len(good))
        elif good:
            print('Сухой прогон. Запись — с ключом --write.')
        return 1 if refused else 0
    print(__doc__)
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
