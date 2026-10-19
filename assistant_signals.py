# -*- coding: utf-8 -*-
"""Ассистент: «будут ли у X сделки», «кто сейчас продаёт агроактивы».

ЗАЧЕМ. Партнёр владельца (19 октября 2026): вопрос «у кого вероятна M&A-
активность» полезен, если отвечать доводами с датой и ссылкой, а не
процентом. Доводы лежат в `static/data/signals.json` (сбор —
`pipeline/ingest/signals.py`): компания заявила о продаже, покупке, поиске
инвестора, размещении акций, обсуждаемая сделка. Здесь из них и из базы
сделок собирается ответ в три блока:

  **Признаки** — каждый с датой и ссылкой: заявления и обсуждаемые сделки,
  последние сделки компании, санкции из профиля (внешняя причина).
  **Что это может значить** — «есть основания ожидать продажи / покупки /
  привлечения инвестора», без процентов и без прогноза.
  **Кто подходит** — из базы: кто недавно покупал в той же отрасли, кто ещё
  в отрасли готовит продажу, что компания покупала раньше.

Без признаков ответ так и говорит: «явных признаков в наших данных нет».
Модель получает этот ответ сводкой и правила `SIGNAL_RULES` (main.py);
счёт, проценты и вероятности после модели снимает `_drop_forecasts`.

Отдельным модулем, а не внутри `assistant_retrieval.py`: тот файл правят
многие задачи, а маршрут признаков — свой, со своим файлом данных.
"""
from __future__ import annotations

import json
import os
import re
import threading
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

import assistant_retrieval as ar

SIGNALS_PATH = Path(__file__).resolve().parent / "static" / "data" / "signals.json"

KIND_LABELS = {
    "sell": "готовит продажу",
    "for_sale": "компанию или долю продают",
    "buy": "присматривает покупки",
    "investor": "ищет инвестора или партнёра",
    "ipo": "готовится к размещению акций",
    "exit": "выходит из бизнеса или рынка",
    "strategy": "заявила рост через покупки",
    "state_sale": "государство готовит продажу",
}
SELL_KINDS = {"sell", "for_sale", "exit", "state_sale"}
BUY_KINDS = {"buy", "strategy"}
MEANING = {
    "sell": "есть основания ожидать продажи актива или доли",
    "buy": "есть основания ожидать новых покупок",
    "investor": "есть основания ожидать входа инвестора или партнёра в капитал",
    "ipo": "есть основания ожидать размещения акций на бирже",
}
MAX_SIGNALS = 6
MAX_LIST = 10

# --- узнать вопрос -------------------------------------------------------------
_FUTURE = (r"(?:сейчас\s+|сегодня\s+|ещ[её]\s+|скоро\s+|вскоре\s+)?"
           r"(?:прода[её]т|продают|выставля\w+|ищет|ищут|готов\w*|планиру\w+|собира\w+"
           r"|хочет|хотят|намерен\w*|может\s+(?:продать|купить)|могут\s+(?:продать|купить)|избавля\w+"
           r"|присматрива\w+|рассматрива\w+)")
SIGNAL_Q = re.compile(
    r"будут\s+ли\b[^?]{0,60}сдел(?:к|ок)|будет\s+ли\b[^?]{0,60}(?:прода|покуп|купит|ipo|размещ)"
    r"|(?:планиру\w+|собира\w+|готов\w+|ищет|намерен\w*)\s+ли\b"
    r"|\bкто\s+" + _FUTURE +
    r"|(?:какие|какая|какой)\s+компани\w*\s+" + _FUTURE +
    r"|(?:у\s+кого|кто|где)\s+[^?]{0,40}(?:возможн|вероятн|ожида|предстоя)\w*\s+[^?]{0,20}(?:m&a|сдел(?:к|ок)|слияни|поглощени|продаж|покупк)"
    r"|(?:возможн|вероятн|ожида|предстоящ|будущ)\w*\s+(?:m&a|сдел(?:к|ок)\w*|слияни\w*|поглощени\w*|продаж\w*|покупк\w*)"
    r"|m&a[- ]активност|сделочн\w+\s+активност|активност\w*\s+(?:в\s+)?(?:m&a|сдел(?:к|ок))"
    r"|признак\w*\s+(?:будущ\w+\s+|возможн\w+\s+)?(?:сдел(?:к|ок)|m&a|продаж|покупк)"
    r"|готов\w+\s+к\s+сдел(?:к|ок)|кто\s+готовится|выставлен\w*\s+на\s+продажу", re.I)
