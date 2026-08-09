# -*- coding: utf-8 -*-
"""Разовая правка: предмет сделки (`asset`) — в именительном падеже.

ЧТО ЧИНИТ. `guess_parties()` в draft.py вырезал предмет подстрокой из
заголовка, в том падеже, который требует управление глагола: «купил X» —
винительный, «присоединение X» — родительный, «долю в X» — предложный.
Владелец увидел это в живых постах канала 9 августа — «Предмет:
Дальневосточного банка» вместо «Дальневосточный банк». Разбор извлекал
предмет ровно так с самого начала притока, поэтому дефект — не в новых
карточках, а во всей истории: правка нормализует `asset` во ВСЕЙ базе и в
`pending.json`, а `pipeline/ingest/casing.py` (то же правило) подключён в
draft.py, чтобы дефект не появлялся у новых карточек.

ПОЧЕМУ БЕЗОПАСНО ПРАВИТЬ ОПТОМ, А НЕ ТАБЛИЦЕЙ ВРУЧНУЮ. Правило `casing.py`
нарочно консервативное (см. его docstring: не трогает то, что после «%»/
числа, что в кавычках, что после головы словосочетания, слова с заглавной
буквы, неоднозначные словоформы вроде «права»). Замер на всей базе (183
карточки с `asset`) дал 19 срабатываний, каждое проверено вручную — список
ниже, с исходным и новым значением, чтобы правку можно было свести к обычной
таблице.

Запуск:
    python3 pipeline/fix_asset_case.py            # сухой прогон
    python3 pipeline/fix_asset_case.py --write     # записать
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, 'ingest'))

from casing import to_nominative_asset             # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

# Замер 9 августа 2026 — старое значение => новое, сверено вручную.
# Проверяется на себе: main() падает, если реальный расчёт casing.py
# разойдётся с этим списком (значит, правило изменилось и таблицу пора
# пересмотреть, а не переписывать эту проверку).
EXPECTED = {
    'g1d36d186': ('лесозаготовительную компанию ПармаВуд', 'лесозаготовительная компания ПармаВуд'),
    'g015e2da2': ('долю в сети клиник Александрия в Нижнем Новгороде', 'доля в сети клиник Александрия в Нижнем Новгороде'),
    'gb9c96965': ('российского бизнеса Jungheinrich AG', 'российский бизнес Jungheinrich AG'),
    'gfd5e2810': ('интернет-провайдера Rnet', 'интернет-провайдер Rnet'),
    'gedfd4c1e': ('платформу персонализированных добавок Bioniq', 'платформа персонализированных добавок Bioniq'),
    'g645d45ba': ('петербургского хостинг-провайдера Infobox', 'петербургский хостинг-провайдер Infobox'),
    'g4ea618a8': ('долю 8', 'доля 8'),
    'g39752167': ('российских активов Kinross Gold', 'российские активы Kinross Gold'),
    'gc5951fac': ('разработчика системы для управления автомобильными грузоперевозками CARGO.RUN',
                  'разработчик системы для управления автомобильными грузоперевозками CARGO.RUN'),
    'g21795ec9': ('долю в компании-владельце разработчика «АльтерОфис»', 'доля в компании-владельце разработчика «АльтерОфис»'),
    'g0431fc51': ('обанкротившегося производителя телевизоров «Квант»', 'обанкротившийся производитель телевизоров «Квант»'),
    'g9254527a': ('усадьбу в Екатеринбурге', 'усадьба в Екатеринбурге'),
    'g8827d795': ('старинную усадьбу в Москве', 'старинная усадьба в Москве'),
    'ge482f106': ('московского фармритейлера «Диалог»', 'московский фармритейлер «Диалог»'),
    'g692dcc6b': ('производителе картошки для чипсов Lay’s', 'производитель картошки для чипсов Lay’s'),
    'g998e5eb5': ('Дальневосточного банка', 'Дальневосточный банк'),
    'g8f7479bd': ('производственную базу', 'производственная база'),
    'g699f00f5': ('баню авторитетов-экстремистов', 'баня авторитетов-экстремистов'),
    'gdfa13cf0': ('площадку с БЦ на улице Наметкина в Москве', 'площадка с БЦ на улице Наметкина в Москве'),
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    pending = json.load(open(PENDING, encoding='utf-8')) if os.path.exists(PENDING) else {'cards': []}
    cards = {d['id']: d for d in data['deals']}
    cards.update({c['id']: c for c in pending['cards']})

    applied, mismatched, missing = [], [], []
    for cid, (old, new) in EXPECTED.items():
        card = cards.get(cid)
        if not card:
            missing.append(cid)
            continue
        current = card.get('asset')
        if current != old:
            mismatched.append((cid, current, old))
            continue
        computed, changed = to_nominative_asset(current)
        if not changed or computed != new:
            mismatched.append((cid, computed, new))
            continue
        applied.append((cid, old, new))

    for cid in missing:
        print('  ПРОПУСК   %s: карточки нет ни в базе, ни в предпросмотре' % cid)
    for cid, got, expected in mismatched:
        print('  ОТКАЗ     %s: сейчас %r, таблица ждала %r — casing.py разошёлся '
              'с замером, таблицу надо пересчитать заново' % (cid, got, expected))
    for cid, old, new in applied:
        print('  ПРАВИМ    %s %r -> %r' % (cid, old, new))

    print('\nприменимо %d, пропущено %d, расхождений %d'
          % (len(applied), len(missing), len(mismatched)))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 1 if mismatched else 0
    if mismatched:
        print('Есть расхождения — не пишем НИЧЕГО.')
        return 1

    for cid, old, new in applied:
        assert cards[cid]['asset'] == old, 'состояние поля изменилось'
        cards[cid]['asset'] = new

    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    if pending['cards']:
        json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('ЗАПИСАНО: %d карточек.' % len(applied))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
