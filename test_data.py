"""Инварианты базы: то, что должно быть верно после любого прогона pipeline.

Раньше эти проверки жили одноразовыми скриптами в прогонах и умирали вместе с
ними: каждое соглашение из CLAUDE.md приходилось перепроверять руками. Здесь
закреплены те инварианты, которые сегодня держатся, — тест, падающий с первого
дня, никто не чинит, его отключают.

Запуск: python3 -m pytest test_data.py -q
"""
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "static" / "data" / "deals_promoted.json"
INDEX = ROOT / "static" / "index.html"
REF_FIELDS = ("buyer", "target", "seller_id", "asset_id")


@pytest.fixture(scope="module")
def base():
    return json.loads(DATA.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def deals(base):
    return base["deals"]


@pytest.fixture(scope="module")
def companies(base):
    return base["companies"]


@pytest.fixture(scope="module")
def all_company_ids(base):
    """Профили лежат в двух местах: JSON и захардкоженный блок в index.html.

    Без второго 68 ссылок из сделок выглядят битыми, хотя они рабочие.
    """
    html = INDEX.read_text(encoding="utf-8")
    tail = html[html.index("const COMPANIES = {"):]
    block = tail[:tail.index("\n};")]
    hardcoded = set(re.findall(r"^\s{2}([A-Za-z0-9_-]+)\s*:\s*\{", block, re.M))
    assert hardcoded, "не удалось прочитать захардкоженные профили из index.html"
    return set(base["companies"]) | hardcoded


def ids_of(rows):
    return [r["id"] for r in rows]


# ---------- целостность ----------

def test_ids_unique(deals):
    dups = [i for i, n in Counter(ids_of(deals)).items() if n > 1]
    assert not dups, f"повторяющиеся id сделок: {dups[:5]}"


def test_company_refs_resolve(deals, all_company_ids):
    broken = [(d["id"], f, d[f]) for d in deals for f in REF_FIELDS
              if d.get(f) and d[f] not in all_company_ids]
    assert not broken, f"ссылки на несуществующие профили: {broken[:5]}"


def test_match_keys_point_to_existing_profiles(base, all_company_ids):
    orphan = [k for k in base["match_keys"] if k not in all_company_ids]
    assert not orphan, f"match_keys без профиля: {orphan[:5]}"


def test_match_key_aliases_are_non_empty_strings(base):
    """Пустой СПИСОК алиасов допустим и осмыслен: у профиля «Первый» он пуст
    нарочно — по такому слову автопоиск дал бы сплошные ложные совпадения.
    А вот пустая строка внутри списка совпала бы с чем угодно."""
    bad = [k for k, v in base["match_keys"].items()
           if any(not str(x).strip() for x in v)]
    assert not bad, f"пустые алиасы: {bad[:5]}"


# ---------- роли сторон ----------

def test_buyer_is_not_seller(deals):
    conflict = [(d["id"], d["buyer"]) for d in deals
                if d.get("buyer") and d.get("buyer") == d.get("seller_id")]
    assert not conflict, f"компания одновременно покупатель и продавец: {conflict[:5]}"


PLACEHOLDER = re.compile(
    r"^(?:[—-]|н/д|не\s+раскры[а-яё]*|публично\s+не\s+[а-яё]+)[.\s]*$", re.I)


ROLE_PAIRS = (("buyer", "target"), ("buyer", "seller_id"), ("target", "seller_id"),
              ("buyer", "asset_id"), ("seller_id", "asset_id"), ("target", "asset_id"))


def test_one_company_holds_one_role_in_a_deal(deals):
    """Компания не может быть в одной сделке и продавцом, и предметом.

    Прогон 32: у трёх карточек профиль продавца стоял в `target` — «Черкизово
    приобрела пять компаний у банка „Траст"», а предметом сделки числился сам
    «Траст». Проверка ловит этот класс целиком, а не только пару покупатель —
    продавец, которая проверялась раньше.
    """
    bad = [(d["id"], a, b) for d in deals for a, b in ROLE_PAIRS
           if d.get(a) and d.get(a) == d.get(b)]
    assert not bad, f"одна компания в двух ролях: {bad[:5]}"


def test_seller_is_not_a_placeholder(deals):
    """«Продавец: не раскрыт» — это пустое поле, а не имя стороны."""
    bad = [(d["id"], d["seller"]) for d in deals
           if d.get("seller") and PLACEHOLDER.match(str(d["seller"]).strip())]
    assert not bad, f"заглушка записана как продавец: {bad[:5]}"


# ---------- обязательные поля ----------

def test_every_deal_has_a_source_link(deals):
    bad = [d["id"] for d in deals
           if not (d.get("src") and any(str(s[1]).startswith("http")
                                        for s in d["src"] if len(s) > 1))]
    assert not bad, f"сделки без ссылки на источник: {bad[:5]}"


def test_dates_are_parseable(deals):
    """Три допустимых вида даты — и каждый что-то значит.

    «2024-03-14» — знаем день; «2024» — знаем только год (день не
    восстановился, и раньше на его месте стояла заглушка «1 января», из-за
    которой сайт утверждал день, которого не знал); «unknown» — не знаем и
    года. Ничего четвёртого быть не должно: любой другой формат сломает и
    сортировку ленты, и подсчёт по годам.
    """
    bad = [(d["id"], d.get("date")) for d in deals
           if not re.fullmatch(r"\d{4}-\d{2}-\d{2}|\d{4}|unknown", str(d.get("date") or ""))]
    assert not bad, f"нераспознаваемая дата: {bad[:5]}"


def test_no_first_of_january_placeholder(deals):
    """«1 января» в базе — почти всегда не дата сделки, а след импорта.

    Год из источника брали, месяц и день не брали. Пока такая запись лежит в
    базе, помесячный график рисует январский всплеск, которого на рынке не
    было. Восстановить день по статье-источнику удалось у 131 карточки, у
    остальных 238 день снят: осталась честная запись «2024».

    Правило не запрещает первое января насовсем — оно запрещает СТОЛПОТВОРЕНИЕ
    на нём: настоящая сделка первого января возможна, но не у сотни карточек
    сразу. Порог 5 на год оставлен с запасом.
    """
    import collections
    jan = collections.Counter(str(d.get("date"))[:4] for d in deals
                              if str(d.get("date") or "").endswith("-01-01"))
    heavy = {y: n for y, n in jan.items() if n > 5}
    assert not heavy, f"первое января снова стало заглушкой: {heavy}"


def test_industry_is_set(deals):
    bad = [d["id"] for d in deals if not d.get("ind")]
    assert not bad, f"сделки без отрасли: {bad[:5]}"


def test_industries_are_from_the_known_list(deals):
    html = INDEX.read_text(encoding="utf-8")
    listed = set(re.search(r'const INDUSTRIES\s*=\s*\[(.*?)\]', html, re.S).group(1)
                 .replace('"', '').split(","))
    listed = {x.strip() for x in listed if x.strip()}
    unknown = sorted({d["ind"] for d in deals if d.get("ind")} - listed)
    assert not unknown, f"отрасль вне списка INDUSTRIES: {unknown}"


def test_company_industries_are_from_the_known_list(companies):
    """Тот же список INDUSTRIES ещё раз строит фильтр каталога компаний
    (`<select id="coind">`, `companyRows()` фильтрует строго `c.ind===coInd`)
    — отрасль вне списка делает профиль ненаходимым НИ ПО ОДНОМУ пункту
    фильтра отрасли, хотя он остаётся виден без фильтра. До 10 августа этот
    инвариант проверялся только у сделок; у компаний нашлось четыре профиля
    вне списка («Металлургия», «Нефтесервис», «Промышленность») — починено
    `pipeline/fix_company_industries_off_list.py`."""
    html = INDEX.read_text(encoding="utf-8")
    listed = set(re.search(r'const INDUSTRIES\s*=\s*\[(.*?)\]', html, re.S).group(1)
                 .replace('"', '').split(","))
    listed = {x.strip() for x in listed if x.strip()}
    unknown = sorted({c["ind"] for c in companies.values() if c.get("ind")} - listed)
    assert not unknown, f"отрасль профиля вне списка INDUSTRIES: {unknown}"


# ---------- соглашения о записи (CLAUDE.md) ----------

WORD_CURRENCY = re.compile(
    r"\b(?:руб(?:лей|ля|\.)?|долл(?:аров|\.)?|евро|USD|EUR|RUB)\b", re.I)


def test_cover_sum_uses_currency_symbol(deals):
    """Валюта — только значком: ₽ после числа, $ и € перед (прогон 14)."""
    bad = [(d["id"], d["sum"]) for d in deals
           if d.get("sum") and WORD_CURRENCY.search(str(d["sum"]))]
    assert not bad, f"валюта словом в обложке: {bad[:5]}"


RUB_BEFORE_NUMBER = re.compile(r"₽\s*\d")


def test_ruble_sign_stands_after_the_number(deals):
    """Значок рубля — ПОСЛЕ числа, и это не косметика.

    «₽25 млрд» — англоязычная запись, просочившаяся из источника. Читателю она
    и так режет глаз рядом с «25 млрд ₽» у соседней карточки, но хуже другое:
    любое правило, читающее сумму (порог подписки, сортировка по величине),
    ищет число ПЕРЕД значком и такую запись молча не видит — сделка просто
    выпадает из выдачи, не вызвав ошибки. Правится `pipeline/normalize_sum.py`.
    """
    bad = [(d["id"], d[field]) for d in deals for field in ("sum",)
           if d.get(field) and RUB_BEFORE_NUMBER.search(str(d[field]))]
    bad += [(d["id"], d["eco"]["sum"]) for d in deals
            if isinstance(d.get("eco"), dict) and d["eco"].get("sum")
            and RUB_BEFORE_NUMBER.search(str(d["eco"]["sum"]))]
    assert not bad, f"значок рубля перед числом: {bad[:5]}"


GLUED_CURRENCY = re.compile(r"[\$€][а-яёА-ЯЁ]")


def test_currency_symbol_not_glued_to_next_word(deals):
    """«191,5 млн $по данным Financial Times» — пропущенный пробел склеивает
    значок валюты со следующим словом, и на экране это читается одним
    слипшимся куском. Значок перед ЦИФРОЙ («$191,5 млн») — верный порядок и
    не задет; проверяем только значок перед русской буквой."""
    bad = [(d["id"], d["sum"]) for d in deals
           if d.get("sum") and GLUED_CURRENCY.search(str(d["sum"]))]
    assert not bad, f"значок валюты слился со словом в обложке: {bad[:5]}"


NAMED_ESTIMATOR = re.compile(r"\((?:по\s+)?оценк[а-яё]*\s+(?-i:[А-ЯЁA-Z])", re.I)


def test_estimate_note_does_not_name_the_estimator(deals):
    """Пометка недостоверности — «(по оценке)»; кто именно оценил, живёт в
    «Оценке и дисконте». Уточнение ПРЕДМЕТА оценки («оценка 100%») — не имя
    оценщика и правилу не противоречит, поэтому проверяем заглавную букву."""
    bad = [(d["id"], d["sum"]) for d in deals
           if d.get("sum") and NAMED_ESTIMATOR.search(str(d["sum"]))]
    assert not bad, f"имя оценщика в пометке суммы: {bad[:5]}"


ESTIMATE_NOTE_START = re.compile(
    r"^(?:по\s+)?(?:оценк|оценочн|экспертн|предположительн|расчётн|расчетн|эксперт)", re.I)


def _is_verbose_estimate_note(paren_text):
    """Скобка похожа на пометку недостоверности («начинается с "оценка"/
    "экспертная"/…»), но это не короткая каноничная форма «по оценке» и не
    содержит цифры — а если цифра есть, скобка объясняет САМО число
    («имплицитная оценка 469 млн ₽»), и это не задеваем.

    Регулярка с `(?!...)` внутри одного выражения однажды уже подвела: жадный
    `[а-яё]*` откатывался и обходил отрицательный просмотр вперёд, из-за чего
    сама каноничная «(по оценке)» ложно считалась нарушением. Проверка на
    равенство строк такой ловушки не боится."""
    inner = paren_text.strip().lower()
    if not ESTIMATE_NOTE_START.match(inner):
        return False
    if any(ch.isdigit() for ch in inner):
        return False
    return inner != "по оценке"


def test_estimate_note_is_short(deals):
    """«900 млн ₽ (оценка на стадии согласования ФАС)» на карточке выглядит
    длинным и неровным рядом с короткими пометками других сделок. Пометка
    недостоверности пишется одним способом — «(по оценке)», без уточнений
    (кто оценил, на какой стадии); содержательные оговорки С ЦИФРОЙ внутри
    («по $59 за акцию», «имплицитная оценка 469 млн ₽») это не задевает —
    они объясняют число, а не помечают его недостоверность."""
    bad = []
    for d in deals:
        s = str(d.get("sum") or "")
        m = re.search(r"\(([^()]*)\)\s*$", s)
        if m and _is_verbose_estimate_note(m.group(1)):
            bad.append((d["id"], s))
    assert not bad, f"длинная пометка об оценке вместо «(по оценке)»: {bad[:5]}"
    # Проверка на себе: каноничная форма и содержательная оговорка с цифрой
    # правилом не задеты, а формулировка из бага — задета.
    assert not _is_verbose_estimate_note("по оценке")
    assert not _is_verbose_estimate_note("имплицитная оценка 469 млн ₽")
    assert _is_verbose_estimate_note("оценка на стадии согласования ФАС")


META_OPENER = re.compile(
    r"^(?:в\s+)?(?:стать[её]|публикаци|сообщени|материал|заметк|издани)[а-яё]*\b", re.I)


def test_rationale_does_not_retell_the_article(deals):
    """«Цель сделки» описывает сделку, а не источник (прогон 9)."""
    bad = [(d["id"], str(d.get("eco", {}).get("rationale"))[:60]) for d in deals
           if META_OPENER.match(str(d.get("eco", {}).get("rationale") or "").strip())]
    assert not bad, f"пересказ статьи в «Цели сделки»: {bad[:5]}"


INTERNAL_JARGON = re.compile(r"bulk|партия\s*\d|тестовый\s+прогон|pipeline|json", re.I)


def test_company_descriptions_have_no_internal_jargon(base):
    """Описание компании — для читателя, а не рассказ о нашем процессе
    («Профиль сформирован по итогам чтения bulk-базы, партия 4») — прогон 23."""
    bad = [(cid, str(c.get("desc"))[:60]) for cid, c in base["companies"].items()
           if INTERNAL_JARGON.search(str(c.get("desc") or ""))]
    assert not bad, f"внутренняя кухня в описании профиля: {bad[:5]}"


# Тот же предикат пустоты, что и на экране (`hasFact` в index.html): заглушкой
# считается только строка, в которой кроме формулировки отсутствия ничего нет.
# «(?:о|об)\s+\S+\s+» — не украшение: в базе есть «Публично О СОГЛАСОВАНИЯХ не
# сообщалось», где между «публично» и «не» стоит дополнение. Шаблон без этого
# молча не считал такую строку заглушкой — тот же класс беззвучного отказа,
# что `\b` после приставки (см. CLAUDE.md).
LAW_PLACEHOLDER = re.compile(
    r"^(?:[—-]|н/д|нет\s+данных|(?:публично|официально)\s+(?:об?\s+\S+\s+)?не\s+(?:раскры|сообщал|разглаш)[а-яё]*"
    r"|не\s+(?:раскры|сообщал|привлекал|указан|назван|разглаш)[а-яё]*"
    r"(?:\s+(?:официально|публично))?)[.\s]*$", re.I)


def is_placeholder(value):
    text = str(value or "").strip()
    return not text or bool(LAW_PLACEHOLDER.match(text))


APPROVAL_BODY = re.compile(
    r"ФАС\b|антимонопольн|правительственн[а-яё]*\s+(?:под)?комисси|правкомисси|подкомисси"
    r"|Банк[а-яё]*\s+России|ЦБ\s+РФ|Центробанк|президент[а-яё]*\s+Р(?:оссии|Ф)|правительств[а-яё]*"
    r"|российск[а-яё]*\s+власт|Минцифр|Минпромторг|Минсельхоз|Роскомнадзор|Росимуществ|регулятор"
    r"|UOKiK|Rekabet|Еврокомисси|CFIUS|OFAC|совет[а-яё]*\s+директоров|собрани[а-яё]*\s+акционеров", re.I)
APPROVAL_ACT = re.compile(r"одобр|разреш|согласова|согласи[ея]|утверд", re.I)
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=(?-i:[А-ЯЁA-Z«\"]))")
# Просмотрено глазами: согласование в тексте есть, но оно про другую сделку
# (подробности — в docstring pipeline/extract_approvals.py).
APPROVAL_EXCEPTIONS = {"g4b26b011", "g96e561ef", "g72fad24b", "g718e3d0e"}


def test_approval_is_not_left_in_prose(deals):
    """Линза «Юрист» не должна говорить «согласования не раскрыли», когда
    согласование описано в той же карточке (прогон 29).

    Ловит следующую партию данных: если в «Дополнительной информации» новой
    сделки написано «ФАС одобрила», а поле «Согласования» пусто, пользователь
    увидит на соседних вкладках факт и утверждение, что факта нет.
    """
    bad = []
    for d in deals:
        if d["id"] in APPROVAL_EXCEPTIONS:
            continue
        if not is_placeholder((d.get("law") or {}).get("appr")):
            continue
        for text in (d.get("extra"), (d.get("eco") or {}).get("rationale"),
                     (d.get("eco") or {}).get("context"), (d.get("eco") or {}).get("share")):
            for sent in SENTENCE.split(str(text or "")):
                if APPROVAL_BODY.search(sent) and APPROVAL_ACT.search(sent):
                    bad.append((d["id"], sent.strip()[:70]))
                    break
    assert not bad, f"согласование осталось в тексте, поле пусто: {bad[:5]}"


HANGING_TAIL = re.compile(r"[;,:—–-]$")
LOWER_START = re.compile(r"^(?-i:[а-яё])")
LAW_FIELDS = ("struct", "appr", "terms")


def test_no_value_ends_with_a_hanging_separator(deals):
    """Значение поля не может кончаться на «;» — это обрубок фразы (прогон 30).

    Так было у 22 «Согласований» из 144: поле нарезали из сплошного текста по
    точке с запятой, и в карточку попадала половина мысли.
    """
    bad = []
    for d in deals:
        for grp in ("eco", "law"):
            for key, value in (d.get(grp) or {}).items():
                if not isinstance(value, str):
                    continue
                text = re.sub(r"\s+", " ", value).strip()
                if text and not is_placeholder(text) and HANGING_TAIL.search(text):
                    bad.append((d["id"], f"{grp}.{key}", text[-40:]))
    assert not bad, f"значение обрывается на разделителе: {bad[:5]}"


def test_law_values_start_with_a_capital(deals):
    """Юридические поля — законченные утверждения, а не куски фразы.

    Строчная буква в начале означала, что подлежащее осталось в `extra`:
    «подали в ФАС ходатайство…» — кто подал, на экране не видно. Проверка
    намеренно ограничена линзой «Юрист»: в `eco.*` строчное начало встречается
    и законно (продолжение перечисления показателей).
    """
    bad = [(d["id"], f"law.{f}", str((d.get("law") or {}).get(f))[:40])
           for d in deals for f in LAW_FIELDS
           if not is_placeholder((d.get("law") or {}).get(f))
           and LOWER_START.match(re.sub(r"\s+", " ", str((d.get("law") or {}).get(f))).strip())]
    assert not bad, f"юридическое поле начинается со строчной буквы: {bad[:5]}"


APPROVING_BODY = re.compile(
    r"ФАС\b|антимонопольн|правительственн[а-яё]*\s+(?:под)?комисси|правкомисси|подкомисси"
    r"|Банк[а-яё]*\s+России|ЦБ\s+РФ|Центробанк|президент[а-яё]*|правительств[а-яё]*|премьер"
    # Власти — не только российские: у «РБИ»/Strabag выгодополучателем сделки
    # были обеспокоены именно ВЛАСТИ США («Власти США считают, что
    # выгодополучателем от покупки будет...»), и узкий вариант с якорем на
    # «российск[а-яё]*» его не ловил — расширяем до любого «власт[а-яё]*».
    r"|власт[а-яё]*|Минцифр|Минпромторг|Минсельхоз|Минфин|Минюст|Роскомнадзор"
    r"|Росимуществ|Росжелдор|регулятор|UOKiK|Rekabet|Еврокомисси|CFIUS|OFAC|OFSI|BIS|EMRA"
    # Министерство — тоже согласующий орган; список был только российским, а
    # у «Росатом/Мали» согласование давало министерство другой страны.
    r"|министерств[а-яё]*|Minist"
    r"|совет[а-яё]*\s+директоров|собрани[а-яё]*\s+акционеров|акционер|суд\b|указ|распоряжени"
    r"|предписани"
    # «Органы власти» без уточнения — источник сам не назвал орган поимённо
    # (Strabag/RBI про несостоявшуюся сделку), но факт согласования — что
    # оно НЕ было получено от властей — всё равно принадлежит этому полю.
    r"|орган[а-яё]*\s+власти"
    # «Регулирующие органы» без уточнения — тот же класс, что «органы
    # власти» выше: у Fonte Capital/«Самолёт» ни один из семи прочитанных
    # источников не назвал орган поимённо («сделка получила все необходимые
    # одобрения регулирующих органов»), но факт согласования подтверждён.
    r"|регулирующ[а-яё]*\s+орган"
    # Военно-промышленная комиссия — согласующий орган для ГОЗ: у ЛОМО/
    # «Калашникова» решение о передаче в управление приняла именно она,
    # а не «правительственная» или «под-» комиссия из уже принятых форм.
    r"|военно-промышленн[а-яё]*\s+комисси"
    # Роскосмос — согласующая госкорпорация для частных ракет: у «Восхода»
    # заключение головного института «Роскосмоса» ЦНИИМаш — единственное
    # согласование, которое называет источник.
    r"|Роскосмос[а-яё]*"
    # Голое «ЦБ» без «РФ» — у Freedom Holding/Повалишина источник
    # (Коммерсантъ) пишет «15 февраля ЦБ одобрил продажу…», без «РФ» и без
    # полного «Банк России»; регулятор тот же самый, просто другое
    # сокращение одного и того же органа.
    r"|ЦБ\b"
    # Агентство по защите и развитию конкуренции Республики Казахстан —
    # антимонопольный орган другой страны (Freedom/Bilim Group), тот же
    # класс, что уже принятые UOKiK/Rekabet/CFIUS: список согласующих
    # органов не должен быть только российским.
    r"|Агентств[а-яё]*\s+по\s+защите\s+и\s+развитию\s+конкуренции"
    # Antimonopoly — английский перевод ФАС/«антимонопольн»: у Balchug
    # Capital/«Радуги» единственный источник, называющий одобрение,—
    # армянское СМИ по-английски («Approved by the Federal Antimonopoly
    # Service of the Russian Federation»). Родня уже принятых Minist/OFAC/
    # CFIUS: список согласующих органов не должен быть только русскоязычным.
    r"|Antimonopoly"
    # «Кабмин» — разговорное сокращение «кабинета министров», то есть
    # правительства: у «Росспиртпрома»/«Амбер Талвис» источник пишет «план
    # приватизации утвердил кабмин» — то же ведомство, что «правительств[а-яё]*»
    # выше, просто другим словом.
    r"|кабмин"
    # Региональный парламент — согласующий орган для приватизации на уровне
    # субъекта РФ: у «Сибагро»/Богдановичского комбикормового завода источник
    # пишет «приватизацию предприятия одобрил свердловский парламент» — не
    # федеральный орган из уже принятого списка, а законодательное собрание
    # региона.
    r"|парламент"
    # OFSI (Office of Financial Sanctions Implementation) — санкционный
    # регулятор Великобритании: у Evraz/североамериканского дивизиона сбор
    # заявок на покупку велся по генеральной лицензии OFSI, и компания
    # именно с ним поддерживала контакт — родня уже принятого OFAC (США),
    # только другая юрисдикция.
    r"|OFSI", re.I)


def test_approval_names_a_body(deals):
    """В «Согласованиях» должен быть назван орган, который согласовывал.

    Ловит A13: под этим заголовком лежали состав команды юрфирмы, описание
    компании и мотив сделки — там нет ни одного органа. Проверка намеренно
    широкая: «премьер подписал распоряжение» — согласование, хотя слова
    «одобрил» в нём нет.
    """
    bad = [(d["id"], str((d.get("law") or {}).get("appr"))[:60]) for d in deals
           if not is_placeholder((d.get("law") or {}).get("appr"))
           and not APPROVING_BODY.search(str((d.get("law") or {}).get("appr")))]
    assert not bad, f"в «Согласованиях» не назван орган: {bad[:5]}"


def test_law_value_does_not_repeat_the_title(deals):
    """Значение поля не начинается с дословного повтора заголовка карточки.

    Так было у 6 «Согласований»: заголовок склеился с фактом без точки, и на
    экране карточка повторяла сама себя.
    """
    bad = []
    for d in deals:
        title = re.sub(r"\s+", " ", str(d.get("title") or "")).strip().lower()
        for f in LAW_FIELDS:
            value = re.sub(r"\s+", " ", str((d.get("law") or {}).get(f) or "")).strip()
            if len(value) > 40 and title and value[:40].lower() in title:
                bad.append((d["id"], f"law.{f}"))
    assert not bad, f"поле начинается с повтора заголовка: {bad[:5]}"


def test_buyer_is_named_once(deals):
    """У покупателя либо профиль (`buyer`), либо имя текстом (`buyer_name`).

    Два источника имени для одной роли расходятся при первой же правке: на
    экране будет одно, в выжимке другое. Текстовый вариант появился в прогоне
    38 для инвестиционных раундов, где профилей у фондов почти нет.
    """
    bad = [(d["id"], d.get("buyer"), d.get("buyer_name")) for d in deals
           if d.get("buyer") and str(d.get("buyer_name") or "").strip()]
    assert not bad, f"у покупателя одновременно профиль и имя текстом: {bad[:5]}"


def test_party_name_is_not_initials_only(deals):
    """Сторона сделки — «Фамилия Имя», а не «Фамилия И.О.».

    Каталог вычитки (A7, 15 августа 2026): разбор источника иногда сохранял
    сторону в газетном сокращении («Иванов И.И.») вместо полного имени из
    того же текста. Один такой случай нашёлся и починен чтением; регулярка
    держит класс закрытым для новых карточек притока.
    """
    pat = re.compile(r"^[А-ЯЁ][а-яё]+ [А-ЯЁ]\.[А-ЯЁ]\.$")
    bad = [(d["id"], field, d[field]) for d in deals
           for field in ("seller", "buyer_name")
           if isinstance(d.get(field), str) and pat.match(d[field].strip())]
    assert not bad, f"сторона записана инициалами вместо имени: {bad[:5]}"


def test_asset_is_not_a_party(base):
    """Предмет сделки — не её сторона, и наоборот.

    Прогон 45: у «Wildberries & Russ приобрела сеть «Рив Гош»» продавцом стоял
    сам «Рив Гош» — проданная компания; у «Инвестиции Softline Venture Partners
    в Kickidler» предметом сделки числился инвестор. На экране это плашка
    «Продавец → Предмет → Покупатель», где две ячейки называют одну компанию.
    Проверка сравнивает названия, а не только ссылки: половина этих карточек хранит
    сторону текстом (`seller`, `buyer_name`), а предмет — профилем.
    """
    def flat(s):
        return re.sub(r"[«»\"'(),.\s]", "", str(s or "")).lower()

    comps = base["companies"]
    bad = []
    for d in base["deals"]:
        for field, ref in (("asset", "buyer"), ("asset", "seller_id")):
            name = comps.get(d.get(ref), {}).get("name")
            if d.get(field) and name and flat(name) == flat(d[field]):
                bad.append((d["id"], field, ref))
        if d.get("asset") and d.get("seller") and flat(d["seller"]) == flat(d["asset"]):
            bad.append((d["id"], "asset", "seller"))
        for text_field in ("buyer_name", "seller"):
            for ref in ("target", "asset_id"):
                name = comps.get(d.get(ref), {}).get("name")
                if d.get(text_field) and name and flat(name) == flat(d[text_field]):
                    bad.append((d["id"], text_field, ref))
    assert not bad, f"предмет сделки записан её стороной: {bad[:5]}"


def test_company_name_is_not_a_deal_composition(base):
    """Имя компании — это имя, а не состав сделки с долями и предлогами.

    У 48 профилей из 1846 в названии стояла доля из заголовка («ООО «Винтео» ,
    51%», «долей в пяти юрлицах сети гипермаркетов OBI»), и это показывалось в
    плашке сторон, в каталоге и в поиске. 37 вычищены в прогоне 37, оставшиеся
    11 — в прогоне 39; тест держит границу.
    """
    dirt = re.compile(r"\d+[,.]?\d*\s*%|\bдолей\b|\bакций\b|оставшиеся", re.I)
    bad = [(cid, c.get("name")) for cid, c in base["companies"].items()
           if dirt.search(re.sub(r"\s+", " ", str(c.get("name") or "")))]
    assert not bad, f"в названии профиля стоит доля из заголовка сделки: {bad[:5]}"


def test_lot_profile_names_more_than_one_entity(base):
    """Признак `lot` ставится записи, за которой несколько юрлиц.

    Профиль-лот («ООО «Датана» и ООО «Датабриз»») — не компания, а состав
    сделки, и интерфейс говорит об этом отдельной строкой. Если признак стоит
    у записи с одним именем, строка врёт.
    """
    bad = []
    for cid, c in base["companies"].items():
        if not c.get("lot"):
            continue
        name = str(c.get("name") or "")
        if not (re.search(r"\bи\b|,", name) or re.search(r"юрлиц|компании,", name, re.I)):
            bad.append((cid, name))
    assert not bad, f"признак лота у записи с одним именем: {bad[:5]}"


def test_no_duplicate_deal_cards(deals):
    """Одна сделка — одна карточка.

    Признак дубля подобран замером на самой базе. Наивный «общее название в
    кавычках + та же сумма + 45 дней» даёт 5 пар, из которых верна одна:
    название в кавычках часто не предмет, а ПРОДАВЕЦ, и банк «Траст»,
    продающий десятки активов, совпадает сам с собой. Признак дубля — ДВА
    общих названия при одной сумме; на нём в базе была ровно одна пара (два
    описания выхода Volkswagen из России), слитая в прогоне 50.
    """
    def quoted(text):
        return {m.group(1).lower() for m in re.finditer(r"«([^»]{2,40})»", str(text or ""))}

    def amount(text):
        m = re.search(r"(\d[\d\s]*(?:[.,]\d+)?)\s*(млрд|млн)", str(text or ""), re.I)
        if not m:
            return None
        num = float(m.group(1).replace(" ", "").replace(",", "."))
        return num * (1000 if m.group(2).lower() == "млрд" else 1)

    def day(text):
        try:
            y, m_, d = (int(x) for x in str(text)[:10].split("-"))
            return date(y, m_, d)
        except ValueError:
            return None

    rows = [(d["id"], day(d.get("date")), quoted(d.get("title")), amount(d.get("sum")))
            for d in deals]
    bad = []
    for i, (id_a, date_a, q_a, sum_a) in enumerate(rows):
        for id_b, date_b, q_b, sum_b in rows[i + 1:]:
            if len(q_a & q_b) < 2 or not (sum_a and sum_b) or not (date_a and date_b):
                continue
            if abs((date_a - date_b).days) > 45:
                continue
            if abs(sum_a - sum_b) / max(sum_a, sum_b) < 0.05:
                bad.append((id_a, id_b, sorted(q_a & q_b)))
    assert not bad, f"две карточки об одной сделке: {bad[:3]}"


def test_no_company_twins(base):
    """Одна компания — один профиль.

    «Альфа-Банк» и «Alfa-Bank» были двумя профилями, и сделки делились между
    ними: «Сделок в базе» показывало половину, каталог показывал компанию
    дважды. Ключ ниже — тот же, которым мерили класс в прогоне 51: имя без
    организационной формы и пунктуации, транслитерированное в латиницу, с
    сглаживанием c/k, ph/f, y/i, ё/е и удвоенных букв.

    Исключения — не поблажка правилу, а разные компании с похожими именами:
    иностранный владелец и его российское юрлицо. Слить их значило бы сделать
    продавца предметом собственной сделки.
    """
    cyr = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
           "з": "z", "и": "i", "й": "i", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
           "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts",
           "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "i", "ь": "", "э": "e",
           "ю": "iu", "я": "ia"}
    allowed = {frozenset(p) for p in (
        ("Essity", "ООО «Эссити»"),                    # владелец и проданный российский бизнес
        ("Fortum", "Фортум"),                          # финский владелец и ПАО «Фортум»
        ("Polymetal", "Полиметалл"),                   # plc и АО «Полиметалл»
    )}

    def key(name):
        s = re.sub(r"\b(ооо|оао|зао|пао|ао|нао|гк|пкф|тд)\b\.?", " ", str(name or "").lower())
        s = "".join(cyr.get(ch, ch) for ch in s)
        s = re.sub(r"[^a-z0-9]+", "", s)
        for a, b in (("ph", "f"), ("sch", "sh"), ("ck", "k"), ("ts", "s"), ("x", "ks"),
                     ("w", "v"), ("q", "k"), ("y", "i"), ("j", "i")):
            s = s.replace(a, b)
        s = s.replace("ch", "\x00").replace("c", "k").replace("\x00", "ch")
        return re.sub(r"(.)\1+", r"\1", s)

    groups = {}
    for cid, c in base["companies"].items():
        k = key(c.get("name"))
        if len(k) >= 3:
            groups.setdefault(k, []).append(str(c.get("name")))
    twins = [names for names in groups.values()
             if len(names) > 1 and frozenset(names) not in allowed]
    assert not twins, f"одна компания записана несколькими профилями: {twins[:3]}"


def test_match_key_alias_is_a_name(base):
    """Псевдоним компании — имя, а не кусок заголовка.

    По этим ключам страница компании собирает упоминания в заголовках сделок.
    «долей русинжгидро» или «продавец 80% долей» не сработают никогда: они
    требуют дословного повтора всей фразы. Дефектным считаем псевдоним, который
    и содержит ролевое/долевое слово, и не пересекается с именем профиля
    (полная форма «имя (продавец 80% долей)» под правило не попадает — она
    начинается с имени).

    Два исключения оставлены намеренно: короткая форма ловит чужие сделки —
    «информ» находит «Башинформсвязь», «агроинвест» — «Бумеранг агроинвест».
    """
    phrase = re.compile(
        r"\b(выкуп\w*|покупк\w*|продаж\w*|приобрет\w*|продавец|покупатель|инвестор|доли|долей"
        r"|долю|акци\w+|пакет\w*|бизнес|актив\w*|до \d+|\d+\s?%|оставш\w+|структур\w+|владелец"
        r"|наследник\w*|основател\w*|бывш\w+|сооснователь)\b", re.I)
    allowed = {"оставшиеся 49 9% акций информ", "долей агроинвест"}

    def flat(s):
        return re.sub(r"[^a-zа-яё0-9]+", "", str(s or "").lower())

    bad = []
    for cid, aliases in base["match_keys"].items():
        name = flat((base["companies"].get(cid) or {}).get("name"))
        for alias in aliases:
            key = flat(alias)
            if not name or not key or key in name or name in key:
                continue
            if phrase.search(alias) and alias not in allowed:
                bad.append((cid, alias))
    assert not bad, f"псевдоним — кусок заголовка, а не имя: {bad[:5]}"


CURATED_IDS = (
    "citibank", "baltika", "rosatom-mali", "berizaryad", "hugoboss", "ksk", "mercedes",
    "technored", "ektos", "tokk-metarus", "adv-erlan", "selectel-itmo", "domodedovo-aukcion",
    "inkab-ipo", "mts-bik", "absolut-strah", "mid-ilyinskaya", "adamas-slh", "agrostroy-zemlya",
)


def CURATED_IDS_DEALS():
    base = json.loads(DATA.read_text(encoding="utf-8"))
    by_id = {d["id"]: d for d in base["deals"]}
    return [by_id[i] for i in CURATED_IDS if i in by_id]


def test_curated_closed_titles_use_completed_action():
    """19 кураторских карточек не должны говорить «продаёт / покупает» рядом
    со статусом «Закрыта». Раньше проверялось по разметке — теперь по базе:
    карточки переехали в deals_promoted.json (единый источник правды)."""
    present = re.compile(r'\b(?:покупает|приобретает|прода[её]т|созда[её]т|получает|входит|проводит|привлекает|выкупает)\b', re.I)
    bad = [d["title"] for d in CURATED_IDS_DEALS()
           if d.get("status") == "Закрыта" and present.search(str(d.get("title") or ""))]
    assert not bad, f"закрытые кураторские карточки в настоящем времени: {bad}"


def test_curated_feedback_fixes_are_kept(deals):
    """Правки из ревью не должны исчезнуть. Проверяем БАЗУ, а не index.html:
    3 августа 2026 кураторские карточки переехали из захардкоженного массива в
    deals_promoted.json — единый источник правды. Пока они жили в разметке,
    инварианты базы их вообще не проверяли, и семь из них нарушались молча."""
    by_id = {d["id"]: d for d in deals}
    sp = by_id["selectel-itmo"]
    assert sp["type"] == "Создание СП"
    assert "ООО «Эмерджентные мультиагентные системы» (ООО «ЭМС»)" in json.dumps(sp, ensure_ascii=False)
    kinds = {e.get("kind") for e in sp.get("events", [])}
    assert "registered" in kinds and "announced" in kinds
    ag = by_id["agrostroy-zemlya"]
    assert ag.get("buyer_name") == "Российский девелопер"
    assert any(e.get("kind") == "closed" and e.get("date") == "2026-07-08"
               for e in ag.get("events", []))
    assert "сделка описана как сложная многосторонняя структура" not in \
        json.dumps(deals, ensure_ascii=False).lower()


def test_artem_feedback_ui_invariants():
    """Ключевые UX-правки из ревью не должны исчезнуть при следующем прогоне."""
    html = INDEX.read_text(encoding="utf-8")
    assert 'class="hero-brand"' in html, "на главной снова пропал логотип"
    assert 'window.hsTimer=null' in html and 'hsTimer=setInterval' not in html, \
        "автопереключение слайдера вернулось"
    assert 'Сделок с теми же сторонами или общей темой пока не найдено' in html
    assert 'Сделок с теми же сторонами или с той же темой в базе нет' not in html
    assert 'Показатели таргета' not in html
    assert 'mailto:' not in html
    assert 'Ход сделки' in html and 'openCorrectionDialog' in html
    assert 'По этой сделке раскрыто немного деталей' in html


def test_citibank_lifecycle_is_canonical(base, deals):
    """Ранняя новость и закрытие — этапы одной сделки, а не две карточки."""
    assert "gf57ea8cb" not in ids_of(deals)
    assert base["merged"].get("gf57ea8cb") == "citibank"
    assert base["merged_deal_stages"].get("gf57ea8cb") == "negotiations-2024-01-01"
    assert "g32b8014f" not in base["companies"]
    assert base["merged_companies"].get("g32b8014f") == "citibank"

    citibank = next(d for d in deals if d["id"] == "citibank")
    assert citibank.get("seller_id") == "gfd061adf"
    assert citibank.get("seller") == "Citigroup Netherlands B.V."
    stages = {e.get("id") for e in citibank.get("events", [])}
    assert {"negotiations-2024-01-01", "approval-2025-11-12", "closed-2026-02-18"} <= stages


def test_stage_history_ui_and_route_are_kept():
    html = INDEX.read_text(encoding="utf-8")
    assert 'class="progress-current"' in html
    assert 'class="progress-history"' in html
    assert 'id="historyToggle"' in html
    assert 'renderDealStage(arg, subarg)' in html
    assert 'Object.assign(MERGED_STAGE, j.merged_deal_stages||{})' in html
    assert 'bindTimeline();' in html
    assert 'else if(sub==="stage" && subarg)' in html


def test_account_async_render_is_revealed():
    """route() анимирует DOM до завершения refreshMe(); renderAccount обязан
    отдельно раскрыть вставленную после await форму, иначе экран пустой."""
    html = INDEX.read_text(encoding="utf-8")
    account = html[html.index("async function renderAccount"):html.index("/* Комментарии", html.index("async function renderAccount"))]
    assert account.count("rerun();") >= 2


def test_flowwow_yandex_is_one_lifecycle(base, deals):
    """Переговоры и срыв Flowwow/Яндекс живут в одной карточке."""
    ids = set(ids_of(deals))
    assert "g718e3d0e" in ids
    assert "gea8ea954" not in ids
    assert base["merged"].get("gea8ea954") == "g718e3d0e"
    assert base["merged_deal_stages"].get("gea8ea954") == "negotiations-2026-02-09"
    card = next(d for d in deals if d["id"] == "g718e3d0e")
    assert card["status"] == "Не состоялась"
    assert card.get("buyer") == "yandex"
    assert card.get("target") == "g578c62cd"
    assert [(e.get("kind"), e.get("date")) for e in card.get("events", [])] == [
        ("negotiations", "2026-02-09"),
        ("cancelled", "2026-05-28"),
    ]


def test_reviewed_duplicate_cards_are_reconciled(base, deals):
    """Ручная ревизия дублей и ролей не должна откатываться."""
    ids = set(ids_of(deals))
    pairs = {
        "gadce1d9c": "g676504a3",
        "g68297df0": "g40477661",
        "g8fe01e40": "g324faec6",
        "g0ca2ebf0": "baltika",
        "gb1f65e04": "hugoboss",
        "gb1866587": "berizaryad",
    }
    for legacy, canonical in pairs.items():
        assert legacy not in ids
        assert base["merged"].get(legacy) == canonical

    labquest = next(d for d in deals if d["id"] == "g40477661")
    assert labquest.get("buyer") == "g67ef3e91"
    assert labquest.get("target") == "g0b6a8c17"
    assert labquest.get("seller") == "Александр и Рашида Марковы"
    assert "g0b6a8c17" in base["companies"]


def test_sequential_tranches_remain_separate(base, deals):
    """Две покупки 3S Group — связанные, но самостоятельные транзакции."""
    by_id = {d["id"]: d for d in deals}
    first, second = by_id["geda130b6"], by_id["gdd85a5b9"]
    assert first["date"] == "2023-12-28"
    assert second["date"] == "2024-06-04"
    assert first.get("related_deal_ids") == ["gdd85a5b9"]
    assert second.get("related_deal_ids") == ["geda130b6"]
    assert first.get("separate_transaction_reviewed") is True
    assert second.get("separate_transaction_reviewed") is True
    assert first.get("seller") == second.get("seller") == "Руслан Сеюков"


def test_ing_sale_is_one_lifecycle(base, deals):
    """Объявление и отмена продажи ИНГ Банка — одна карточка."""
    ids = set(ids_of(deals))
    assert "g2d90c4d5" in ids
    assert "geb8eaeab" not in ids
    assert base["merged"].get("geb8eaeab") == "g2d90c4d5"
    assert base["merged_deal_stages"].get("geb8eaeab") == "announced-2025-01-28"
    card = next(d for d in deals if d["id"] == "g2d90c4d5")
    assert card.get("buyer") == "gc905c016"
    assert card.get("target") == "gc0e9c501"
    assert card.get("seller_id") == "g84ef6ac1"
    assert card.get("status") == "Не состоялась"
    assert [(e.get("kind"), e.get("date")) for e in card.get("events", [])] == [
        ("signed", "2025-01-28"),
        ("cancelled", "2026-04-07"),
    ]


def test_high_confidence_party_corrections_are_kept(deals):
    """Ручная проверка источников не должна теряться при новых прогонах."""
    by_id = {d["id"]: d for d in deals}
    expected = {
        "g02a89309": ("gf1f56e08", "g67b53b6a", "gee90a2b1"),
        "g18569a1c": ("gc9913f2a", "g8cff91963", "ge00b1b13"),
        "gbb7e25e1": ("g549ab474", "g2e85f5e5", "g7ffb3b7a"),
        "g90363dc7": ("ged6b4e16", "g04181f17", "gda7d982b"),
    }
    for deal_id, (buyer, target, seller) in expected.items():
        card = by_id[deal_id]
        assert card.get("buyer") == buyer
        assert card.get("target") == target
        assert card.get("seller_id") == seller
        assert card.get("party_evidence"), deal_id


# ---------- падеж имени стороны сделки ----------

# ЛОЖНЫЕ СРАБАТЫВАНИЯ ПРИЗНАКА, ПРОВЕРЕННЫЕ ГЛАЗАМИ (9 августа).
# Признак судит по первому слову имени и у этих шестнадцати ошибается:
# «Структуры Алексея Репика» — именительный МНОЖЕСТВЕННОГО числа, который
# pymorphy принимает за родительный единственного; «Севергрупп», «Ростех»,
# «Росхим», «Свой», «Кредит Европа банк» — бренды, у которых косвенная форма
# просто совпала по буквам; «Суховерхов Андрей Владимирович» — фамилия перед
# именем; «Данис», «Хвича», «Александра» — личные имена, которых нет в
# словаре. Список закрытый НАМЕРЕННО: новое имя в косвенном падеже обязано
# уронить тест, а не тихо пополнить исключения.
PARTY_CASE_EXCEPTIONS = {
    "gf5c8e14e", "g02eed099", "gf12c6323", "gf23149cf", "g7596ae81",   # «Структуры X»
    "gbb7e25e1", "gd4645195", "gadb5b474",                            # «Севергрупп», «Ростех»
    "gdf93c62d", "gf8dfe9c4", "g14443784",                            # фамилия впереди имени
    "g8cb1eb00", "gff6e08fe",                                         # личные имена вне словаря
    "gmru-svoj-kredit-evropa-strah", "gmru-roshim-vnt",               # бренды
    "c3c15a888",                                                      # «Финам»: бренд на -м, pymorphy3 считает дательным
}


def test_party_name_is_in_the_nominative_case(deals):
    """Имя стороны пишется в именительном падеже, а не в том, что диктует предлог.

    `guess_parties()` вырезает сторону подстрокой после предлога — «купил у
    Автодома», «у Агрохолдинга „Василина"», «у Индустриального фонда», — и
    родительный уезжает на экран как имя. Владелец нашёл это 9 августа в
    карточке «Флит Лизинга»; прогон признака по всей базе дал 37 кандидатов, из
    которых 21 оказались настоящим дефектом (починены
    `pipeline/fix_party_name_case.py`).

    Тест держит границу на будущее: любое НОВОЕ имя, первое слово которого
    уверенно стоит в косвенном падеже, роняет прогон. Проверен на себе — на
    данных до правки падает на 21 карточке.
    """
    pytest.importorskip("pymorphy3")
    import sys
    sys.path.insert(0, str(ROOT / "pipeline" / "ingest"))
    import review                                     # noqa: E402

    # ПРАВИЛО У ТЕСТА И У СКРИПТА ОДНО. Если проверять базу своей копией
    # признака, копия и оригинал разойдутся на первой же правке — и тест
    # начнёт охранять не то, что пропускает `review.py`.
    bad = []
    for deal in deals:
        if deal["id"] in PARTY_CASE_EXCEPTIONS:
            continue
        for field in ("seller", "buyer_name"):
            problem = review.name_is_nominative(deal.get(field))
            if problem:
                bad.append((deal["id"], field, deal.get(field), problem))
    assert not bad, "имя стороны в косвенном падеже: %r" % (bad[:6],)
