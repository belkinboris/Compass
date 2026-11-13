# -*- coding: utf-8 -*-
"""Приток, шаг 7: применить решения владельца и партнера к черновикам.

ОТКУДА РЕШЕНИЯ. Кнопки и ответы в Telegram приходят вебхуком на сайт, сайт
пишет их в таблицу; этот скрипт забирает их по публичному API
(`/api/moderation/decisions?token=…`) — потому что напрямую до базы сайта из
контейнера рутины не достать: она в приватной сети хостинга.

ТРИ ИСХОДА ПО КАЖДОМУ ЧЕРНОВИКУ:
  * «Опубликовать» (или ответ с текстом) — карточка переносится в базу; если
    в ответе был текст, он ложится в `post_override` и канал получит именно
    его, а не автоформат;
  * «Придержать» — черновик остается в pending с пометкой `held`, больше не
    рассылается и не публикуется по таймауту; снять пометку — руками;
  * МОЛЧАНИЕ — карточка ждет. С 12 ноября 2026 молчание НЕ публикует
    (владелец: «Отмени правило молчания 1 день что выпускается пост. Теперь
    если вдруг мы не отреагировали, то пиши мне и артему в личку, что
    такой-то пост не опубликован»). Через сутки без решения
    `pipeline/publish/remind_undecided.py` пишет владельцу и партнеру в личку.

ДВА ШАГА, НЕ ОДИН. `--write` только применяет решения ЛОКАЛЬНО (пишет
`pending.json`/`deals_promoted.json`/состояние) — сайту, что решение
применено, говорит НЕ он, а отдельный `--consume`, который рутина обязана
вызвать ПОСЛЕДНИМ, после успешного `git push`. Раньше `--write` подтверждал
сайту сразу — и решение по Wegosty (17 августа) потерялось: контейнер умер
между локальной записью и push, сайт уже необратимо считал решение
примененным, а результат исчез вместе с контейнером. Подробности — docstring
`consume_pending`.

Запуск:
    python3 pipeline/ingest/approve.py             # сухой прогон
    python3 pipeline/ingest/approve.py --write     # применить локально
    python3 pipeline/ingest/approve.py --consume   # подтвердить сайту — ПОСЛЕ push
"""
import json
import subprocess
import os
import time
import sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'publish'))

import format_post                                        # noqa: E402
import promote                                            # noqa: E402
import readiness                                          # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
# Сколько часов показанная карточка ждет решения, прежде чем о ней напомнят
# в личку (remind_undecided.py). Молчание НЕ публикует с 12 ноября 2026.
REMIND_HOURS = 24


def fetch_decisions():
    """Решения с сайта. Сайт недоступен — вернем пусто и скажем об этом:
    таймауты все равно применимы, а решения дождутся следующего прогона."""
    site = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')
    token = os.environ.get('MODERATION_TOKEN') or os.environ.get('TELEGRAM_WEBHOOK_SECRET') or ''
    if not token:
        print('MODERATION_TOKEN/TELEGRAM_WEBHOOK_SECRET не заданы — решения не прочитать.')
        return [], None
    # Связь контейнера с сайтом рвется (13 ноября 2026: публикация пять раз
    # подряд не прочитала решения) — пять попыток с паузой, прежде чем сдаться.
    import time
    tries = 1 if os.environ.get('PYTEST_CURRENT_TEST') else 5
    err = None
    for attempt in range(tries):
        try:
            import httpx
            r = httpx.get('%s/api/moderation/decisions' % site, params={'token': token}, timeout=20)
            if r.status_code != 200:
                print('Сайт ответил %s на запрос решений — работаем без них.' % r.status_code)
                return [], None
            return normalize_channels(r.json().get('decisions', [])), (site, token)
        except Exception as e:
            err = e
            if attempt < tries - 1:
                time.sleep(4)
    print('Решения недоступны (%s) — работаем без них.' % err)
    return [], None


# Кнопки «🏠 Только недвижимость» / «📰 Только основной» под проектом поста
# (владелец, 10 ноября 2026): это одобрение поста с выбором канала. Для всех
# читателей решений это `post_yes`; канал едет рядом (`channels`) и
# записывается карточке в `post_channels` (pipeline/publish/channels.py).
CHANNEL_VERDICTS = {'post_realty': ['realty'], 'post_main': ['main']}


def normalize_channels(decisions):
    out = []
    for d in decisions or []:
        if d.get('verdict') in CHANNEL_VERDICTS:
            d = dict(d, channels=CHANNEL_VERDICTS[d['verdict']], verdict='post_yes')
        out.append(d)
    return out


def consume(handle, ids):
    """Сказать сайту «решения применены». True — сайт принял; False — нет.

    13 ноября 2026: связь контейнера с сайтом рвется, а запрос шел один раз и
    код ответа не читался — публикация писала «Сайту подтверждено», решения
    оставались живыми и три часа держали push остальных прогонов."""
    if not (handle and ids):
        return True
    site, token = handle
    import httpx
    tries = 1 if os.environ.get('PYTEST_CURRENT_TEST') else 5
    err = None
    for n in range(tries):
        try:
            r = httpx.post('%s/api/moderation/decisions/consume' % site,
                           json={'token': token, 'ids': ids}, timeout=20)
            if r.status_code < 300:
                return True
            err = 'сайт ответил %s' % r.status_code
        except Exception as e:
            err = e
        if n + 1 < tries:
            time.sleep(4)
    print('НЕ ПОДТВЕРЖДЕНО сайту: решения не помечены примененными (%s). '
          'Повторное применение ничего не ломает; подтвердит следующий прогон.' % err)
    return False


PENDING_CONSUME = os.path.join(ROOT, 'data', 'inbox', 'consume_pending.json')


