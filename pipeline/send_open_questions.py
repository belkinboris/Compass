# -*- coding: utf-8 -*-
"""Открытые вопросы по карточкам — в консоль основателей, по одному сообщению.

ЗАЧЕМ. В CLAUDE.md, разделе «Известные проблемы», накопились 44 карточки, где
дочитывание нашло расхождение, но менять данные без человека нельзя: сделка,
похоже, не закрылась; покупателем оказался не тот, кто в заголовке; два
источника спорят о сумме. Читать это в репозитории владелец не будет — просьба
4 сентября 2026: «44 карточки запули в телеграм, можешь сразу с вопросом, что
непонятно, мы на каждую ответим где нужен наш вердикт».

КАК ВОЗВРАЩАЕТСЯ ОТВЕТ. Каждое сообщение несет маркер `[карточка <id>]` — тот
же, что у проекта карточки в консоли (см. send_drafts.py). Ответ текстом на
такое сообщение вебхук пишет вердиктом `note` в moderation_decisions, а
рутина забирает его через /api/moderation/decisions и читает
`pipeline/ingest/read_notes.py`. То есть ответ не теряется и не требует, чтобы
кто-то пересказал его мне руками, — это уже работающий мост, а не новый.

ЧТО В СООБЩЕНИИ. Три строки для человека и вопрос: что стоит в карточке
сейчас, что нашли при проверке, что именно нужно решить. Без нашего диалекта
(«дельта-поиск», «структурные поля», «реестровый признак») — правило «Язык для
людей» из CLAUDE.md касается и сообщений консоли.

ТЕМП. Telegram пускает в группу около 20 сообщений в минуту; 44 сообщения
подряд упрутся в 429 и половина не дойдет молча (урок 6 августа). Поэтому
пауза между сообщениями и повтор по `retry_after` — заимствованы у
send_drafts.send_one, а не написаны заново.

ПОВТОРНАЯ ОТПРАВКА ОБЯЗАНА СВЕРЯТЬСЯ С ТЕКУЩЕЙ РЕАЛЬНОСТЬЮ, А НЕ ТОЛЬКО С
СОБОЙ. 18 сентября 2026 партия из 69 «свежих» вопросов (после чистки
дублей внутри самого этого файла) на деле несла минимум 6 УЖЕ РЕШЕННЫХ —
владелец узнал их сам («Я дал решение… но у меня стойкое ощущение, что я
на многие уже отвечал») и был прав: `QUESTIONS` — статический снимок на
момент последней правки файла, а реальность (карточка `CLAUDE.md`'s
«Известные проблемы» с маркером `[ИСПРАВЛЕНО/РАЗРЕШЕНО]», либо сам статус
карточки в базе) с тех пор ушла вперед, и никто не сверял список ПЕРЕД
отправкой. `_already_resolved()` — обязательная проверка на выходе:
маркер решения в том же bullet'е CLAUDE.md для этого id, статус карточки
уже совпадает с тем, что спрашивает `ask` («ставим не состоялась?» —
а статус уже «Не состоялась»), или карточки нет ни в базе, ни в `merged`.
Найденное «устарело» не отправляется НИКОГДА, даже с `--only`.

ОТПРАВЛЕННОЕ ПОМНИТСЯ. `open_questions_sent.json` лежит в git рядом со
скриптом: контейнер рутины одноразовый, и файл в data/inbox (он не хранится в
git) означал бы повторную рассылку тех же 44 вопросов при следующем запуске.

Запуск:
    python3 pipeline/send_open_questions.py              # показать, что уйдет
    python3 pipeline/send_open_questions.py --write      # отправить
    python3 pipeline/send_open_questions.py --write --limit 5
    python3 pipeline/send_open_questions.py --write --only g6ad6fe69
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))

import console_topics                                      # noqa: E402
import telegram_endpoint                                  # noqa: E402
from send_drafts import send_one, PAUSE                   # noqa: E402

SITE = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')
STATE = os.path.join(HERE, 'open_questions_sent.json')

# Вопросы лежат в pipeline/open_questions.json (с 31 октября 2026: 158 записей
# занимали 160 КБ кода, а вся история партий — в git этого файла). Новый вопрос
# дописывается в конец JSON: {"id", "title", "now", "found", "ask"} и, если к
# одной карточке вопросов несколько, свой "key" (см. _key ниже).
OPEN_QUESTIONS_FILE = os.path.join(HERE, 'open_questions.json')
QUESTIONS = json.load(open(OPEN_QUESTIONS_FILE, encoding='utf-8'))


HEADER = "\n".join([
    "🗂 Открытые вопросы по карточкам — %d штук" % len(QUESTIONS),
    "",
    "Это места, где проверка нашла расхождение, а решение за вами: сделка,"
    " похоже, не закрылась; покупателем оказался не тот, кто в заголовке;"
    " два источника спорят о сумме. Сами мы данные не меняли.",
    "",
    "Дальше пойдут %d сообщений подряд, по одному на карточку. В каждом:"
    " что стоит в базе сейчас, что нашли, что нужно решить." % len(QUESTIONS),
    "Отвечайте прямо на нужное сообщение — ответ попадет к рутине, она"
    " применит его и ответит вам тем же реплаем.",
    "Отвечать все сразу не нужно: вопросы не пропадут и повторно приходить"
    " не будут.",
])


def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE, encoding='utf-8'))
    return {"sent": {}}


def _key(item):
    """Ключ «уже отправлено». Обычно это id карточки, но у вопроса «а не завести
    ли отдельную карточку» id — это карточка, ПРИ ЧТЕНИИ КОТОРОЙ находка
    всплыла, и таких вопросов к одной карточке бывает несколько. Без своего
    ключа второй вопрос молча не ушел бы никогда."""
    return item.get("key") or item["id"]


_RESOLVED_MARK_RE = None  # инициализируется лениво — модуль re импортирован ниже


def _find_deal_bullet(claude_text, deal_id):
    """Текст того же bullet'а «Известных проблем» (или «Соглашений»), что
    содержит упоминание `deal_id` в обратных кавычках — не окно фиксированной
    длины (оно ловит СОСЕДНИЙ bullet), а точные границы «до следующего
    bullet'а верхнего уровня»."""
    import re
    global _RESOLVED_MARK_RE
    if _RESOLVED_MARK_RE is None:
        _RESOLVED_MARK_RE = re.compile(r'\[(ИСПРАВЛЕНО|ОТМЕНЕНО|РАЗРЕШЕНО|Перепроверено и РАЗРЕШЕНО)\b')
    bullets = list(re.finditer(r'^- \*\*', claude_text, re.M))
    needle = '`' + deal_id + '`'
    for i, m in enumerate(bullets):
        s = m.start()
        e = bullets[i + 1].start() if i + 1 < len(bullets) else len(claude_text)
        chunk = claude_text[s:e]
        if needle in chunk:
            yield chunk


