# -*- coding: utf-8 -*-
"""`pipeline/cbr_sync_bank_finance.py` — только то, что не требует сети:
чтение банковских записей из `fns_registry.py`. Живой сбор данных
(`collect()`) — ручной прогон, тот же класс, что `cbr_fetch_bank_summary.py`
(живая диагностика, не воспроизводимый юнит-тест)."""
from pipeline.cbr_sync_bank_finance import bank_entries


def test_bank_entries_only_returns_bank_decisions_with_a_regnum():
    entries = bank_entries()
    assert entries, "в реестре должна быть хотя бы одна банковская запись с cbr_regnum"
    for row in entries:
        assert row["decision"] == "bank"
        assert row.get("cbr_regnum")


def test_bank_entries_company_ids_are_unique():
    ids = [row["company_id"] for row in bank_entries()]
    assert len(ids) == len(set(ids))


def test_output_path_is_valid_json_when_present():
    """`static/data/bank_finance.json` — если файл уже существует (обычно
    после `--write`), он обязан быть валидным JSON, а не наполовину
    записанным мусором: `main()` сравнивает свежие данные с этим файлом
    побайтово через `json.loads`, и битый файл уронит КАЖДЫЙ следующий
    прогон рутины «качество», не только этот скрипт."""
    import json

    from pipeline.cbr_sync_bank_finance import OUTPUT_PATH

    if not OUTPUT_PATH.exists():
        return
    data = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    for company_id, entry in data.items():
        assert isinstance(entry, dict) and "regnum" in entry, company_id


def test_full_balance_output_path_is_valid_json_with_sections_when_present():
    """Этап 8, П2-8: `bank_full_balance.json` — отдельный файл (полный
    баланс), та же защита побитого JSON, что и у сводки, плюс форма
    записи (regnum/legal_name/as_of/sections)."""
    import json

    from pipeline.cbr_sync_bank_finance import FULL_BALANCE_OUTPUT_PATH

    if not FULL_BALANCE_OUTPUT_PATH.exists():
        return
    data = json.loads(FULL_BALANCE_OUTPUT_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    for company_id, entry in data.items():
        assert isinstance(entry, dict), company_id
        assert "regnum" in entry and "as_of" in entry and "sections" in entry, company_id
        assert isinstance(entry["sections"], list) and entry["sections"], company_id
        for section in entry["sections"]:
            assert "title" in section and "rows" in section, company_id
            for row in section["rows"]:
                assert set(row) == {"num", "name", "note", "period_rub", "prior_year_rub"}, company_id


def test_write_if_changed_skips_write_when_data_is_unchanged(tmp_path):
    """Идемпотентность полного баланса — та же защита от пустых коммитов,
    что и у сводки: одинаковые данные не переписывают файл на диске."""
    import json

    from pipeline.cbr_sync_bank_finance import _write_if_changed

    path = tmp_path / "bank_full_balance.json"
    data = {"g28ff15bb": {"regnum": 1481, "as_of": "2026-04-01", "sections": []}}
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    before = path.stat().st_mtime_ns

    _write_if_changed(path, data, write=True, label="test")

    after = path.stat().st_mtime_ns
    assert before == after, "файл не должен переписываться, если данные не изменились"


def test_write_if_changed_writes_only_with_write_flag(tmp_path):
    from pipeline.cbr_sync_bank_finance import _write_if_changed

    path = tmp_path / "bank_full_balance.json"
    data = {"g28ff15bb": {"regnum": 1481}}

    _write_if_changed(path, data, write=False, label="test")
    assert not path.exists(), "без --write файл не должен создаваться"

    _write_if_changed(path, data, write=True, label="test")
    assert path.exists()
