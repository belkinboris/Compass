# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — двадцать первая партия майнинга уже собранного
текста карточек. Три уровня очереди дочитывания снова пусты (12 сентября
2026, восемнадцатый час подряд).

Тот же расширенный триггер, что и в партиях 9-20. С учётом уже занятых
108 профилей (пассы 1-20) замер дал 192 уникальные компании-кандидата.
Партия крупнее обычной (11 вместо 6): почти все найденные кандидаты этого
прохода оказались чистыми (однозначное направление, сумма долей сходится
или партиально объяснима свободным обращением), и фиксированная стоимость
партии (перечитывание CLAUDE.md/REVISION_BRIEF.md) одна что на 6, что на 11
записей — отбирать меньше не было смысла.

- `g4a74dc09` (Fusion Factor Fintech Limited, seller_id сделки `g089e507d`
  — «Займер» купил 50% платёжной системы БЭСТ): FFF — холдинговая
  структура АО «Киви», контролируемая бывшим гендиректором Qiwi Андреем
  Протопоповым.
- `g3cc9e79b` (Globaltruck, target сделки `gfe268487` — «Монополия»
  купила 75,07% акций): до сделки (апрель 2023) 61% контролировал
  основатель Александр Елисеев через кипрскую GT Globaltruck Ltd, 19,4% —
  РФПИ с соинвесторами; остаток — свободное обращение на бирже (ПАО «ГТМ»
  было публичной компанией).
- `g82bd57f9` (Авиапарк, target сделки `g8e9d37ba` — выставление на
  продажу): по данным на декабрь 2022 года владелец — АО «ТВК «Авиапарк»»,
  принадлежащее кипрской Darkforest Holding Company; текущие бенефициары
  Darkforest не раскрыты.
- `g761804d9` (Segezha Packaging, target сделки `g22b470f6` — Segezha
  Group продала актив за €1): исторически, до покупки «Сегежским ЦБК» в
  2006 году, актив (тогда — Korsnas Packaging) принадлежал шведскому
  инвестхолдингу Kinnevik.
- `g56e5e7e7` (Bidzaar, target сделки `g1fa8d09e` — раунд А): после
  раунда доли распределились 76% — основатель и гендиректор Cognitive
  Technologies Андрей Черногоров, 24% — основатель «Сбер Еаптеки» Антон
  Буздалин (до раунда Черногоров владел 100%).
- `g6eb3c726` (GrimTeam, buyer сделки `ga0a49202` — покупка сети квестов
  «Клаустрофобия»): в обеих компаниях (GrimTeam и цель) 51% принадлежит
  инвестору Вадиму Змовику, 33% — инвестору Павлу Вараксину, 16% —
  сооснователю Евгению Авину (Антонову).
- `g1617e6cd` (МедТехСервис, target сделки `gc991514e` — «Лето Финанс»
  купила 50%): проданные 50% принадлежали трём совладельцам — Сергею
  Дьяченко (17%), Фёдору Железнякову (17%), Петру Железнякову (16%).
- `gbaa98e6b` (Russ Outdoor, buyer сделки `g3ef24264` — покупка
  «Метронома»): по данным ЕГРЮЛ, головная структура Russ Outdoor —
  ООО «Стинн».
- `g898ca701` (Берахим, target сделки `g07fffba3` — ГК «Промомед» купила
  контрольную долю): после сделки (декабрь 2022) оставшиеся доли —
  40% у основателя Евгения Черторижского, 9% — у гендиректора Ирины
  Аксёновой (плюс 51% у «Промомед» — уже известно из сделки).
- `g980e9dff` (Rubetek, target сделки `g7edd263c` — инвестиция ERA
  Capital): после сделки (2025) 45% — у ERA Capital, 45% — у основателя
  и гендиректора Антона Мальцева, 10% — у фонда «Основа Капитал»
  Александра Бабаева.
