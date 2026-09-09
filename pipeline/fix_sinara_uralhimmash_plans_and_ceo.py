# -*- coding: utf-8 -*-
"""Месячная очередь, 9 сентября 2026 — дочитывание карточки `g92ef210a`
(«Группа "Синара" купила у Газпромбанка около 75% акций "Уралхиммаша"»,
добавлена в базу 3 августа 2026, полностью обыскана в тот же день).

Дельта-поиск (саб-агент + личная проверка) нашёл два новых факта:

1) Планы «Синары» на завод. Личный WebFetch (kommersant.ru/doc/7250559
   — тот же источник, что уже стоит в `src`, дочитан глубже) подтвердил
   дословно: «В планах компании сохранить профиль предприятия и
   развивать новые направления бизнеса.» Добавлено в `eco.rationale`
   (стояло прочерком).

2) Смена гендиректора завода в конце 2025 года. Личный WebFetch
   (runews24.ru, 1 декабря 2025) подтвердил дословно: «С первого декабря
   2025 года пост руководителя занимает Сергей Гавриков, который ранее
   уже возглавлял завод»; «Евгений Гриценко, занимавший должность
   генерального директора ранее в текущем году, не покидает холдинг, а
   продолжит свою работу в должности вице-президента группы «Синара»».
   Добавлено в `law.struct`.

Итоговая сумма сделки, финансовый консультант и точный размер пакета,
сохранённого Газпромбанком, по-прежнему нигде не названы (проверено
Коммерсантъ, Forbes, Интерфакс, TASS, ao-journal.ru) — карточка права,
что оставляет их как есть.

Запуск:
    python3 pipeline/fix_sinara_uralhimmash_plans_and_ceo.py            # сухой прогон
    python3 pipeline/fix_sinara_uralhimmash_plans_and_ceo.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_ECO_RATIONALE = '—'
NEW_ECO_RATIONALE = (
    'В планах группы «Синара» сохранить профиль предприятия и развивать '
    'новые направления бизнеса.'
)

OLD_LAW_STRUCT = (
    'Газпромбанк сохранил небольшой пакет акций и пообещал продолжить '
    'расширение площадки и запуск новых мощностей. Оперативное '
    'управление предприятием осталось за прежним менеджментом. '
    'Управляющую компанию «Уралхиммаша» возглавляет Тамара Кобаладзе.'
)
NEW_LAW_STRUCT = OLD_LAW_STRUCT + (
    ' С 1 декабря 2025 года гендиректором самого завода вновь стал '
    'Сергей Гавриков, ранее уже возглавлявший предприятие; его '
    'предшественник на этом посту Евгений Гриценко перешёл на должность '
    'вице-президента группы «Синара».'
)

NEW_SRC = ['RuNews24', 'https://runews24.ru/society/01/12/2025/sovet-direktorov-uralximmasha-naznachil-sergeya-gavrikova-novyim-generalnyim-direktorom-s-1-dekabrya']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['g92ef210a']

    assert d['eco']['rationale'] == OLD_ECO_RATIONALE, \
        'g92ef210a eco.rationale уже другой: %r' % (d['eco']['rationale'],)
    assert d['law']['struct'] == OLD_LAW_STRUCT, \
        'g92ef210a law.struct уже другой: %r' % (d['law']['struct'],)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[1] not in urls, 'источник уже добавлен'

    print('g92ef210a: eco.rationale заполнен (планы «Синары»); law.struct '
          'дополнен (смена гендиректора завода); добавлен источник '
          'runews24.ru')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['eco']['rationale'] = NEW_ECO_RATIONALE
    d['law']['struct'] = NEW_LAW_STRUCT
    d['src'].append(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