def _already_resolved(item, claude_text, deals_by_id, merged):
    """Правда только на выходе, не на входе: перед отправкой сверяем вопрос
    с ТЕКУЩИМ состоянием, а не верим тому, что записано в QUESTIONS (см.
    докстроку файла, урок 18 сентября 2026). Возвращает причину строкой,
    если вопрос устарел, иначе None."""
    import re
    deal_id = item['id']
    for chunk in _find_deal_bullet(claude_text, deal_id):
        m = _RESOLVED_MARK_RE.search(chunk)
        if m:
            return 'в CLAUDE.md уже стоит маркер решения: ' + chunk[m.start():m.start() + 80].replace('\n', ' ')
    real_id = merged.get(deal_id, deal_id)
    deal = deals_by_id.get(real_id)
    if deal is None:
        return 'карточки больше нет ни в базе, ни в merged'
    ask_lower = item['ask'].lower()
    if 'не состоял' in ask_lower and deal.get('status') == 'Не состоялась':
        return 'статус уже «Не состоялась»'
    return None


# Сначала искать самому, спрашивать — только если ответа нет (владелец,
# 1 ноября 2026: «надо чтобы ты сам решал все такие вопросы, спрашивай у
# меня, только если не можешь сам найти ответ»). Новый вопрос обязан нести
# `searched` — где искали (издания, реестры, раскрытия, сайты сторон) и
# почему этого не хватило. Без него вопрос не уходит: так в консоль не
# попадает то, что решается поиском (5 из 7 вопросов 1 ноября 2026).
SEARCH_MIN_CHARS = 40


def not_searched(item):
    """Причина не отправлять вопрос: не записано, где искали ответ."""
    text = str(item.get("searched") or "").strip()
    if len(text) < SEARCH_MIN_CHARS:
        return "не записано, где искали ответ сами (поле searched) — сначала поиск, потом вопрос"
    return None


def render(item, number, total):
    searched = ["Где искали сами: " + item["searched"], ""] if item.get("searched") else []
    return "\n".join([
        "❓ Вопрос %d из %d — нужен ваш ответ" % (number, total),
        "[карточка %s] %s" % (item["id"], item["title"]),
        "",
        "Сейчас в базе: " + item["now"],
        "",
        "Что нашли: " + item["found"],
        "",
    ] + searched + [
        "Что решить: " + item["ask"],
        "",
        "Карточка: %s/#/deal/%s" % (SITE, item["id"]),
        "Ответьте на это сообщение — ответ дойдет до рутины.",
    ])


