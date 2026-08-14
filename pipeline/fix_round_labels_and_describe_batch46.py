# -*- coding: utf-8 -*-
"""Сорок шестая партия: систематический промер «раунд/описание вместо
имени компании» (родня находки из партии 45) + 10 описаний.

НАЙДЕНО. После партии 45 (Series C -> inDriver, Раунд Series A -> EBAC
Online) промерил класс целиком: искал профили, чьё ИМЯ ЦЕЛИКОМ совпадает
с названием стадии раунда или общим описанием («Series X», «Раунд X»,
«Посевный», «Pre-seed», «Онлайн-<слово>», IPO/SPO). Нашлось ЕЩЁ ТРИ:

  - `g260b4f63` «Посевный» — предмет посевного раунда Muver (приложение
    для таксистов). Переименован в «Muver».
  - `gdca01a07` «Онлайн-школа» — общее описание без бренда; предмет —
    Allright.io (онлайн-школа английского). Переименован в «Allright.io».
  - `g4ef4610e` «Раунд A» — предмет раунда A: Welldone (растительное
    мясо). Переименован в «Welldone».
  - `g5dcbd18b` «Pre-seed» — тот же класс, но профиль уже ОСИРОТЕЛ: обе
    сделки, для которых он когда-то стоял `target`, давно переведены на
    верные профили KEK Entertainment/StudyFree (партия 30, см. журнал),
    и ни одна сделка на него больше не ссылается. Профиль и его запись
    в `match_keys` удалены — держать заглушку без единой ссылки нет
    смысла.

Как и в партии 45, это не смена личности профиля, а исправление
опечатки/недоразбора парсера: под старым именем профиль не представлял
никакой реальной сущности, только ярлык этапа финансирования.

Плюс 10 описаний обычным G2-кандидатам (включая три переименованных).

Запуск:
    python3 pipeline/fix_round_labels_and_describe_batch46.py            # сухой прогон
    python3 pipeline/fix_round_labels_and_describe_batch46.py --write    # записать
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'
PLACEHOLDER = re.compile(r'^\s*(описание компании пока не добавлено'
                          r'|профиль сформирован по итогам чтения)', re.I)

RENAMES = {
    'g260b4f63': ('Посевный', 'Muver'),
    'gdca01a07': ('Онлайн-школа', 'Allright.io'),
    'g4ef4610e': ('Раунд A', 'Welldone'),
}
NEW_ALIASES = {
    'g260b4f63': ['muver'],
    'gdca01a07': ['allright.io', 'allright'],
    'g4ef4610e': ['welldone'],
}

ORPHAN_ID = 'g5dcbd18b'
ORPHAN_NAME = 'Pre-seed'

DESCRIPTIONS = {
    'g260b4f63': 'Приложение для заказа поездок для таксистов; в 2021 '
                 'году привлекло $1,2 млн на посевной стадии при '
                 'оценке $8 млн.',
    'gdca01a07': 'Онлайн-школа английского языка; в 2019 году привлекла '
                 '$1,5 млн от Buran Venture Capital.',
    'g4ef4610e': 'Производитель растительного мяса; в 2021 году '
                 'привлёк $1,5 млн в раунде A от Phystech Ventures и '
                 'Lever VC.',
    'g9750f529': 'Производитель промышленной робототехники; в 2026 '
                 'году привлёк 200 млн ₽ в раунде A при оценке 800 '
                 'млн ₽.',
    'gc6965a4f': 'Американский владелец польских и французских '
                 'активов по упаковке; в 2026 году российские активы '
                 'переданы во временное управление указом президента.',
    'g1fc696f8': 'Девелопер торговых центров («Сибирский городок», '
                 '«Июнь»); в 2021 году 19 ТЦ перешли под контроль '
                 '«Сбербанк Капитала» в счёт долгов.',
    'gbdcc4780': 'Материнская компания сервиса микрозаймов CarMoney; в '
                 '2023 году привлекла 225–229 млн ₽ через закрытую '
                 'подписку на платформе Rounds.',
    'ge28b8234': 'Ростовский производственный комплекс (птичники, '
                 'инкубаторы) обанкротившегося холдинга «Евродон»; '
                 'выставлен на торги в 2024 году за 835,7 млн ₽.',
    'g58575e9c': 'Компания Игоря Шилова; в 2023 году купила российский '
                 'бизнес Essity (бренды Zewa, Libresse, Libero) — три '
                 'завода и около 1300 сотрудников.',
    'g1c2d0229': 'Структура Александра Говора (владельца сети «Вкусно '
                 '— и точка»); в 2025 году купила у ВТБ отель Courtyard '
                 'by Marriott Kazan Kremlin.',
}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    comps = data['companies']
    mk = data['match_keys']

    # --- переименования ---
    for cid, (old, new) in RENAMES.items():
        assert comps[cid]['name'] == old, 'профиль %s уже переименован' % cid
        existing_names = {c.get('name') for c in comps.values()}
        assert new not in existing_names, 'имя %r уже занято' % new
        print('ПЕРЕИМЕНОВАНИЕ  %-12s %r -> %r' % (cid, old, new))
        if write:
            comps[cid]['name'] = new
            mk[cid] = NEW_ALIASES[cid]

    # --- удаление осиротевшего профиля ---
    assert comps[ORPHAN_ID]['name'] == ORPHAN_NAME, 'профиль Pre-seed уже другой'
    refs = [d['id'] for d in data['deals']
            if d.get('buyer') == ORPHAN_ID or d.get('target') == ORPHAN_ID
            or d.get('seller_id') == ORPHAN_ID]
    assert not refs, 'на Pre-seed всё ещё есть ссылки: %s' % refs
    print('УДАЛЕНИЕ  %-12s %r (0 ссылок сделок)' % (ORPHAN_ID, ORPHAN_NAME))
    if write:
        del comps[ORPHAN_ID]
        mk.pop(ORPHAN_ID, None)

    # --- описания ---
    wrote, skipped = 0, []
    for cid, text in DESCRIPTIONS.items():
        c = comps.get(cid)
        assert c, 'профиля %s нет в базе' % cid
        assert 15 <= len(text) <= 220, 'описание %s вне 1–2 строк: %d' % (cid, len(text))
        old = str(c.get('desc') or '')
        if old.strip() == text:
            continue
        if old and not PLACEHOLDER.match(old):
            skipped.append((cid, c.get('name'), old[:60]))
            continue
        print('  ОПИСАНИЕ %-12s %-40s %s' % (cid, str(c.get('name'))[:40], text[:50]))
        if write:
            c['desc'] = text
        wrote += 1

    print('\nОписаний записано: %d' % wrote)
    if skipped:
        print('Пропущено (уже есть своё описание): %d' % len(skipped))
        for cid, name, old in skipped[:5]:
            print('   %s %s — %r' % (cid, name, old))

    real = sum(1 for v in comps.values()
               if (v.get('desc') or '').strip() and not PLACEHOLDER.match(str(v.get('desc'))))
    print('Всего профилей с описанием: %d из %d (%d%%)'
          % (real, len(comps), round(100 * real / len(comps))))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
