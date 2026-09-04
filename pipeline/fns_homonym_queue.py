# -*- coding: utf-8 -*-
"""Этап 9, П8-9: повторный вопрос владельцу по решаемым `no_match`.

ЗАЧЕМ ОТДЕЛЬНО ОТ `fns_unresolved_queue.py`. Та очередь спрашивает про
компании, которых ЕЩЁ НЕТ в реестре вовсе (`unresolved_companies()`
специально пропускает всё, что уже в `by_company_id()`). Но среди
`decision=no_match` за партии 22-23 августа осталось ~20-30 НАСТОЯЩИХ,
хорошо узнаваемых компаний, где поиск ФНС упёрся в омонимию (частая
фамилия/слово, десятки одноимённых юрлиц по стране) или дал ноль
результатов, — а не в то, что компании не существует. Владелец сам сказал
23 августа: «если нужно — я сам буду смотреть». `CANDIDATES` ниже — это
курированный список: из 245 записей `no_match` исключены объекты
недвижимости («ТРЦ», «бизнес-центр», земельные участки, месторождения —
это предмет сделки, а не сторона), паевые фонды без своего ИНН, зарубежные
активы без юрлица РФ и собирательные «структуры такого-то» (нужно сначала
читать карточку, а не спрашивать ИНН вслепую). Отбирались настоящие,
узнаваемые операционные компании, где владелец правдоподобно знает ИНН
или может быстро посмотреть сам — список составлен чтением всех 245
причин `no_match`, не автоматическим фильтром.

МЕХАНИКА ОТВЕТА — НЕ ТА ЖЕ, ЧТО У `fns_unresolved_queue.py`. Эти компании
УЖЕ есть в реестре (`no_match`), и `unresolved_companies()`/`fns_asked`
их не видит и не защищает от повторного вопроса — нужен свой маркер и
свой штамп. Маркер `[инн-омоним <id>]` -> `deal_id = "инн-омоним~<id>"`
(отдельный префикс от `"инн~"`, чтобы `pipeline/fns_notes_to_registry.py`
не спутал два разных сценария: там ответ ДОПИСЫВАЕТ новую запись, здесь —
ПРАВИТ существующую `no_match` на месте, дубль `company_id` запрещён
тестом `test_fns_registry_company_id_is_not_duplicated`). Штамп
«уже спросили» — тот же `fns_asked` на профиле компании, что и у другой
очереди: поля не пересекаются (any `no_match`-профиль никогда не попадёт
в `unresolved_companies()`, он уже в реестре), так что общий штамп не
рискует конфликтом между двумя очередями.

ТЕМП. Тот же принцип, что у `send_queue_to_console` в `fns_unresolved_
queue.py`: не заливать консоль разом. Брифом названо «по 3-5 в день
ПОВЕРХ обычной очереди» — здесь `BATCH_PER_RUN = 5`.

Запуск:
    python3 pipeline/fns_homonym_queue.py                    # список, без сети
    python3 pipeline/fns_homonym_queue.py --write             # отправить в консоль, проставить fns_asked
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from pipeline.fns_registry import by_company_id  # noqa: E402

DATA = os.path.join(ROOT, "static", "data", "deals_promoted.json")
SITE = os.environ.get("APP_BASE_URL", "https://projectcompass.ru").rstrip("/")
PREFIX = "инн-омоним~"
BATCH_PER_RUN = 5

# (company_id, короткая причина ДЛЯ ЧЕЛОВЕКА — не дословный reason реестра,
# а то, что нужно, чтобы узнать компанию с одного взгляда). Полный reason
# всё равно виден по ссылке на карточку.
CANDIDATES = [
    ("g354705fa", "Аскона — 27 омонимов по стране, головной бренд не выделяется"),
    ("g743a138b", "Финансовая группа БКС — 105 омонимов аббревиатуры, ни один не похож на брокера"),
    ("gd853e266", "Верный (сеть супермаркетов) — 112 омонимов"),
    ("gc91d0776", "ритейлер «Реми» (Дальний Восток) — 32 омонима"),
    ("g179a1f41", "ЭТМ (дистрибьютор электрики) — 57 омонимов, есть похожий, но не подтверждён"),
    ("g66d6e4ea", "Приосколье — 16 результатов, головное АО не выделяется"),
    ("g2a9bffc0", "Бизнес-Недвижимость (дочка АФК «Система») — 100 омонимов"),
    ("g04328d0f", "Sokolov (ювелирный бренд) — 148 омонимов (частая фамилия)"),
    ("g23deb0cc", "Гулливер (розничная сеть) — 103 омонима"),
    ("g63814c8a", "Медкапитал — два юрлица по одному адресу, не различить"),
    ("gb330c34a", "КСЭ / Курьер Сервис Экспресс (купил Boxberry) — 18 региональных омонимов"),
    ("gc2792a44", "АФК «Система» — поиск не нашёл публичную ПАО среди тёзок"),
    ("g47bca1da", "«Детский мир» — пять тёзок, само юрлицо после реорганизации 2023"),
    ("g7ac0b3cc", "Банк «ФК Открытие» — не нашли среди тёзок (возможно, уже в составе ВТБ)"),
    ("g391967cd", "РУСАЛ — только региональные дочки, не головная компания"),
    ("gce43e9d9", "АТОЛ (производитель кассового оборудования) — тёзки не по профилю"),
    ("gbaa98e6b", "Russ Outdoor — поиск дал ноль результатов"),
    ("gfd1c35bc", "SkyNet (петербургский провайдер) — ни один тёзка не из Петербурга"),
    ("gf15f54d1", "«Юнирест» / Rostic's — два тёзки с разным ОКВЭД"),
    ("g6d8a19ee", "Квадра (энергокомпания) — головное ПАО не нашли"),
    ("g90b3b906", "Полиметалл (золотодобыча) — тёзки не по профилю"),
    ("g434cdc43", "Росбанк — поиск дал ноль результатов (неожиданно для крупного банка)"),
    ("gb07318fc", "Henderson (сеть одежды) — тёзки не по профилю"),
    ("g0087fb92", "1С — известное юрлицо не попало в топ результатов"),
    ("g7814a42a", "My.Games — поиск дал ноль результатов"),
    ("gaf243db4", "Tutu.ru — поиск дал ноль результатов"),
    ("g000c8096", "Островок (сервис бронирования) — 121 омоним, ни один не про отели"),
    ("g5ca09975", "Группа «Инград» (девелопер) — поиск дал ноль результатов"),
    ("g7313d9af", "Ригла — минимум шесть региональных юрлиц, какое считать «Риглой» — вопрос к вам"),
]


def eligible(registry_idx=None, companies=None):
    """[(company_id, name, short_note)] — кандидаты, которые ЕЩЁ no_match в
    реестре (кто-то мог решить их другим путём) и ещё не спрошены
    (`fns_asked` не стоит)."""
    if registry_idx is None:
        registry_idx = by_company_id()
    if companies is None:
        companies = json.load(open(DATA, encoding="utf-8"))["companies"]
    rows = []
    for cid, note in CANDIDATES:
        row = registry_idx.get(cid)
        if not row or row["decision"] != "no_match":
            continue  # решено другим путём — не спрашиваем
        profile = companies.get(cid)
        if not profile or profile.get("fns_asked"):
            continue
        rows.append((cid, profile.get("name") or cid, note))
    return rows


def console_message(cid, name, note):
    """[инн-омоним <id>] — main.py::telegram_webhook должен научиться
    разбирать этот же маркер как заметку с deal_id="инн-омоним~<id>"
    (та же логика, что уже разбирает "[инн <id>]", другой префикс)."""
    return ("🔁 [инн-омоним %s] — ПОВТОРНЫЙ ВОПРОС, компания уже отмечена «не нашли»\n"
            "%s\n"
            "%s\n"
            "Карточка: %s/#/companies/%s\n\n"
            "Ответьте номером ИНН (10 или 12 цифр), если знаете точно, — заменим "
            "«не нашли» на подтверждённую запись. Не знаете — можно не отвечать."
            % (cid, name, note, SITE, cid))


def main():
    # ИТОГ ПРОГОНА (28 августа, П1-11) — печатается ВСЕГДА, при любом выходе
    # из функции, одной строкой с голыми числами: тот же приём, что и в
    # fns_unresolved_queue.py, и по той же причине — пять прогонов триггера
    # подряд не оставили следа при непустой очереди, и «print внутри if» это
    # не поймал ни разу.
    write = "--write" in sys.argv
    registry_idx = by_company_id()
    base = json.load(open(DATA, encoding="utf-8"))
    rows = eligible(registry_idx, base["companies"])
    print("Решаемых no_match, ещё не спрошенных: %d" % len(rows))
    if not rows:
        print("ИТОГ ПРОГОНА: очередь пуста, отправлять некому (отправлено=0).")
        return

    batch = rows[:BATCH_PER_RUN]
    print("В этот прогон (%d):" % len(batch))
    for cid, name, note in batch:
        print("  %s (%s) — %s" % (name, cid, note))

    if not write:
        print("\nСухой прогон. Отправка — с ключом --write.")
        print("ИТОГ ПРОГОНА: сухой прогон, ничего не отправлено (отправлено=0).")
        return

    HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(HERE, "ingest"))
    sys.path.insert(0, HERE)                               # console_topics
    import console_topics
    import send_drafts

    targets = send_drafts.send_targets()
    if not targets:
        print("Ни TELEGRAM_REVIEW_GROUP_ID, ни TELEGRAM_REVIEW_CHAT_IDS не заданы — "
              "консоли нет, ничего не отправлено.")
        print("ИТОГ ПРОГОНА: консоли нет, ничего не отправлено (отправлено=0).")
        return
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("TELEGRAM_BOT_TOKEN не задан — консоли нет, ничего не отправлено.")
        print("ИТОГ ПРОГОНА: токена нет, ничего не отправлено (отправлено=0).")
        return

    import httpx
    from datetime import date as _date

    sent = []
    thread = console_topics.thread_id('decision')
    with httpx.Client(timeout=20) as client:
        for cid, name, note in batch:
            text = console_message(cid, name, note)
            ok = all(send_drafts.send_one(client, token, chat, text, None, thread) for chat in targets)
            if ok:
                sent.append(cid)
            time.sleep(send_drafts.PAUSE)

    if sent:
        today = os.environ.get("FNS_QUEUE_DATE") or _date.today().isoformat()
        for cid in sent:
            base["companies"][cid]["fns_asked"] = today
        json.dump(base, open(DATA, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("В консоль отправлено: %d, fns_asked проставлен." % len(sent))
    print("ИТОГ ПРОГОНА: отправлено в консоль %d." % len(sent))


if __name__ == "__main__":
    main()