SELL_Q = re.compile(r"прода[её]т|продают|продаж|продать|выставл|избавл|выход|уход", re.I)
BUY_Q = re.compile(r"покупа|купит|купить|покупк|приобрет|присматрива|поглощ", re.I)
IPO_Q = re.compile(r"\bipo\b|размещ|бирж", re.I)
INVESTOR_Q = re.compile(r"инвестор|партн[её]р", re.I)


def is_signal_question(question: str) -> bool:
    q = " ".join(str(question or "").split())
    if not q or ar.PREP_WORDS.search(q):
        return False
    return bool(SIGNAL_Q.search(q))


def _kinds_asked(question: str) -> set[str] | None:
    kinds: set[str] = set()
    if SELL_Q.search(question):
        kinds |= SELL_KINDS
    if BUY_Q.search(question):
        kinds |= BUY_KINDS
    if IPO_Q.search(question):
        kinds.add("ipo")
    if INVESTOR_Q.search(question):
        kinds.add("investor")
    return kinds or None


# --- данные --------------------------------------------------------------------
_LOCK = threading.Lock()
_CACHE: dict = {}


def load_signals(path: Path = SIGNALS_PATH) -> list[dict]:
    """Список признаков; файл перечитывается, когда поменялся на диске."""
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        return []
    with _LOCK:
        if _CACHE.get("path") == str(path) and _CACHE.get("mtime") == mtime:
            return _CACHE["rows"]
        try:
            rows = json.loads(Path(path).read_text(encoding="utf-8")).get("signals") or []
        except (OSError, ValueError):
            rows = []
        _CACHE.update(path=str(path), mtime=mtime, rows=rows)
        return rows


MONTHS_NOM = ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август",
              "сентябрь", "октябрь", "ноябрь", "декабрь"]


def fmt_date(ds: str) -> str:
    ds = str(ds or "")
    if re.fullmatch(r"\d{4}-\d{2}", ds):
        return f"{MONTHS_NOM[int(ds[5:7]) - 1]} {ds[:4]}"
    return ar._fmt_date(ds)


def _company_link(idx, cid: str) -> str:
    name = ar._company_name(idx.companies, cid) or cid
    return f"[{name}](#/companies/{cid})"


def _source(sig: dict) -> str:
    src = sig.get("source") or []
    if len(src) >= 2 and src[1]:
        return f"[{src[0] or 'источник'}]({src[1]})"
    return ""


def _signal_line(sig: dict, idx, with_company: bool = False) -> str:
    text = sig.get("summary") or ""
    if with_company:
        text = f"{_company_link(idx, sig['company_id'])}: " + re.sub(r"^.*?\s—\s", "", text, count=1)
    parts = [f"{fmt_date(sig.get('date'))} — {text}"]
    src = _source(sig)
    if src:
        parts.append(f"({src})")
    deal = idx.by_id.get(sig.get("deal_id") or "")
    if deal:
        parts.append(f"— [сделка в «Компасе»](#/deal/{deal.id})")
    return "- " + " ".join(parts)


def _signals_of(cid: str, rows: list[dict]) -> list[dict]:
    mine = [s for s in rows if s.get("company_id") == cid or s.get("object_id") == cid]
    return sorted(mine, key=lambda s: str(s.get("date") or ""), reverse=True)


def _industry_of(cid: str, idx) -> str:
    return (idx.companies.get(cid) or {}).get("ind") or ""


