#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Приёмка карточки: последнее чтение целиком перед консолью и каналом.

ЗАЧЕМ. 11 сентября 2026 владелец открыл две свежие карточки подряд —
Positive Technologies/CyberOK и «Совко Капитал Партнерс»/Совкомбанк — и в
каждой нашёл то, что видно с первого взгляда: предмет в косвенном падеже с
описанием вместо имени, некликабельные стороны, дословную фразу газеты под
«Юристом», «Зачем», которое не отвечает на «зачем», единственный источник
там, где статья сама ссылается на пресс-релиз. «Это уже не первый раз… нужно
подойти с архитектурной точки зрения, чтобы такого больше не было».

ПОЧЕМУ ЭТО ПОВТОРЯЛОСЬ. Каждый из дефектов уже был закрыт правилом — но
правило стоит на ОДНОМ пути (draft.py, review.py, link_parties) и проверяет
ОДНО поле по ФОРМЕ (дословность, регэксп). Карточка приходит несколькими
путями (ворота притока, кнопка «в работу», правки дочитывания), а вопросы
владельца — про СМЫСЛ («это имя компании?», «это ответ на зачем?», «это
условие сделки или пресс-релиз?»), на который регэксп не отвечает. Не было
шага, где кто-то читает ГОТОВУЮ карточку и пост целиком глазами читателя.
Владельцу приходилось быть этим читателем.

ЧТО ЭТО. Шаг приёмки: одно чтение на карточку по чек-листу
(`CARD_ACCEPTANCE_BRIEF.md`) — читатель (саб-агент рутины) правит карточку
через уже существующие механизмы (профили и привязки здесь, факты с цитатой
через review.py, проза через proofread.py) и отвечает файлом; скрипт
проверяет ответ механически и ставит штамп `accepted`. БЕЗ ШТАМПА карточка
не показывается в консоли (send_drafts), не выходит по молчанию (approve) и
не уходит постом в канал (send_telegram) — три места, куда карточка попадает
любым путём. Забыть шаг нельзя: он не совет в промпте, а замок на выходе.

ГРАНИЦА. Скрипт не судит о смысле — это делает читатель. Скрипт делает две
вещи: (1) собирает досье с механическими НАХОДКАМИ (`findings`), чтобы
читатель знал, куда смотреть, и (2) не даёт ответу читателя внести
выдумку: новое имя в заголовке, профиль-описание, профиль-близнец,
описание с пресс-атрибуцией. Штамп ставится только когда находок не
осталось (кроме названных в `no_profile` с причиной).

Запуск:
    python3 pipeline/ingest/accept_card.py --queue            # досье по всем без штампа
    python3 pipeline/ingest/accept_card.py --queue <id>       # досье по одной
    python3 pipeline/ingest/accept_card.py --check  answers.json
    python3 pipeline/ingest/accept_card.py --apply  answers.json [--write]
    python3 pipeline/ingest/accept_card.py --self-check