def foreign_decision(d):
    """Решение не о карточке очереди: этап, сводка, правка поста, ИНН."""
    return '~' in str(d.get('deal_id') or '')


def unproven(detail, base=None):
    """Решения, результата которых нет в базе на origin/main.

    post_yes — карточка в базе с `post_approved` (или пост уже вышел);
    post_no / post_hold — `no_post` / `post_held` (или пост вышел); approve —
    карточка в базе. Остальные виды (сырье, этапы, заметки) здесь не
    проверяются: их результат живет не в базе."""
    if base is None:
        try:
            subprocess.run(['git', 'fetch', '-q', 'origin', 'main'], cwd=ROOT, timeout=120)
            raw = subprocess.run(['git', 'show', 'origin/main:static/data/deals_promoted.json'], cwd=ROOT,
                                 capture_output=True, text=True, timeout=120).stdout
            base = json.loads(raw)
        except Exception as e:  # не прочитали main — ничего не гасим вслепую
            print('origin/main не прочитан (%s) — подтверждение отложено целиком.' % e)
            return list(detail)
    deals = {d['id']: d for d in base.get('deals') or []}
    posted = set(base.get('telegram_posts') or {})
    try:
        queued = {c.get('id') for c in json.load(open(PENDING, encoding='utf-8')).get('cards') or []}
    except Exception:
        queued = set()
    out = []
    for d in detail:
        did, v = d.get('deal_id'), d.get('verdict')
        card = deals.get(did)
        if v in ('post_yes', 'post_realty', 'post_main'):
            ok = did in posted or (card is not None and card.get('post_approved'))
        elif v == 'post_no':
            ok = did in posted or (card is not None and card.get('no_post'))
        elif v == 'post_hold':
            ok = did in posted or (card is not None and card.get('post_held'))
        elif v == 'approve':
            # карточка вышла — или осталась в очереди (придержана приемкой):
            # решение ей записано, держать его живым на сайте незачем
            ok = card is not None or did in queued
            if d.get('has_text') and card is not None and did not in queued:
                ok = bool(card.get('post_override'))
        else:
            ok = True
        if not ok:
            out.append(d)
    return out


def consume_pending():
    """Второй, ОТДЕЛЬНЫЙ шаг: сказать сайту «решения применены» — только
    ПОСЛЕ того, как результат `--write` пережил git push.

    ПОЧЕМУ ОТДЕЛЬНЫЙ ШАГ. `--write` раньше вызывал `consume()` сам, сразу
    после локальной записи, — а git commit/push идет дальше по рутине,
    отдельными шагами. Умер контейнер в этом окне (как и было с
    решением по Wegosty 17 августа) — сайт уже необратимо считает решение
    примененным, а локальный результат исчез вместе с контейнером: следующий
    прогон его не увидит и не повторит. Инвариант: необратимая отметка
    ставится только после того, как результат УЖЕ пережил смерть контейнера.
    `--write` теперь кладет id примененных решений в файл рядом (не в git —
    он нужен только внутри одного прогона, между `--write` и этим шагом);
    рутина вызывает `approve.py --consume` ПОСЛЕДНИМ, после `git push`.

    ЕСЛИ ЭТОТ ШАГ НЕ ВЫЗВАН ВООБЩЕ (контейнер умер до него) — не страшно и
    не теряется: `plan_raw`/`plan_actions` следующего прогона видят решение
    снова живым на сайте, но `decided_raw`/состав базы уже подтверждают, что
    оно применено (закоммичено), — карточка не создастся дважды (см.
    docstring `plan_raw`), и следующий прогон просто консьюмит его заново."""
    if not os.path.exists(PENDING_CONSUME):
        print('Нечего подтверждать — файла %s нет.' % PENDING_CONSUME)
        return 0
    saved = json.load(open(PENDING_CONSUME, encoding='utf-8'))
    site, token, ids = saved.get('site'), saved.get('token'), saved.get('ids') or []
    if not (site and token and ids):
        os.remove(PENDING_CONSUME)
        return 0
    # ПОДТВЕРЖДАЕМ САЙТУ ТОЛЬКО ТО, ЧТО ВИДНО В origin/main (11 ноября 2026).
    # Решения «📣 Пост в канал» по «АГР Холдингу» и Hefei Hengyi пропали: их
    # погасили на сайте, а в main отметки `post_approved` так и не оказалось
    # (прогон публикации остановился на красном тесте, правка в его рабочей
    # копии не дожила до push, а подтверждение ушло). Владелец: «не может же
    # так получаться, что посты не выходят и потом теряются». Теперь каждое
    # решение о посте и о карточке сверяется с базой на origin/main; не видно
    # результата — решение остается живым на сайте, следующий прогон применит
    # его заново (применение идемпотентно).
    keep = unproven(saved.get('detail') or [])
    if keep:
        print('НЕ ПОДТВЕРЖДАЮ сайту %d решений: их результата нет в origin/main — применит следующий прогон: %s'
              % (len(keep), ', '.join('%s %s' % (d['verdict'], d['deal_id']) for d in keep)))
        ids = [i for i in ids if i not in {d['id'] for d in keep}]
    if not consume((site, token), ids):
        return 1        # файл остается: следующий `--consume` повторит
    os.remove(PENDING_CONSUME)
    # Ответы владельцу на «Добавить в карточку» / «Это другая сделка» — только
    # теперь, когда записанное пережило push (то же правило, что «поправлено»
    # в ответах на заметки: не раньше, чем правка в origin/main).
    if saved.get('answers'):
        import drop_pending
        drop_pending.notify_console(saved['answers'])
    print('Подтверждено примененных решений: %d.' % len(ids))
    return 0


