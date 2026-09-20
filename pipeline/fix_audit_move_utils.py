# -*- coding: utf-8 -*-
"""Общий помощник для партий FIELD_MISPLACED: перенос предложения между полями.

Общая часть всех fix_audit_*_batch скриптов этой ночи: аудит уже даёт
дословную цитату (`quote`) и решение (`action`), но цитата у него часто
куда куски предложения, а не предложение целиком — при переносе так
оставался бы обрывок с висящей заглавной буквой в середине. Эта функция
расширяет цитату до границ предложения (по точке) внутри поля-источника,
проверяет, что назначение не занято тем же самым текстом (не плодит
дубль) и не тронуто решением читателя (review.py, FIXES), и переносит.
"""
from __future__ import annotations

import re


def extend_to_sentences(full_text: str, quote: str) -> str:
    """Расширить `quote` до границ предложений внутри `full_text`."""
    i = full_text.find(quote)
    if i < 0:
        raise ValueError("цитата не найдена дословно")
    j = i + len(quote)
    # назад до начала текста или до "* Заглавная" после точки+пробела —
    # ищем по ВСЕМУ тексту (не по срезу): иначе граничный символ после
    # пробела обрезался бы срезом и совпадение перед самой цитатой
    # терялось (просмотр вперёд смотрел за пределы среза).
    start = 0
    for m in re.finditer(r"(?<=[.!?])\s+(?=[А-ЯЁA-Z«\"'\d])", full_text):
        if m.end() > i:
            break
        start = m.end()
    # вперёд до конца текста или до конца предложения, где лежит правый край
    end = len(full_text)
    m2 = re.search(r"[.!?](?=\s+[А-ЯЁA-Z«\"']|\s*$)", full_text[j:])
    if m2:
        end = j + m2.end()
    return full_text[start:end].strip()


def get_field(card: dict, path: str):
    if "." not in path:
        return card.get(path)
    a, b = path.split(".", 1)
    return (card.get(a) or {}).get(b)


def set_field(card: dict, path: str, value: str):
    if "." not in path:
        card[path] = value
        return
    a, b = path.split(".", 1)
    card.setdefault(a, {})[b] = value


def apply_move(card: dict, src_path: str, quote: str, dst_path: str, write: bool,
               decided: set, card_id: str, log: list) -> bool:
    """True — применено (или сухой прогон подтвердил бы применение)."""
    src_text = get_field(card, src_path) or ""
    if quote not in src_text:
        log.append("%s: цитата не найдена в %s — пропущено" % (card_id, src_path))
        return False
    chunk = extend_to_sentences(src_text, quote)
    if (card_id, src_path) in decided or (card_id, dst_path) in decided:
        log.append("%s: %s или %s решены читателем — пропущено" % (card_id, src_path, dst_path))
        return False
    dst_text = get_field(card, dst_path) or ""
    if chunk in dst_text:
        # Уже есть там — просто убрать дубль из источника.
        new_src = src_text.replace(chunk, "").strip()
        new_src = re.sub(r"\s+", " ", new_src)
        log.append("%s: %s → %s (уже дублировано в назначении, дубль убран из источника) «%s…»"
                   % (card_id, src_path, dst_path, chunk[:50]))
        if write:
            set_field(card, src_path, new_src if new_src else "—")
        return True
    new_dst = chunk if not dst_text or dst_text in ("—", "-", "") else (dst_text + " " + chunk)
    new_src = src_text.replace(chunk, "").strip()
    new_src = re.sub(r"\s+", " ", new_src)
    log.append("%s: %s → %s «%s…»" % (card_id, src_path, dst_path, chunk[:50]))
    if write:
        set_field(card, dst_path, new_dst)
        set_field(card, src_path, new_src if new_src else "—")
    return True
