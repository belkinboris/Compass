# -*- coding: utf-8 -*-
"""Документы, которые читает КАЖДЫЙ прогон, не должны расти сами.

PRODUCT_ROADMAP.md и CLAUDE.md — постоянная стоимость любой работы: их
читают все три рутины каждый час. Поэтому у них есть потолок, а у бэклога —
правило «здесь только открытая работа». Тесты ниже не про красоту файла, а
про счёт: без них файл отрастает обратно, и налог на каждый следующий
прогон растёт сам собой (это уже случалось с журналом работ).
"""
import io
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
ROADMAP = io.open(os.path.join(ROOT, "PRODUCT_ROADMAP.md"), encoding="utf-8").read()
CLAUDE = io.open(os.path.join(ROOT, "CLAUDE.md"), encoding="utf-8").read()
BACKLOG = ROADMAP[ROADMAP.index("## 4. Бэклог"):ROADMAP.index("## 5. Журнал работ")]
JOURNAL = ROADMAP[ROADMAP.index("## 5. Журнал работ"):]

# Замер 20 сентября 2026 — 168 798 знаков после переноса закрытого в архив.
# Запас взят небольшой намеренно: как только он выбран, это сигнал сдвинуть
# журнал (`roadmap_archive.py --journal --write`), а не поднять потолок.
ROADMAP_LIMIT = 200_000
# 24 сентября 2026 CLAUDE.md разнесён по месту чтения: 97 → 17 тыс. знаков.
# Правило одной рутины живёт в routines/, устройство подсистемы — в docs/.
# Потолок взят с запасом под правила, нужные КАЖДОМУ прогону, — и только им.
CLAUDE_LIMIT = 30_000
VERDICT = re.compile(r"\b(ЗАКРЫТ|СДЕЛАН|ПРОВЕРЕН|СНЯТ|ИСЧЕРПАН)[А-ЯЁ]*\b")
# Вердикт о готовности пишут жирным («**СДЕЛАНО 30 августа**»). Те же слова
# в обычном тексте — про подвопрос внутри ещё открытой задачи («вопрос закрыт
# чтением источника»), и это не повод считать задачу сделанной.
BOLD_VERDICT = re.compile(r"\*\*\s*(ЗАКРЫТ|СДЕЛАН|ПРОВЕРЕН|ГОТОВ)[А-ЯЁ]*\b")


def _items(text):
    """Пункты бэклога. Пункт кончается на следующем пункте ИЛИ на заголовке
    блока: последний пункт блока иначе «съедает» заголовок соседнего вместе
    с его вступлением — ровно так 20 сентября 2026 пропал блок «E. Живая
    база», и тот же промах сначала был в этой проверке."""
    starts = [m.start() for m in re.finditer(r"^- ", text, re.M)]
    out = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(text)
        body = text[s:e]
        head = re.search(r"^#{2,3} ", body[1:], re.M)
        if head:
            body = body[:1 + head.start()]
        out.append(body)
    return out


def test_roadmap_stays_within_its_budget():
    assert len(ROADMAP) <= ROADMAP_LIMIT, (
        "PRODUCT_ROADMAP.md вырос до %d знаков при потолке %d — сдвиньте журнал "
        "и закрытые пункты в архив: python3 pipeline/roadmap_archive.py "
        "--journal --write" % (len(ROADMAP), ROADMAP_LIMIT))


def test_claude_md_stays_within_its_budget():
    assert len(CLAUDE) <= CLAUDE_LIMIT, (
        "CLAUDE.md вырос до %d знаков при потолке %d — здесь живут правила, "
        "а не очереди и не журнал" % (len(CLAUDE), CLAUDE_LIMIT))


