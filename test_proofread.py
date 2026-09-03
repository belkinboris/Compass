"""Вычитка карточек (pipeline/proofread.py): факты не меняются, и это проверяется.

Вычитка переписывает текст поля целиком — единственная защита от искажения
здесь механическая: числа, имена, валюты, пресс-атрибуция, кавычки. Тесты
держат каждую границу с двух сторон (плохая правка отклонена, хорошая
принята), штамп и совместимость с таблицей правок review.py.

Запуск: python3 -m pytest test_proofread.py -q
"""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "pipeline"))
sys.path.insert(0, str(ROOT / "pipeline" / "ingest"))

import proofread  # noqa: E402


def card_fixture():
    return {
        "id": "x1", "title": "«Русагро» получила контроль над «Агро-Белогорьем»",
        "sum": "31 млрд ₽",
        "eco": {
            "fin": "РУСАГРО заплатила 31 млрд рублей за 77,5% в «Агро-Белогорье», сообщают "
                   "«Ведомости» со ссылкой на данные аудированной отчетности за I полугодие 2025 года.",
            "val": "Руководитель департамента M&A BGP Capital Иван Пешков оценивает капитализацию "
                   "холдинга в 38–43 млрд рублей.",
            "context": "—",
        },
        "law": {
            "appr": "Выход на биржу стал обязательным после предписания ФАС. Торги начались "
                    "(Retail.ru, 30 июня 2025 года).",
            "terms": "«Русагро» заплатила 31 млрд руб. за 77,5% в группе. Там сказано, что порядка "
                     "6 млрд руб. составило гарантийное обеспечение за 2021–2024 гг.",
        },
        "events": [{"kind": "closed", "date": "2024-11-13",
                    "note": "Сделка закрыта, сообщает компания. Сумма — 31 млрд руб."}],
    }


GOOD_FIN = ("По данным аудированной отчётности за первое полугодие 2025 года, за 77,5% "
            "«Агро-Белогорья» «Русагро» заплатила 31 млрд ₽.")


def test_self_check_passes():
    """Правила проверены на себе — как в review.py и ops_status.py."""
    proofread._self_check()


def test_good_edit_is_accepted_and_press_attribution_is_refused():
    card = card_fixture()
    edit = dict(id="x1", field="eco.fin", old=card["eco"]["fin"], new=GOOD_FIN)
    bad, _ = proofread.check(edit, card)
    assert not bad, bad
    bad, _ = proofread.check(dict(edit, new=GOOD_FIN + " Об этом пишет РБК."), card)
    assert any("пресс-атрибуция" in b for b in bad), bad
    bad, _ = proofread.check(dict(edit, new=GOOD_FIN.replace("По данным аудированной отчётности",
                                                             "Как сообщалось")), card)
    assert any("безличный пересказ" in b for b in bad), bad


def test_registry_attribution_is_allowed_but_press_is_not():
    """«По данным ЕГРЮЛ» — квалификация числа, «по данным Ведомостей» — пресса."""
    assert not proofread.press_attribution("По данным ЕГРЮЛ, доля перешла в марте 2024 года.")
    assert not proofread.press_attribution("По оценке аналитика Ивана Пешкова, капитализация 40 млрд ₽.")
    assert proofread.press_attribution("По данным «Ведомостей», доля перешла в марте 2024 года.")
    assert proofread.press_attribution("Доля перешла в марте (Интерфакс).")
    assert proofread.press_attribution("Продавец — Иван Петров. Источник: Kommersant.")


