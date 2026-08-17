# -*- coding: utf-8 -*-
"""g0201b97a («Ингосстрах» продал «Ингосстрах Банк» холдингу «Авторитэйл»)
несла в заголовке «99,99%» — опечатку, которую не заметили при вычитке
23 карточек 2026 года, попавшую туда, видимо, при первом разборе (у карточки
уже есть deep_researched/followup_researched пометки, но именно заголовок
это чтение не задело). Найдено ночной вычиткой 40 карточек (17-18 августа
2026): собственная eco.rationale карточки говорит «100%», заголовок — «99,99%»,
а ТРИ независимых источника (Интерфакс, Ведомости, АСН-Новости) сходятся на
третьем, отличном от обоих, значении.

Дословная цитата (data/inbox/raw, https://www.interfax.ru/business/1011377,
идентично у vedomosti.ru/.../1095294-ingosstrah-prodal-bank и asn-news.ru/
news/88904 — забрано fetch_article_texts.py 17.08.2026):

    «На момент принятия решения о сделке компания "Ингосстрах" контролировала
    99,9% в капитале банка.»

99,9% — не 99,99% (опечатка в заголовке) и не 100% (округление в
eco.rationale, которое эта правка не трогает: «продал 100% акций» там же
относится к самой сделке купли-продажи, а не к доле Ингосстраха ДО неё,
разница в один разряд процента не считается противоречием).

Запуск:
    python3 pipeline/fix_ingosstrah_bank_stake_typo.py            # сухой прогон
    python3 pipeline/fix_ingosstrah_bank_stake_typo.py --write     # запись
"""
import json
import sys

PATH = "static/data/deals_promoted.json"
ID = "g0201b97a"

OLD_TITLE = 'Продажа «Ингосстрахом» 99,99% акций АО «Ингосстрах Банк» холдингу ГК «Авторитэйл»'
NEW_TITLE = 'Продажа «Ингосстрахом» 99,9% акций АО «Ингосстрах Банк» холдингу ГК «Авторитэйл»'


def main(write):
    with open(PATH, encoding="utf-8") as f:
        base = json.load(f)
    by_id = {d["id"]: d for d in base["deals"]}
    d = by_id.get(ID)
    assert d is not None, f"{ID} не найдена"

    assert d["title"] == OLD_TITLE, "title уже другой — уже правили?"
    d["title"] = NEW_TITLE
    print(f"{ID}: title (99,99% -> 99,9%) исправлен")

    if write:
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(base, f, ensure_ascii=False, indent=1)
        print("\nЗАПИСАНО.")
    else:
        print("\nСухой прогон — ничего не записано. Добавьте --write.")


if __name__ == "__main__":
    main(write="--write" in sys.argv)