def _signal_industries(sig: dict, idx) -> set[str]:
    """Отрасль, о которой признак: у обсуждаемой сделки — отрасль сделки
    (ВТБ продаёт «Росгосстрах» — это страхование, а не банки), у заявления о
    конкретном активе — отрасль актива, иначе — отрасль самой компании."""
    deal = idx.by_id.get(sig.get("deal_id") or "")
    if deal and deal.industries:
        inds = set(deal.industries)
    elif sig.get("object_id"):
        inds = {_industry_of(sig["object_id"], idx)}
    else:
        inds = {_industry_of(sig["company_id"], idx)}
    return {i for i in inds if i and i != "Не определена"}


def _meaning_key(kind: str) -> str:
    if kind in SELL_KINDS:
        return "sell"
    if kind in BUY_KINDS:
        return "buy"
    return kind


def _recent_buyers(industry: str, idx, exclude: set[str], today: date, limit: int = 4) -> list[tuple[str, object]]:
    """Кто покупал в отрасли за два года: (id покупателя, его последняя такая сделка)."""
    since = (today - timedelta(days=730)).isoformat()
    count: Counter = Counter()
    last: dict = {}
    for doc in idx.docs:
        if industry not in doc.industries or doc.date < since or not doc.purchase_like:
            continue
        bid = doc.raw.get("buyer")
        if not bid or bid in exclude or bid not in idx.companies:
            continue
        count[bid] += 1
        if bid not in last or doc.date > last[bid].date:
            last[bid] = doc
    order = sorted(count, key=lambda b: (-count[b], last[b].date), reverse=False)
    order = sorted(order, key=lambda b: (count[b], last[b].date), reverse=True)
    return [(b, last[b]) for b in order[:limit]]


def _company_deals(cid: str, idx, limit: int = 3):
    """Последние сделки компании — свежие первыми."""
    return sorted(idx.company_deals.get(cid, []), key=lambda d: d.date, reverse=True)[:limit]


def _role_word(doc, cid: str) -> str:
    return ar._role(doc, cid) or "упомянута в сделке"


def _sanctions_line(cid: str, idx) -> str:
    rows = (idx.companies.get(cid) or {}).get("sanctions") or []
    if not rows:
        return ""
    names = {"us": "США", "eu": "ЕС", "uk": "Великобритании"}
    lists = sorted({names.get(r.get("list"), r.get("list")) for r in rows if r.get("list")})
    first = min((str(r.get("since") or "") for r in rows if r.get("since")), default="")
    url = next((r.get("url") for r in rows if r.get("url")), "")
    text = "- Внешняя причина: компания в санкционных списках " + ", ".join(lists)
    if first:
        text += f" (с {fmt_date(first)})"
    if url:
        text += f" — [список]({url})"
    return text