def test_foreign_number_and_new_name_are_refused():
    card = card_fixture()
    edit = dict(id="x1", field="eco.fin", old=card["eco"]["fin"], new=GOOD_FIN)
    bad, _ = proofread.check(dict(edit, new=GOOD_FIN.replace("31 млрд", "32 млрд")), card)
    assert any("числа, которых не было" in b for b in bad), bad
    bad, _ = proofread.check(dict(edit, new=GOOD_FIN.replace("«Русагро»", "«Мираторг»")), card)
    assert any("имена, которых не было" in b for b in bad), bad
    # «Русагро» при этом остаётся в заголовке карточки — потеря из поля
    # допустима с замечанием; имя, которого больше нигде нет, — отказ.
    val = dict(id="x1", field="eco.val", old=card["eco"]["val"],
               new="Руководитель департамента M&A BGP Capital Пётр Сидоров оценивает капитализацию "
                   "холдинга в 38–43 млрд ₽.")
    bad, _ = proofread.check(val, card)
    assert any("имена, которых не было" in b for b in bad), bad
    assert any("пропало имя" in b for b in bad), bad
    # Иванов на Ивана не ложится — общее начало короче пяти знаков.
    assert not proofread.name_match("Иванов", "Иван")
    assert proofread.name_match("Пешкова", "Пешков") and proofread.name_match("Ивана", "Иван")


def test_number_may_leave_a_field_only_if_it_stays_on_the_card():
    """Дубль между полями снимается, факт с карточки — нет."""
    card = card_fixture()
    terms = dict(id="x1", field="law.terms", old=card["law"]["terms"],
                 new="Условия сделки включают гарантийное обеспечение порядка 6 млрд ₽ по "
                     "налоговым доначислениям за 2021–2024 годы.")
    bad, notes = proofread.check(terms, card)
    assert not bad, bad
    assert any("77.5%" in n for n in notes), notes    # 31 и 77,5% остались в eco.fin
    # Если после правок карточки числа нигде нет — отказ.
    after = copy.deepcopy(card)
    after["eco"]["fin"] = "Сумма не раскрыта."
    after["sum"] = "Не раскрыта"
    after["events"][0]["note"] = "Сделка закрыта."
    bad, _ = proofread.check(terms, card, after)
    assert any("пропали числа" in b for b in bad), bad


def test_press_parenthetical_numbers_do_not_count_as_lost():
    """«(Retail.ru, 30 июня 2025 года)» — дата заметки, не факт сделки."""
    card = card_fixture()
    edit = dict(id="x1", field="law.appr", old=card["law"]["appr"],
                new="Выход на биржу стал обязательным после предписания ФАС; торги начались.")
    bad, _ = proofread.check(edit, card)
    assert not bad, bad
    # А орган из «Согласований» пропасть не может.
    bad, _ = proofread.check(dict(edit, new="Выход на биржу стал обязательным; торги начались."), card)
    assert any("органа" in b for b in bad), bad


def test_long_quote_and_straight_quotes_are_refused():
    card = card_fixture()
    edit = dict(id="x1", field="eco.fin", old=card["eco"]["fin"], new=GOOD_FIN)
    long_q = GOOD_FIN + " «Сделка закрыта и оплачена полностью в срок по договору», — говорится в отчётности."
    bad, _ = proofread.check(dict(edit, new=long_q), card)
    assert any("длинная цитата" in b for b in bad), bad
    bad, _ = proofread.check(dict(edit, new=GOOD_FIN.replace("«Русагро»", '"Русагро"')), card)
    assert any("кавычки" in b for b in bad), bad


def test_structural_fields_and_placeholders_are_refused():
    card = card_fixture()
    bad, _ = proofread.check(dict(id="x1", field="sum", old="31 млрд ₽", new="31 млрд ₽."), card)
    assert any("не вычитывается" in b for b in bad), bad
    bad, _ = proofread.check(dict(id="x1", field="title", old=card["title"], new=card["title"] + "."), card)
    assert any("не вычитывается" in b for b in bad), bad
    bad, _ = proofread.check(dict(id="x1", field="eco.context", old="—", new="Контекст."), card)
    assert any("заглушка" in b for b in bad), bad
    bad, _ = proofread.check(dict(id="x1", field="eco.fin", old=card["eco"]["fin"], new="—"), card)
    assert any("заглушка" in b for b in bad), bad