def hours_pending(card, now):
    """Одно определение — readiness.hours_pending (отсчет от pending_since,
    иначе от приемки или чтения)."""
    return readiness.hours_pending(card, now)


# Вердикты и их роли. КАРТОЧНЫЕ решают судьбу карточки (approve/hold);
# ПОСТОВЫЕ — модификатор канала (post_yes/post_no: выйдет ли пост, когда
# карточка выйдет); СЫРЬЕВЫЕ (take/drop) относятся к черновикам, которые
# ворота не пропустили; 'note' — заметка для рутины притока, approve ее НЕ
# потребляет и НЕ трактует. Смешение ролей уже стреляло: старый код считал
# «любой не-approve вердикт» придержанием, и post_no придержал бы карточку.
CARD_VERDICTS = {'approve', 'hold', 'discard'}
POST_VERDICTS = {'post_yes', 'post_no', 'post_hold'}   # post_hold — пост придержан (10 ноября 2026)
RAW_VERDICTS = {'take', 'drop'}
ORPHAN_MAX_DAYS = 7                     # решение по сырью без черновика дольше этого — устарело


def _old_ids_for(draft, sent_titles):
    """Прежние номера той же новости (по ключу заголовка) среди показанных."""
    key = promote.raw_key(draft.get('title'))
    return [did for did, title in (sent_titles or {}).items()
            if did != str(draft.get('draft_id')) and promote.raw_key(title) == key]


def _older_than(decision, now, days):
    try:
        made = datetime.fromisoformat(str(decision.get('created_at')))
        if made.tzinfo is None:
            made = made.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return False
    return (now - made) > timedelta(days=days)


def last_by_deal(decisions, verdicts):
    """Последнее по времени решение нужного класса на каждый id."""
    result = {}
    for d in decisions:                      # список уже упорядочен по created_at
        if d['verdict'] in verdicts:
            result[d['deal_id']] = d
    return result


def late_decisions(deals, cards, decisions):
    """Карточные решения по карточкам, которых в очереди уже нет, а в базе —
    есть: владелец нажал «выкинуть» (или «придержать») ПОСЛЕ того, как
    карточка вышла на сайт. Раньше такие решения не применялись и молча
    гасились на сайте (`g4f594e81`, 27 октября 2026; бэклог H1).
    Возвращает [(карточка из базы, решение)]."""
    in_queue = {c['id'] for c in cards}
    by_deal = last_by_deal(decisions, CARD_VERDICTS)
    out = []
    for deal in deals:
        d = by_deal.get(deal.get('id'))
        if d and deal['id'] not in in_queue:
            out.append((deal, d))
    return out


def apply_late_discard(data, state, deal, now):
    """Снять уже опубликованную карточку по позднему «выкинуть»: как сделал
    бы approve.py, увидев решение вовремя. Пост в канале (если был) остается —
    его удаление решает человек; отметка `telegram_posts` не трогается."""
    data['deals'] = [x for x in data['deals'] if x['id'] != deal['id']]
    for s in deal.get('src') or []:
        if len(s) > 1 and str(s[1]).startswith('http'):
            state.setdefault('discarded_urls', {})[str(s[1])] = {
                'id': deal['id'], 'title': deal.get('title'),
                'at': now.isoformat(timespec='seconds'), 'by': 'late_discard'}


def dead_ends(cards, comps=None):
    """Готовые, но не показанные карточки (readiness `ready_unsent`): ждущая
    второго чтения, приемки или переприемки — очередь притока, а не тупик,
    и здесь ее нет. Поправленная после показа и заново принятая (`reshow`,
    D7) — тоже ждет показа новой версии."""
    return [c for c in cards if readiness.state(c, comps) in ('ready_unsent', 'reshow')]