# --- ответы ------------------------------------------------------------------------
def _answer_company(cid: str, question: str, idx, rows: list[dict], today: date):
    name = ar._company_name(idx.companies, cid) or cid
    link = _company_link(idx, cid)
    mine = _signals_of(cid, rows)
    kinds = _kinds_asked(question)
    lines = ["**Признаки**"]
    if mine:
        for sig in mine[:MAX_SIGNALS]:
            lines.append(_signal_line(sig, idx))
    else:
        lines.append(f"- Явных признаков будущих сделок у {link} в наших данных нет: ни заявлений о продаже "
                     "или покупке, ни обсуждаемых сделок.")
    deals = _company_deals(cid, idx)
    if deals:
        lines.append("- Последние сделки компании: " + "; ".join(
            f"[{d.title}](#/deal/{d.id}) — {_role_word(d, cid)}, {fmt_date(d.date)}" for d in deals))
    sanc = _sanctions_line(cid, idx)
    if sanc:
        lines.append(sanc)
    lines.append(f"- Отчётность и собственники — на [странице компании](#/companies/{cid}).")

    lines += ["", "**Что это может значить**"]
    if mine:
        seen = []
        for sig in mine:
            key = _meaning_key(sig.get("kind"))
            if key in MEANING and key not in seen:
                seen.append(key)
        for key in seen:
            lines.append(f"- По заявлениям и обсуждаемым сделкам {MEANING[key]}.")
        lines.append("- Это не прогноз: заявление о планах не всегда заканчивается сделкой, а сроки и цену "
                     "стороны обычно не называют.")
    else:
        lines.append("- Без заявлений компании и обсуждаемых сделок говорить о её будущих сделках рано.")

    picks = []
    if mine:
        inds = set()
        for sig in mine:
            inds |= _signal_industries(sig, idx)
        inds = inds or {_industry_of(cid, idx)}
        sell_side = any(s.get("kind") in SELL_KINDS for s in mine) and (kinds is None or kinds & SELL_KINDS)
        buy_side = any(s.get("kind") in BUY_KINDS for s in mine) and (kinds is None or kinds & BUY_KINDS)
        exclude = {cid} | {s.get("object_id") for s in mine if s.get("object_id")}
        if sell_side:
            for ind in sorted(i for i in inds if i and i != "Не определена")[:2]:
                buyers = _recent_buyers(ind, idx, exclude, today)
                if buyers:
                    picks.append(f"- Недавно покупали в отрасли «{ind}»: " + "; ".join(
                        f"{_company_link(idx, b)} — [{d.title}](#/deal/{d.id}), {fmt_date(d.date)}" for b, d in buyers))
            bought = [d for d in _company_deals(cid, idx, limit=50) if d.raw.get("buyer") == cid
                      and d.status == "Закрыта" and set(d.industries) & inds][:3]
            if bought:
                picks.append("- Активы компании в этой отрасли, купленные раньше (по нашим данным): " + "; ".join(
                    f"[{d.title}](#/deal/{d.id}), {fmt_date(d.date)}" for d in bought))
        if buy_side:
            on_sale = [s for s in rows if s.get("kind") in SELL_KINDS and s.get("company_id") not in exclude
                       and _signal_industries(s, idx) & inds]
            on_sale.sort(key=lambda s: str(s.get("date") or ""), reverse=True)
            if on_sale:
                picks.append("- Что в той же отрасли сейчас продают: " + "; ".join(
                    f"{_company_link(idx, s['company_id'])} ({fmt_date(s.get('date'))})" for s in on_sale[:4]))
        same = [s for s in rows if s.get("company_id") not in exclude and s.get("kind") in
                {k for sig in mine for k in ([sig.get("kind")] if sig.get("kind") else [])}
                and _signal_industries(s, idx) & inds]
        same.sort(key=lambda s: str(s.get("date") or ""), reverse=True)
        others = []
        for s in same:
            if s["company_id"] not in others:
                others.append(s["company_id"])
        if others:
            picks.append("- Похожие признаки в отрасли: " + ", ".join(_company_link(idx, o) for o in others[:4]))
    if picks:
        lines += ["", "**Кто подходит**"] + picks
    docs = []
    for sig in mine:
        d = idx.by_id.get(sig.get("deal_id") or "")
        if d and d not in docs:
            docs.append(d)
    for d in idx.company_deals.get(cid, []):
        if d not in docs:
            docs.append(d)
    ret = ar.Retrieval("signals", "\n".join(lines), docs[:ar.MAX_DEALS_FOR_MODEL], name, pool=docs)
    ret.company_id = cid        # main.py: профиль компании (отчётность) для модели
    return ret


