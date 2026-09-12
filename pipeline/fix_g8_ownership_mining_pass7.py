# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — седьмая партия майнинга уже собранного текста
карточек. Три уровня очереди дочитывания снова пусты (12 сентября 2026,
второй час подряд).

Тот же уточнённый метод. С учётом уже занятых 21 профиля (пассы 1-6)
замер дал 51 кандидата; отобраны три с однозначным, не оспариваемым
фактом. Отклонены (тот же класс, что и раньше): «ВТБ Капитал»/«АФК
Система» — слово-триггер о структуре, которую эти компании САМИ
контролируют, а не о том, кто владеет ими; «Дельта Холдинг», «Прайм
рост», «Саратов-Птица», «Дедал», СБК Премьер/Fabcell — оговорки («не
раскрывались», «неизвестен», «оспаривает»); Сергей Дашков/Павел Тё/Олег
Сохацкий — профили физлиц, а не компаний (полю `ownership` для персон не
место).

- `gd45e6602` (DP World, buyer сделки `gf1f8c278`, ещё не закрытой на дату
  публикации, но факт о собственной структуре DP World не зависит от
  исхода сделки): консорциум подконтролен правительству ОАЭ.
- `g444cac01` (М.Видео, buyer сделки `gdb2a120f`): общий с продавцом
  (SFI) конечный бенефициар — Саид Гуцериев.
- `g01ee00e7` (Баимская — профиль предмета сделки `g392ccc1e`): до
  продажи KAZ Minerals принадлежала холдингу Aristus Holdings Limited,
  бенефициары — Роман Абрамович и Александр Абрамов.

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass7.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass7.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'gd45e6602': [{
        'name': 'Правительство ОАЭ (Дубай)',
        'id': None,
        'as_of': '2019',
        'source': ['Ведомости', 'https://www.vedomosti.ru/business/articles/2019/10/27/814823-arabskaya-dp-world'],
    }],
    'g444cac01': [{
        'name': 'Саид Гуцериев',
        'id': None,
        'as_of': '2021-10',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/4889357'],
    }],
    'g01ee00e7': [{
        'name': 'Aristus Holdings Limited (бенефициары — Роман Абрамович и Александр Абрамов)',
        'id': None,
        'as_of': '2018-08',
        'source': ['Ведомости', 'https://www.vedomosti.ru/business/articles/2018/08/02/777232-abramovich-abramov'],
    }],
}


def main(write=False):
    """Идемпотентен, как pass1-6."""
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
