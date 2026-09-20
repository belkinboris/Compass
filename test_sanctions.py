# -*- coding: utf-8 -*-
"""Санкционная отметка у людей: что можно писать, а что нельзя.

Главное, что здесь проверяется, — не механика сведения имён, а запрет:
на сайт попадает только то, что человек прочитал и сверил. Ошибка в этом
месте — не опечатка в цифре, а обвинение живого человека.
"""
import io
import json
import os

import pytest

from pipeline import sanctions_match as sm

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(io.open(os.path.join(ROOT, "static", "data", "deals_promoted.json"),
                         encoding="utf-8"))
CONFIRMED = sm.load_confirmed()
REJECTED = sm.load_rejected()


def test_confirmed_and_rejected_do_not_overlap():
    both = set(CONFIRMED) & set(REJECTED)
    assert not both, "профиль одновременно сверен и отклонён: %s" % both


def test_every_confirmed_mark_names_a_list_and_a_document():
    for cid, marks in CONFIRMED.items():
        assert cid in DATA["companies"], "сверен профиль, которого нет в базе: %s" % cid
        assert marks, "пустая отметка у %s" % cid
        for m in marks:
            assert m["list"] in sm.LIST_LABEL, (cid, m)
            assert m["kind"] in ("person", "entity"), (cid, m)
            assert m["url"].startswith("https://"), (cid, m)
            assert m.get("why"), "не сказано, чем подтверждено совпадение: %s" % cid
            if m.get("matched_by") == "inn":
                assert m.get("inn"), "отметка по ИНН без самого ИНН: %s" % cid


def test_inn_marks_really_repeat_the_inn_from_the_registry():
    """Отметка «совпал ИНН» обязана совпадать с реестром ФНС, а не с памятью."""
    inns = sm.base_inns()
    for cid, marks in CONFIRMED.items():
        for m in marks:
            if m.get("matched_by") == "inn":
                assert inns.get(cid) == m["inn"], (cid, m["inn"], inns.get(cid))


def test_company_name_key_survives_the_legal_form():
    assert sm.entity_key("ПАО Сбербанк") == sm.entity_key("PJSC SBERBANK")
    assert sm.entity_key("ООО «Лузалес»") == sm.entity_key("LUZALES LLC")


def test_a_name_made_only_of_common_business_words_gets_no_key():
    """Иначе «РТ-Инвест» сходится с «M INVEST, OOO», а это разные компании."""
    for name in ("Capital Group", "KR Properties", "РТ-Инвест", "Digital Security"):
        assert sm.entity_key(name) == "", name


def test_common_words_stay_inside_the_key():
    """«Почта Банк» и «Почта России» — разные компании, и ключи у них разные."""
    assert sm.entity_key("Почта Банк") != sm.entity_key("Почта России")
    assert sm.entity_key("Яндекс") != sm.entity_key("АО Яндекс Банк")
    assert sm.entity_key("Сахалин-2") != sm.entity_key("Сахалин-8")


def test_site_shows_only_what_a_human_confirmed():
    for cid, c in DATA["companies"].items():
        marks = c.get("sanctions")
        if not marks:
            continue
        assert cid in CONFIRMED, "отметка в базе без сверки человеком: %s" % cid
        assert [m["list"] for m in marks] == [m["list"] for m in CONFIRMED[cid]]


def test_base_matches_the_confirmed_file():
    """Правка файла сверки без --write оставила бы сайт со старой отметкой."""
    copy = json.loads(json.dumps(DATA))
    assert sm.apply_to_base(copy, CONFIRMED) == 0


def test_rejected_entries_say_why():
    for cid, why in REJECTED.items():
        assert cid in DATA["companies"], cid
        assert len(why) > 40, "причина отказа должна быть читаемой фразой: %s" % cid


def test_name_key_survives_different_spellings():
    """Одно имя в трёх странах пишут по-разному — ключ обязан совпасть."""
    ru = sm.key_of("Алексей Мордашов")
    assert ru == sm.key_of("Alexey Alexandrovich MORDASHOV")
    assert ru == sm.key_of("Alexej Mordašov")
    assert ru == sm.key_of("Aleksej Aleksandrovitj MORDASJOV")
    assert sm.key_of("Артём Чайка") == sm.key_of("Артём Юрьевич ЧАЙКА")


def test_different_people_get_different_keys():
    assert sm.key_of("Дмитрий Хотимский") != sm.key_of("Сергей Хотимский")
    assert sm.key_of("Искандер Махмудов") != sm.key_of("Искандер Махмудова")


def test_company_is_not_mistaken_for_a_person():
    for name in ("ООО Лузалес", "ГК «Урбантех»", "Восток Ойл", "Синтерра Медиа",
                 "Сбербанк", "Фольксваген Груп Рус"):
        assert not sm.looks_like_person(name), name
    for name in ("Искандер Махмудов", "Елена Батурина", "Осина Екатерина Борисовна"):
        assert sm.looks_like_person(name), name


@pytest.mark.skipif(not os.path.exists(os.path.join(sm.LISTS_DIR, "SDN.CSV")),
                    reason="перечни не скачаны (--fetch)")
def test_confirmed_people_are_still_in_the_lists():
    """Санкции снимают — отметка не должна пережить исключение из списка."""
    assert sm.main(["--check"]) == 0