def main():
    args = sys.argv[1:]
    write = '--write' in args
    only = args[args.index('--only') + 1] if '--only' in args else None
    limit = int(args[args.index('--limit') + 1]) if '--limit' in args else None

    state = load_state()
    todo = [q for q in QUESTIONS if _key(q) not in state["sent"]]
    if only:
        todo = [q for q in QUESTIONS if only in (q["id"], _key(q))]
    if limit:
        todo = todo[:limit]

    # Маркер решения мог уехать вместе со своим разделом: 24 сентября 2026
    # CLAUDE.md разнесен по routines/ и docs/, поэтому читаем все три места.
    claude_text = open(os.path.join(ROOT, 'CLAUDE.md'), encoding='utf-8').read()
    for folder in ('routines', 'docs'):
        base = os.path.join(ROOT, folder)
        for name in sorted(os.listdir(base)) if os.path.isdir(base) else []:
            if name.endswith('.md'):
                claude_text += '\n' + open(os.path.join(base, name), encoding='utf-8').read()
    base = json.load(open(os.path.join(ROOT, 'static', 'data', 'deals_promoted.json'), encoding='utf-8'))
    deals_by_id = {d['id']: d for d in base['deals']}
    merged = base.get('merged', {})
    # Карточка может еще не дойти до базы — лежать в очереди приемки
    # (pending.json), а вопрос про нее все равно нужен (24 октября 2026,
    # 42 карточки очереди приемки оказались не сделками). Без этого любой
    # такой вопрос помечался «карточки больше нет ни в базе, ни в merged» и
    # навсегда прятался в `open_questions_sent.json` как устаревший.
    pending_path = os.path.join(ROOT, 'static', 'data', 'pending.json')
    if os.path.exists(pending_path):
        pending = json.load(open(pending_path, encoding='utf-8'))
        for c in pending.get('cards') or []:
            deals_by_id.setdefault(c['id'], c)

    unsearched = [(q, not_searched(q)) for q in todo if not_searched(q)]
    if unsearched:
        print("Не отправляю — ответ сначала ищется самостоятельно:", len(unsearched))
        for q, reason in unsearched:
            print("  %s [%s] — %s" % (q['id'], _key(q), reason))
        todo = [q for q in todo if not not_searched(q)]

    stale = []
    fresh_todo = []
    for q in todo:
        reason = _already_resolved(q, claude_text, deals_by_id, merged)
        if reason:
            stale.append((q, reason))
        else:
            fresh_todo.append(q)
    if stale:
        print("Пропущено как устаревшие (не отправляю):", len(stale))
        for q, reason in stale:
            print("  %s [%s] — %s" % (q['id'], _key(q), reason))
            state['sent'][_key(q)] = 'stale-skip'
        json.dump(state, open(STATE, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1, sort_keys=True)
    todo = fresh_todo

    total = len(QUESTIONS)
    if not todo:
        print("Все %d вопросов уже отправлены." % total)
        return 0
    print("К отправке: %d из %d (уже отправлено %d)" % (len(todo), total, len(state["sent"])))

    token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
    chats = console_topics.console_chats()
    if write and (not token or not chats):
        print("Отправлять некому: нет TELEGRAM_BOT_TOKEN или адреса консоли.")
        return 1

    if not write:
        for q in todo:
            print("\n" + "-" * 60)
            print(render(q, QUESTIONS.index(q) + 1, total))
        print("\nСухой прогон. Отправить: --write")
        return 0

    import httpx
    sent = 0
    thread = console_topics.thread_id('decision')
    with httpx.Client(timeout=20) as client:
        # Шапка — один раз, первым сообщением: 44 сообщения без объяснения,
        # что это и зачем, читаются как поломка бота.
        if not state.get("header_sent") and not only:
            if all(send_one(client, token, chat, HEADER, None, thread) for chat in chats):
                state["header_sent"] = True
                json.dump(state, open(STATE, 'w', encoding='utf-8'),
                          ensure_ascii=False, indent=1, sort_keys=True)
                time.sleep(PAUSE)
        for i, q in enumerate(todo):
            text = render(q, QUESTIONS.index(q) + 1, total)
            ok = all(send_one(client, token, chat, text, None, thread) for chat in chats)
            if ok:
                state["sent"][_key(q)] = True
                sent += 1
                json.dump(state, open(STATE, 'w', encoding='utf-8'),
                          ensure_ascii=False, indent=1, sort_keys=True)
            print("  %s %s" % ("отправлено" if ok else "НЕ ДОШЛО", q["id"]))
            if i < len(todo) - 1:
                time.sleep(PAUSE)
    print("Отправлено вопросов: %d из %d" % (sent, len(todo)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