def plan_actions(cards, decisions, now, comps=None):
    """(публикуем, придерживаем, ждем) — чистая функция, ее держат тесты.
    `comps` — справочник компаний: с ним отпечаток приемки сверяется и по
    именам профилей сторон (readiness.fingerprint).

    Ответ с текстом на сообщение [пост <id>] приходит вердиктом 'approve' с
    edited_text — правя пост, человек одновременно одобряет карточку."""
    by_deal = last_by_deal(decisions, CARD_VERDICTS)
    # ОДОБРЕННЫЙ ОБЩИЙ ПОСТ ВЫПУСКАЕТ ВСЕ СВОИ КАРТОЧКИ. У общего поста
    # (`post_covers`, указ № 738) кнопка одна — «📣 Пост одобрен», и
    # нажавший ее одобрил и сделки, о которых пост. Раньше это был только
    # модификатор канала: 16 октября 2026 партнер одобрил пост утром,
    # карточки ждали суток молчания, пост ждал карточек — к ночи не вышло
    # ничего. Свое карточное решение («придержать», «выкинуть») сильнее.
    post_mod = last_by_deal(decisions, POST_VERDICTS)
    joint_ok = {}
    for card in cards:
        if card.get('post_covers') and (post_mod.get(card['id']) or {}).get('verdict') == 'post_yes':
            for cid in card['post_covers']:
                joint_ok[cid] = card['id']
    publish, hold, wait, discard = [], [], [], []
    for card in cards:
        decision = by_deal.get(card['id'])
        if decision and decision['verdict'] == 'approve':
            publish.append((card, decision.get('edited_text'), 'решение: опубликовать'))
        elif not decision and card['id'] in joint_ok:
            publish.append((card, None, 'решение: одобрен общий пост (%s)' % joint_ok[card['id']]))
        elif decision and decision['verdict'] == 'discard':
            # «Выкинуть» сильнее «придержать»: карточка не выйдет никуда и
            # исчезает из очереди насовсем. Просьба владельца 6 августа: у
            # нероссийского контура и не-M&A «придержать» оставляло бы мусор
            # висеть в очереди вечно.
            discard.append((card, 'решение: выкинуть'))
        elif decision:
            hold.append((card, 'решение: придержать'))
        else:
            # ЧЕГО ЖДЕТ КАРТОЧКА — ОДНО МЕСТО: readiness.state (31 октября 2026).
            # До 12 ноября 2026 молчание публиковало только ПОКАЗАННУЮ, прочитанную и принятую
            # карточку; все остальное ждет с текстом по состоянию. Что здесь
            # жило и живет:
            # — НЕПРОЧИТАННАЯ НЕ ВЫХОДИТ ПО МОЛЧАНИЮ — главная защита от
            #   косячных карточек: черновик рождается из заголовка, владелец
            #   9 августа нашел в трех таких карточках каркасный дефект
            #   («Инвестиция» у покупки 100%, «Внуково» в прямых кавычках).
            #   Молчание — согласие на ПРОЧИТАННУЮ карточку (review.py).
            # — ПРИЕМКА (11 сентября 2026): без штампа accept_card.py консоль
            #   карточку и не показывала, так что «молчание» — не согласие,
            #   а отсутствие вопроса.
            # — ВТОРОЕ ЧТЕНИЕ: принятая с 9 октября без `second_read` ждет
            #   приток, а не владельца (раньше approve этого не знал и печатал
            #   «ждем решения» и «ТУПИК»).
            # — НЕ ПРОПУЩЕННАЯ ПРИЕМКОЙ (`hold_reason`) ждет решения человека:
            #   консоль обещает «без вашего слова не публикуются никогда».
            # — НЕ ПОКАЗАННАЯ по молчанию не выходит: молчание — согласие
            #   только того, кто сообщение получил.
            # Явное решение владельца («опубликовать») выше всех этих веток.
            # — С 12 НОЯБРЯ 2026 МОЛЧАНИЕ НЕ ПУБЛИКУЕТ НИЧЕГО (решение
            #   владельца): показанная карточка ждет кнопки или ответа, а
            #   через сутки remind_undecided.py напоминает в личку.
            st = readiness.state(card, comps)
            if st == 'shown':
                wait.append((card, 'ждет решения %.0f ч' % hours_pending(card, now)))
            else:
                wait.append((card, readiness.WAIT_TEXT[st]))
    return publish, hold, wait, discard


def plan_raw(drafts, decisions, decided_raw=None, sent_titles=None):
    """(в работу, отброшено) для сырья. По молчанию сырье НЕ публикуется:
    ворота его не пропустили, и молчание не делает его сделкой.

    `decided_raw` — уже примененные решения (`moderation_state.json`).
    Решение с сайта считается ЖИВЫМ, пока сайт не подтвердит, что оно
    применено (`consume`, теперь отдельный шаг ПОСЛЕ git push — см. `main`
    и docstring `consume_pending`). Если контейнер умер до этого шага,
    следующий прогон увидит то же «живое» решение еще раз — а draft
    `to_card()` каждый раз рождает НОВЫЙ случайный id, значит повторное
    применение создало бы ВТОРУЮ карточку того же черновика. Эта проверка
    — не про сеть и не про сырье-задвоение (для того — дедуп по draft_id в
    `main`), а про то, что РЕШЕНИЕ уже необратимо записано локально и в
    git: раз оно есть в `decided_raw`, повторно его применять нельзя,
    какой бы ответ ни пришел с сайта."""
    by_draft = last_by_deal(decisions, RAW_VERDICTS)
    decided_raw = decided_raw or {}
    # РЕШЕНИЕ ПО СТАРОМУ НОМЕРУ НАХОДИТ НОВОСТЬ ПО ЗАГОЛОВКУ (28 октября
    # 2026). Номер сырья менялся от прогона к прогону (draft.draft_id_for),
    # и нажатие по номеру из вчерашнего сообщения не находило ничего.
    # send_drafts запоминает «номер -> заголовок» показанного сырья
    # (`raw_sent_titles`); решение по номеру, которого в hold нет, переходит
    # на черновик с тем же ключом заголовка. Прямое попадание по номеру
    # всегда сильнее.
    present = {str(d.get('draft_id')) for d in drafts}
    by_key = {}
    for did, decision in by_draft.items():
        if did in present or did in decided_raw:
            continue
        title = (sent_titles or {}).get(did)
        if title:
            by_key.setdefault(promote.raw_key(title), decision)
    take, drop = [], []
    for draft in drafts:
        did = str(draft.get('draft_id'))
        if did in decided_raw:
            continue
        decision = by_draft.get(did) or by_key.get(promote.raw_key(draft.get('title')))
        if decision and decision['verdict'] == 'take':
            take.append(draft)
        elif decision:
            drop.append(draft)
    return take, drop