def test_a_searched_document_keeps_its_answer_the_size_of_one_entry():
    """У KNOWN_ISSUES.md и архива потолка НЕТ намеренно — вместо него этот тест.

    21 сентября 2026 потолок на KNOWN_ISSUES.md простоял полдня и был снят по
    возражению владельца, и возражение точное: «просто не будет хватать места
    к примеру в known issues на запись новых проблем и решений, а в таком
    случае они каждый раз будут вырабатываться заново». То есть потолок на
    ЭТОМ файле экономит ровно те токены, ради которых он и ставился, — и
    тратит их заново при каждом переоткрытии забытого бага.

    Разница между двумя видами документов не в важности, а в способе чтения.
    CLAUDE.md читают ЦЕЛИКОМ каждый прогон: там каждый знак умножается на
    число прогонов, и потолок — единственное, что держит его коротким.
    KNOWN_ISSUES.md и архив ИЩУТ по запросу (`docs_budget.py --find`): цена
    вопроса равна размеру ОДНОЙ записи, а не файла, и файл может расти вечно,
    пока это так. Поэтому проверяется не длина файла, а то, от чего зависит
    цена ответа: каждая запись живёт под своим заголовком (иначе поиск
    вернёт соседнюю) и ни одна не разрослась до размера, при котором её
    дешевле не открывать.
    """
    import pipeline.docs_budget as db

    for name, (level, _what) in db.SEARCHED.items():
        text = io.open(os.path.join(ROOT, name), encoding="utf-8").read()
        entries = db._entries(name, text)
        assert entries, "%s: ни одной записи уровня «%s» — поиск вернёт весь файл" % (name, level)
        # Текст ВНЕ записей — то, что поиск не найдёт никогда. Шапка файла
        # (объяснение, зачем он) — законное исключение, поэтому меряем хвост
        # после первого заголовка, а не весь остаток.
        first = text.index("\n" + level + " ") if ("\n" + level + " ") in text else 0
        covered = sum(len(e[2]) for e in entries)
        tail = len(text) - first
        assert covered >= tail * 0.8, (
            "%s: под заголовками лежит %d знаков из %d — остальное поиск не "
            "найдёт, потому что оно не принадлежит ни одной записи" % (name, covered, tail))
        if name != "KNOWN_ISSUES.md":
            # Размер записи архива решается НЕ здесь: архив только принимает
            # записи журнала, которые до этого лежали в PRODUCT_ROADMAP.md под
            # жёстким потолком в 200 тыс. знаков. Запись на 55 тыс. съела бы
            # там четверть потолка и была бы видна задолго до переезда, так
            # что второй забор на выходе ничего не добавляет. Две такие
            # записи в архиве есть (июль–август 2026, до разделения журнала) —
            # переписывать историю ради косметики незачем.
            continue
        # Замер 21 сентября 2026: 356 записей, медиана 579 знаков, самая
        # длинная 9 798. Потолок взят чуть выше сегодняшнего максимума — он
        # ловит не рост файла (файл пусть растёт), а запись, которая
        # перестала быть ответом на один вопрос и стала главой.
        big = [(e[0], e[1][:60], len(e[2])) for e in entries if len(e[2]) > 12_000]
        assert not big, (
            "%s: запись выросла до размера главы — открыть её будет почти так же "
            "дорого, как весь файл: %s. Разбейте по симптомам: одна запись — "
            "один ответ." % (name, big))


def test_a_finished_item_does_not_pretend_to_be_open():
    """Хуже зачёркнутого пункта только незачёркнутый, который уже сделан.

    20 сентября 2026 в бэклоге стояли открытыми G12 и G13, а внутри у обоих
    было написано «СДЕЛАНО 30 августа». Читатель бэклога видел работу,
    которой нет."""
    liars = []
    for item in _items(BACKLOG):
        if item.startswith("- ~~"):
            continue
        head = item.split("\n")[0]
        if BOLD_VERDICT.search(item) and not VERDICT.search(head):
            liars.append(re.sub(r"\s+", " ", head)[:80])
    assert not liars, "пункт не зачёркнут, но внутри вердикт о готовности: %s" % liars


def test_a_closed_item_leaves_only_a_line():
    """Закрытый пункт остаётся строкой-напоминанием, а разбор уезжает в архив."""
    long = []
    for item in _items(BACKLOG):
        if item.startswith("- ~~") and len(item) > 700:
            long.append(re.sub(r"\s+", " ", item)[:80])
    assert not long, ("закрытый пункт всё ещё несёт разбор (>700 знаков): %s — "
                      "перенесите: python3 pipeline/roadmap_archive.py --archive "
                      "--write" % long)