"""
import json
import os
import re
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
for p in (HERE, os.path.join(ROOT, 'pipeline', 'publish'), os.path.join(ROOT, 'pipeline'), ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

import casing                      # noqa: E402
import link_parties                # noqa: E402
import review                      # noqa: E402
import format_post                 # noqa: E402
import check_post                  # noqa: E402
import proofread                   # noqa: E402
import source_names                # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
RAW_DIR = os.path.join(ROOT, 'data', 'inbox', 'raw')

STAMP = 'accepted'
CHECKLIST = ('sources', 'parties', 'asset', 'title', 'why', 'fields', 'wording', 'post', 'status')
ROLES = {'target': ('asset', 'target'), 'buyer': ('buyer_name', 'buyer'), 'seller': ('seller', 'seller_id')}
PROSE_FIELDS = proofread.PROOFREAD_FIELDS
PLACEHOLDER = re.compile(r'^\s*(—|-|не раскрыт[а-яё]*|публично не сообщал[а-яё]*|не привлекал[а-яё]*|нет данных|n/?a)?\s*$', re.I)


def has(v):
    return bool(v) and not PLACEHOLDER.match(str(v))


# ---------------------------------------------------------------------------
# Загрузка: карточка может лежать в базе или в очереди предпросмотра

def load():
    base = json.load(open(DATA, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8')) if os.path.exists(PENDING) else {'cards': []}
    return base, pending


def save(base, pending):
    for path, obj in ((DATA, base), (PENDING, pending)):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(obj, f, indent=1, ensure_ascii=False)
            f.write('\n')


def find_card(cid, base, pending):
    for c in pending.get('cards', []):
        if c['id'] == cid:
            return c, 'pending'
    for c in base['deals']:
        if c['id'] == cid:
            return c, 'base'
    return None, None


def queue(base, pending):
    """Что ждёт приёмки: вся очередь предпросмотра без штампа и карточки базы,
    которым ещё предстоит ПЕРВЫЙ пост (свежие, без записи в telegram_posts) —
    ровно те, кого гейты ниже по течению не пропустят."""
    out = [c for c in pending.get('cards', []) if not c.get(STAMP)]
    posts = base.get('telegram_posts') or {}
    for c in base['deals']:
        if c.get(STAMP) or c['id'] in posts or c.get('no_post') or c.get('post_override'):
            continue
        if format_post.is_fresh(c):
            out.append(c)
    return out


# ---------------------------------------------------------------------------
# Механические находки — куда смотреть читателю (и что не даст поставить штамп)

def _text(card, field):
    return proofread.get_field(card, field) if '.' in field else card.get(field)


def _title_words(text):
    # В заголовке первое слово — тоже имя (титул начинается со стороны:
    # «Иванов купил…»), поэтому начало предложения НЕ пропускается. Обычное
    # первое слово («Пакет», «Правительство») найдётся в карточке по
    # `name_match` без учёта регистра и отказ не вызовет.
    return proofread.capitalised_words(text or '', skip_sentence_start=False)


def findings(card, base, waived=None):
    """Список (код, текст). Пусто — механика претензий не имеет; смысл судит
    читатель. `waived` — роли, для которых читатель назвал причину без профиля."""
    waived = waived or (card.get(STAMP + '_notes') or {}).get('no_profile') or {}
    out = []
    asset = card.get('asset')
    if asset:
        fixed, changed = casing.to_nominative_asset(asset)
        if changed:
            out.append(('asset_case', 'предмет в косвенном падеже: %r → %r' % (asset, fixed)))
        if review.ASSET_IS_A_DESCRIPTION.search(asset):
            out.append(('asset_description', 'предмет — описание, а не имя компании: %r' % asset))
    if not (card.get('target') or card.get('asset_id') or has(asset)) \
            and card.get('type') in ('M&A', 'Продажа с торгов', 'Инвестиция') and 'target' not in waived:
        out.append(('asset_missing', 'предмет сделки не назван (ни профиль, ни текст)'))
    for role, (text_field, id_field) in ROLES.items():
        text = card.get(text_field)
        linked = card.get(id_field) or (role == 'target' and card.get('asset_id'))
        if has(text) and not linked and role not in waived:
            out.append(('party_unlinked:' + role, '%s «%s» — текстом, без профиля' % (role, text)))
    for f in ('title', 'asset', 'buyer_name', 'seller'):
        if '"' in str(card.get(f) or ''):
            out.append(('straight_quotes:' + f, 'прямые кавычки в %s' % f))
    for f in PROSE_FIELDS:
        v = _text(card, f)
        if not has(v):
            continue
        p = proofread.press_attribution(v)
        if p:
            out.append(('press:' + f, 'пресс-язык в %s: %s' % (f, p)))
        if proofread.long_quotes(v):
            out.append(('quote:' + f, 'длинная цитата в кавычках в %s' % f))
    rationale = _text(card, 'eco.rationale')
    if has(rationale):
        first = (format_post._sentences(rationale) or [''])[0]
        if format_post.NOT_A_MOTIVE.search(first):
            out.append(('why', '«Цель сделки» начинается с оценки рынка, а не с мотива'))
        if has(card.get('extra')) and proofread.typo_flat(rationale) == proofread.typo_flat(card['extra']) \
                if hasattr(proofread, 'typo_flat') else False:
            out.append(('why_dup', '«Цель сделки» дословно повторяет «Дополнительную информацию»'))
    if not any(str(s[1]).startswith('http') for s in card.get('src') or [] if len(s) > 1):
        out.append(('source', 'ни одной http-ссылки в источниках'))
    if card.get('type') == 'Продажа с торгов' and not (card.get('seller') or card.get('seller_id')) \
            and 'seller' not in waived:
        out.append(('auction_seller', 'у продажи с торгов продавец назван всегда — здесь его нет'))
    try:
        text = format_post.render(card, base.get('companies') or {})
        for p in check_post.check(text):
            out.append(('post', 'пост: %s' % p))
    except Exception as e:  # пост, который не собирается, — тоже находка
        out.append(('post', 'пост не собирается: %s' % e))
    return out


# ---------------------------------------------------------------------------
# Досье для читателя

def candidates(name, base, limit=5):
    """Профили, похожие на имя: по ключу близнецов и по вхождению слов."""
    if not has(name):
        return []
    comps = base['companies']
    key = link_parties.company_key(name)
    out = [(cid, c['name'], 'тот же ключ') for cid, c in comps.items()
           if len(key) >= 3 and link_parties.company_key(c.get('name')) == key]
    words = [w for w in re.findall(r'[A-Za-zА-Яа-яЁё0-9-]{4,}', name.lower())
             if w not in ('ооо', 'зао', 'пао', 'акции', 'доля', 'компания', 'группа', 'холдинг')]
    for cid, c in comps.items():
        low = (c.get('name') or '').lower()
        if any(w in low for w in words) and all(cid != o[0] for o in out):
            out.append((cid, c['name'], 'по слову'))
        if len(out) >= limit:
            break
    return out


def cached_text_available(url):
    if not os.path.isdir(RAW_DIR):
        return False
    for name in os.listdir(RAW_DIR):
        if not name.endswith('-articles.jsonl'):
            continue
        with open(os.path.join(RAW_DIR, name), encoding='utf-8') as f:
            for line in f:
                if url in line:
                    return True
    return False


def dossier(card, base):
    comps = base.get('companies') or {}
    lines = ['=' * 78, '%s  %s  %s' % (card['id'], card.get('date'), card.get('status')),
             'Заголовок: %s' % card.get('title'),
             'Тип: %s · Отрасль: %s · Сумма: %s' % (card.get('type'), card.get('ind'), card.get('sum'))]
    for role, (tf, idf) in ROLES.items():
        ref = card.get(idf) or (role == 'target' and card.get('asset_id'))
        prof = comps.get(ref, {}).get('name') if ref else None
        lines.append('%-10s текст: %r | профиль: %s' % (role, card.get(tf), '%s (%s)' % (prof, ref) if ref else '—'))
        if not ref:
            for cid, nm, why in candidates(card.get(tf), base):
                lines.append('           кандидат: %s  %s  [%s]' % (cid, nm, why))
    for f in ('extra',) + tuple(PROSE_FIELDS) + ('law.appr', 'law.terms'):
        v = _text(card, f)
        if has(v):
            lines.append('%s: %s' % (f, v))
    lines.append('Источники:')
    for s in card.get('src') or []:
        url = s[1] if len(s) > 1 else ''
        lines.append('  %s — %s%s' % (s[0], url, '  [текст в кэше]' if cached_text_available(url) else ''))
    lines.append('Пост, как он уйдёт подписчику:')
    try:
        lines.extend('  | ' + l for l in format_post.render(card, comps).splitlines())
    except Exception as e:
        lines.append('  пост не собирается: %s' % e)
    f = findings(card, base)
    lines.append('Механические находки: %s' % ('нет' if not f else ''))
    lines.extend('  - %s' % t for _c, t in f)
    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Ответ читателя: проверка и применение

# Отрасли профилей на 11 сентября 2026 — та же таблица, что `INDUSTRIES` в
# static/index.html; к ней добавляется всё, что уже стоит у профилей базы.
KNOWN_INDUSTRIES = {
    'E-commerce', 'Автопром', 'Агро', 'Банки', 'ГМК и добыча', 'Гостиницы и туризм',
    'ЖКХ и обращение с отходами', 'Здравоохранение', 'ИТ и интернет', 'Искусственный интеллект',
    'Лесопром', 'Машиностроение', 'Медиа', 'Недвижимость', 'Нефть и газ', 'Образование',
    'Пищепром и напитки', 'Порты и инфраструктура', 'Потребительские товары', 'Производство тары',
    'Профессиональные услуги', 'Развлечения', 'Ритейл', 'Рынок ценных бумаг', 'Страхование',
    'Строительство', 'Телеком', 'Транспорт и логистика', 'Уголь', 'Управление активами',
    'Фармацевтика', 'Финансовые услуги', 'Финтех', 'Химия и удобрения', 'Холдинги', 'Энергетика',
    'Не определена'}


def industries(base):
    return KNOWN_INDUSTRIES | {c.get('ind') for c in base['companies'].values() if c.get('ind')}


def check_answer(ans, card, base):
    """Причины, по которым ответ принимать нельзя. Пусто — можно."""
    bad = []
    comps = base['companies']
    verdict = ans.get('verdict')
    if verdict not in ('accept', 'hold'):
        bad.append('verdict — accept или hold')
    if verdict == 'hold' and not str(ans.get('hold_reason') or '').strip():
        bad.append('hold без hold_reason — человеку нечего решать')
    if verdict == 'accept':
        cl = ans.get('checklist') or {}
        missing = [k for k in CHECKLIST if cl.get(k) is not True]
        if missing:
            bad.append('чек-лист не закрыт: %s' % ', '.join(missing))
    taken_roles = {r: card.get(idf) for r, (_tf, idf) in ROLES.items()}
    for p in ans.get('profiles') or []:
        role = p.get('role')
        if role not in ROLES:
            bad.append('profiles: роль %r не из target/buyer/seller' % role)
            continue
        if p.get('id'):
            if p['id'] not in comps:
                bad.append('profiles: профиля %s нет в базе' % p['id'])
            elif p['id'] in {v for r, v in taken_roles.items() if r != role and v}:
                bad.append('profiles: %s уже стоит в другой роли этой карточки' % p['id'])
            continue
        name = str(p.get('name') or '').strip()
        if not name:
            bad.append('profiles: у нового профиля нет имени')
            continue
        if '"' in name:
            bad.append('profiles: прямые кавычки в имени %r' % name)
        if review.ASSET_IS_A_DESCRIPTION.search(name):
            bad.append('profiles: %r — описание, а не имя компании' % name)
        fixed, changed = casing.to_nominative_asset(name)
        if changed:
            bad.append('profiles: имя %r в косвенном падеже (%r)' % (name, fixed))
        key = link_parties.company_key(name)
        twins = [cid for cid, c in comps.items() if len(key) >= 3 and link_parties.company_key(c.get('name')) == key]
        if twins:
            bad.append('profiles: %r — уже есть профиль %s, привяжите его вместо нового' % (name, twins))
        desc = str(p.get('desc') or '')
        if len(desc) < 20:
            bad.append('profiles: у %r нет описания (что это за компания)' % name)
        if proofread.press_attribution(desc):
            bad.append('profiles: описание %r с пресс-атрибуцией' % name)
        if p.get('ind') and p['ind'] not in industries(base):
            bad.append('profiles: отрасль %r не из списка' % p['ind'])
    for role, reason in (ans.get('no_profile') or {}).items():
        if role not in ROLES:
            bad.append('no_profile: роль %r не из target/buyer/seller' % role)
        elif not str(reason or '').strip():
            bad.append('no_profile: у %s нет причины' % role)
    title = ans.get('title')
    if title:
        old_blob = ' '.join(str(card.get(k) or '') for k in ('title', 'asset', 'buyer_name', 'seller', 'extra'))
        old_blob += ' ' + ' '.join(str(_text(card, f) or '') for f in PROSE_FIELDS)
        for p in ans.get('profiles') or []:
            old_blob += ' ' + str(p.get('name') or '') + ' ' + str(comps.get(p.get('id'), {}).get('name') or '')
        for ref in (card.get('target'), card.get('asset_id'), card.get('buyer'), card.get('seller_id')):
            old_blob += ' ' + str(comps.get(ref, {}).get('name') or '')
        known = proofread.all_words(old_blob)
        for w in _title_words(title):
            if not any(proofread.name_match(w, k) for k in known):
                bad.append('title: имя %r не встречается в карточке — новых имён в заголовке быть не может' % w)
        for n in proofread.numbers(title) - proofread.numbers(old_blob):
            bad.append('title: числа %r нет в карточке' % n)
        if '"' in title:
            bad.append('title: прямые кавычки')
        if not (20 <= len(title) <= 180):
            bad.append('title: длина вне 20–180 знаков')
    asset = ans.get('asset')
    if asset:
        fixed, changed = casing.to_nominative_asset(asset)
        if changed:
            bad.append('asset: косвенный падеж, ожидалось %r' % fixed)
        if review.ASSET_IS_A_DESCRIPTION.search(asset):
            bad.append('asset: описание вместо имени')
        if '"' in asset:
            bad.append('asset: прямые кавычки')
    share = ans.get('share')
    if share:
        if proofread.press_attribution(share):
            bad.append('share: пресс-атрибуция')
        card_blob = ' '.join(str(card.get(k) or '') for k in ('title', 'sum', 'asset', 'extra')) \
            + ' ' + ' '.join(str(_text(card, f) or '') for f in PROSE_FIELDS)
        for n in proofread.numbers(share) - proofread.numbers(card_blob):
            bad.append('share: числа %r нет в карточке' % n)
    status = ans.get('status')
    if status and status not in review.STATUS_WORDS:
        bad.append('status: %r не из списка статусов' % status)
    for s in ans.get('src_add') or []:
        if not (isinstance(s, list) and len(s) == 2 and str(s[1]).startswith('http')):
            bad.append('src_add: ожидается пара [имя, http-адрес]')
        elif any(len(x) > 1 and x[1] == s[1] for x in card.get('src') or []):
            bad.append('src_add: адрес уже в источниках: %s' % s[1])
    return bad


def apply_answer(ans, card, base, day=None):
    """Применяет проверенный ответ к карточке. Возвращает строки отчёта и
    признак «штамп поставлен»."""
    comps = base['companies']
    lines = []
    for p in ans.get('profiles') or []:
        role = p['role']
        tf, idf = ROLES[role]
        cid = p.get('id')
        if not cid:
            cid = _new_profile_id(base, p['name'])
            comps[cid] = {'name': p['name'], 'ind': p.get('ind') or card.get('ind') or 'Не определена',
                          'desc': p['desc'], 'kpi': []}
            if p.get('group'):
                comps[cid]['group'] = True
            keys = p.get('match_keys') or []
            if keys:
                base.setdefault('match_keys', {})[cid] = list(keys)
            lines.append('профиль %s: %s' % (cid, p['name']))
        card[idf] = cid
        if role == 'buyer':
            card.pop('buyer_name', None)
        elif role == 'target':
            card.pop('asset_id', None)
            if not has(card.get('asset')) and not ans.get('asset'):
                card['asset'] = comps[cid]['name']
        lines.append('%s -> %s (%s)' % (role, cid, comps[cid]['name']))
    for k in ('title', 'asset', 'status'):
        if ans.get(k) and card.get(k) != ans[k]:
            lines.append('%s: %r -> %r' % (k, card.get(k), ans[k]))
            card[k] = ans[k]
    if ans.get('share'):
        card.setdefault('eco', {})['share'] = ans['share']
        lines.append('eco.share -> %r' % ans['share'])
    for s in ans.get('src_add') or []:
        label = s[0] if has(s[0]) and not re.match(r'^(tg|web):', str(s[0])) else source_names.edition_label(s[1])
        card.setdefault('src', []).append([label, s[1]])
        lines.append('src + %s' % s[1])
    waived = ans.get('no_profile') or {}
    left = findings(card, base, waived=waived)
    if ans.get('verdict') == 'accept' and not left:
        card[STAMP] = day or date.today().isoformat()
        notes = {k: v for k, v in (('no_profile', waived), ('notes', ans.get('notes'))) if v}
        if notes:
            card[STAMP + '_notes'] = notes
        lines.append('ПРИНЯТА (%s)' % card[STAMP])
        return lines, True
    if ans.get('verdict') == 'hold':
        card['hold_reason'] = ans['hold_reason']
        lines.append('НА РЕШЕНИЕ ЧЕЛОВЕКУ: %s' % ans['hold_reason'])
    else:
        lines.append('штамп НЕ поставлен — остались находки: ' + '; '.join(t for _c, t in left))
    return lines, False


def _new_profile_id(base, name):
    import hashlib
    for n in range(1000):
        cid = 'g' + hashlib.sha1(('%s|%d' % (name, n)).encode('utf-8')).hexdigest()[:8]
        if cid not in base['companies']:
            return cid
    raise RuntimeError('не удалось выбрать id профиля')


# ---------------------------------------------------------------------------
# Правила проверяются на себе

def _self_check():
    base = {'companies': {'gsb': {'name': 'ПАО «Совкомбанк»', 'ind': 'Банки', 'desc': 'Банк.'}},
            'deals': [], 'telegram_posts': {}}
    card = {'id': 'gtest', 'title': '«Совко капитал партнерс» нарастил долю в Совкомбанке за счет акционера',
            'type': 'M&A', 'date': '2026-09-09', 'status': 'Обсуждается', 'buyer_name': '«Совко капитал партнерс»',
            'src': [['Ведомости', 'https://www.vedomosti.ru/x']],
            'eco': {'rationale': 'По оценке компании, объем рынка может достичь 8 млрд рублей.'},
            'law': {'struct': 'Книгу заявок закрыли семь инвесторов, пишут «Ведомости».'}}
    codes = {c for c, _t in findings(card, base)}
    assert 'party_unlinked:buyer' in codes and 'asset_missing' in codes and 'why' in codes, codes
    assert any(c.startswith('press:') for c in codes), codes
    # Описание вместо имени, близнец, чужое имя в заголовке — отказ.
    bad = check_answer({'verdict': 'accept', 'checklist': {k: True for k in CHECKLIST},
                        'profiles': [{'role': 'buyer', 'name': 'компания-разработчик решений в области ИБ', 'desc': 'x' * 30},
                                     {'role': 'target', 'name': 'Совкомбанк', 'desc': 'y' * 30}],
                        'title': 'Иванов купил долю в Совкомбанке'}, card, base)
    assert any('описание' in b for b in bad) and any('уже есть профиль' in b for b in bad) \
        and any('Иванов' in b for b in bad), bad
    # hold без причины, accept с незакрытым чек-листом — отказ.
    assert check_answer({'verdict': 'hold'}, card, base)
    assert any('чек-лист' in b for b in check_answer({'verdict': 'accept', 'checklist': {}}, card, base))
    # Верный ответ: привязка, новый профиль, честная пустота у продавца — штамп.
    ok = {'verdict': 'accept', 'checklist': {k: True for k in CHECKLIST},
          'profiles': [{'role': 'target', 'id': 'gsb'},
                       {'role': 'buyer', 'name': '«Совко Капитал Партнерс»', 'ind': 'Холдинги',
                        'desc': 'Холдинговая компания основных акционеров Совкомбанка.', 'group': True}],
          'no_profile': {'seller': 'один из акционеров, имя не раскрыто'},
          'title': '«Совко Капитал Партнерс» увеличил долю в Совкомбанке',
          'asset': 'акции Совкомбанка', 'status': 'Закрыта',
          'src_add': [['Совкомбанк', 'https://sovcombank.ru/press']]}
    assert not check_answer(ok, card, base), check_answer(ok, card, base)
    # Но проза ещё с пресс-языком и «Зачем» о рынке — штампа нет, пока не вычитано.
    _lines, stamped = apply_answer(json.loads(json.dumps(ok)), json.loads(json.dumps(card)), json.loads(json.dumps(base)))
    assert not stamped, _lines
    card2 = json.loads(json.dumps(card))
    card2['law']['struct'] = 'Пакет продан в формате ускоренного формирования книги заявок.'
    card2['eco']['rationale'] = '—'
    base2 = json.loads(json.dumps(base))
    lines, stamped = apply_answer(json.loads(json.dumps(ok)), card2, base2, day='2026-09-11')
    assert stamped and card2[STAMP] == '2026-09-11' and card2['target'] == 'gsb' and card2.get('buyer') \
        and 'buyer_name' not in card2 and len(base2['companies']) == 2, (lines, card2)
    assert card2['accepted_notes']['no_profile']['seller']
    assert not findings(card2, base2), findings(card2, base2)
    return True


# ---------------------------------------------------------------------------

def main(argv):
    if '--self-check' in argv:
        _self_check()
        print('Самопроверка приёмки пройдена.')
        return 0
    base, pending = load()
    if '--queue' in argv:
        rest = [a for a in argv if a != '--queue']
        cards = queue(base, pending)
        if rest:
            cards = [c for c in cards if c['id'] in rest] or \
                [c for c in (find_card(r, base, pending)[0] for r in rest) if c]
        print('Ждут приёмки: %d' % len(cards))
        for c in cards:
            print(dossier(c, base))
        return 0
    path = next((a for a in argv if a.endswith('.json')), None)
    if not path:
        print(__doc__)
        return 1
    answers = json.load(open(path, encoding='utf-8'))
    if not isinstance(answers, list):
        print('Файл ответов обязан быть списком объектов с id и verdict.')
        return 1
    _self_check()
    write = '--write' in argv
    apply = '--apply' in argv
    refused, stamped, changed = 0, 0, 0
    for ans in answers:
        card, where = find_card(str(ans.get('id')), base, pending)
        if not card:
            print('  ОТКАЗ  %s: карточки нет ни в базе, ни в очереди' % ans.get('id'))
            refused += 1
            continue
        bad = check_answer(ans, card, base)
        if bad:
            refused += 1
            print('  ОТКАЗ  %s (%s):' % (card['id'], where))
            for b in bad:
                print('         - %s' % b)
            continue
        if not apply:
            left = findings(card, base, waived=ans.get('no_profile') or {})
            print('  ГОДЕН  %s (%s)%s' % (card['id'], where,
                                          '' if not left else ' — но штамп не встанет, пока есть: ' + '; '.join(t for _c, t in left)))
            continue
        lines, ok = apply_answer(ans, card, base)
        changed += 1
        stamped += int(ok)
        print('  %s %s (%s)' % ('ПРИНЯТА' if ok else 'ПРАВКИ ', card['id'], where))
        for l in lines:
            print('         %s' % l)
    print('\nответов %d, отказов %d, применено %d, штампов %d' % (len(answers), refused, changed, stamped))
    if apply and write and changed:
        save(base, pending)
        print('Записано.')
    elif apply and changed:
        print('Сухой прогон. Запись — с ключом --write.')
    return 1 if refused else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