def test_event_note_is_addressed_as_events_index_note():
    card = card_fixture()
    edit = dict(id="x1", field="events.0.note", old=card["events"][0]["note"],
                new="Сделка закрыта; сумма — 31 млрд ₽.")
    bad, _ = proofread.check(edit, card)
    assert not bad, bad
    assert proofread.get_field(card, "events.0.note") == card["events"][0]["note"]
    assert proofread.get_field(card, "events.5.note") is None


def test_stamp_is_idempotent():
    card = {"id": "y"}
    assert proofread.stamp_proofread(card, "2026-09-02") is True
    assert proofread.stamp_proofread(card, "2026-09-03") is False
    assert card["proofread"] == "2026-09-02"


def test_run_writes_whole_cards_only_and_second_run_changes_nothing(monkeypatch):
    """Карточка с отказом не трогается; повторный прогон — пустой."""
    card = card_fixture()
    other = card_fixture()
    other["id"] = "x2"
    data = {"deals": [card, other], "companies": {}}
    monkeypatch.setattr(proofread, "unapplied_fixes", lambda c, fields=None: [])
    monkeypatch.setattr(proofread, "absorb_fixes", lambda c, fields: 0)
    edits = [
        dict(id="x1", field="eco.fin", old=card["eco"]["fin"], new=GOOD_FIN),
        dict(id="x2", field="eco.fin", old=other["eco"]["fin"], new=GOOD_FIN),
        dict(id="x2", field="eco.val", old=other["eco"]["val"],
             new="Капитализация холдинга — 38–43 млрд ₽ по оценке Ивана Петрова."),   # чужое имя
    ]
    log = []
    changed = proofread.run(edits, data, write=True, day="2026-09-02", out=log.append)
    assert changed == 1
    assert card["eco"]["fin"] == GOOD_FIN and card["proofread"] == "2026-09-02"
    assert "proofread" not in other and other["eco"]["fin"] != GOOD_FIN, "карточка с отказом записана"
    # Второй прогон с теми же правками: x1 «уже применено», ничего не пишется.
    log.clear()
    again = proofread.run(edits[:1], data, write=True, day="2026-09-03", out=log.append)
    assert again in (0, 1) and card["proofread"] == "2026-09-02"
    assert any("уже применено" in line for line in log)


def test_fixes_table_survives_proofreading():
    """Запись FIXES, применённая ДО вычитки, считается применённой и после неё;
    запись, добавленная ПОСЛЕ, — нет (иначе review.py пропустил бы её навсегда)."""
    import review
    card = {"id": "z", "eco": {"context": "Старый текст с фактом о 5 млрд руб."}}
    fix = {"id": "z", "field": "eco.context", "old": None,
           "new": "Старый текст с фактом о 5 млрд руб.", "quote": "…", "why": "…"}
    assert review.already_applied(fix, card)
    monkeypatch_fixes = [fix]
    saved = review.FIXES
    try:
        review.FIXES = monkeypatch_fixes
        assert proofread.unapplied_fixes(card) == []
        proofread.absorb_fixes(card, {"eco.context"})
        card["eco"]["context"] = "Старый текст с фактом о 5 млрд ₽ — вычитанный."
        assert review.already_applied(fix, card), "запись, применённая до вычитки, потеряна"
        later = dict(fix, new="Совсем другой факт о 7 млрд руб.")
        assert not review.already_applied(later, card), "запись после вычитки объявлена применённой"
        # Пока есть неприменённая запись — вычитка отказывает в записи карточки.
        review.FIXES = [later]
        assert proofread.unapplied_fixes(card) == [later]
    finally:
        review.FIXES = saved
    assert review.fix_fingerprint("a «b» c") == review.fix_fingerprint('a "b" c')