- `ged2d56b7` (Бумеранг агроинвест, buyer сделки `gb30e66af` — покупка
  85% производителя салатов «Прованс»): фонд контролируют «Бумеранг
  капитал» Вагана Гаспаряна (49%), его гендиректор Перфильев (1%), АО
  «Пикалевская сода» бывшего гендиректора «Фосагро» Максима Волкова
  (25%) и ЗПИФ «Рэвард Капитал» бенефициара Александра Раппопорта (25%,
  с сентября 2025 года).

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass21.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass21.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'g4a74dc09': [{
        'name': 'АО «Киви» (контролируется Андреем Протопоповым)',
        'id': None,
        'as_of': '2026-06',
        'source': ['Forbes.ru', 'https://www.forbes.ru/finansy/562732-gruppa-zajmer-kupila-50-plateznoj-sistemy-best-u-vladel-ca-ao-kivi'],
    }],
    'g3cc9e79b': [
        {
            'name': 'Александр Елисеев (через кипрскую GT Globaltruck Ltd)',
            'id': None,
            'share': '61%',
            'as_of': '2023-04',
            'source': ['Forbes', 'https://www.forbes.ru/biznes/487111-rbk-uznal-o-vozmoznoj-prodaze-61-gruzoperevozcika-globaltruck-gruppe-monopolia'],
        },
        {
            'name': 'РФПИ с соинвесторами',
            'id': None,
            'share': '19,4%',
            'as_of': '2023-04',
            'source': ['Forbes', 'https://www.forbes.ru/biznes/487111-rbk-uznal-o-vozmoznoj-prodaze-61-gruzoperevozcika-globaltruck-gruppe-monopolia'],
        },
    ],
    'g82bd57f9': [{
        'name': 'Darkforest Holding Company (Кипр)',
        'id': None,
        'as_of': '2022-12',
        'source': ['Ведомости', 'https://www.vedomosti.ru/realty/articles/2025/07/24/1126543-aviapark-vistavlen-na-prodazhu'],
    }],
    'g761804d9': [{
        'name': 'Kinnevik (шведский инвестхолдинг)',
        'id': None,
        'as_of': 'до 2006',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6000855'],
    }],
    'g56e5e7e7': [
        {
            'name': 'Андрей Черногоров',
            'id': None,
            'share': '76%',
            'as_of': '2021-06',
            'source': ['vc.ru', 'https://vc.ru/services/260552-cervis-avtomatizacii-zakupok-dlya-biznesa-bidzaar-privlek-2-mln-ot-svoego-osnovatelya-i-sozdatelya-sber-eapteki'],
        },
        {
            'name': 'Антон Буздалин',
            'id': None,
            'share': '24%',
            'as_of': '2021-06',
            'source': ['vc.ru', 'https://vc.ru/services/260552-cervis-avtomatizacii-zakupok-dlya-biznesa-bidzaar-privlek-2-mln-ot-svoego-osnovatelya-i-sozdatelya-sber-eapteki'],
        },
    ],
    'g6eb3c726': [
        {
            'name': 'Вадим Змовик',
            'id': None,
            'share': '51%',
            'as_of': '2025-07',
            'source': ['РБК', 'https://www.rbc.ru/technology_and_media/15/08/2025/689db55a9a7947b058474799'],
        },
        {
            'name': 'Павел Вараксин',
            'id': None,
            'share': '33%',
            'as_of': '2025-07',
            'source': ['РБК', 'https://www.rbc.ru/technology_and_media/15/08/2025/689db55a9a7947b058474799'],
        },
        {
            'name': 'Евгений Авин (Антонов)',
            'id': None,
            'share': '16%',
            'as_of': '2025-07',
            'source': ['РБК', 'https://www.rbc.ru/technology_and_media/15/08/2025/689db55a9a7947b058474799'],
        },
    ],
    'g1617e6cd': [
        {
            'name': 'Сергей Дьяченко',
            'id': None,
            'share': '17%',
            'as_of': 'до 2024-02',
            'source': ['Интерфакс', 'https://www.interfax.ru/business/945677'],
        },
        {
            'name': 'Фёдор Железняков',
            'id': None,
            'share': '17%',
            'as_of': 'до 2024-02',
            'source': ['Интерфакс', 'https://www.interfax.ru/business/945677'],
        },
        {
            'name': 'Пётр Железняков',
            'id': None,
            'share': '16%',
            'as_of': 'до 2024-02',
            'source': ['Интерфакс', 'https://www.interfax.ru/business/945677'],
        },
    ],
    'gbaa98e6b': [{
        'name': 'ООО «Стинн» (головная структура)',
        'id': None,
        'as_of': '2023-06',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6055321'],
    }],
    'g898ca701': [
        {
            'name': 'Евгений Черторижский (основатель)',
            'id': None,
            'share': '40%',
            'as_of': '2022-12',
            'source': ['Ведомости', 'https://www.vedomosti.ru/business/news/2023/01/12/958849-promomed-vikupil-dolyu'],
        },
        {
            'name': 'Ирина Аксёнова (генеральный директор)',
            'id': None,
            'share': '9%',
            'as_of': '2022-12',
            'source': ['Ведомости', 'https://www.vedomosti.ru/business/news/2023/01/12/958849-promomed-vikupil-dolyu'],
        },
    ],
    'g980e9dff': [
        {
            'name': 'Антон Мальцев (основатель и гендиректор)',
            'id': None,
            'share': '45%',
            'as_of': '2025-02',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/7497438'],
        },
        {
            'name': '«Основа Капитал» (Александр Бабаев)',
            'id': None,
            'share': '10%',
            'as_of': '2025-02',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/7497438'],
        },
    ],
    'ged2d56b7': [
        {
            'name': '«Бумеранг капитал» (Ваган Гаспарян)',
            'id': None,
            'share': '49%',
            'as_of': '2025-09',
            'source': ['Ведомости', 'https://www.vedomosti.ru/business/articles/2025/09/10/1138375-vlozhilis-v-proizvoditelya-salatov'],
        },
        {
            'name': 'Перфильев (гендиректор «Бумеранг капитала»)',
            'id': None,
            'share': '1%',
            'as_of': '2025-09',
            'source': ['Ведомости', 'https://www.vedomosti.ru/business/articles/2025/09/10/1138375-vlozhilis-v-proizvoditelya-salatov'],
        },
        {
            'name': 'АО «Пикалевская сода» (Максим Волков)',
            'id': None,
            'share': '25%',
            'as_of': '2025-09',
            'source': ['Ведомости', 'https://www.vedomosti.ru/business/articles/2025/09/10/1138375-vlozhilis-v-proizvoditelya-salatov'],
        },
        {
            'name': 'ЗПИФ «Рэвард Капитал» (Александр Раппопорт)',
            'id': None,
            'share': '25%',
            'as_of': '2025-09',
            'source': ['Ведомости', 'https://www.vedomosti.ru/business/articles/2025/09/10/1138375-vlozhilis-v-proizvoditelya-salatov'],
        },
    ],
}


def main(write=False):
    """Идемпотентен, как pass1-20."""
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    companies = data['companies']

    pending = {}
    for cid, entries in NEW_OWNERSHIP.items():
        assert cid in companies, 'нет такого профиля: %s' % cid
        current = companies[cid].get('ownership')
        if current:
            assert current == entries, 'ownership уже занят другим значением у %s: %r' % (cid, current)
            continue
        pending[cid] = entries

    if not pending:
        print('Все профили уже заполнены — нечего применять.')
        return

    print('Заполняю ownership: %s' % ', '.join('%s (%s)' % (cid, companies[cid]['name']) for cid in pending))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    for cid, entries in pending.items():
        companies[cid]['ownership'] = entries

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
