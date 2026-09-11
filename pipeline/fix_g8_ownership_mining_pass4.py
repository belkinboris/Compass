# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — четвёртая партия майнинга уже собранного текста
карточек. Три уровня очереди дочитывания пусты шестой час подряд.

Замер тем же уточнённым методом (пасс3): слово-триггер и имя профиля стороны
сделки — в одном предложении. С учётом уже занятых профилей (пассы 1-3)
замер дал 65 кандидатов. Из них отобраны пять с однозначным, не оспариваемым
фактом и точным источником; отклонены кандидаты, где: (а) слово-триггер
относится к ДРУГОЙ стороне того же предложения, а не к проверяемому профилю
(например, «Т2 Мобайл, подконтрольное...» — на деле фраза о том, что Т2
Мобайл САМ контролирует другую компанию, а не наоборот); (б) есть явная
оговорка («не установлен», «неизвестны», «оспариваемая», «не раскрываются»).

- `gd05f527f` (СМП-банк, target сделки `g2bb8cf3a`): подконтролен Аркадию и
  Борису Ротенбергам до продажи ПСБ (Forbes.ru, «ПСБ подтвердил покупку
  СМП-банка у Ротенбергов»).
- `g18853272` (ГК «Рота», buyer сделки `g92f41a2d`): бенефициар — депутат
  Госдумы Дмитрий Саблин (уже назван в `desc` профиля — перенос в
  структуру).
- `g1fb5eea7` (ЗАО «Вива Армения», buyer сделки `gf6be51a1`): контролируется
  кипрской Fedilco Group Limited, конечные бенефициары — Чже Джанг и
  Константин Соколов (собственный текст карточки, `extra`; регуляторное
  согласие на сделку получено 2 июля 2024 года — `as_of` привязан к этой
  дате).
- `g0a130abd` (Экспобанк, buyer сделки `ga5b07998`): бенефициар — Игорь Ким,
  включён в санкционный список Великобритании как контролирующее лицо банка
  24 февраля 2025 года.
- `g9b05a98a` (Трансхим, target сделки `gefb52584`): ДО передачи Александру
  Удодову (август 2024) бенефициаром через ООО «Дезимпэкс» выступал продюсер
  Александр Достман (уже назван в `desc` профиля — перенос в структуру).

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass4.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass4.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'gd05f527f': [{
        'name': 'Аркадий и Борис Ротенберги',
        'id': None,
        'as_of': '2022-12',
        'source': ['Forbes.ru', 'https://www.forbes.ru/finansy/483388-psb-podtverdil-pokupku-smp-banka-u-rotenbergov'],
    }],
    'g18853272': [{
        'name': 'Дмитрий Саблин',
        'id': None,
        'as_of': '2022-12',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/5796344'],
    }],
    'g1fb5eea7': [{
        'name': 'Fedilco Group Limited (Кипр; бенефициары — Чже Джанг и Константин Соколов)',
        'id': None,
        'as_of': '2024-07',
        'source': ['ComNews', 'https://www.comnews.ru/content/246269/2026-07-08/2026-w28/1009/rostelekom-posle-10-let-peregovorov-izbavilsya-edinstvennogo-zarubezhnogo-aktiva'],
    }],
    'g0a130abd': [{
        'name': 'Игорь Ким',
        'id': None,
        'as_of': '2025-02',
        'source': ['vc.ru', 'https://vc.ru/money/2108288-sanktsii-es-protiv-rossijskih-bankov'],
    }],
    'g9b05a98a': [{
        'name': 'Александр Достман (через ООО «Дезимпэкс», до передачи Удодову)',
        'id': None,
        'as_of': '2024',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/7196213'],
    }],
}


def main(write=False):
    """Идемпотентен, как pass1-3."""
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
