# -*- coding: utf-8 -*-
"""Глубокое дочитывание, партия 1: правки, не укладывающиеся в модель
review.py (одна цитата — одно поле целиком), с ручным `assert` на исходное
состояние, по образцу `pipeline/fix_proofreading_round4.py`.

1. СЛИЯНИЕ ДУБЛЯ. gdcc03f9d («Продажа госпакета 67,25% акций ЮГК — АО
   «БТС-Мост Холдинг») и cc16fce80 («Росимущество продало ЮГК структуре
   Байсарова») — одна и та же сделка под двумя id: тот же buyer (g27b935b9),
   тот же target (g2c0e743d), та же дата (2026-06-19), тот же четвёртый
   голландский аукцион, сумма отличается лишь округлением (93,16 vs
   93,2 млрд ₽). cc16fce80 уже несёт `deep_researched: 2026-08-14` и
   `reviewed: 2026-08-18` — глубже проверена, остаётся она. Уникальные
   источники gdcc03f9d (официальные страницы Росимущества, РИА, Forbes,
   Эксперт, вторая ссылка на Ъ) переносятся в src cc16fce80, а не
   теряются. Ссылка на старый id продолжает работать через `merged`
   (родственный урок CLAUDE.md: «слияние карточек не должно обрывать
   ссылку»).

2. gf5c8e14e (ГК «Филанко»/«Нэтлинк»+«Комитен Корп»): law.struct нёс
   «сделка по Нэтлинк — в процессе закрытия» — четыре независимых
   источника (CNews, IT-World, AKM, и прямая цитата с сайта самого
   покупателя citytelecom.ru, уже в src карточки) сходятся: ОБЕ сделки
   закрыты одновременно 19 января 2026 года. Дословная цитата (проверена
   в скачанном тексте): «Компания «Ситителеком» закрыла сделки по
   приобретению операторов связи «Нэтлинк» и «Комитен»».

3. gedfd4c1e (Herbalife/Bioniq): status стоял «Подписана», хотя ЖЕ поле
   `extra` ЭТОЙ карточки уже пишет «закрыта 30 апреля 2026 года» (по
   данным SEC Form 8-K) — внутреннее противоречие полей одной карточки.
   Внешнее подтверждение того же (nutraingredients.com, 10.08.2026):
   Herbalife запустил продукт «Bioniq GO» в США «as part of its Bioniq
   brand acquired earlier this year» — бренд уже называется частью
   портфеля, не предметом ожидаемой сделки. Через review.py эту правку
   не провести формально: ни «закрыта» (участие, не совпадает с формой
   «закрыл» в STATUS_WORDS — тот же класс, что и урок про «продавц\\w*»),
   ни фраза Ъ «После завершения сделки» (эта цитата — из анонса о
   БУДУЩИХ планах на март 2026 года, использовать её для статуса значило
   бы подменить объявление о намерениях подтверждением факта).

4. gf14ff7aa (Альфа-банк/А1/Альфа-Капитал — ЗПИФ «специальных ситуаций»):
   status стоял «Обсуждается», хотя официальный реестр ПИФ Банка России
   (`list_pif.xlsx`, снимок на 16.08.2026, строка 7614) показывает фонд
   со статусом «Сформирован»: номер правил ДУ 7630-СД присвоен
   26.02.2026, дата окончания формирования — 02.04.2026, договор ДУ
   действует до 30.06.2033, пять пакетов изменений правил зарегистрировано
   в течение 2026 года. Реестр ЦБ — не газетная цитата со словом статуса
   из STATUS_WORDS, а первичный государственный источник; правка ручная,
   а не через словарь-подтверждение review.py.

Запуск:
    python3 pipeline/fix_deep_batch1_manual.py            # сухой прогон
    python3 pipeline/fix_deep_batch1_manual.py --write    # запись
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

MERGE_OLD = 'gdcc03f9d'
MERGE_NEW = 'cc16fce80'

STRUCT_OLD = ('Приобретение 100% долей трёх операционных юридических лиц '
              '(ООО «Комитен Корп», ООО «К-Ритейл», ООО «Нетлинк») с '
              'последующей интеграцией в единый контур «Ситителеком»; '
              'сделка по Комитен закрыта 19 января 2026 года, сделка по '
              'Нэтлинк — в процессе закрытия.')
STRUCT_NEW = ('Приобретение 100% долей трёх операционных юридических лиц '
              '(ООО «Комитен Корп», ООО «К-Ритейл», ООО «Нетлинк») с '
              'последующей интеграцией в единый контур «Ситителеком»; обе '
              'сделки — по «Комитен Корп» и по «Нэтлинк» — закрыты '
              'одновременно, 19 января 2026 года.')
STRUCT_QUOTE_CHECK = 'закрыла сделки по приобретению операторов связи'


def by_id(data):
    return {d['id']: d for d in data['deals']}


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    ids = by_id(data)

    old_card = ids[MERGE_OLD]
    new_card = ids[MERGE_NEW]
    assert new_card.get('deep_researched'), \
        'cc16fce80 должна быть уже deep_researched — иначе слияние не туда'
    assert old_card['buyer'] == new_card['buyer'] == 'g27b935b9'
    assert old_card['target'] == new_card['target'] == 'g2c0e743d'
    assert old_card['date'] == new_card['date'] == '2026-06-19'
    new_urls = {s[1] for s in new_card.get('src') or []}
    to_transfer = [s for s in old_card.get('src') or [] if s[1] not in new_urls]

    struct_card = ids['gf5c8e14e']
    assert struct_card['law']['struct'] == STRUCT_OLD, \
        'law.struct у gf5c8e14e уже другой — правка неактуальна'

    herbalife = ids['gedfd4c1e']
    assert herbalife['status'] == 'Подписана', \
        'status у gedfd4c1e уже другой — правка неактуальна'
    assert 'закрыта 30 апреля 2026' in (herbalife.get('extra') or ''), \
        'extra не подтверждает закрытие — не переносить статус вслепую'

    alfa = ids['gf14ff7aa']
    assert alfa['status'] == 'Обсуждается', \
        'status у gf14ff7aa уже другой — правка неактуальна'

    print('Слияние: %s -> %s, переносим %d источник(ов) в src' %
          (MERGE_OLD, MERGE_NEW, len(to_transfer)))
    for s in to_transfer:
        print('   + %s' % s)
    print('law.struct gf5c8e14e: убираем «в процессе закрытия»')
    print('status gedfd4c1e: Подписана -> Закрыта')
    print('status gf14ff7aa: Обсуждается -> Закрыта')

    if '--write' not in argv:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    new_card.setdefault('src', []).extend(to_transfer)
    data['deals'] = [d for d in data['deals'] if d['id'] != MERGE_OLD]
    data.setdefault('merged', {})[MERGE_OLD] = MERGE_NEW

    struct_card['law']['struct'] = STRUCT_NEW

    herbalife['status'] = 'Закрыта'
    alfa['status'] = 'Закрыта'

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
