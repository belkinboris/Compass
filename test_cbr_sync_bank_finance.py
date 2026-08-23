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
