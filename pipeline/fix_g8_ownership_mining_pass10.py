# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — десятая партия майнинга уже собранного текста
карточек. Три уровня очереди дочитывания снова пусты (12 сентября 2026,
пятый час подряд).

Триггер расширен ещё раз (добавлено «контролируем\\w*» к «принадлежит»/
«владеет» из партии 9). Замер с учётом уже занятых 30 профилей (пассы
1-9) дал 257 уникальных компаний-кандидатов — метод продолжает находить
много нового; отобраны шесть с однозначным направлением (проверено по
`target`/`buyer`/`seller_id` каждой сделки — предложение обязано быть о
СОБСТВЕННОЙ структуре профиля, а не о том, чем он сам владеет или кем
владеет сосед по предложению) и без оговорок.

Отклонены (тот же класс направления, что и раньше): Газпром Тех, ЭР-Телеком
Холдинг, «Вартон», ЛУКОЙЛ, АО «Вектор Рейл», «Кассир.ру», TR Holdings,
«Волга-Флот», СберИнвест, Росимущество, Росатом — во всех предложение
говорит, ЧЕМ владеет ЭТА компания, а не кто владеет ЕЮ; МТС Банк/KD Pay —
источник сам отмечает нестыковку долей в тексте; «Перспектива»/Primo RPA/
«ЦОД СПб» — предложение восстанавливает уже известные условия сделки, а
не новый факт о владении.

- `g16606d0d` (ООО «Юнайтед Индастриал Дистрибушен», buyer сделки
  `g531446fe` — покупатель сельхозтехники CNH Industrial): 99%
  принадлежит Михаилу Мураховскому.
- `g093b0f50` (Nexign, target сделки `gc79e6178`): до выкупа
  «МегаФоном» принадлежала ООО «ЮэСэМ Телеком» (холдинг USM).
- `g3104e805` (ООО «Смарт сервис ЛТД», buyer сделки `g0a0d451a` —
  покупатель российского бизнеса KFC): принадлежит Константину Котову
  и Андрею Осколкову.
- `ge96b97f1` («Апрель», target сделки `g303803bc`): до сделки
  принадлежало Всеволоду Шеховцеву (60,75%) и Сергею Кокареву (39,25%).
- `g4b69137f` (TicketsCloud, target сделки `gc4c76129`): 75,5% у Егора
  Егерева, 24,5% — у британской TicketsCloud Ltd.
- `g40580395` (АО «Аэромар», target сделки `g2c27516d`): после выкупа
  доли Lufthansa принадлежит на 100% «Аэрофлоту».

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass10.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass10.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'g16606d0d': [{
        'name': 'Михаил Мураховский',
        'id': None,
        'share': '99%',
        'as_of': '2023',
        'source': ['Интерфакс', 'https://www.interfax.ru/business/898224'],
    }],
    'g093b0f50': [{
        'name': 'ООО «ЮэСэМ Телеком» (холдинг USM)',
        'id': None,
        'as_of': '2023-01',
        'source': ['РБК', 'https://www.rbc.ru/technology_and_media/13/01/2023/63c17ded9a7947853241d24c'],
    }],
    'g3104e805': [{
        'name': 'Константин Котов и Андрей Осколков',
        'id': None,
        'as_of': '2023',
        'source': ['Интерфакс', 'https://www.interfax.ru/business/874172'],
    }],
    'ge96b97f1': [
        {
            'name': 'Всеволод Шеховцев',
            'id': None,
            'share': '60,75%',
            'as_of': '2023',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/5985458'],
        },
        {
            'name': 'Сергей Кокарев',
            'id': None,
            'share': '39,25%',
            'as_of': '2023',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/5985458'],
        },
    ],
    'g4b69137f': [
        {
            'name': 'Егор Егерев',
            'id': None,
            'share': '75,5%',
            'as_of': '2023',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/5861955'],
        },
        {
            'name': 'TicketsCloud Ltd (Великобритания)',
            'id': None,
            'share': '24,5%',
            'as_of': '2023',
            'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/5861955'],
        },
    ],
    'g40580395': [{
        'name': 'Аэрофлот',
        'id': None,
        'share': '100%',
        'as_of': '2026-09',
        'source': ['Интерфакс', 'https://www.interfax.ru/business/1112456'],
    }],
}


def main(write=False):
    """Идемпотентен, как pass1-9."""
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