def test_samples_pass_the_check():
    """Образцы для владельца (pipeline/proofread_samples/) обязаны проходить
    проверку целиком: это и есть демонстрация правил на живых карточках.
    Проверяется, только пока карточки ещё не вычитаны в базе."""
    base = json.loads((ROOT / "static" / "data" / "deals_promoted.json").read_text(encoding="utf-8"))
    for path in sorted((ROOT / "pipeline" / "proofread_samples").glob("*.json")):
        edits = json.loads(path.read_text(encoding="utf-8"))
        log = []
        code = proofread.run(edits, base, write=False, out=log.append)
        refused = [line for line in log if line.strip().startswith("ОТКАЗ")
                   and "поле уже другое" not in line]
        assert not refused, f"{path.name}: {refused[:3]}"
        assert code in (0, 1)


@pytest.mark.parametrize("field", proofread.PROOFREAD_FIELDS)
def test_allowed_fields_are_prose_only(field):
    assert proofread.field_allowed(field)
    assert not proofread.field_allowed("sum") and not proofread.field_allowed("law.adv")
    assert proofread.field_allowed("events.0.note") and not proofread.field_allowed("events.0.date")

def test_outlets_found_by_the_running_routine_are_recognised():
    """Прогоны вычитки 1-9 (3 сентября 2026) девять раз подряд упирались в один
    и тот же класс: издание не в списке — значит его имя нельзя снять, не
    получив отказ «из new пропало имя». Список расширен по факту, а не на глаз;
    настоящие имена компаний по-прежнему именами и остаются."""
    for outlet in ('Хабр', 'Хабра', 'Абирега', 'Известий', 'ADPASS', 'PrimaMedia',
                   'УФА1.ру', 'МР7.ру', 'Ъ-СПб', 'НГ.ru', 'Прайм', 'АКМ',
                   'ФВ', 'ДП', 'ЧП', 'СМИ'):
        assert proofread.outlet_like(outlet), outlet
    for name in ('Сбербанк', 'Яндекс', 'Русагро', 'Транснефть', 'Ковалёва',
                 'Хабаровск', 'Новый', 'Прайс'):
        assert not proofread.outlet_like(name), name


def test_attribution_to_a_newly_listed_outlet_can_be_removed():
    """Снятие «по данным Хабра» больше не считается потерей имени: до правки
    проверка требовала сохранить «Хабра» как имя собственное."""
    card = card_fixture()
    card["eco"]["fin"] = "По данным Хабра, выручка выросла до 5 млрд \u20bd."
    edit = dict(id="x1", field="eco.fin", old=card["eco"]["fin"],
                new="Выручка выросла до 5 млрд \u20bd.")
    bad, _ = proofread.check(edit, card)
    assert not any("пропало имя" in b for b in bad), bad


def test_marking_one_card_clean_is_actually_written(tmp_path, monkeypatch, capsys):
    """Прогон, записавший РОВНО ОДНУ карточку, обязан сохраниться на диск.

    `run` возвращает и число записанных карточек, и код ошибки (0/1), а `main`
    раньше считал единицу кодом ошибки — и `--mark-clean <один id>` молча не
    писал ничего: скрипт печатал «карточек к записи 1», штамп не появлялся,
    карточка возвращалась в очередь на следующий час навсегда. Тот же класс,
    что «„готово“ подменяет „мы перестали пытаться“» из CLAUDE.md.
    """
    base = {"deals": [{"id": "solo", "title": "Карточка, которую править нечем",
                       "extra": "—"}], "companies": {}}
    data_file = tmp_path / "deals_promoted.json"
    data_file.write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(proofread, "DATA", str(data_file))

    assert proofread.main(["--write", "--mark-clean", "solo"]) == 0
    assert "ЗАПИСАНО: 1" in capsys.readouterr().out

    written = json.loads(data_file.read_text(encoding="utf-8"))
    assert written["deals"][0].get("proofread"), "штамп не попал на диск"
