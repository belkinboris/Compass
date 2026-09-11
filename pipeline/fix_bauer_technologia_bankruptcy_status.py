# -*- coding: utf-8 -*-
"""Месячная очередь качества, 11 сентября 2026 — карточка `cd175a614`
(«Продажа земли и недвижимости ООО «Бауэр технология» ИП Руслану
Прудникову», статус уже «Не состоялась» — суд впервые отменил сделку с
иностранными активами, проведённую в обход правкомиссии). Судьба
самого ООО «Бауэр технология» и его актива после отмены сделки была
неизвестна.

Личный WebFetch подтвердил дословно (SPARK-Interfax,
https://spark-interfax.ru/moskva-taganski/ooo-bauer-tekhnologiya-inn-7703617713-ogrn-1067760340823-6567c642cab942bc8e968023938f297c):
руководитель — «Кожихов Игорь Геннадьевич, конкурсный управляющий»
(признак процедуры банкротства); учредитель — «Гаспарян Андраник
Багратович».

Судьба конкретного участка земли/недвижимости, который суд обязал
вернуть в конкурсную массу, — не прослеживается в открытых источниках
(новых торгов или имени покупателя не нашлось); честно фиксируется
только сам факт банкротства.

Запуск:
    python3 pipeline/fix_bauer_technologia_bankruptcy_status.py            # сухой прогон
    python3 pipeline/fix_bauer_technologia_bankruptcy_status.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_ECO_CONTEXT = (
    'ООО «Бауэр технология» находится в процедуре банкротства '
    '(конкурсное производство) — руководителем компании по данным '
    'реестра значится конкурсный управляющий. Судьба конкретного '
    'участка земли и недвижимости, который суд обязал вернуть в '
    'конкурсную массу, в открытых источниках не прослеживается.'
)

NEW_SRC = ['SPARK-Interfax', 'https://spark-interfax.ru/moskva-taganski/ooo-bauer-tekhnologiya-inn-7703617713-ogrn-1067760340823-6567c642cab942bc8e968023938f297c']


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    d = by_id['cd175a614']

    assert d['eco'].get('context') is None, 'eco.context уже занят: %r' % (d['eco'].get('context'),)
    urls = {s[1] for s in d['src']}
    assert NEW_SRC[1] not in urls, 'источник уже добавлен'

    print('cd175a614: eco.context заполнен (банкротство ООО «Бауэр '
          'технология», конкурсное производство); добавлен источник')

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    d['eco']['context'] = NEW_ECO_CONTEXT
    d['src'].append(NEW_SRC)

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
