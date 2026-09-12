# -*- coding: utf-8 -*-
"""G8 (PRODUCT_ROADMAP.md) — одиннадцатая партия майнинга уже собранного
текста карточек. Три уровня очереди дочитывания снова пусты (12 сентября
2026, шестой час подряд).

Тот же расширенный триггер (бенефициар/подконтролен/принадлежит/владеет/
контролируем), что и в партиях 9-10 — метод по-прежнему далёк от
исчерпания: с учётом уже занятых 36 профилей (пассы 1-10) замер дал 368
срабатываний / 251 уникальную компанию. Отобраны шесть с однозначным
направлением (проверено по `target`/`buyer`/`seller_id` каждой сделки) и
без оговорок.

Отклонены в этом же заходе (по знакомым причинам): Zebra Toys — владельцы
названы только числом («пятеро сооснователей»), без имён, не годится для
структурированной записи; АО «Новый интеллект» — предложение говорит о
владельце ПРОМЕЖУТОЧНОЙ SPV («Аргентум»), а не о самой компании; ООО
«Баск» — восстанавливает уже известные условия сделки, а не новый факт;
Russ Outdoor — направление предложения неоднозначно (не ясно, кто чья
головная структура); «Технониколь» — крупная известная компания,
предложение говорит о её ПРИОБРЕТАЮЩЕЙ SPV, а не о ней самой.

- `g23a1df20` (АО «УК «Белая скала»», buyer сделки `g323cf076` —
  покупатель складского портфеля Raven Russia на торгах): контролируется
  через ООО «СФО Аврора» фондом «Актив» (учредители Сергей Винокуров и
  Елена Кузнецова).
- `g0b6a8c17` (ФораЛаб, target сделки `g40477661`): с мая 2023 года 90%
  принадлежит основателю «ЛабКвест» Дарье Пикалюк.
- `g95370c0d` (НаПоправку, target сделки `gc09bde7e`): на момент раунда
  100% принадлежало кипрской Napopravky Cyprus Limited.
- `ge438bc54` (ООО «Первый», buyer сделки `g3e3f233c` — покупатель
  бизнес-центра на Арбате): принадлежит семье основателя сети
  «Мария-Ра» Александра Ракшина.
- `gff01c2ae` (Кидбург, target сделки `gbc69f146`): до сделки
  принадлежала кипрской Iolyco Investments (40% которой было у
  финского фонда CapMan II).
- `ge828c124` (Hilding Anders, seller сделки `g39cb44b9`): до продажи
  доли в «Асконе» сам шведский концерн принадлежал инвестфондам KKR & Co.

Запуск:
    python3 pipeline/fix_g8_ownership_mining_pass11.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_mining_pass11.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

NEW_OWNERSHIP = {
    'g23a1df20': [{
        'name': 'Фонд «Актив» (через ООО «СФО Аврора»; учредители — Сергей Винокуров и Елена Кузнецова)',
        'id': None,
        'as_of': '2026',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/8780667'],
    }],
    'g0b6a8c17': [{
        'name': 'Дарья Пикалюк (основатель «ЛабКвест»)',
        'id': None,
        'share': '90%',
        'as_of': '2023-05',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/6029977'],
    }],
    'g95370c0d': [{
        'name': 'Napopravky Cyprus Limited',
        'id': None,
        'share': '100%',
        'as_of': '2020',
        'source': ['РБК', 'https://www.rbc.ru/spb_sz/18/09/2020/5f64b4819a794705892028f8'],
    }],
    'ge438bc54': [{
        'name': 'Семья Александра Ракшина (основателя сети «Мария-Ра»)',
        'id': None,
        'as_of': '2023',
        'source': ['Ведомости', 'https://www.vedomosti.ru/realty/articles/2023/09/26/997089-struktura-rostelekoma-i-sberbanka-prodala-ofisnii-kompleks'],
    }],
    'gff01c2ae': [{
        'name': 'Iolyco Investments (Кипр; 40% которой принадлежало CapMan II)',
        'id': None,
        'as_of': '2023-02',
        'source': ['Ведомости', 'https://www.vedomosti.ru/business/articles/2023/02/14/962821-finskii-investfond-prodal-dolyu-v-seti-kidburg'],
    }],
    'ge828c124': [{
        'name': 'KKR & Co.',
        'id': None,
        'as_of': '2025',
        'source': ['Коммерсантъ', 'https://www.kommersant.ru/doc/7958520'],
    }],
}


def main(write=False):
    """Идемпотентен, как pass1-10."""
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
