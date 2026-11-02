# -*- coding: utf-8 -*-
"""Вычитка базы, партия «k» (2 ноября 2026): то, что таблица FIXES не умеет.
Пара к pipeline/ingest/fixes/reread_2026_11_02_k.py.

Статьи открыты заново и сохранены save_source.py
(data/inbox/triage/sources_2026-11-02.json); история участников ООО — ЕГРЮЛ
через datanewton.ru (адрес — в src карточки, запись FIXES) и ФНС на сайте.

- g5f25f452 (Flysound): по ЕГРЮЛ 8 апреля 2026 года 100% ООО «Флайсаунд»
  получило ООО «Кинопоиск», а вышли пятеро участников: ООО «Лауднесс
  Филмс-Сентру де Пош Продусау Лда» (51%), Андрей Бельчиков (31,85%), Сергей
  Большаков и Светлана Волкова (по 7,35%), Алексей Кобзарь (2,45%). Покупатель —
  формальный, а не профиль группы (docs/card_parties.md: «Flysound купил
  «Кинопоиск», а не «Плюс Студия»»): профиля «Кинопоиска» в базе нет, поэтому
  ссылка на «Яндекс» снимается и покупатель пишется текстом; «Плюс Студия»
  «Яндекса» названа в law.struct. Продавцы — текстом с доказательством
  (prior: fix_sellers_from_registry_2026_10_14.py). Предмет был описанием
  («студия звукового постпродакшена Flysound») — теперь доля с формой и числом;
  имя профиля было с латиницей внутри кириллицы («ООО «ФЛАЙСOUND»») — теперь
  бренд Flysound (legal_short поставит party_legal_names.py --write). Заметка
  консультанта АГП начиналась обрывком «АГП) — …». Право.ру отдает 404 —
  ссылка снята (замена — русская версия пресс-релиза АГП, запись FIXES).
- g113002a7 (Flocktory): доказательство продавца — Интерфакс и ЕГРЮЛ
  (АО «КИВИ», 100% до 16 апреля 2026 года).
- g01054f2a (хладокомбинат): доказательство продавца — ЕГРЮЛ (ни одна
  статья продавца не называет); описание профиля продавца было заглушкой.

    python3 pipeline/archive/2026-11/fix_reread_2026_11_02_k.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DN_FLY = 'https://datanewton.ru/contragents/1187746718697/history/timeline'
DN_ICE = 'https://datanewton.ru/contragents/1151215002432/history/timeline'
INTERFAX = 'https://interfax.com/newsroom/top-stories/117223/'
PRAVO = ['Право.ру', 'https://pravo.ru/company_news/263249/?erid=2VfnxwG23f8']


def set_val(obj, key, old, new):
    assert obj.get(key) == old, (key, obj.get(key), old)
    obj[key] = new


def main(argv):
    raw = open(BASE, encoding='utf-8').read()
    data = json.loads(raw)
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']

    # g5f25f452 — Flysound
    c = deals['g5f25f452']
    set_val(c, 'buyer', 'yandex', None)
    assert not c.get('buyer_name'), c.get('buyer_name')
    c.pop('buyer', None)
    c['buyer_name'] = 'ООО «Кинопоиск»'
    sellers = ('ООО «Лауднесс Филмс-Сентру де Пош Продусау Лда», Андрей Бельчиков, Сергей Большаков, '
               'Светлана Волкова и Алексей Кобзарь')
    assert not c.get('seller') and not c.get('seller_id'), (c.get('seller'), c.get('seller_id'))
    c['seller'] = sellers
    ev = c.setdefault('party_evidence', {})
    ev['buyer'] = [{'value': 'ООО «Кинопоиск»', 'method': 'registry_owner_history', 'url': DN_FLY}]
    ev['seller'] = [{'value': sellers, 'method': 'registry_owner_history', 'url': DN_FLY}]
    np = c.setdefault('accepted_notes', {}).setdefault('no_profile', {})
    np['buyer'] = ('ООО «Кинопоиск» (ОГРН 1077759854919) — формальный покупатель по ЕГРЮЛ (datanewton, '
                   '08.04.2026); профиля в базе нет, сделку объявляла «Плюс Студия» «Яндекса» — это в law.struct.')
    np['seller'] = ('пятеро прежних участников ООО «Флайсаунд» по истории участников ЕГРЮЛ (datanewton, '
                    '08.04.2026): четыре физлица и '
                    'ООО «Лауднесс Филмс-Сентру де Пош Продусау Лда» (51%); профилей у них нет.')
    set_val(c, 'asset', 'студия звукового постпродакшена Flysound', '100% доли в ООО «Флайсаунд»')
    adv = c['law']['adv']
    assert adv[0][1] == 'Адвокатское бюро «Андрей Городисский и Партнеры»' and adv[0][2].startswith('АГП) — '), adv
    adv[0][2] = ('Консультант «Яндекса»: проверка Flysound, документы сделки, переговоры и закрытие; '
                 'команду возглавлял партнер Алексей Городисский')
    assert PRAVO in c['src'], c['src']
    c['src'] = [s for s in c['src'] if s != PRAVO]
    p = comps['g6212c4a5']
    set_val(p, 'name', 'ООО «ФЛАЙСOUND» (Flysound)', 'Flysound')
    set_val(p, 'desc',
            'Студия звукового постпродакшена полного цикла (с 2011 года, среди работ — «Майор Гром», «Притяжение»); '
            'в 2026 году ее купила «Плюс Студия» («Яндекс»).',
            'Студия звукового постпродакшена полного цикла (с 2011 года, среди работ — «Майор Гром», «Притяжение»); '
            'в 2026 году перешла к «Яндексу».')

    # g113002a7 — Flocktory
    c = deals['g113002a7']
    # описание профиля шло в пост первой фразой и пересказывало сделку
    # (находка приемки post), а не говорило, кто это
    set_val(comps['g113002a7-target'], 'desc',
            'Платформа маркетинговой автоматизации; исторически входила в российский периметр Qiwi, '
            'в 2026 году ее купил Альфа-Банк.',
            'Платформа лидогенерации и маркетинговой автоматизации на больших данных. Система Flocktory 2.0 '
            'внесена в российский реестр ПО.')
    assert c.get('seller_id') == 'gd5d02d09', c.get('seller_id')
    c.setdefault('party_evidence', {})['seller'] = [
        {'value': 'АО «Qiwi»', 'method': 'manual_source_review', 'url': INTERFAX}]

    # g01054f2a — хладокомбинат
    c = deals['g01054f2a']
    assert c.get('seller') == 'Николай Александрович Одинцов' and c.get('seller_id') == 'ga4383970'
    c.setdefault('party_evidence', {})['seller'] = [
        {'value': 'Николай Александрович Одинцов', 'method': 'registry_owner_history', 'url': DN_ICE}]
    set_val(comps['ga4383970'], 'desc', 'Описание компании пока не добавлено.',
            'Николай Одинцов с 2019 года до апреля 2026 года был единственным владельцем '
            'ООО «Йошкар-Олинский хладокомбинат» (по ЕГРЮЛ).')

    print('g5f25f452: покупатель → ООО «Кинопоиск» (текстом, ссылка на «Яндекс» снята), продавцы по ЕГРЮЛ, '
          'предмет, профиль Flysound (имя, desc), заметка АГП, Право.ру (404) снят')
    print('g113002a7: доказательство продавца')
    print('g01054f2a: доказательство продавца, описание профиля продавца')
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    assert open(BASE, encoding='utf-8').read() == raw, 'база изменилась во время прогона — перезапустите'
    out = json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else '')
    open(BASE, 'w', encoding='utf-8').write(out)
    print('записано')


if __name__ == '__main__':
    main(sys.argv[1:])
