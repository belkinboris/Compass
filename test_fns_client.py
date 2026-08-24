# -*- coding: utf-8 -*-
"""`fns_client.FULL_LINE_SECTIONS`/`full_lines_payload()` — этап 8, П3-8:
владелец и партнёр попросили показывать «не только эти показатели, а все
из БФО», а не выжимку из 15 полей `BO_LINES`. Коды и названия строк сверены
с независимой справочной таблицей (Cbonds) и живым ответом `bo()` для
Яндекса/ТехноНИКОЛЬ/Роснефти 23-24 августа 2026 — все встреченные вживую
коды входят в `FULL_LINE_SECTIONS` без исключений."""
from fns_client import FULL_LINE_SECTIONS, full_lines_payload


def test_full_line_sections_codes_are_unique_across_the_whole_table():
    """Один код не может значить две разные строки в разных секциях —
    иначе значение из raw_lines попадёт не туда (родня уже применённого
    правила «в упорядоченном словаре одно слово не может принадлежать двум
    отраслям» из CLAUDE.md, только здесь про коды строк БФО)."""
    seen = {}
    for title, lines in FULL_LINE_SECTIONS:
        for code, name in lines:
            assert code not in seen, f"код {code} уже занят секцией {seen.get(code)!r}, встречен снова в {title!r}"
            seen[code] = title
    assert len(seen) > 80, "ожидался полный набор строк трёх форм, а не выжимка"


def test_full_line_sections_cover_codes_actually_seen_live():
    """Коды, реально встреченные в живых ответах `bo()` 23-24 августа 2026
    (Яндекс, ТехноНИКОЛЬ, Роснефть, Медскан) — все обязаны быть в таблице,
    иначе на экране у этих компаний часть строк просто исчезнет молча."""
    seen_live = {
        "1100", "1110", "1150", "1170", "1180", "1190", "1200", "1210", "1220", "1230",
        "1240", "1250", "1260", "1300", "1310", "1350", "1360", "1370", "1400", "1410",
        "1420", "1450", "1500", "1510", "1520", "1540", "1600", "1700", "2100", "2110",
        "2120", "2200", "2210", "2220", "2300", "2310", "2320", "2330", "2340", "2350",
        "2400", "2410", "2411", "2412", "2460", "2500", "2900", "2910", "3600", "4100",
        "4110", "4111", "4112", "4119", "4120", "4121", "4122", "4123", "4129", "4200",
        "4210", "4211", "4213", "4214", "4220", "4221", "4222", "4223", "4300", "4310",
        "4311", "4313", "4314", "4319", "4320", "4323", "4400", "4450", "4490", "4500",
    }
    known = {code for _, lines in FULL_LINE_SECTIONS for code, _ in lines}
    missing = seen_live - known
    assert not missing, f"коды из живых данных отсутствуют в таблице: {sorted(missing)}"


def test_full_lines_payload_skips_codes_without_a_value():
    """Плейсхолдер — не данные: код без значения в `raw_lines` не должен
    появляться на экране пустой строкой."""
    payload = full_lines_payload({"1110": "5000", "1150": None})
    assets = next(s for s in payload if s["title"] == "I. Внеоборотные активы")
    codes = {row["code"] for row in assets["rows"]}
    assert "1110" in codes
    assert "1150" not in codes


def test_full_lines_payload_omits_sections_with_no_filled_rows():
    """Секция без единой заполненной строки не попадает в ответ вовсе —
    родня правилу у банковского баланса (`cbr_f806.parse_full_table`)."""
    payload = full_lines_payload({"1110": "5000"})
    titles = {s["title"] for s in payload}
    assert "I. Внеоборотные активы" in titles
    assert "Отчёт о финансовых результатах" not in titles
    assert "Денежные потоки от текущих операций" not in titles


def test_full_lines_payload_converts_thousands_to_rubles():
    """API отдаёт тыс. руб (как и везде в `fns_client.py`) — на экране
    должны быть рубли, тот же формат, что у остальных `*_rub` полей."""
    payload = full_lines_payload({"1110": "5000"})
    assets = next(s for s in payload if s["title"] == "I. Внеоборотные активы")
    row = next(r for r in assets["rows"] if r["code"] == "1110")
    assert row["value_rub"] == 5_000_000


def test_full_lines_payload_keeps_negative_and_zero_values():
    """Ноль и отрицательное значение — тоже данные, не то же самое, что
    отсутствие значения (непокрытый убыток по 1370 бывает отрицательным)."""
    payload = full_lines_payload({"1370": "-12000", "1360": "0"})
    equity = next(s for s in payload if s["title"] == "III. Капитал и резервы")
    rows = {r["code"]: r["value_rub"] for r in equity["rows"]}
    assert rows["1370"] == -12_000_000
    assert rows["1360"] == 0


def test_full_lines_payload_handles_empty_input():
    assert full_lines_payload({}) == []
    assert full_lines_payload(None) == []
