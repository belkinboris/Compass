# -*- coding: utf-8 -*-
"""Подтягивание свежих данных с GitHub без пересборки сайта (data_refresh.py).

Сеть здесь не нужна и не должна быть нужна: `_download` подменяется целиком,
`BASE_DIR` — временной папкой. Проверяем ровно то, чем эта механика опасна:
она ЗАМЕНЯЕТ живой файл базы, на котором стоит весь сайт.
"""
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import data_refresh
import main


def _base(n: int = 100) -> dict:
    return {
        "deals": [{"id": "g%03d" % i, "title": "сделка %d" % i, "date": "2026-01-15"}
                  for i in range(n)],
        "companies": {"c1": {"name": "Компания"}},
        "match_keys": {},
    }


def _bytes(data) -> bytes:
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Своя папка вместо репозитория и чистое состояние модуля.

    `_STATE` глобален (его читает /api/data/status), поэтому между тестами
    его надо обнулять — иначе счётчики и запомненный ETag протекают из теста
    в тест, и «повторная закачка ничего не пишет» проходила бы по ложной
    причине.
    """
    monkeypatch.setattr(data_refresh, "BASE_DIR", str(tmp_path))
    monkeypatch.setitem(data_refresh._STATE, "files", {})
    for key in ("checks", "downloads", "writes", "rejects", "fails_in_row"):
        monkeypatch.setitem(data_refresh._STATE, key, 0)
    for key in ("last_try", "last_ok", "last_change", "last_error", "last_error_at"):
        monkeypatch.setitem(data_refresh._STATE, key, None)
    monkeypatch.setitem(data_refresh._STATE, "last_change_files", [])
    # Побочные действия успешной замены проверяются отдельным тестом; здесь
    # они молчат, чтобы не строить настоящий индекс и не писать в базу.
    calls = {"caches": 0, "subs": 0}
    monkeypatch.setattr(data_refresh, "drop_in_process_caches",
                        lambda: calls.__setitem__("caches", calls["caches"] + 1))
    monkeypatch.setattr(data_refresh, "_rescan_subscriptions",
                        lambda: calls.__setitem__("subs", calls["subs"] + 1))
    (tmp_path / "static" / "data").mkdir(parents=True)
    path = tmp_path / "static" / "data" / "deals_promoted.json"
    path.write_bytes(_bytes(_base(100)))
    return {"root": tmp_path, "base_path": path, "calls": calls}


def _serve(responses):
    """Подменяет загрузчик: путь файла -> (код, тело) или исключение."""
    seen = []

    def fake(url, etag=None, modified=None):
        key = url.rsplit("/", 1)[-1]
        seen.append({"url": url, "etag": etag, "modified": modified})
        answer = responses.get(key, (404, b""))
        if isinstance(answer, Exception):
            raise answer
        code, body = answer[0], answer[1]
        return code, body, answer[2] if len(answer) > 2 else None, answer[3] if len(answer) > 3 else None

    fake.seen = seen
    return fake


def test_broken_json_never_replaces_the_base(env, monkeypatch):
    """Обрыв закачки посреди файла не должен стереть базу.

    Половина JSON разбирается как «не JSON», и это единственный момент, когда
    мы вообще узнаём об обрыве: длина ответа могла быть какой угодно.
    """
    before = env["base_path"].read_bytes()
    monkeypatch.setattr(data_refresh, "_download",
                        _serve({"deals_promoted.json": (200, b'{"deals": [{"id": "g1"')}))
    report = data_refresh.refresh_once()
    assert env["base_path"].read_bytes() == before
    assert report["changed"] == []
    assert any("deals_promoted" in e for e in report["errors"])
    assert env["calls"]["caches"] == 0, "кэши сбрасывать не за что — файл не менялся"


def test_half_sized_base_is_rejected(env, monkeypatch):
    """Файл, где сделок вдвое меньше, — обрезанная закачка или чужой файл.

    Порог 90% выбран так, чтобы законные слияния дублей (единицы карточек)
    проходили, а потеря сотен — нет.
    """
    before = env["base_path"].read_bytes()
    monkeypatch.setattr(data_refresh, "_download",
                        _serve({"deals_promoted.json": (200, _bytes(_base(50)))}))
    report = data_refresh.refresh_once()
    assert env["base_path"].read_bytes() == before
    assert "падение больше 10%" in report["errors"][0]
    assert data_refresh._STATE["rejects"] == 1


def test_base_without_companies_is_rejected(env, monkeypatch):
    """Валидный JSON — ещё не наша база: у сайта на `companies` стоит каталог."""
    before = env["base_path"].read_bytes()
    monkeypatch.setattr(data_refresh, "_download",
                        _serve({"deals_promoted.json": (200, b'{"deals": [{"id": "g1"}]}')}))
    data_refresh.refresh_once()
    assert env["base_path"].read_bytes() == before


def test_good_base_is_written_atomically(env, monkeypatch):
    """Замена идёт через временный файл: посетитель, качающий базу в этот
    момент, не должен получить половину."""
    fresh = _bytes(_base(140))
    monkeypatch.setattr(data_refresh, "_download",
                        _serve({"deals_promoted.json": (200, fresh, 'W/"новый"', "Wed, 03 Sep 2026 10:00:00 GMT")}))
    real_replace, seen = os.replace, []

    def spy(src, dst):
        # В момент подмены в НАЗНАЧЕНИИ обязана лежать ещё старая версия:
        # значит, писали не «поверх», а рядом.
        seen.append((src, dst, Path(dst).read_bytes()))
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", spy)
    report = data_refresh.refresh_once()

    assert report["changed"] == [data_refresh.MAIN_FILE]
    assert env["base_path"].read_bytes() == fresh
    assert len(seen) == 1
    src, dst, during = seen[0]
    assert src != dst and src.startswith(dst), "писать надо во временный файл рядом"
    assert len(json.loads(during)["deals"]) == 100, "в назначении до самой замены — старая база"
    assert not list(env["base_path"].parent.glob("*.tmp*")), "временный файл не должен оставаться"


def test_successful_change_drops_caches_and_rescans_subscriptions(env, monkeypatch):
    """Файл заменён, а процесс отвечает по старому — главный подводный камень:
    снаружи это выглядит как «данные не доехали», хотя они на диске."""
    monkeypatch.setattr(data_refresh, "_download",
                        _serve({"deals_promoted.json": (200, _bytes(_base(101)))}))
    data_refresh.refresh_once()
    assert env["calls"] == {"caches": 1, "subs": 1}


def test_only_the_base_triggers_the_heavy_follow_up(env, monkeypatch):
    """Очередь предпросмотра меняется чаще всех, а индекс ассистента от неё не
    зависит: пересобирать его на каждую карточку модерации — секунда впустую."""
    monkeypatch.setattr(data_refresh, "_download", _serve({
        "deals_promoted.json": (304, b""),
        "pending.json": (200, _bytes({"cards": [{"id": "g1"}]})),
    }))
    report = data_refresh.refresh_once()
    assert report["changed"] == ["static/data/pending.json"]
    assert env["calls"] == {"caches": 0, "subs": 0}


def test_assistant_index_is_really_rebuilt(tmp_path, monkeypatch):
    """Отдельно от подмен: `drop_in_process_caches()` обязана реально
    выбросить старый индекс, а не просто не упасть."""
    import assistant_retrieval
    small = tmp_path / "мини.json"
    small.write_bytes(_bytes(_base(3)))
    monkeypatch.setattr(assistant_retrieval, "DATA_PATH", small)
    monkeypatch.setattr(assistant_retrieval, "load_firms", lambda *a, **k: [])
    first = assistant_retrieval.get_index(force=True)
    small.write_bytes(_bytes(_base(4)))
    monkeypatch.setattr(data_refresh, "_rescan_subscriptions", lambda: None)
    data_refresh.drop_in_process_caches()
    second = assistant_retrieval.get_index()
    assert second is not first and len(second.docs) == 4


def test_network_failure_keeps_the_file_and_lands_in_status(env, monkeypatch):
    """Недоступный GitHub — не авария: сайт живёт на файле, приехавшем
    деплоем. Но молчать об этом нельзя, иначе «работает» и «молча не
    работает» неразличимы."""
    import httpx
    before = env["base_path"].read_bytes()
    monkeypatch.setattr(data_refresh, "_download",
                        _serve({"deals_promoted.json": httpx.ConnectError("сеть закрыта")}))
    report = data_refresh.refresh_once()
    assert env["base_path"].read_bytes() == before
    assert report["errors"] and "сеть закрыта" in report["errors"][0]
    status = data_refresh.status()
    assert status["last_error"] and "сеть закрыта" in status["last_error"]
    assert status["last_error_at"] and status["last_ok"] is None
    assert status["fails_in_row"] == 1
    assert status["deals_on_disk"] == 100, "статус называет данные, на которых сайт живёт сейчас"


def test_not_modified_and_same_bytes_write_nothing(env, monkeypatch):
    """Условный запрос экономит 7 МБ на каждой проверке, а проверок 288 в
    сутки. И даже если 304 потерялся по дороге, то же содержимое не должно
    приводить к записи и пересборке индекса."""
    same = env["base_path"].read_bytes()
    fake = _serve({"deals_promoted.json": (200, same, 'W/"тот же"', None)})
    monkeypatch.setattr(data_refresh, "_download", fake)
    mtime = env["base_path"].stat().st_mtime_ns
    assert data_refresh.refresh_once()["changed"] == []
    assert env["base_path"].stat().st_mtime_ns == mtime
    assert data_refresh._STATE["writes"] == 0

    # Второй заход обязан отправить ETag, полученный в первом.
    monkeypatch.setattr(data_refresh, "_download",
                        _serve({"deals_promoted.json": (304, b"")}))
    data_refresh.refresh_once()
    assert fake.seen[0]["etag"] is None
    assert data_refresh._STATE["files"][data_refresh.MAIN_FILE]["etag"] == 'W/"тот же"'
    assert env["calls"]["caches"] == 0


def test_missing_optional_file_is_not_an_error(env, monkeypatch):
    """Выгрузки ЦБ и очередь предпросмотра в ветке могут отсутствовать вовсе —
    это норма, а не сбой: иначе счётчик неудач всегда был бы ненулевым и
    перестал бы что-либо значить."""
    monkeypatch.setattr(data_refresh, "_download",
                        _serve({"deals_promoted.json": (304, b"")}))  # остальные — 404
    report = data_refresh.refresh_once()
    assert report == {"changed": [], "errors": []}
    assert data_refresh.status()["last_ok"] is not None
    assert data_refresh.status()["fails_in_row"] == 0


def test_missing_base_in_the_branch_is_an_error(env, monkeypatch):
    """А вот отсутствие САМОЙ базы — сбой: скорее всего, опечатались в ветке
    (DATA_BRANCH), и молча жить на старом файле в этом случае нельзя."""
    monkeypatch.setattr(data_refresh, "_download", _serve({}))
    report = data_refresh.refresh_once()
    assert report["errors"] and "404" in report["errors"][0]


def test_switch_and_branch_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("DATA_REFRESH_ENABLED", "0")
    assert data_refresh.enabled() is False
    assert data_refresh.start() is False, "выключено — потока быть не должно"
    monkeypatch.setenv("DATA_REFRESH_ENABLED", "1")
    monkeypatch.setenv("DATA_BRANCH", "release")
    assert data_refresh.enabled() and data_refresh.branch() == "release"
    assert data_refresh.raw_url("static/data/deals_promoted.json").endswith(
        "/belkinboris/Compass/release/static/data/deals_promoted.json")
    monkeypatch.setenv("DATA_REFRESH_MINUTES", "0.1")
    assert data_refresh.interval_seconds() == 60, "чаще минуты не ходим"
    monkeypatch.setenv("DATA_REFRESH_MINUTES", "не число")
    assert data_refresh.interval_seconds() == 300


def test_refresh_never_starts_under_pytest(monkeypatch):
    """Тот же гвард, что у докачки ФНС: прогон тестов не должен ходить в сеть
    и уж тем более переписывать рабочий static/data."""
    monkeypatch.setenv("DATA_REFRESH_ENABLED", "1")
    assert os.environ.get("PYTEST_CURRENT_TEST")
    assert data_refresh.start() is False


def test_status_shows_how_long_the_process_lives(monkeypatch):
    """Журнала сборок за ночь простоя у владельца уже нет, причину установить
    было нечем. Время жизни процесса — единственная мера частоты пересборок,
    доступная изнутри: перезапуск на Timeweb бывает только по ней."""
    monkeypatch.setattr(data_refresh, "_STARTED_AT", data_refresh.time.time() - 3 * 3600 - 720)
    process = data_refresh.status()["process"]
    assert process["uptime"] == "3 ч 12 мин", "по-русски, а не «uptime 11520 s»"
    assert 11500 < process["uptime_seconds"] < 11600
    assert process["started_at"].endswith("+00:00")
    assert data_refresh._human_age(0) == "0 мин"
    assert data_refresh._human_age(2 * 86400 + 3600) == "2 дн 1 ч"


def test_code_version_is_read_honestly_or_left_empty(tmp_path, monkeypatch):
    """Версия кода — только та, которую реально можно узнать. Выдуманная
    версия хуже отсутствующей: по ней принимают решение «данные и код
    разъехались», а это неправда."""
    monkeypatch.setenv("CODE_VERSION", "abcdef1234567890")
    assert data_refresh.code_version() == {
        "commit": "abcdef123456", "source": "переменная окружения CODE_VERSION", "branch": None}

    monkeypatch.delenv("CODE_VERSION")
    monkeypatch.setattr(data_refresh, "BASE_DIR", str(tmp_path))
    assert data_refresh.code_version()["commit"] is None, "нет .git — значит null"

    # Обычный деплой выглядит как отсоединённая голова: в HEAD сразу хеш.
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "HEAD").write_text("0123456789abcdef0123456789abcdef01234567\n")
    assert data_refresh.code_version()["commit"] == "0123456789ab"

    # А если голова на ветке — заодно видно, ИЗ КАКОЙ ветки собран сайт: код
    # обязан ехать из release, данные — из main.
    (tmp_path / ".git" / "HEAD").write_text("ref: refs/heads/release\n")
    (tmp_path / ".git" / "refs" / "heads").mkdir(parents=True)
    (tmp_path / ".git" / "refs" / "heads" / "release").write_text("fedcba9876543210" + "0" * 24)
    version = data_refresh.code_version()
    assert version["commit"] == "fedcba987654" and version["branch"] == "release"


def test_status_separates_the_version_of_code_from_the_version_of_data(env, monkeypatch):
    """По одному запросу должно быть видно, разъехались ли они и насколько:
    база на диске законно новее кода, и это норма, а не рассинхрон."""
    monkeypatch.setattr(data_refresh, "_download",
                        _serve({"deals_promoted.json": (200, _bytes(_base(120)))}))
    assert data_refresh.status()["data"]["pulled_at"] is None, \
        "своих обновлений ещё не было — файл приехал деплоем"
    data_refresh.refresh_once()
    body = data_refresh.status()
    assert body["data"]["deals"] == 120
    assert body["data"]["pulled_at"] and body["data"]["branch"] == data_refresh.branch()
    assert body["data"]["base_mtime"]
    assert "commit" in body["code"] and "files_mtime" in body["code"]


def test_status_endpoint_is_closed_by_the_moderation_token(monkeypatch):
    monkeypatch.setenv("MODERATION_TOKEN", "тайна-данных")
    with TestClient(main.app) as client:
        assert client.get("/api/data/status").status_code == 404
        assert client.get("/api/data/status", params={"token": "чужой"}).status_code == 404
        body = client.get("/api/data/status", params={"token": "тайна-данных"}).json()
    assert body["branch"] and body["repo"] == "belkinboris/Compass"
    assert body["deals_on_disk"] > 1000, "статус читает настоящий файл сайта"
    assert [f["path"] for f in body["files"]][0] == data_refresh.MAIN_FILE
