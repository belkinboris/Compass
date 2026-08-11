# -*- coding: utf-8 -*-
"""Приток, шаг 7: применить решения владельца и партнёра к черновикам.

ОТКУДА РЕШЕНИЯ. Кнопки и ответы в Telegram приходят вебхуком на сайт, сайт
пишет их в таблицу; этот скрипт забирает их по публичному API
(`/api/moderation/decisions?token=…`) — потому что напрямую до базы сайта из
контейнера рутины не достать: она в приватной сети хостинга.

ТРИ ИСХОДА ПО КАЖДОМУ ЧЕРНОВИКУ:
  * «Опубликовать» (или ответ с текстом) — карточка переносится в базу; если
    в ответе был текст, он ложится в `post_override` и канал получит именно
    его, а не автоформат;
  * «Придержать» — черновик остаётся в pending с пометкой `held`, больше не
    рассылается и не публикуется по таймауту; снять пометку — руками;
  * МОЛЧАНИЕ СУТКИ — публикуем как есть. Немой шаг, который держит весь поток,
    у нас уже был (тормоз E9), второй раз те же грабли не берём. Про правило
    молчания написано в самом сообщении-черновике.

Запуск:
    python3 pipeline/ingest/approve.py            # сухой прогон
    python3 pipeline/ingest/approve.py --write    # применить
"""
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
SILENCE_HOURS = 24


def fetch_decisions():
    """Решения с сайта. Сайт недоступен — вернём пусто и скажем об этом:
    таймауты всё равно применимы, а решения дождутся следующего прогона."""
    site = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')
    token = os.environ.get('MODERATION_TOKEN') or os.environ.get('TELEGRAM_WEBHOOK_SECRET') or ''
    if not token:
        print('MODERATION_TOKEN/TELEGRAM_WEBHOOK_SECRET не заданы — решения не прочитать.')
        return [], None
    try:
        import httpx
        r = httpx.get('%s/api/moderation/decisions' % site, params={'token': token}, timeout=20)
        if r.status_code != 200:
            print('Сайт ответил %s на запрос решений — работаем без них.' % r.status_code)
            return [], None
        return r.json().get('decisions', []), (site, token)
    except Exception as e:
        print('Решения недоступны (%s) — работаем без них.' % e)
        return [], None


def consume(handle, ids):
    if not (handle and ids):
        return
    site, token = handle
    try:
        import httpx
        httpx.post('%s/api/moderation/decisions/consume' % site,
                   json={'token': token, 'ids': ids}, timeout=20)
    except Exception as e:
        print('Не удалось пометить решения применёнными (%s) — не страшно: '
              'повторное применение идемпотентно.' % e)


def hours_pending(card, now):
    try:
        since = datetime.fromisoformat(str(card.get('pending_since')))
    except ValueError:
        return 0.0
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    return (now - since).total_seconds() / 3600.0


# Вердикты и их роли. КАРТОЧНЫЕ решают судьбу карточки (approve/hold);
# ПОСТОВЫЕ — модификатор канала (post_yes/post_no: выйдет ли пост, когда
# карточка выйдет); СЫРЬЕВЫЕ (take/drop) относятся к черновикам, которые
# ворота не пропустили; 'note' — заметка для рутины притока, approve её НЕ
# потребляет и НЕ трактует. Смешение ролей уже стреляло: старый код считал
# «любой не-approve вердикт» придержанием, и post_no придержал бы карточку.
CARD_VERDICTS = {'approve', 'hold', 'discard'}
POST_VERDICTS = {'post_yes', 'post_no'}
RAW_VERDICTS = {'take', 'drop'}


def last_by_deal(decisions, verdicts):
    """Последнее по времени решение нужного класса на каждый id."""
    result = {}
    for d in decisions:                      # список уже упорядочен по created_at
        if d['verdict'] in verdicts:
            result[d['deal_id']] = d
    return result


