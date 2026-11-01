# -*- coding: utf-8 -*-
"""Имена роутеров читаются через `main` (тесты, скрипты, `inspect.getsource`),
но ПОДМЕНЯЮТСЯ только в модуле-владельце.

До 1 ноября 2026 весь сервер лежал в main.py, и десятки тестов делали
`monkeypatch.setattr(main, "call_llm", ...)`. После разнесения по `app/`
такая подмена меняла бы только копию имени в `main`, а роутер в
`app/assistant.py` продолжал бы звать настоящую функцию — тест молча
проверял бы не то. Поэтому `main.<имя>` остается ЧИТАЕМЫМ (все имена
скопированы сюда), а запись в него падает с подсказкой, где владелец:
`monkeypatch.setattr(app.assistant, "call_llm", ...)`.

Кросс-модульные вызовы подменяемых имен в роутерах идут через атрибут
модуля (`assistant.call_llm(...)`, `core._review_chat_ids(...)`), а не через
`from ... import` — иначе подмена в модуле-владельце до них не дойдет
(docs/server_layout.md, раздел «Как подменять в тестах»)."""
import sys
import types

OWNER: dict[str, str] = {}


class _MainModule(types.ModuleType):
    def __setattr__(self, name, value):
        owner = OWNER.get(name)
        if owner is not None:
            raise AttributeError(
                "main.%s только читается: имя живет в app.%s. Подменяйте там: "
                "monkeypatch.setattr(%s, %r, ...) после `from app import %s`."
                % (name, owner, owner, name, owner))
        super().__setattr__(name, value)


def install(main_globals: dict, modules) -> None:
    """Скопировать в `main` имена модулей (первый владелец в списке — главный)
    и запретить подмену через `main`."""
    for mod in modules:
        short = mod.__name__.rsplit(".", 1)[-1]
        for name, value in vars(mod).items():
            if name.startswith("__") or name == "router" or name in main_globals:
                # Свое у main (импорт или определение) остается своим.
                continue
            OWNER.setdefault(name, short)
            main_globals[name] = value
    sys.modules[main_globals["__name__"]].__class__ = _MainModule
