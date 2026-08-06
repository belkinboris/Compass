# -*- coding: utf-8 -*-
"""Приток, шаг 6: консоль основателей в Telegram — три типа сообщений.

ЗАЧЕМ ИМЕННО ТРИ. Просьба владельца: группа должна работать консолью, и
сообщения в ней должны различаться с первого взгляда. У одной сделки два
разных артефакта с разными решениями, и есть третий поток, который раньше
вообще не доходил до людей:

  📣 [пост <id>] — ПРОЕКТ ПОСТА В КАНАЛ. Кнопки: «пост в канал» / «без
     поста». Ответ на это сообщение своим текстом заменяет текст поста и
     одновременно одобряет карточку. «Без поста» — карточка выйдет на сайт,
     а канал промолчит (телеграм-состояние засеется как бэклог).

  🗂 [карточка <id>] — ПРОЕКТ КАРТОЧКИ САЙТА: поля + ссылка на предпросмотр.
     Кнопки: «опубликовать» / «придержать». Ответ на это сообщение — ЗАМЕТКА:
     её читает суточная рутина притока и применяет через review.py с его
     механическими проверками цитат, а не пишет в базу напрямую.

  ⚠️ [сырьё <draft_id>] — СОМНИТЕЛЬНАЯ СДЕЛКА: черновик, который ворота НЕ
     пропустили, с причиной. Раньше эти 29 штук лежали файлом в git, и
     смотреть их можно было только в репозитории. Кнопки: «это сделка — в
     работу» (черновик станет карточкой предпросмотра и придёт сюда же
     сообщениями 📣 и 🗂) / «не сделка — убрать» (больше не покажется).
     Ответ — заметка для рутины притока, как у карточки.

КАК ВОЗВРАЩАЕТСЯ РЕШЕНИЕ. Кнопка или ответ приходят вебхуком на сайт, сайт
пишет их в таблицу moderation_decisions; рутина публикации забирает решения
по /api/moderation/decisions и применяет approve.py. Напрямую из контейнера
рутины решения не прочитать: база сайта в приватной сети хостинга. Решение
дописывается в само сообщение группы («— ✅ Одобрено (Борис)»), чтобы второй
человек видел, что первый уже нажал.

МОЛЧАНИЕ — СОГЛАСИЕ ТОЛЬКО ДЛЯ КАРТОЧЕК ПРЕДПРОСМОТРА: сутки без ответа —
approve.py публикует как есть (немой шаг, держащий поток, уже был — E9).
Сырьё по таймауту НЕ публикуется никогда: ворота его не пропустили, и
молчание не делает его сделкой.

Запуск:
    python3 pipeline/ingest/send_drafts.py            # план без отправки
    python3 pipeline/ingest/send_drafts.py --write    # отправить
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)                                  # telegram_endpoint в корне
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'publish'))

import format_post                                       # noqa: E402
import promote                                           # noqa: E402
import telegram_endpoint                                 # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')
HOLD_DIR = os.path.join(ROOT, 'data', 'inbox', 'hold')
SITE = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')


def reviewers():
    """Личные id владельца и партнёра — ПРАВО решать, а не адрес отправки.
    Проверяется вебхуком по from.id: в группе chat.id один на всех."""
    return [x.strip() for x in os.environ.get('TELEGRAM_REVIEW_CHAT_IDS', '').split(',') if x.strip()]


def send_targets():
    """Куда слать. Группа (TELEGRAM_REVIEW_GROUP_ID) — одна копия на всех;
    без неё — личное сообщение каждому из TELEGRAM_REVIEW_CHAT_IDS."""
    group = os.environ.get('TELEGRAM_REVIEW_GROUP_ID', '').strip()
    return [group] if group else reviewers()


# --- три типа сообщений -----------------------------------------------------
def field(label, value):
    return '%s: %s\n' % (label, value) if value else ''


def card_message(card):
    """🗂 Проект карточки сайта: поля + предпросмотр. Ответ = заметка."""
    src = next((s[1] for s in card.get('src') or [] if len(s) > 1), '')
    return ('🗂 [карточка %s] — НА САЙТ, на проверку\n'
            '%s\n\n'
            '%s%s%s%s%s%s%s'
            'Предпросмотр: %s/#/preview/%s\n\n'
            '✅/✋ — кнопками. Ответ на это сообщение — заметка для рутины '
            '(«дата не та, в источнике 4 мая»): применит через проверки, не дословно.\n'
            'Молчание сутки — уйдёт на сайт как есть.'
            % (card['id'], str(card.get('title') or ''),
               field('Дата', card.get('date')), field('Отрасль', card.get('ind')),
               field('Тип', card.get('type')), field('Статус', card.get('status')),
               field('Покупатель', card.get('buyer_name')),
               field('Продавец', card.get('seller')),
               field('Предмет', card.get('asset')) + field('Сумма', card.get('sum'))
               + field('Источник', src),
               SITE, card['id']))


def post_message_text(card, companies):
    """📣 Проект поста в канал — ровно тот текст, что уйдёт подписчикам."""
    return ('📣 [пост %s] — В КАНАЛ, на проверку\n'
            'Ниже — текст поста как он уйдёт подписчикам. Ответ на это '
            'сообщение своим текстом ЗАМЕНИТ пост (и одобрит карточку).\n'
            '━━━━━━━━━━━━\n%s'
            % (card['id'], format_post.render(card, companies)))


def raw_message(draft):
    """⚠️ Сырьё, которое ворота не пропустили, — с причиной."""
    src = next((s[1] for s in draft.get('src') or [] if len(s) > 1), '')
    reasons = '\n'.join('• %s' % r for r in (draft.get('hold_reasons') or ['причина не записана']))
    return ('⚠️ [сырьё %s] — СОМНИТЕЛЬНАЯ, нужно ваше слово\n'
            '%s\n\n'
            'Почему не пропущена автоматически:\n%s\n\n'
            '%s%s%s%s'
            '✅ «Это сделка» — уйдёт в предпросмотр и вернётся сюда карточкой '
            'и постом. 🗑 «Не сделка» — больше не покажется. Ответ — заметка '
            'для рутины притока. По молчанию НЕ публикуется.'
            % (draft.get('draft_id'), str(draft.get('title') or ''), reasons,
               field('Дата', draft.get('date')),
               field('Покупатель', draft.get('buyer_name')),
               field('Продавец', draft.get('seller')) + field('Предмет', draft.get('asset')),
               field('Источник', src)))


def card_keyboard(card):
    return {'inline_keyboard': [[
        {'text': '✅ Опубликовать', 'callback_data': 'mod:%s:ok' % card['id']},
        {'text': '✋ Придержать', 'callback_data': 'mod:%s:hold' % card['id']},
    ]]}


def post_keyboard(card):
    return {'inline_keyboard': [[
        {'text': '📣 Пост в канал', 'callback_data': 'mod:%s:post_ok' % card['id']},
        {'text': '🔕 Без поста', 'callback_data': 'mod:%s:post_no' % card['id']},
    ]]}


def raw_keyboard(draft):
    return {'inline_keyboard': [[
        {'text': '✅ Это сделка — в работу', 'callback_data': 'mod:%s:take' % draft['draft_id']},
        {'text': '🗑 Не сделка', 'callback_data': 'mod:%s:drop' % draft['draft_id']},
    ]]}


def latest_hold_drafts():
    names = sorted(n for n in os.listdir(HOLD_DIR) if n.endswith('.json')) \
        if os.path.isdir(HOLD_DIR) else []
    if not names:
        return []
    doc = json.load(open(os.path.join(HOLD_DIR, names[-1]), encoding='utf-8'))
    return [d for d in doc.get('drafts', []) if d.get('draft_id')]


# СКОЛЬКО СЫРЬЯ ПОКАЗЫВАТЬ ЗА ПРОГОН. Ворота отправляют на решение куда
# больше, чем проходит: 6 августа это 11 карточек против 75 черновиков, и без
# предела в группу ушло бы 97 сообщений разом. Консоль, где нужные 22 тонут в
# 75 сомнительных, человек перестаёт читать вообще — а сырьё по молчанию не
# публикуется никогда, значит показать его позже ничего не стоит. Карточки и
# посты предела НЕ имеют: это то, ради чего консоль заведена, и по молчанию
# они через сутки уходят на сайт — не показать их значит опубликовать молча.
RAW_PER_RUN = 10

# ТЕМП ОТПРАВКИ. Telegram пускает в группу около 20 сообщений в минуту, а
# 21-е возвращает 429 с полем `retry_after`. Прогон 6 августа отправил ровно
# 20 сообщений из 32 и упёрся: одиннадцатая карточка и всё сырьё остались
# недоставленными, причём вслух об этом сказала только строка в логе прогона,
# которого никто не читает. Пауза между сообщениями убирает причину; повтор
# по `retry_after` оставлен на случай, когда в группу пишет кто-то ещё.
PAUSE = 3.5
RETRIES = 3


def send_one(client, token, chat, text, keyboard):
    """Отправить одно сообщение, дождавшись, если Telegram просит подождать."""
    for attempt in range(RETRIES):
        r = client.post(telegram_endpoint.method_url(token, 'sendMessage'), json={
            'chat_id': chat, 'text': text, 'reply_markup': keyboard,
            'disable_web_page_preview': True,
        })
        if r.status_code == 200 and r.json().get('ok'):
            return True
        wait = 0
        try:
            wait = int(r.json().get('parameters', {}).get('retry_after') or 0)
        except ValueError:
            wait = 0
        if wait and attempt < RETRIES - 1:
            print('  Telegram просит подождать %d с — жду' % wait)
            time.sleep(wait + 1)
            continue
        print('  не дошло до %s: %s' % (chat, r.text[:120]))
        return False
    return False


def build_plan():
    """(текст, клавиатура, как отметить отправленным) для всего неразосланного.

    Возвращает ещё и число сомнительных черновиков, отложенных до следующего
    прогона: предел, о котором не сказано вслух, читается как «это всё».
    """
    plan = []
    pending = promote.load_pending() if os.path.exists(PENDING) else {'cards': []}
    comps = json.load(open(DATA, encoding='utf-8'))['companies']
    for card in pending['cards']:
        # У ОДНОЙ КАРТОЧКИ ДВА СООБЩЕНИЯ, И ОТМЕТКА У КАЖДОГО СВОЯ. Раньше
        # флаг был один на оба: если 429 приходил МЕЖДУ ними, карточка
        # считалась разосланной целиком, и проект поста не уходил уже никогда
        # — канал молча терял текст, который никто не одобрял. Старые записи
        # знают только `draft_sent`, поэтому его значение и служит ответом за
        # пост, пока не появился отдельный флаг.
        if not card.get('draft_sent'):
            plan.append((card_message(card), card_keyboard(card),
                         ('card', card, 'draft_sent')))
        if not card.get('post_draft_sent', card.get('draft_sent')):
            plan.append((post_message_text(card, comps), post_keyboard(card),
                         ('card', card, 'post_draft_sent')))
    state = promote.load_state()
    seen = set(state.get('sent_raw', [])) | set(state.get('decided_raw', {}))
    fresh_raw = [d for d in latest_hold_drafts() if str(d['draft_id']) not in seen]
    for draft in fresh_raw[:RAW_PER_RUN]:
        plan.append((raw_message(draft), raw_keyboard(draft), ('raw', draft, None)))
    return plan, pending, state, max(0, len(fresh_raw) - RAW_PER_RUN)


def main(write=False):
    plan, pending, state, deferred = build_plan()
    chats = send_targets()
    group = bool(os.environ.get('TELEGRAM_REVIEW_GROUP_ID', '').strip())
    print('Сообщений к отправке: %d | адресов: %d%s'
          % (len(plan), len(chats), ' (общая группа)' if group else ''))
    if deferred:
        print('Сомнительных черновиков отложено до следующего прогона: %d '
              '(за раз показываем %d, чтобы карточки не тонули в сырье).'
              % (deferred, RAW_PER_RUN))
    for text, _kb, _mark in plan[:4]:
        print('\n%s\n%s' % ('-' * 40, text[:400]))
    if not plan:
        return 0
    token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    if not (write and token and chats):
        if not chats:
            print('\nНи TELEGRAM_REVIEW_GROUP_ID, ни TELEGRAM_REVIEW_CHAT_IDS не заданы — отправлять некому.')
        if not token:
            print('TELEGRAM_BOT_TOKEN не задан — показываю план, не отправляю.')
        if not write:
            print('Сухой прогон. Отправка — с ключом --write.')
        return 0

    import httpx
    sent = 0
    with httpx.Client(timeout=20) as client:
        for i, (text, keyboard, (kind, item, mark)) in enumerate(plan):
            if i:
                time.sleep(PAUSE)
            ok_all = True
            for chat in chats:
                if not send_one(client, token, chat, text, keyboard):
                    ok_all = False
            if ok_all:
                sent += 1
                if kind == 'card':
                    item[mark] = True
                else:
                    state.setdefault('sent_raw', []).append(str(item['draft_id']))
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    promote.save_state(state)
    print('Отправлено сообщений: %d' % sent)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
