# -*- coding: utf-8 -*-
"""Аудит адреса фактов (13 сентября 2026) — 6 находок ROLE_WRONG/CONTRADICTION,
не прошедшие обычный конвейер `review.py` FIXES (пять партий) по двум
самостоятельным причинам:

  * ВНУТРЕННЯЯ АРИФМЕТИКА/СОГЛАСОВАННОСТЬ КАРТОЧКИ С СОБОЙ (g1125c0ec,
    g572a4aca, g3cac5f0f, g81a766ac) — «цитата» у этих находок не внешний
    источник, а сама же карточка: правильное значение уже стоит РЯДОМ, в
    другом поле или другом предложении того же поля, и правка — это
    приведение поля к тому, что карточка САМА о себе уже говорит, а не
    перенос новой цитаты. `review.py`'s дословность требует, чтобы `new`
    буквально лежал в `quote`, а здесь `new` — арифметический вывод
    (3,5/2,5=1,4x; 25% от 1,4 млрд ≈ 350 млн, не 355 млрд) или подстановка
    из соседнего поля, а не подстрока.
  * ПРЕДМЕТ-ЛОТ И ПРЕДМЕТ-ИМЯ В КОСВЕННОМ ПАДЕЖЕ (g3bb1fadb, ksk) — поле
    `asset` не входит в список полей с падежным послаблением
    (`name_is_supported` даёт его только seller/buyer_name), и лот из
    нескольких активов также не ложится подстрокой ни в какую отдельную
    цитату. Профильная ссылка на ЧУЖУЮ сторону (Газпром/Cargill) для этих
    двух карточек уже снята партией `fix_role_wrong_contradiction_audit_
    batch1.py` (field=target, new=None) — здесь только текст `asset`.

Каждая правка — `assert` на предыдущее значение поля перед записью: если
поле уже не то, что ожидалось (карточку тронул кто-то другой), скрипт
падает, а не переписывает вслепую.

Запуск:
    python3 pipeline/fix_role_wrong_contradiction_internal_consistency.py            # сухой прогон
    python3 pipeline/fix_role_wrong_contradiction_internal_consistency.py --write
"""
import json
import sys

PATH = 'static/data/deals_promoted.json'


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    changes = []

    d = deals['g1125c0ec']
    old = 'Мультипликатор EV/выручка — около 1,4x: цена 3,5 млрд ₽ плюс условное вознаграждение до 500 млн ₽ против выручки 2,5 млрд ₽ за 2024 год (цена подтверждена отчётностью «Ростелекома»).'
    assert d.get('eco', {}).get('val') == old, 'g1125c0ec/eco.val уже другое: %r' % d.get('eco', {}).get('val')
    new = ('EV/выручка ≈ 1,4x без учёта условного вознаграждения; до 1,6x при включении '
           'максимальных 500 млн ₽ (цена подтверждена отчётностью «Ростелекома»). '
           'Расчёт: 3,5 млрд ₽ / 2,5 млрд ₽ = 1,4x; (3,5 + 0,5) млрд ₽ / 2,5 млрд ₽ = 1,6x.')
    changes.append((d, ('eco', 'val'), old, new))

    d = deals['g572a4aca']
    old = ('Финансовые показатели 2022 года: выручка — 1,4 млрд ₽; EBITDA — 355 млрд ₽; '
           'рентабельность по EBITDA — 25%. Результаты за 9 месяцев 2023 года: выручка — '
           '1,16 млрд ₽; операционная прибыль — 8,24 млн ₽; EBITDA — 406 млн ₽ (рентабельность '
           'по EBITDA — 35%); чистая прибыль — 55,8 млн ₽; чистый долг — 1,9 млрд ₽.')
    assert d.get('eco', {}).get('target_fin') == old, 'g572a4aca/eco.target_fin уже другое'
    new = old.replace('EBITDA — 355 млрд ₽', 'EBITDA — 355 млн ₽')
    assert new != old
    changes.append((d, ('eco', 'target_fin'), old, new))

    d = deals['g3cac5f0f']
    old = ("Гуламгусейн Иманов владеет по 70% в торговых ООО «Абсолют» и ООО «Бизнес Контроль», "
           "51% в ООО «Здоровье нации» (косметология) и 70% в ООО «Смарт Дистрибьюшен», которое "
           "продаёт и производит бытовую технику Jackie's. Выручка последнего в 2023 году "
           "составила 339,3 млн ₽, чистая прибыль — 1,9 млн ₽. К августу 2026 года оба "
           "совладельца, участвовавшие в сделке 2024 года, вышли из капитала: по данным ЕГРЮЛ, "
           "единственным владельцем ООО «Шмит Компани» стал Игорь Михайлович Росляков — его "
           "доля выросла с 50% до 100%, а доля Гуламгусейна Мехди Оглы Иманова снизилась с 50% "
           "до 0%.")
    assert d.get('eco', {}).get('context') == old, 'g3cac5f0f/eco.context уже другое'
    new = old.replace('снизилась с 50% до 0%', 'снизилась с 30% до 0%')
    assert new != old
    changes.append((d, ('eco', 'context'), old, new))

    d = deals['g81a766ac']
    old = 'Русагро увеличило долю в ГК «Агро-Белогорье» с 22,5% до 47,5% по решению суда'
    assert d.get('title') == old, 'g81a766ac/title уже другое: %r' % d.get('title')
    new = 'Русагро увеличило долю в ГК «Агро-Белогорье» с 22,5% до 100%'
    changes.append((d, ('title',), old, new))

    d = deals['g3bb1fadb']
    assert d.get('asset') is None, 'g3bb1fadb/asset уже не пусто: %r' % d.get('asset')
    new = ('лот: 50% «Севернефтегазпрома»; по 0,01% «Газпром ЮРГМ Трейдинг» и «Газпром ЮРГМ '
           'Девелопмент»; 25% ООО «Ачим Девелопмент»')
    changes.append((d, ('asset',), None, new))

    d = deals['ksk']
    assert d.get('asset') is None, 'ksk/asset уже не пусто: %r' % d.get('asset')
    new = 'зерновой терминал КСК в Новороссийске'
    changes.append((d, ('asset',), None, new))

    print('ПРАВКИ (%d):' % len(changes))
    for card, path, old, new in changes:
        print('  %s %s' % (card['id'], '.'.join(path)))
        print('    было: %r' % (old,))
        print('    стало: %r' % (new,))
        if write:
            obj = card
            for p in path[:-1]:
                obj = obj.setdefault(p, {})
            obj[path[-1]] = new

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в', PATH)
    else:
        print('\nСУХОЙ ПРОГОН — для записи добавьте --write')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