def _answer_market(question: str, industry: str | None, idx, rows: list[dict], today: date):
    kinds = _kinds_asked(question)
    pick = [s for s in rows if (kinds is None or s.get("kind") in kinds)
            and (not industry or industry in _signal_industries(s, idx))]
    pick.sort(key=lambda s: str(s.get("date") or ""), reverse=True)
    scope = f" в отрасли «{industry}»" if industry else ""
    lines = ["**Признаки**"]
    if not pick:
        lines.append(f"- Явных признаков будущих сделок{scope} в наших данных нет.")
        lines += ["", "**Что это может значить**",
                  "- Без заявлений компаний и обсуждаемых сделок говорить о будущих сделках рано."]
        return ar.Retrieval("signals", "\n".join(lines), [], industry or "признаки сделок")
    by_company: dict[str, list[dict]] = {}
    for s in pick:
        by_company.setdefault(s["company_id"], []).append(s)
    shown = list(by_company)[:MAX_LIST]
    for cid in shown:
        lines.append(_signal_line(by_company[cid][0], idx, with_company=True))
    if len(by_company) > len(shown):
        lines.append(f"- И ещё {len(by_company) - len(shown)} — спросите о конкретной компании.")
    groups = Counter(_meaning_key(s.get("kind")) for cid in shown for s in by_company[cid][:1])
    lines += ["", "**Что это может значить**"]
    for key, _n in groups.most_common():
        if key in MEANING:
            names = [ _company_link(idx, cid) for cid in shown if _meaning_key(by_company[cid][0].get("kind")) == key][:4]
            lines.append(f"- {', '.join(names)}: {MEANING[key]}.")
    lines.append("- Это не прогноз: заявления и переговоры не всегда заканчиваются сделкой.")
    picks = []
    if industry and (kinds is None or kinds & SELL_KINDS):
        buyers = _recent_buyers(industry, idx, set(shown), today)
        if buyers:
            picks.append(f"- Недавно покупали в отрасли «{industry}»: " + "; ".join(
                f"{_company_link(idx, b)} — [{d.title}](#/deal/{d.id}), {fmt_date(d.date)}" for b, d in buyers))
    if picks:
        lines += ["", "**Кто подходит**"] + picks
    docs = []
    for s in pick:
        d = idx.by_id.get(s.get("deal_id") or "")
        if d and d not in docs:
            docs.append(d)
    return ar.Retrieval("signals", "\n".join(lines), docs[:ar.MAX_DEALS_FOR_MODEL],
                        industry or "признаки сделок", pool=docs)


MARKET_Q = re.compile(r"\bкто\b|у\s+кого|\bкакие\b|\bкакая\b|\bкакой\b|\bгде\b|\bрынк|\bрынок|в\s+отрасл", re.I)


def _company_by_signal_names(question: str, idx, rows: list[dict]) -> str | None:
    """Запасной поиск компании среди тех, у кого есть признаки: длинное слово
    имени профиля, названное в вопросе в любом падеже («у Мосгорломбарда» —
    профиль «МГКЛ (Мосгорломбард)»). Общий поиск требует ВСЕХ значимых слов
    имени и такую компанию не узнаёт. Два кандидата — никого."""
    terms = ar.query_terms(question)
    found = set()
    for cid in {s.get("company_id") for s in rows}:
        name = ar._company_name(idx.companies, cid)
        for word in ar._significant(name or ""):
            if len(word) >= 5 and any(ar._name_word_match(word, t) for t in terms):
                found.add(cid)
                break
    return next(iter(found)) if len(found) == 1 else None


def answer(question: str, context_type: str | None = None, context_id: str | None = None,
           idx=None, rows: list[dict] | None = None, today: date | None = None):
    """Ответ маршрута «признаки» или None, если вопрос не о будущих сделках."""
    if not is_signal_question(question):
        return None
    idx = idx or ar.get_index()
    rows = load_signals() if rows is None else rows
    today = today or date.today()
    intent = ar.route(question, idx)
    cid = intent.company_id if intent.kind in ("company", "largest", "recent") else None
    if not cid and intent.company_ids:
        cid = intent.company_ids[0]
    if not cid and context_type == "company" and context_id and context_id in idx.companies \
            and not MARKET_Q.search(question):
        # Вопрос со страницы компании («Разобрать с ассистентом») — о ней,
        # даже если в имени есть слово отрасли.
        cid = context_id
    if not cid and not intent.industry:
        cid = _company_by_signal_names(question, idx, rows)
    if cid:
        return _answer_company(cid, question, idx, rows, today)
    if intent.industry or MARKET_Q.search(question):
        return _answer_market(question, intent.industry, idx, rows, today)
    # «Будут ли у «Ромашки» сделки?» — компанию не узнали: список чужих
    # признаков был бы ответом не на тот вопрос.
    return ar.Retrieval("signals", "**Признаки**\n- Эту компанию я не нашёл среди компаний «Компаса», поэтому "
                        "признаков её будущих сделок назвать не могу. Уточните название, как оно написано на "
                        "странице компании, или спросите о целой отрасли.", [], None)