def plan_actions(cards, decisions, now):
    """(публикуем, придерживаем, ждём) — чистая функция, её держат тесты.

    Ответ с текстом на сообщение [пост <id>] приходит вердиктом 'approve' с
    edited_text — правя пост, человек одновременно одобряет карточку."""
    by_deal = last_by_deal(decisions, CARD_VERDICTS)
    publish, hold, wait, discard = [], [], [], []
    for card in cards:
        decision = by_deal.get(card['id'])
        if decision and decision['verdict'] == 'approve':
            publish.append((card, decision.get('edited_text'), 'решение: опубликовать'))
        elif decision and decision['verdict'] == 'discard':
            # «Выкинуть» сильнее «придержать»: карточка не выйдет никуда и
            # исчезает из очереди насовсем. Просьба владельца 6 августа: у
            # нероссийского контура и не-M&A «придержать» оставляло бы мусор
            # висеть в очереди вечно.
            discard.append((card, 'решение: выкинуть'))
        elif decision:
            hold.append((card, 'решение: придержать'))
        elif card.get('held'):
            wait.append((card, 'придержана ранее — ждёт ручного решения'))
        elif not card.get('reviewed'):
            # НЕПРОЧИТАННАЯ КАРТОЧКА НЕ ВЫХОДИТ ПО МОЛЧАНИЮ, И ЭТО ГЛАВНАЯ
            # ЗАЩИТА ОТ КОСЯЧНЫХ КАРТОЧЕК. Черновик рождается из ЗАГОЛОВКА:
            # `guess_parties()` режет его и раскладывает куски по полям, тип
            # ставит классификатор. Владелец 9 августа открыл три такие
            # карточки рядом со статьями и нашёл в каждой каркасный дефект —
            # «Инвестиция» у покупки 100% долей, «бывшая лизинговая „дочка"
            # Mercedes-Benz» вместо ООО «МБ РУС Финанс», «Внуково» в прямых
            # кавычках вместо АО «Международный аэропорт „Внуково"» — и сказал
            # прямо: такие карточки не должны появляться, пока не изучена
            # статья. Раньше сутки молчания публиковали карточку КАК ЕСТЬ,
            # то есть ровно в том виде, в каком её собрал разбор заголовка.
            # Отметку `reviewed` ставит только `review.py` — при правках сам,
            # при бедном источнике через `--mark-read`. Молчание по-прежнему
            # согласие, но согласие на ПРОЧИТАННУЮ карточку.
            wait.append((card, 'не прочитана против источника — молчание её не публикует'))
        elif card.get('draft_sent') and hours_pending(card, now) >= SILENCE_HOURS:
            publish.append((card, None, 'молчание %d ч — публикуем как есть' % SILENCE_HOURS))
        else:
            wait.append((card, 'ждём решения (%.0f ч из %d)' % (hours_pending(card, now), SILENCE_HOURS)))
    return publish, hold, wait, discard