def test_every_backlog_block_keeps_its_heading():
    """Заголовок блока — не украшение: по нему видно, какое направление ещё
    открыто, а какое пройдено целиком.

    20 сентября 2026 моя разовая правка заглушки последнего пункта блока A
    забрала с собой заголовок «E. Живая база» и абзац о том, как устроен
    приток: регулярка `.*?(?=^- |\Z)` дотянулась до следующего ПУНКТА, а
    между ними стоял заголовок соседнего блока. Четыре открытых пункта E
    после этого читались как пункты A. Список ниже меняется только
    осознанно — когда направление закрыто целиком и блок убран руками."""
    blocks = re.findall(r"^### ([A-ZА-Я])\.", BACKLOG, re.M)
    assert blocks == ["A", "E", "B", "C", "D", "F", "G"], blocks


def test_the_journal_in_the_main_file_is_short():
    days = sorted({m.group(1) for m in
                   re.finditer(r"^### (\d{4}-\d{2}-\d{2})", JOURNAL, re.M)})
    assert len(days) <= 3, (
        "в основном файле журнал за %d дней (%s…%s) — сдвиньте старые записи: "
        "python3 pipeline/roadmap_archive.py --journal --write"
        % (len(days), days[0], days[-1]))


def test_the_release_step_is_written_down_where_it_is_read():
    """Шаг «выложить код в release» записан в правилах, а не в голове.

    22 сентября 2026 ветка задачи была сведена в `main`, полный pytest
    прошёл, всё выложено — и на сайте не появилось ничего. Прод собирается
    из ветки `release`, а не из `main`: туда идёт только код, данные сайт
    тянет сам. Шаг держался в pull request'ах, то есть нигде, и владелец в
    это время не находил кнопку, которую мы «уже сделали».

    Тест держит связку из трёх частей: правило названо в CLAUDE.md, у него
    есть исполнитель (`pipeline/release.py`), и оба говорят про одну ветку.
    """
    claude = io.open(os.path.join(ROOT, "CLAUDE.md"), encoding="utf-8").read()
    assert "release" in claude, "в правилах не сказано, что код выкладывается в release"
    assert "pipeline/release.py" in claude, "правило есть, а чем его выполнить — не сказано"

    script = os.path.join(ROOT, "pipeline", "release.py")
    assert os.path.exists(script), "правило ссылается на скрипт, которого нет"
    text = io.open(script, encoding="utf-8").read()
    assert "data_refresh" in text, "скрипт не объясняет, почему данные не требуют пересборки"


def test_a_document_with_a_cyrillic_name_is_not_deployed_as_code():
    """git экранирует кириллические имена — и проверка суффикса на них молчит.

    `git diff --name-only` отдаёт «finance/ЗАПИСКА.md» как
    "finance/\\320\\227..." в кавычках, поэтому path.endswith(".md") не
    срабатывает и документ уезжает в `release` как код, вызывая пересборку
    сайта. Пересборка на каждый коммит однажды уложила сайт на девять минут,
    ради чего release.py и сравнивает ветки по коду.
    """
    from pipeline import release
    assert release.is_code("main.py")
    assert release.is_code("pipeline/ingest/draft.py")
    assert not release.is_code("CLAUDE.md")
    assert not release.is_code("finance/ЗАПИСКА_финмодель.md")
    assert not release.is_code("finance/Компас_финмодель_24м.xlsx")
    assert not release.is_code("finance/build_model.py")
    assert not release.is_code("static/data/deals_promoted.json")


# ---------------------------------------------------------------------------
# Документы, которые читаются на шаге (24 сентября 2026)
# ---------------------------------------------------------------------------

def _governed():
    """CLAUDE.md, файлы рутин и документы подсистем — то, что прогон читает
    сам, а не находит поиском. Тексты запуска до переноса — архив, в них
    ссылки на старые места законны."""
    out = {"CLAUDE.md": CLAUDE}
    for folder in ("routines", "docs"):
        base = os.path.join(ROOT, folder)
        for name in sorted(os.listdir(base)):
            if name.endswith(".md") and not name.startswith("launch_texts_"):
                out["%s/%s" % (folder, name)] = io.open(
                    os.path.join(base, name), encoding="utf-8").read()
    return out


