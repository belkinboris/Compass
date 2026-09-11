# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — вторая партия майнинга уже собранного текста
карточек (три уровня очереди дочитывания пусты третий час подряд,
11 сентября 2026). Тот же метод, что в pass1: слова «бенефициар»/
«подконтрольный»/«конечный владелец» рядом с профилем стороны сделки,
у которого ещё нет поля `ownership`. Оба факта уже читались (стоят в
`extra` карточек с дословной цитатой источника) — перенос в структуру,
не новое чтение.

- `ga2d76207` (Kismet Capital Group, buyer сделки `g9d134cf4`): профиль
  уже описан как «Инвестиционная компания Ивана Таврина» — формализовано
  структурой; доля не названа явно (сколько именно Таврину принадлежит в
  самом Kismet, а не в HeadHunter), поле `share` пусто.
- `g5ef5049d` (АО «Актуальные инвестиции», target сделки `gb5ac2288`):
  Коммерсантъ называет всех четырёх учредителей с точными долями —
  «учредители «Актуальных инвестиций» — кипрские Chevre Investments
  Limited (64,68%) и Nortox Investments Limited (34,12%), а также
  Надежда Анисимова (0,5%) и Лев Кветной (0,7%)».
- `delo` (Группа компаний «Дело», target сделки `g24e6d8ee`): сделка
  Росатом/ТМХ/Шишкарев о консолидации на базе «Дела» НЕ СОСТОЯЛАСЬ
  (расторгнута в ноябре 2025, выкупленный ТМХ 1% вернулся Шишкареву
  25 февраля 2026) — текущая структура ровно та, что была ДО сделки и
  не изменилась ею: «Шишкарев (владел контролирующей долей 51%). Доля
  госкорпорации «Росатом»... на уровне 49%» (РБК/Ведомости). `as_of` —
  дата возврата доли (подтверждающее сделку событие), не дата исходной
  структуры.

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass2.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass2.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'ga2d76207': [{
        'name': 'Иван Таврин',
        'id': None,
        'as_of': '2023-01',
        'source': ['Forbes Russia', 'https://www.forbes.ru/tekhnologii/484184-kismet-tavrina-zaplatila-za-dolu-v-headhunter-147-mln'],
    }],
    'g5ef5049d': [
        {
            'name': 'Chevre Investments Limited',
            'id': None,
            'share': '64,68%',
            'as_of': '2021-10',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/5039601'],
        },
        {
            'name': 'Nortox Investments Limited',
            'id': None,
            'share': '34,12%',
            'as_of': '2021-10',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/5039601'],
        },
        {
            'name': 'Лев Кветной',
            'id': None,
            'share': '0,7%',
            'as_of': '2021-10',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/5039601'],
        },
        {
            'name': 'Надежда Анисимова',
            'id': None,
            'share': '0,5%',
            'as_of': '2021-10',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/5039601'],
        },
    ],
    'delo': [
        {
            'name': 'Сергей Шишкарёв',
            'id': None,
            'share': '51%',
            'as_of': '2026-02',
            'source': ['Ведомости', 'https://www.vedomosti.ru/business/articles/2026/02/26/1179096-shishkarev-vikupil-1-uk-delo-u-transmashholdinga'],
        },
        {
            'name': 'Росатом',
            'id': 'rosatom',
            'share': '49%',
            'as_of': '2026-02',
            'source': ['РБК', 'https://www.rbc.ru/business/25/12/2024/676aff8d9a7947bb1f5e22e9'],
        },
    ],
}


def main(write=False):
    """Идемпотентен, как pass1 — каждый ключ применяется независимо."""
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