def main(write=False):
    if not os.path.exists(PENDING):
        print('Черновиков нет.')
        return 0
    pending = json.load(open(PENDING, encoding='utf-8'))
    decisions, handle = fetch_decisions()
    now = datetime.now(timezone.utc)
    base_now = json.load(open(DATA, encoding='utf-8'))
    publish, hold, wait, discard = plan_actions(pending['cards'], decisions, now, base_now.get('companies') or {})
    late = late_decisions(base_now['deals'], pending['cards'], decisions)
    for deal, d in late:
        posted = deal['id'] in (base_now.get('telegram_posts') or {})
        print('  ПОЗДНЕЕ РЕШЕНИЕ по опубликованной %-11s %s — %s%s'
              % (deal['id'], str(deal.get('title') or '')[:56],
                 {'discard': 'снимаем с сайта', 'hold': 'уже вышла, придержать нечего',
                  'approve': ('текст владельца станет текстом поста'
                              if str(d.get('edited_text') or '').strip() else 'уже вышла')}.get(d['verdict'], d['verdict']),
                 '; пост в канале был — удалите руками, если нужно' if posted and d['verdict'] == 'discard' else ''))
    # ГОТОВАЯ КАРТОЧКА, КОТОРУЮ ВЛАДЕЛЕЦ НЕ ВИДЕЛ, — ТУПИК, А НЕ ОЧЕРЕДЬ
    # (27 октября 2026: 13 принятых карточек трое суток не показывались;
    # владелец — «если карточка готова, в чем проблема ее показать?»).
    # Сухой прогон approve.py — первый шаг каждого прогона публикации, и он
    # называет такие карточки по имени: следующий шаг — send_drafts.py --write.
    for card in dead_ends(pending['cards'], base_now.get('companies') or {}):
        print('  ТУПИК: %s «%s» — готова, но в консоли не показана: '
              'python3 pipeline/ingest/send_drafts.py --write' % (card['id'], str(card.get('title') or '')[:70]))

    # СЫРЬЕ РАЗБИРАЕТСЯ ДО СУХОГО ПРОГОНА. Раньше решения по сырью («это
    # сделка — в работу» / «не сделка») применялись только под `--write`, а
    # сухой прогон о них молчал: проверить, дойдет ли нажатие, было нечем —
    # ровно тот случай, когда «ничего не напечатало» неотличимо от «нечего
    # делать».
    import promote
    state = promote.load_state()
    decided_raw = state.get('decided_raw', {})
    # Одно и то же недорешенное сырье переносится вперед КАЖДЫЙ день, пока
    # по нему нет решения (иначе оно бы пропадало из консоли, не дождавшись
    # ответа) — draft_id d59961733 (Wegosty/tadviser) лежал сразу в трех
    # дневных файлах (18, 19, 21 августа). Без дедупликации по draft_id
    # `plan_raw` находил его в списке трижды, и единственное решение «в
    # работу» превращалось в ТРИ карточки-близнеца с тремя разными id (найдено
    # 21 августа: g855e50b1/gf544dd13/g5cba276f — один и тот же черновик).
    # Держим первое найденное вхождение — содержание одинаковое, id решает.
    raw_all = []
    seen_draft_ids = set()
    hold_dir = os.path.join(ROOT, 'data', 'inbox', 'hold')
    if os.path.isdir(hold_dir):
        for name in sorted(os.listdir(hold_dir)):
            if name.endswith('.json'):
                for draft in json.load(open(os.path.join(hold_dir, name),
                                            encoding='utf-8')).get('drafts', []):
                    did = str(draft.get('draft_id'))
                    if did not in seen_draft_ids:
                        seen_draft_ids.add(did)
                        raw_all.append(draft)
    taken, dropped = plan_raw(raw_all, decisions, decided_raw, state.get('raw_sent_titles') or {})
    # ПРЕДЛОЖЕНИЯ «К КАРТОЧКЕ … ДОБАВИТЬ» (card_news.py, 6 ноября 2026):
    # кнопки «Добавить в карточку» / «Новый этап сделки» / «Это другая
    # сделка». Запись предложения лежит в moderation_state.json (в git), так
    # что ее видит любой контейнер; решение без записи — не наше, сайту
    # остается живым, как сырье без черновика.
    import card_news
    offers, offers_orphan = [], []
    for nid, d in card_news.decided_offers(decisions).items():
        entry = card_news.book(state).get(nid)
        if entry is None:
            offers_orphan.append(d)
        elif entry.get('outcome') != 'decided':
            offers.append((entry, d))
    # РЕШЕНИЕ, КОТОРОЕ НЕКУДА ПРИМЕНИТЬ, НЕЛЬЗЯ ОБЪЯВЛЯТЬ ПРИМЕНЕННЫМ.
    # Сырье лежит в `data/inbox/hold/` — а эта папка не хранится в git и
    # живет на диске той рутины, которая ее создала. Прогон в другом
    # контейнере черновика не видит, `plan_raw` его молча пропускает — и до
    # 7 сентября 2026 `--consume` все равно подтверждал сайту ВСЕ решения
    # подряд, включая непримененные: нажатие владельца исчезало без следа и
    # без единой строки в отчете. Такие решения оставляем сайту живыми (их
    # применит рутина, у которой черновик есть) и называем вслух.
    applied_keys = {promote.raw_key(d.get('title')) for d in taken + dropped}
    sent_titles = state.get('raw_sent_titles') or {}

    def _retargeted(d):
        title = sent_titles.get(str(d['deal_id']))
        return bool(title) and promote.raw_key(title) in applied_keys

    orphan = [d for d in decisions
              if d['verdict'] in RAW_VERDICTS
              and str(d['deal_id']) not in seen_draft_ids
              and str(d['deal_id']) not in decided_raw
              and not _retargeted(d)]

    for card, override, why in publish:
        print('  ПУБЛИКУЕМ   %-11s %s%s' % (card['id'], str(card.get('title'))[:56],
                                            ' [текст поста заменён]' if override else ''))
        print('              %s' % why)
    for card, why in hold:
        print('  ПРИДЕРЖАНА  %-11s %s' % (card['id'], why))
    for card, why in discard:
        print('  ВЫКИНУТА    %-11s %s' % (card['id'], str(card.get('title'))[:56]))
    for card, why in wait:
        print('  ЖДЕТ        %-11s %s' % (card['id'], why))

    for draft in taken:
        print('  В РАБОТУ    %-11s %s' % (draft['draft_id'], str(draft.get('title'))[:56]))
    for entry, d in offers:
        print('  %-11s %-11s %s -> %s' % ({'card_add': 'В КАРТОЧКУ', 'card_stage': 'НОВЫЙ ЭТАП',
                                           'card_other': 'ДРУГАЯ'}[d['verdict']], entry['id'],
                                          str((entry.get('news') or {}).get('title'))[:50], entry['deal_id']))
    for d in offers_orphan:
        print('  НЕ ПРИМЕНЕНО %-10s решение «%s» по предложению, которого нет в памяти — оставляю сайту'
              % (d['deal_id'], d['verdict']))
    for draft in dropped:
        print('  ОТБРОШЕНА   %-11s %s' % (draft['draft_id'], str(draft.get('title'))[:56]))
    # Решение, чей черновик не появился ни на одном диске за неделю, не
    # применит уже никто: сырье держится в hold несколько дней, потом
    # уезжает, а решение так и висело бы у сайта «живым» — и консоль каждый
    # раз считала бы его нерешенным (28 октября 2026: 40 нажатий с 22
    # сентября без черновика). Такое решение запоминается в decided_raw по
    # id (повторно оно не применится) и подтверждается сайту.
    stale_orphan = [d for d in orphan if _older_than(d, now, ORPHAN_MAX_DAYS)]
    orphan = [d for d in orphan if d not in stale_orphan]
    for d in orphan:
        print('  НЕ ПРИМЕНЕНО %-10s решение «%s» есть, а черновика нет на этом диске — '
              'оставляю сайту для рутины притока' % (d['deal_id'], d['verdict']))
    for d in stale_orphan:
        print('  УСТАРЕЛО    %-11s решение «%s» старше %d дней, черновика нет — '
              'запоминаю и подтверждаю сайту' % (d['deal_id'], d['verdict'], ORPHAN_MAX_DAYS))

    if not write:
        print('Сухой прогон. Применение — с ключом --write.')
        return 0

    data = json.load(open(DATA, encoding='utf-8'))
    existing = {d['id'] for d in data['deals']}
    post_mod = last_by_deal(decisions, POST_VERDICTS)
    # РЕШЕНИЕ О ПОСТЕ ПОМНИТСЯ У КАРТОЧКИ, А НЕ ТОЛЬКО В РЕШЕНИЯХ САЙТА.
    # Решения забираются и подтверждаются сайту за один прогон; если карточка
    # в этот прогон не вышла (придержана, тупик приемки, показана заново), ее
    # «без поста» пропадало вместе с подтвержденными решениями. 28 октября
    # 2026 партнер нажал «без поста» у лицензии на участок в Башкирии
    # (`gf2b5f78c`), карточку придержали из-за тестов, показали заново — и
    # утром пост вышел в канал («мы вроде вчера обсудили, что только на сайт»).
    for card in pending['cards']:
        post = post_mod.get(card['id'])
        # Владелец отменил нажатую по ошибке «Пост в канал» (3 ноября 2026,
        # лагерь у «Усть-Качки»: «Отмени публикацию. Случайно одобрил»):
        # отметка у карточки сильнее решения на сайте.
        if card.get('post_cancelled'):
            post = post_mod[card['id']] = {'verdict': 'post_no'}
        if post:
            card['post_verdict'] = post['verdict']
            if post.get('channels'):
                card['post_channels'] = list(post['channels'])
    # Кнопка под проектом поста у карточки, которая УЖЕ на сайте (пост
    # показали заново после правки) — та же отметка у карточки в базе.
    for deal in data['deals']:
        post = post_mod.get(deal['id'])
        if post and post['verdict'] == 'post_yes':
            deal['post_approved'] = True
            deal.pop('no_post', None)
            deal.pop('post_held', None)
            if post.get('channels'):
                deal['post_channels'] = list(post['channels'])
        elif post and post['verdict'] == 'post_hold' and not deal.get('post_approved'):
            deal['post_held'] = True
        elif post and post['verdict'] == 'post_no' and not deal.get('post_approved'):
            deal['no_post'] = True
            deal.pop('post_held', None)
    fresh = []
    for card, override, _why in publish:
        assert card['id'] not in existing, 'карточка %s уже в базе' % card['id']
        clean = {k: v for k, v in card.items()
                 if k not in ('pending_since', 'draft_sent', 'held', 'post_draft_sent',
                               '_pending_post_preview', 'post_verdict')}
        # КОГДА КАРТОЧКА ПОЯВИЛАСЬ НА САЙТЕ — это не то же самое, что дата
        # сделки. Лента сортируется по дате СДЕЛКИ, и одобренная сегодня
        # карточка о сделке 28 июля встает в середину списка: владелец 7 августа
        # сказал «не вижу новых карточек», хотя они были на месте. Без этого
        # поля отличить свежее пополнение от старожила нечем.
        # Заранее заданный `added` сильнее сегодняшнего дня: старая новость,
        # выпущенная на сайт с опозданием (Мадрид, Nestlé, «Ашан» — три недели
        # в очереди), встает в ленту по своей дате, а не наверх. Владелец
        # 9 октября 2026: «будет тупо, если они сверху будут».
        clean['added'] = card.get('added') or now.date().isoformat()
        if override:
            clean['post_override'] = format_post.owner_text_as_html(override)
        # «Без поста»: карточка выходит на сайт, а канал молчит. send_telegram
        # увидит признак и засеет telegram_posts как бэклог, не отправляя.
        post = post_mod.get(card['id']) or (
            {'verdict': card['post_verdict']} if card.get('post_verdict') else None)
        if post and post['verdict'] == 'post_no':
            clean['no_post'] = True
        # «✋ Придержать пост»: карточка выходит, пост ждет в «Что придержано».
        if post and post['verdict'] == 'post_hold':
            clean['post_held'] = True
        # ПОСТ — ТОЛЬКО ПО КНОПКЕ (владелец, 3 ноября 2026: «без кнопки
        # никогда»): одобрение карточки выпускает только карточку; пост ждет
        # «📣 Пост в канал» (или текста владельца в ответ на проект поста).
        if (post and post['verdict'] == 'post_yes') or override:
            clean['post_approved'] = True
        if post and post.get('channels'):
            clean['post_channels'] = list(post['channels'])
        import strip_yo  # pipeline/strip_yo.py: база без «е» (27 октября 2026)
        clean = strip_yo.strip_values(clean)
        data['deals'].append(clean)
        fresh.append(clean)
    for card, _why in hold:
        card['held'] = True
    base_changed = False
    for deal, d in late_decisions(data['deals'], pending['cards'], decisions):
        # ОТВЕТ СВОИМ ТЕКСТОМ НА ПРОЕКТ ПОСТА КАРТОЧКИ, КОТОРАЯ УЖЕ НА САЙТЕ
        # (11 ноября 2026, «АГР Холдинг» и Hefei): решение приходит как
        # `approve` с текстом, карточки в очереди уже нет — оно считалось
        # «уже вышла» и гасилось, а пост уходил нашим текстом. Владелец: «вышел
        # пост не таким текстом, каким я его правил в консоли». Текст владельца —
        # это текст поста и разрешение на пост (как у карточки из очереди).
        if d['verdict'] == 'approve' and str(d.get('edited_text') or '').strip():
            text = format_post.owner_text_as_html(d['edited_text'])
            if deal.get('post_override') != text:
                deal['post_override'] = text
                deal['post_approved'] = True
                deal.pop('no_post', None)
                deal.pop('post_held', None)
                base_changed = True
                print('  ТЕКСТ ПОСТА   %-11s %s (текст владельца к карточке на сайте)'
                      % (deal['id'], str(deal.get('title'))[:56]))
            continue
        if d['verdict'] == 'discard':
            apply_late_discard(data, state, deal, now)
            base_changed = True
            print('  СНЯТА С САЙТА %-11s %s (позднее «выкинуть»)' % (deal['id'], str(deal.get('title'))[:56]))
            import fix_files
            for path in fix_files.drop_fixes_for(deal['id']):
                print('  СНЯТ ФАЙЛ ПРАВОК %s' % os.path.relpath(path, ROOT))
    gone_ids = {c['id'] for c, _o, _w in publish} | {c['id'] for c, _w in discard}
    pending['cards'] = [c for c in pending['cards'] if c['id'] not in gone_ids]
    # Файлы правок выкинутой карточки больше никому не нужны (бэклог A25).
    import fix_files
    for card, _why in discard:
        for path in fix_files.drop_fixes_for(card['id']):
            print('  СНЯТ ФАЙЛ ПРАВОК %s' % os.path.relpath(path, ROOT))

    # СЫРЬЕ: «это сделка — в работу» превращает черновик в карточку
    # предпросмотра (дальше он придет в группу сообщениями «пост» и
    # «карточка»); «не сделка» запоминается навсегда — promote больше не
    # покажет этот draft_id.
    # «ВЫКИНУТЬ» — ТОЖЕ РЕШЕНИЕ, КОТОРОЕ НЕЛЬЗЯ ЗАБЫВАТЬ. Черновик, из
    # которого выросла выкинутая карточка, остается лежать в старом файле
    # data/inbox/drafts/<дата>.json (его никто не чистит), и promote.py
    # перечитывает ВСЕ файлы партии на каждом прогоне — без этой записи
    # тот же адрес источника завтра снова пройдет ворота под новым id и
    # приедет владельцу тем же вопросом, который он уже закрыл. Тот же
    # класс памяти, что raw_titles/decided_raw для сырья, только для
    # решения на уровне уже прошедшей ворота карточки.
    for card, _why in discard:
        for s in card.get('src') or []:
            if len(s) > 1 and str(s[1]).startswith('http'):
                state.setdefault('discarded_urls', {})[str(s[1])] = {
                    'id': card['id'], 'title': card.get('title'),
                    'at': now.isoformat(timespec='seconds')}
    pending_ids = {c['id'] for c in pending['cards']} | existing
    # Карточка, рожденная кнопкой «это сделка — в работу», проходит те же
    # шаги, что и карточка из ворот: иначе стороны остаются текстом и
    # карточка некликабельна (замер 11 сентября 2026 — 107 из 145).
    # «Это другая сделка» — тот же путь, что «Это сделка — в работу»: черновик
    # (сырье из hold или сборка из записи новости) становится карточкой.
    # «Добавить» и «Новый этап» пишут факты с цитатой в ту карточку; ответ
    # владельцу уходит после push (`--consume`), и «добавлено» в нем — только
    # если источник новости правда стоит в карточке.
    offer_answers = []
    for entry, d in offers:
        verdict = d['verdict']
        if verdict == 'card_other':
            draft = card_news.draft_for(entry, raw_all, data['companies'])
            if str(draft.get('draft_id')) not in {str(x.get('draft_id')) for x in taken}:
                taken.append(draft)
            entry.update(outcome='decided', decision=verdict, decided_at=now.isoformat(timespec='seconds'))
            offer_answers.append(card_news.other_text(entry))
            continue
        done, failed, where = card_news.apply_offer(entry, verdict, data, pending, now)
        card, _w = card_news.find_card(entry['deal_id'], data, pending['cards'])
        if where == 'base':
            base_changed = True
        card_news.mark_raw(state, entry, 'enrich:%s' % entry['deal_id'])
        offer_answers.append(card_news.closure_text(entry, card, done, failed, where))
        print('  %s: %s%s' % (entry['deal_id'], ', '.join(done) or 'ничего',
                              ('; не внесено — ' + '; '.join('%s: %s' % x for x in failed)) if failed else ''))
    import link_parties
    party_index = link_parties.build_index(data['companies'])
    for draft in taken:
        card = promote.to_card(draft, promote.new_id(pending_ids))
        for line in link_parties.link_card(card, party_index, data['companies']):
            print('              %s | связано -> %s' % (card['id'], line))
        pending_ids.add(card['id'])
        card['pending_since'] = now.isoformat(timespec='seconds')
        # Откуда карточка: решение владельца по сырью. Нужно, чтобы при слиянии
        # с существующей карточкой или выкидывании ответить в консоль, что с
        # его решением стало (28 октября 2026, «Аккую»: карточку слили в
        # g2f22b1dc, владелец об этом не узнал).
        card['from_raw'] = {'draft_id': str(draft['draft_id']), 'title': str(draft.get('title') or '')[:200]}
        pending['cards'].append(card)
        state.setdefault('decided_raw', {})[str(draft['draft_id'])] = 'take'
        state.setdefault('raw_titles', {})[promote.raw_key(draft.get('title'))] = 'take'
        for old_id in _old_ids_for(draft, sent_titles):
            state['decided_raw'][old_id] = 'take'
        print('              %s -> предпросмотр %s' % (draft['draft_id'], card['id']))
    for draft in dropped:
        state.setdefault('decided_raw', {})[str(draft['draft_id'])] = 'drop'
        for old_id in _old_ids_for(draft, sent_titles):
            state['decided_raw'][old_id] = 'drop'
        # Память и по заголовку: та же новость назавтра приходит с НОВЫМ
        # draft_id, и партнер жал «не сделка» по Рижскому вокзалу трижды.
        state.setdefault('raw_titles', {})[promote.raw_key(draft.get('title'))] = 'drop'
        # Не печатаем повторно: план по сырью уже назван выше, до сухого
        # возврата, и второй такой же строкой отчет только шумит.

    if fresh or base_changed:
        # Новые карточки рождаются с facts (basis rule) — иначе клиент, который
        # читает только facts, не покажет их ни в одном показателе.
        if ROOT not in sys.path:
            sys.path.insert(0, ROOT)
        import facts as facts_layer
        from pipeline import fns_registry as _fns_registry
        facts_layer.derive_all(data, facts_layer.build_ctx(data, _fns_registry.REGISTRY))
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    promote.save_state(state)
    # Заметки ('note') НЕ потребляем: их читает суточная рутина притока и
    # применяет через review.py; потребив их здесь, мы бы их спрятали.
    # НЕ подтверждаем сайту прямо сейчас — только откладываем: подтверждение
    # необратимо, а то, что мы только что записали, еще не пережило git push
    # (см. docstring `consume_pending`). Рутина вызывает
    # `approve.py --consume` последним шагом, после успешного push.
    for d in stale_orphan:
        state.setdefault('decided_raw', {})[str(d['deal_id'])] = d['verdict']
    if stale_orphan:
        promote.save_state(state)
    orphan_ids = {d['id'] for d in orphan} | {d['id'] for d in offers_orphan}
    # ЧУЖИЕ РЕШЕНИЯ НЕ ГАСИМ (30 октября 2026). Решение с «~» в deal_id — не
    # о карточке: этап (`<id>~closed`), сводка (`digest~2026-10`), правка
    # поста (`<id>~edit`), ИНН (`инн~<id>`). Их читает и гасит send_telegram
    # (или скрипты ФНС), а он идет ПОСЛЕ `approve.py --consume`: погашенное
    # здесь решение «в канал» по этапу он уже не видел, пост, выпущенный
    # сайтом, не записывался вышедшим — и через сутки молчания этап выходил
    # снова («Агропромкредит», третий пост).
    ids_to_consume = [d['id'] for d in decisions
                      if d['verdict'] != 'note' and d['id'] not in orphan_ids
                      and not foreign_decision(d)]
    if handle and ids_to_consume:
        site, token = handle
        detail = [{'id': d['id'], 'deal_id': str(d.get('deal_id') or ''), 'verdict': d['verdict'],
                   'has_text': bool(str(d.get('edited_text') or '').strip())}
                  for d in decisions if d['id'] in set(ids_to_consume)]
        json.dump({'site': site, 'token': token, 'ids': ids_to_consume, 'answers': offer_answers,
                   'detail': detail},
                  open(PENDING_CONSUME, 'w', encoding='utf-8'))
        print('Решений отложено на подтверждение после push: %d (approve.py --consume).'
              % len(ids_to_consume))
    print('Опубликовано: %d. В базе: %d. В предпросмотре: %d (из сырья взято %d, отброшено %d).'
          % (len(fresh), len(data['deals']), len(pending['cards']), len(taken), len(dropped)))
    if taken:
        # Черновики, взятые в работу, сразу уходят в группу сообщениями
        # «пост» и «карточка» — иначе они ждали бы утренней рутины сутки.
        try:
            import send_drafts
            send_drafts.main(write=True)
        except Exception as e:
            print('Рассылка новых черновиков не удалась (%s) — их отправит '
                  'следующий прогон.' % e)
    if fresh:
        # Личные уведомления по подпискам — как раньше делал promote.notify.
        import promote
        promote.notify(fresh, data['companies'])
    return 0


if __name__ == '__main__':
    if '--consume' in sys.argv:
        sys.exit(consume_pending())
    sys.exit(main(write='--write' in sys.argv))