def plan_raw(drafts, decisions):
    """(в работу, отброшено) для сырья. По молчанию сырьё НЕ публикуется:
    ворота его не пропустили, и молчание не делает его сделкой."""
    by_draft = last_by_deal(decisions, RAW_VERDICTS)
    take, drop = [], []
    for draft in drafts:
        decision = by_draft.get(str(draft.get('draft_id')))
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
    publish, hold, wait, discard = plan_actions(pending['cards'], decisions, now)

    for card, override, why in publish:
        print('  ПУБЛИКУЕМ   %-11s %s%s' % (card['id'], str(card.get('title'))[:56],
                                            ' [текст поста заменён]' if override else ''))
        print('              %s' % why)
    for card, why in hold:
        print('  ПРИДЕРЖАНА  %-11s %s' % (card['id'], why))
    for card, why in discard:
        print('  ВЫКИНУТА    %-11s %s' % (card['id'], str(card.get('title'))[:56]))
    for card, why in wait:
        print('  ЖДЁТ        %-11s %s' % (card['id'], why))

    if not write:
        print('Сухой прогон. Применение — с ключом --write.')
        return 0

    data = json.load(open(DATA, encoding='utf-8'))
    existing = {d['id'] for d in data['deals']}
    post_mod = last_by_deal(decisions, POST_VERDICTS)
    fresh = []
    for card, override, _why in publish:
        assert card['id'] not in existing, 'карточка %s уже в базе' % card['id']
        clean = {k: v for k, v in card.items()
                 if k not in ('pending_since', 'draft_sent', 'held', 'post_draft_sent')}
        # КОГДА КАРТОЧКА ПОЯВИЛАСЬ НА САЙТЕ — это не то же самое, что дата
        # сделки. Лента сортируется по дате СДЕЛКИ, и одобренная сегодня
        # карточка о сделке 28 июля встаёт в середину списка: владелец 7 августа
        # сказал «не вижу новых карточек», хотя они были на месте. Без этого
        # поля отличить свежее пополнение от старожила нечем.
        clean['added'] = now.date().isoformat()
        if override:
            clean['post_override'] = override
        # «Без поста»: карточка выходит на сайт, а канал молчит. send_telegram
        # увидит признак и засеет telegram_posts как бэклог, не отправляя.
        post = post_mod.get(card['id'])
        if post and post['verdict'] == 'post_no':
            clean['no_post'] = True
        data['deals'].append(clean)
        fresh.append(clean)
    for card, _why in hold:
        card['held'] = True
    gone_ids = {c['id'] for c, _o, _w in publish} | {c['id'] for c, _w in discard}
    pending['cards'] = [c for c in pending['cards'] if c['id'] not in gone_ids]

    # СЫРЬЁ: «это сделка — в работу» превращает черновик в карточку
    # предпросмотра (дальше он придёт в группу сообщениями «пост» и
    # «карточка»); «не сделка» запоминается навсегда — promote больше не
    # покажет этот draft_id.
    import promote
    state = promote.load_state()
    # «ВЫКИНУТЬ» — ТОЖЕ РЕШЕНИЕ, КОТОРОЕ НЕЛЬЗЯ ЗАБЫВАТЬ. Черновик, из
    # которого выросла выкинутая карточка, остаётся лежать в старом файле
    # data/inbox/drafts/<дата>.json (его никто не чистит), и promote.py
    # перечитывает ВСЕ файлы партии на каждом прогоне — без этой записи
    # тот же адрес источника завтра снова пройдёт ворота под новым id и
    # приедет владельцу тем же вопросом, который он уже закрыл. Тот же
    # класс памяти, что raw_titles/decided_raw для сырья, только для
    # решения на уровне уже прошедшей ворота карточки.
    for card, _why in discard:
        for s in card.get('src') or []:
            if len(s) > 1 and str(s[1]).startswith('http'):
                state.setdefault('discarded_urls', {})[str(s[1])] = {
                    'id': card['id'], 'title': card.get('title'),
                    'at': now.isoformat(timespec='seconds')}
    raw_all = []
    if os.path.isdir(os.path.join(ROOT, 'data', 'inbox', 'hold')):
        hold_dir = os.path.join(ROOT, 'data', 'inbox', 'hold')
        for name in sorted(os.listdir(hold_dir)):
            if name.endswith('.json'):
                raw_all += json.load(open(os.path.join(hold_dir, name),
                                          encoding='utf-8')).get('drafts', [])
    taken, dropped = plan_raw(raw_all, decisions)
    pending_ids = {c['id'] for c in pending['cards']} | existing
    for draft in taken:
        card = promote.to_card(draft, promote.new_id(pending_ids))
        pending_ids.add(card['id'])
        card['pending_since'] = now.isoformat(timespec='seconds')
        pending['cards'].append(card)
        state.setdefault('decided_raw', {})[str(draft['draft_id'])] = 'take'
        state.setdefault('raw_titles', {})[promote.raw_key(draft.get('title'))] = 'take'
        print('  В РАБОТУ    %s -> предпросмотр %s' % (draft['draft_id'], card['id']))
    for draft in dropped:
        state.setdefault('decided_raw', {})[str(draft['draft_id'])] = 'drop'
        # Память и по заголовку: та же новость назавтра приходит с НОВЫМ
        # draft_id, и партнёр жал «не сделка» по Рижскому вокзалу трижды.
        state.setdefault('raw_titles', {})[promote.raw_key(draft.get('title'))] = 'drop'
        print('  ОТБРОШЕНА   %s %s' % (draft['draft_id'], str(draft.get('title'))[:56]))

    if fresh:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    promote.save_state(state)
    # Заметки ('note') НЕ потребляем: их читает суточная рутина притока и
    # применяет через review.py; потребив их здесь, мы бы их спрятали.
    consume(handle, [d['id'] for d in decisions if d['verdict'] != 'note'])
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
    sys.exit(main(write='--write' in sys.argv))
