# -*- coding: utf-8 -*-
"""Sokolov/Антон Пак (`g68975b9d`): «Шаг 0» (вычитка карточки ДО поиска,
REVISION_BRIEF.md) нашёл серьёзное заражение полей — партия
`batch_digest_r1_auto.py` («digest ChatGPT round1») приписала карточке
Sokolov факты и источники ЧЕТЫРЁХ посторонних сделок сразу: `eco.val`
нёс оценку сделки по «Аквариусу» (sostav.ru), `eco.context` — историю
переименования «Софт Плюс» (ComNews/Solar), `law.struct` — опровержение
входа «МТ-Интеграции» в «Аквариус» (Ведомости). В `src` та же партия
дописала СЕМЬ посторонних источников (Аквариус ×3, Ipsos/Komkon, рекламное
агентство adindex.ru, «Hello Blogger», и даже голую поисковую страницу
Mergers.ru без единой статьи) — из 11 записей в `src` только 3 реально
про Sokolov (Коммерсантъ doc/7959262, Т-Банк, The Moscow Times).

Причина: у партии `digest ChatGPT round1` было несколько карточек в
одном проходе, и присвоение `id` каждой записи `FIXES` сломалось —
судя по остальным записям того же файла, факты про «Аквариус» и «Софт
Плюс» должны были уйти на СВОИ карточки (в базе они, видимо, не заведены
вовсе — это уже не в рамках сегодняшней починки, только измерено и
записано в журнал). `review.py` не поймал это при записи, потому что
проверяет дословность цитаты, а не то, что цитата ДЕЙСТВИТЕЛЬНО про
предмет ЭТОЙ карточки — тот же класс слепого пятна, что уже описан в
CLAUDE.md для похожих, более узких промахов.

Верные значения трёх полей взяты из уже привязанных, дословно
процитированных источников САМОЙ карточки (Коммерсантъ, Т-Банк) —
push'ить наружу за новыми фактами не пришлось, эти факты уже лежали в
кэше карточки, просто не в тех полях.

Запуск: python3 pipeline/fix_sokolov_field_contamination.py           # проверка
        python3 pipeline/fix_sokolov_field_contamination.py --write   # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g68975b9d'

BAD_ECO_VAL = (
    'Собеседник издания оценивает стоимость сделки по приобретению '
    '«Аквариуса» в диапазоне 50−80 млрд руб., учитывая долговую '
    'нагрузку и производственные мощности.')
BAD_ECO_CONTEXT = 'До ноября 2023 г. «Софт Плюс» носил другое название — ООО «ХЕКСВЕЙ».'
BAD_LAW_STRUCT = (
    'Информация о входе ГК «МТ-Интеграция» (ранее ГК «Максима») в '
    'состав акционеров группы компаний «Аквариус» не соответствует '
    'действительности, сообщил «Ведомостям» представитель компании.')

NEW_ECO_VAL = (
    'По словам гендиректора «Infoline-Аналитики» Михаила Бурмистрова, '
    'холдинг Sokolov находится в хорошей финансовой форме и, учитывая '
    'западные публичные аналоги, мог быть оценен более чем в 6 EBITDA. '
    'Сопоставимые компании на российском рынке торгуются сейчас с '
    'мультипликаторами около 4–5 EBITDA, однако сумму сделки эксперт '
    'оценивает в широком диапазоне — от 30 млрд до 40 млрд руб.')
NEW_ECO_CONTEXT = (
    'Артему Соколову ювелирный бизнес перешел в 2014 году от родителей '
    '— Елены и Алексея Соколовых, основавших холдинг в 1993 году. '
    'Вначале это было производство украшений, позже появилась '
    'одноименная розничная сеть, объединяющая на начало 2025 года, по '
    'собственным данным, около 1 тыс. магазинов по всей России.')
NEW_LAW_STRUCT = (
    'Управляющая компания ювелирного холдинга SOKOLOV – WELVART '
    'HOLDING AG DMCC (ОАЭ) – объявляет о продаже 100% акций АО '
    '«Ювелит», АО «Лакса Трейдинг» и их дочерних компаний (ООО «СВ '
    'Ритейл» и АО «Кварт») акционерному обществу «Аурум Бокс», '
    'принадлежащему Антону Паку.')

# Только эти три источника действительно про Sokolov — остальные восемь
# (Аквариус ×3, Ipsos/Komkon, adindex.ru, Hello Blogger, голая страница
# поиска Mergers.ru) относятся к чужим сделкам и снимаются целиком.
GOOD_SRCS = [
    ['Коммерсантъ', 'https://www.kommersant.ru/doc/7959262'],
    ['Т-Банк', 'https://www.tbank.ru/invest/social/profile/SOKOLOV/'
     '59adca64-bb09-4e72-926d-ed02e63dbda3/'],
    ['The Moscow Times', 'https://ru.themoscowtimes.com/2025/08/14/'
     'benefitsiar-yuvelirnogo-kholdinga-sokolov-prodal-ego-chastnomu-'
     'investoru-paku-gazeta-a171592'],
]


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    card = next((c for c in data['deals'] if c['id'] == CARD_ID), None)
    assert card is not None, '%r не найдена в базе' % CARD_ID
    assert card['eco'].get('val') == BAD_ECO_VAL, (
        'eco.val изменился с ожидаемого: %r' % card['eco'].get('val'))
    assert card['eco'].get('context') == BAD_ECO_CONTEXT, (
        'eco.context изменился с ожидаемого: %r' % card['eco'].get('context'))
    assert card['law'].get('struct') == BAD_LAW_STRUCT, (
        'law.struct изменился с ожидаемого: %r' % card['law'].get('struct'))
    src = card.get('src') or []
    assert len(src) == 11, 'src изменился с ожидаемых 11 записей: %d' % len(src)

    print('ПРАВИМ  %s: eco.val — оценка мультипликатора Бурмистрова' % CARD_ID)
    print('ПРАВИМ  %s: eco.context — история холдинга (2014, семья Соколовых)' % CARD_ID)
    print('ПРАВИМ  %s: law.struct — юрлица и структура сделки' % CARD_ID)
    print('СНИМАЕМ %s: 8 посторонних источников из src (11 -> 3)' % CARD_ID)
    if write:
        card['eco']['val'] = NEW_ECO_VAL
        card['eco']['context'] = NEW_ECO_CONTEXT
        card['law']['struct'] = NEW_LAW_STRUCT
        card['src'] = GOOD_SRCS
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
