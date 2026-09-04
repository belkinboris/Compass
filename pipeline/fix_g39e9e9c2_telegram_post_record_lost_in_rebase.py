"""Восстанавливает запись `telegram_posts["g39e9e9c2"]`, потерянную при
неверном разрешении конфликта `git rebase` (см. PRODUCT_ROADMAP.md, запись
про «ours/theirs в rebase»).

Что сломано: коммит `e97a591` («Публикация: «Azimut отель Ярославль»
выставили на торги») реально отправил пост в канал и записал
`telegram_posts["g39e9e9c2"]` = message_id. Параллельный прогон рутины
притока разрешил конфликт rebase командой `git checkout --theirs` на этом
файле — а во время `rebase` смысл `ours`/`theirs` обратный обычному merge:
`theirs` — это переносимый (свой) коммит, `ours` — то, что уже влилось.
Взятие `--theirs` отбросило чужую (публикации) параллельно запушенную
правку. Сама КАРТОЧКА сделки (`deals["g39e9e9c2"]`) была восстановлена тем
же прогоном притока (см. журнал), а запись в `telegram_posts` — нет: пост
УЖЕ УШЁЛ В КАНАЛ, но локальная база следующим прогоном публикации увидела
бы сделку как «ещё не отправленную» и отправила бы дубль.

Почему `null`, а не настоящий message_id: message_id того реального
сообщения в чате не сохранился ни в одном логе этой сессии (только текст
успешного результата отправки без самого числа). `null` в `telegram_posts`
имеет собственное, уже документированное в `send_telegram.py` значение —
«не публиковать заново, пока не появится настоящий новый факт через
`enrich.py`» (тот же механизм, что `seed_telegram_posts_backlog.py`
использует для исторического бэклога). Это не идеальное состояние (правка
поста через «⟳ Обновлено» будет недоступна, пока кто-то не подставит
настоящий message_id), но оно гарантированно не даёт продублировать пост,
который уже стоит в канале, — а это единственное, что решает этот скрипт.

Запуск: без аргументов — сухой прогон; `--write` — запись.
"""
import json
import sys

PATH = "static/data/deals_promoted.json"


def main():
    write = "--write" in sys.argv
    with open(PATH, encoding="utf-8") as f:
        data = json.load(f)

    deals = data["deals"]
    ids = set(deals.keys()) if isinstance(deals, dict) else {d["id"] for d in deals}
    assert "g39e9e9c2" in ids, "карточка отсутствует в базе — расследовать заново"

    posts = data.setdefault("telegram_posts", {})
    assert "g39e9e9c2" not in posts, (
        "запись telegram_posts['g39e9e9c2'] уже существует — "
        "проверьте, не восстановлена ли она уже другим прогоном"
    )

    print("До: 'g39e9e9c2' отсутствует в telegram_posts")

    if write:
        posts["g39e9e9c2"] = None
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("Записано: telegram_posts['g39e9e9c2'] = null")
    else:
        print("Сухой прогон — ничего не записано. Для записи: --write")


if __name__ == "__main__":
    main()
