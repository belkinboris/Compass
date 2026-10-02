# -*- coding: utf-8 -*-
"""Куда уходит пост: основной канал, канал «Компас - Недвижимость» или оба.

Решение владельца 2 октября 2026: «все новости про недвижимость — в новый
канал; если прям сделка и сумма больше миллиарда — постить и там и там и
делать кросс-ссылку на второй пост». Повод виден по счёту: из 145 постов
основного канала к тому дню 50 были про недвижимость, и большая часть из них —
торги «Дом.РФ» на особняки за несколько миллионов. Подписчику основного канала
это шум, подписчику канала недвижимости — его лента.

Правило (одно место на публикацию и на черновик в консоли):
  • не недвижимость — только основной канал, как было;
  • недвижимость — канал недвижимости;
  • недвижимость, сделка состоялась или подписана, и сумма от 1 млрд ₽ —
    оба канала, и каждый пост ссылается на свою пару.

«Недвижимость» — отрасль карточки (`ind`), та же, что в фильтрах сайта.
«Сумма» — число из карточки, если это цена сделки: названа сторонами, по
данным СМИ или «около». Стартовая цена торгов, оценка всей компании и
«не раскрыта» суммой сделки не считаются (смысл суммы решает
`deal_multiples.sum_basis` — единственное место, где это решается).
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import deal_multiples as dm  # noqa: E402

MAIN = 'main'
REALTY = 'realty'
REALTY_INDUSTRY = 'Недвижимость'
BIG_DEAL_RUB = 1_000_000_000
# «Прям сделка»: состоялась или подписана. «Обсуждается» (в том числе
# объявленные торги) и «Не состоялась» — новость, но не сделка.
DONE_STATUSES = ('Закрыта', 'Подписана', 'Согласование получено')
AMOUNT_BASES = ('disclosed', 'reported', 'estimate', 'range', 'lower_bound', 'raise')


def is_realty(deal):
    return deal.get('ind') == REALTY_INDUSTRY or deal.get('type') == 'Продажа недвижимости'


def amount_rub(deal):
    """Сумма сделки в рублях или None. Цена в валюте берётся пересчитанной по
    курсу ЦБ из слоя фактов (`facts.price.value_rub`)."""
    price = (deal.get('facts') or {}).get('price') or {}
    if price.get('value_rub') and price.get('meaning') in ('disclosed', 'foreign_currency'):
        return float(price['value_rub'])
    if dm.sum_basis(deal) in AMOUNT_BASES:
        return dm.parse_rub_sum(deal.get('sum'))
    return None


def is_big_deal(deal):
    return deal.get('status') in DONE_STATUSES and (amount_rub(deal) or 0) >= BIG_DEAL_RUB


def channels_for(deal, realty_known=True):
    """Кортеж каналов в порядке отправки. Основной — первым: его номер
    поста нужен посту в канале недвижимости для ссылки.

    Адрес канала недвижимости неизвестен (`realty_known=False`) — пост идёт в
    основной, как до 2 октября 2026: потерять пост хуже, чем выпустить его не
    в тот канал."""
    if not realty_known or not is_realty(deal):
        return (MAIN,)
    return (MAIN, REALTY) if is_big_deal(deal) else (REALTY,)


def post_link(chat_id, message_id):
    """Ссылка на пост закрытого канала: t.me/c/<номер без -100>/<пост>.
    Открывается у тех, кто подписан на канал."""
    raw = str(chat_id)
    internal = raw[4:] if raw.startswith('-100') else raw.lstrip('-')
    return 'https://t.me/c/%s/%s' % (internal, message_id)


CROSSLINK_LABEL = {
    MAIN: 'Этот пост — и в основном канале «Компаса»',
    REALTY: 'Этот пост — и в канале «Компас - Недвижимость»',
}


def with_crosslink(text, other, chat_id, message_id):
    """Текст поста со ссылкой на его пару в другом канале (`other`)."""
    return '%s\n\n<a href="%s">%s →</a>' % (text, post_link(chat_id, message_id),
                                            CROSSLINK_LABEL[other])


def destination(deal):
    """Куда уйдёт пост — для шапки черновика в консоли."""
    chans = channels_for(deal)
    if chans == (REALTY,):
        return 'В КАНАЛ «Компас - Недвижимость»'
    if REALTY in chans:
        return 'В ОБА КАНАЛА — основной и «Компас - Недвижимость»'
    return 'В КАНАЛ'
