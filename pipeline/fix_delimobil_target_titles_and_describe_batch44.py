# -*- coding: utf-8 -*-
"""Сорок четвёртая партия: три правки + 9 описаний.

1. G3 (остаток от 9 августа): снятие юрлица в заголовках «Кузнецкой ТЭЦ»
   и «Уралхиммаша» — падеж проверен вручную (прилагательное «Кузнецкой»
   склоняется обычно, «ТЭЦ» несклоняема; «Уралхиммаша» — регулярный Р.п.
   мужского рода), не пропущен через pymorphy. Заголовки — единственное,
   что меняется; поле `asset` остаётся в именительном падеже как отдельное
   структурное поле.

2. НАЙДЕНО: испорченная ссылка `target`. У сделки g796316fe («Винченцо
   Трани увеличил долю в ПАО «Каршеринг Россия» («Делимобиль») до 66%»)
   `target` указывал на g7f250a60 «АО Дельта Холдинг» — но по тексту
   сделки именно «Дельта Холдинг» ВЫШЕЛ из капитала «Делимобиля», продав
   свою долю Трани: он продавец, а не предмет сделки. Настоящий предмет
   (юрлицо «Делимобиля») уже был отдельным, но ни с одной сделкой не
   связанным профилем — gca67e7ba «ПАО «Каршеринг Россия» (объект)».
   Родня уже дважды найденного в этой сессии класса («стороной сделки
   может быть записан профиль совсем другой сущности» — ЛСР/Domina
   Пулково, Уфабурмаш): `target` перенесён на верный профиль, «Дельта
   Холдинг» — на `seller`/`seller_id`. Заодно у профиля «Дельта Холдинг»
   в имени не было кавычек-«ёлочек» вокруг названия, хотя в тексте самой
   сделки они есть («АО «Дельта Холдинг»») — поправлено на то же
   написание.

3. Описания 9 профилям (включая освобождённый профиль «Делимобиля» и
   переименованный «Дельта Холдинг»), прочитанные по своим связанным
   сделкам.

Запуск:
    python3 pipeline/fix_delimobil_target_titles_and_describe_batch44.py            # сухой прогон
    python3 pipeline/fix_delimobil_target_titles_and_describe_batch44.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

TITLE_FIXES = {
    'gb0759159': (
        'СГК и «Кузбассэнерго» продали 100% акций АО «Кузнецкая ТЭЦ»',
        'СГК и «Кузбассэнерго» продали 100% акций «Кузнецкой ТЭЦ»',
    ),
    'g92ef210a': (
        'Группа «Синара» купила у Газпромбанка около 75% акций АО «Уралхиммаш»',
        'Группа «Синара» купила у Газпромбанка около 75% акций «Уралхиммаша»',
    ),
}

DELIM_DEAL_ID = 'g796316fe'
DELTA_ID = 'g7f250a60'
DELIM_TARGET_ID = 'gca67e7ba'
DELTA_OLD_NAME = 'АО Дельта Холдинг'
DELTA_NEW_NAME = 'АО «Дельта Холдинг»'

DESCRIPTIONS = {
    'g5c2009c6': 'Оператор связи под брендом «Ситителеком»; в 2026 году '
                 'купил операторов «Нэтлинк» и «Комитен Корп», добавив '
                 'свыше 200 км оптики.',
    'g4a5ba7c7': 'Структура бизнесмена Андрея Зокина; в 2026 году через '
                 'неё в два этапа куплено 80% сервиса SuperJob.',
    'g78add6eb': 'ООО «ЛайфСтрим», видеосервис «Смотрешка»; в 2026 году '
                 'куплен онлайн-кинотеатром Wink (структурой '
                 '«Ростелекома») за 3,5 млрд ₽.',
    'gb02cbc20': 'Разработчик ИИ-платформы Razum AI, основан Владимиром '
                 'Нелюбом (экс-«Группа Астра»); в 2026 году 26% '
                 'выкупила сама «Группа Астра».',
    'g4a74dc09': 'Гонконгская компания CEO Qiwi Андрея Протопопова; в '
                 '2024 году через неё менеджмент выкупил у Qiwi plc '
                 'российский бизнес (АО «КИВИ») за 23,75 млрд ₽.',
    'g3e551f6e': 'В 2026 году купила у «Газпрома» спутниковый завод '
                 '«Газпром СПКА» в Щёлкове вместе с центром управления '
                 'полётами.',
    'g417388ed': 'Компания бывших менеджеров российского Bosch; в 2026 '
                 'году купила завод «Энгельс Электроинструменты» '
                 '(бывший завод Bosch).',
    'g9d2e4c88': 'Строит промышленные и торговые объекты, владеет '
                 'заводом металлоконструкций в Петушках; в 2026 году '
                 '51% выкупила RBE Group.',
    DELIM_TARGET_ID: 'Юрлицо каршеринга «Делимобиль»; в 2026 году '
                      'акционер «Дельта Холдинг» вышел из капитала, '
                      'продав 12,9% Винченцо Трани.',
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    by_id = {d['id']: d for d in data['deals']}

    # --- 1. заголовки ---
    for did, (old, new) in TITLE_FIXES.items():
        d = by_id[did]
        assert d['title'] == old, 'заголовок %s уже изменён: %r' % (did, d['title'])
        print('ЗАГОЛОВОК %-12s: %s -> %s' % (did, old[:40], new[:40]))
        if write:
            d['title'] = new

    # --- 2. Делимобиль / Дельта Холдинг ---
    deal = by_id[DELIM_DEAL_ID]
    assert deal['target'] == DELTA_ID, 'target сделки уже не Дельта Холдинг'
    assert deal.get('seller') is None and deal.get('seller_id') is None, \
        'seller сделки уже заполнен'
    assert comps[DELTA_ID]['name'] == DELTA_OLD_NAME, 'имя Дельта Холдинг уже изменено'
    assert comps[DELIM_TARGET_ID]['name'] == 'ПАО «Каршеринг Россия» (объект)'

    print('ПЕРЕНОС TARGET  %s: %s -> %s' % (DELIM_DEAL_ID, DELTA_ID, DELIM_TARGET_ID))
    print('SELLER  %s: -> %s (%s)' % (DELIM_DEAL_ID, DELTA_ID, DELTA_NEW_NAME))
    print('ПЕРЕИМЕНОВАНИЕ  %s: %r -> %r' % (DELTA_ID, DELTA_OLD_NAME, DELTA_NEW_NAME))

    if write:
        deal['target'] = DELIM_TARGET_ID
        deal['seller_id'] = DELTA_ID
        deal['seller'] = DELTA_NEW_NAME
        comps[DELTA_ID]['name'] = DELTA_NEW_NAME

    # --- 3. описания ---
    wrote, skipped = 0, []
    for cid, text in DESCRIPTIONS.items():
        c = comps.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert 15 <= len(text) <= 220, 'описание %s вне 1–2 строк: %d' % (cid, len(text))
        old = str(c.get('desc') or '')
        if old.strip() == text:
            continue
        if old and not PLACEHOLDER.match(old):
            skipped.append((cid, c.get('name'), old[:60]))
            continue
        print('  ОПИСАНИЕ %-12s %-40s %s' % (cid, str(c.get('name'))[:40], text[:50]))
        if write:
            c['desc'] = text
        wrote += 1

    print('\nОписаний записано: %d' % wrote)
    if skipped:
        print('Пропущено (уже есть своё описание): %d' % len(skipped))
        for cid, name, old in skipped[:5]:
            print('   %s %s — %r' % (cid, name, old))

    real = sum(1 for v in comps.values()
               if (v.get('desc') or '').strip() and not PLACEHOLDER.match(str(v.get('desc'))))
    print('Всего профилей с описанием: %d из %d (%d%%)'
          % (real, len(comps), round(100 * real / len(comps))))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
