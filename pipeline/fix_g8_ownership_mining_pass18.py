# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — восемнадцатая партия майнинга уже собранного
текста карточек. Три уровня очереди дочитывания снова пусты (12 сентября
2026, тринадцатый час подряд).

Тот же расширенный триггер, что и в партиях 9-17. С учётом уже занятых
78 профилей (пассы 1-17) замер дал 210 уникальных компаний-кандидатов —
метод по-прежнему далёк от исчерпания. Отобраны шесть с однозначным
направлением (проверено по `target`/`buyer`/`seller_id` каждой сделки) и
без оговорок.

- `g163cfc8b` (Циан, target сделки `g0dedddbd` — продажа Goldman Sachs 9%
  акций): на начало 2022 года «Эльбрус Капитал» владел 45,1% акций, ещё
  8% принадлежали основателю площадки Дмитрию Дёмину.
- `gcodspb` (ЦОД СПб, target сделки `gf080e8f0` — покупка СберИнвестом
  30%): СберИнвест владеет 30% компании.
- `gfb08c766` (ПИК-специализированный застройщик, target сделки
  `g134cf416` — делистинг с Мосбиржи): «Недвижимые активы» владеет 98%
  акций.
- `gfa05d8ea` (Kuppersberg, target сделки `g6aabf02a` — рассмотрение
  покупки Merlion): бренд принадлежит ООО «Эм-джи русланд», в котором
  50% у Зазы Горгиджанова, 45% — у Андижана Моисеева, 5% — у Дмитрия
  Шашкина.
- `gcf6f1146` (Вестсайд, buyer сделки `gc1a34417` — покупка «Дойче
  Лизинг Восток»): 49% компании принадлежит ООО «АБ Холдинг» —
  материнской структуре Альфа-Банка.
- `g1a796215` (ООО «Мерит», buyer сделки `g3c56d235` — покупка
  российского каталога Sony Music): принадлежит Александру Аксёнову
  (80%) и Лилии Беляевой (20%).

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass18.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass18.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'g163cfc8b': [
        {
            'name': 'Эльбрус Капитал',
            'id': None,
            'share': '45,1%',
            'as_of': '2022',
            'source': ['CNews', 'https://www.cnews.ru/news/top/2023-02-14_goldman_sachs_prodal_aktsii_tsian'],
        },
        {
            'name': 'Дмитрий Дёмин (через MPOC Technologies)',
            'id': None,
            'share': '8%',
            'as_of': '2022',
            'source': ['CNews', 'https://www.cnews.ru/news/top/2023-02-14_goldman_sachs_prodal_aktsii_tsian'],
        },
    ],
    'gcodspb': [{
        'name': 'СберИнвест',
        'id': 'gac30cf97',
        'share': '30%',
        'as_of': '2025',
        'source': ['TAdviser', 'https://www.tadviser.ru/a/965928'],
    }],
    'gfb08c766': [{
        'name': '«Недвижимые активы»',
        'id': None,
        'share': '98%',
        'as_of': '2026',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/8938431'],
    }],
    'gfa05d8ea': [
        {
            'name': 'ООО «Эм-джи русланд» (Заза Горгиджанов)',
            'id': None,
            'share': '50%',
            'as_of': '2024',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6636078'],
        },
        {
            'name': 'ООО «Эм-джи русланд» (Андижан Моисеев)',
            'id': None,
            'share': '45%',
            'as_of': '2024',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6636078'],
        },
        {
            'name': 'ООО «Эм-джи русланд» (Дмитрий Шашкин)',
            'id': None,
            'share': '5%',
            'as_of': '2024',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6636078'],
        },
    ],
    'gcf6f1146': [{
        'name': 'ООО «АБ Холдинг» (материнская структура Альфа-Банка)',
        'id': None,
        'share': '49%',
        'as_of': '2023',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/5979256'],
    }],
    'g1a796215': [
        {
            'name': 'Александр Аксёнов',
            'id': None,
            'share': '80%',
            'as_of': '2022',
            'source': ['VC.ru', 'https://vc.ru/media/584636-struktura-byvshih-menedzherov-warner-music-russia-kupila-kompaniyu-kotoraya-upravlyaet-rossiyskim-katalogom-sony-music'],
        },
        {
            'name': 'Лилия Беляева',
            'id': None,
            'share': '20%',
            'as_of': '2022',
            'source': ['VC.ru', 'https://vc.ru/media/584636-struktura-byvshih-menedzherov-warner-music-russia-kupila-kompaniyu-kotoraya-upravlyaet-rossiyskim-katalogom-sony-music'],
        },
    ],
}


def main(write=False):
    """Идемпотентен, как pass1-17."""
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