def test_every_routine_has_its_file_and_every_file_its_routine():
    """Порядок работы рутины лежит в её файле, а текст запуска только
    ссылается на него. Таблица в routines/README.md — единственный список:
    файл без строки в таблице никто не запустит, строка без файла —
    рутина, которой некуда смотреть."""
    readme = io.open(os.path.join(ROOT, "routines", "README.md"), encoding="utf-8").read()
    listed = set(re.findall(r"`(routines/[a-z_]+\.md)`", readme))
    on_disk = {"routines/%s" % n for n in os.listdir(os.path.join(ROOT, "routines"))
               if n.endswith(".md") and n != "README.md" and not n.startswith("launch_texts_")}
    assert listed == on_disk, "таблица рутин и файлы разошлись: %s" % (listed ^ on_disk)
    assert "routines/" in CLAUDE, "CLAUDE.md не говорит рутине, где её порядок работы"


def test_a_document_read_on_a_step_is_split_not_trimmed():
    """У файла рутины и документа подсистемы потолок есть, но он значит
    «разделите по темам», а не «вычистите»: владелец 24 сентября 2026 —
    «мы не можем сказать: начинаем выборочно удалять проблемы, потому что
    знаков слишком много»."""
    import pipeline.docs_budget as db
    big = [(name, len(io.open(os.path.join(ROOT, name), encoding="utf-8").read()), limit)
           for name, limit, _how in db.step_docs()
           if len(io.open(os.path.join(ROOT, name), encoding="utf-8").read()) > limit]
    assert not big, ("документ перерос свой потолок — разделите его по темам на два "
                     "и поправьте карту в CLAUDE.md, ничего не вычищая: %s" % big)


_REF_FILE = re.compile(r"`?((?:docs|routines|pipeline)/[\w./-]+\.md)`?")
_REF_SECTION = re.compile(r"(?:раздел[а-я]*|см\.)\s+((?:«(?:[^«»]|«[^«»]*»)+»(?:,\s*|\s+и\s+)?)+)")


def _headings(include_archive=False):
    heads = []
    for dirpath, _dirs, files in os.walk(ROOT):
        if "/." in dirpath or "node_modules" in dirpath or "/data/" in dirpath + "/":
            continue
        for f in files:
            if not f.endswith(".md") or (not include_archive and "ARCHIVE" in f):
                continue
            text = io.open(os.path.join(dirpath, f), encoding="utf-8").read()
            heads += re.findall(r"(?m)^#{1,6}\s+(.+)$", text)
    return heads


def _norm(x):
    return re.sub(r"[«»\"„“”`\s]+", " ", x).strip().lower()


def test_every_reference_in_the_read_documents_leads_somewhere():
    """Ссылка на документ или раздел, которого нет, — знание без адреса.

    24 сентября 2026 при переносе CLAUDE.md нашлось: таблица рутин
    отсылала к разделу «Конкурент раньше и богаче», стёртому чисткой
    18 сентября, — вместе с ним пропали правило «новая сделка — первой» и
    нерешённый вопрос владельцу о частоте притока; текст запуска притока
    велел читать раздел, которого давно не было. Проверяются документы,
    которые прогон читает сам; ссылка может вести и в архив — он ищется,
    — но тогда раздел должен там найтись."""
    heads = [_norm(h) for h in _headings(include_archive=True)]
    missing = []
    for name, text in _governed().items():
        for path in _REF_FILE.findall(text):
            if not os.path.exists(os.path.join(ROOT, path.rstrip("."))):
                missing.append("%s → файл %s" % (name, path))
        for group in _REF_SECTION.findall(text):
            for ref in re.findall(r"«((?:[^«»]|«[^«»]*»)+)»", group):
                r = _norm(ref)
                if len(r) < 6 or any(r in h for h in heads):
                    continue
                missing.append("%s → раздел «%s»" % (name, ref))
    assert not missing, "ссылки ведут в никуда:\n  " + "\n  ".join(missing)
