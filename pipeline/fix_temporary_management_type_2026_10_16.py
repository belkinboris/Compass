# -*- coding: utf-8 -*-
"""Тип сделки «Временное управление»: перевод карточек и общий пост указа № 738.

ЧТО ЧИНИТ. Решение владельца 16 октября 2026: передача активов во временное
управление по указу президента — не M&A и не национализация. Собственник не
меняется, государство передаёт только управление. Раньше такие карточки
стояли типом «M&A» (у трёх — с пометкой `kind: custody`, у Fortum — даже
«Финансирование · структурная сделка»), и в части из них управляющий был
записан покупателем, а владелец — продавцом.

ЧТО ДЕЛАЕТ.
1. Базу (`static/data/deals_promoted.json`): 13 карточек о временном
   управлении получают тип «Временное управление» и `kind: custody`; поля
   buyer/buyer_name/seller/seller_id очищаются (снятые текстовые имена — в
   `retracted`, чтобы обогащение не вернуло их), `no_parties` — одной
   формулировкой, как у CanPack. Управляющий и собственник уже названы в
   прозе каждой карточки — проверено чтением; у Akzo Nobel управляющий был
   только в заголовке, поэтому в начало `law.struct` дописано предложение
   (отпечаток прежнего текста записи FIXES — в `proofread_absorbed`).
   Не тронуты: «Рольф» (g69a22dab) — продажа Росимуществом после обращения
   акций в доход государства по суду, собственность перешла, это M&A;
   c51777ade — кадровое назначение в «Данон Россия», не передача активов.
2. Очередь модерации (`static/data/pending.json`): пять карточек указа
   № 738 от 15 октября 2026 (Tarkett, «Каппа Рус», «Менсен Пакаджинг СНГ»,
   «Онтэкс РУ», «Эвиосис Пэкэджинг Кубань») — тот же перевод, «Центр
   Капитал» убран из покупателей и назван в `law.struct`. Владелец решил:
   пять карточек на сайт, в канал — ОДИН общий пост. Четыре карточки —
   `no_post` (на сайт без поста, как кнопка «без поста»); у Tarkett —
   `post_override` (текст общего поста) и `post_covers` (пять id): пост
   уходит под её id, ждёт, пока на сайте будут все пять, и не переписывается
   правками одной карточки (`send_telegram.py`, `format_post.is_joint_post`).
   Tarkett — потому что её прежний проект поста владелец уже решил кнопкой
   (кнопки под ним сняты), и нажатие под старым одиночным проектом не может
   случайно отменить общий пост. Показ общего поста в консоли —
   `pipeline/send_joint_post_2026_10_16.py`, после того как pending.json
   доехал до сайта.

Запуск:
    python3 pipeline/fix_temporary_management_type_2026_10_16.py            # сухой прогон
    python3 pipeline/fix_temporary_management_type_2026_10_16.py --write    # записать
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import review  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

NEW_TYPE = 'Временное управление'
NO_PARTIES = 'Временное управление по указу, собственность не переходила — покупателя и продавца нет.'
PARTY_FIELDS = ('buyer', 'buyer_name', 'seller', 'seller_id')
SITE = 'https://projectcompass.ru'

# id -> тип, который должен стоять сейчас (assert на старое значение).
BASE_CARDS = {
    'g9c4b80a7': 'M&A',            # CanPack, указ № 1012, «Стальэлемент»
    'c975894bf': 'M&A',            # Ariston и BSH, «Газпром бытовые системы»
    'cbb730efc': 'M&A',            # Ульяновский станкозавод DMG MORI, Росимущество
    'c870f1e2a': 'M&A',            # Silgan, Росимущество
    'c374fc2ca': 'M&A',            # Danone и «Балтика», указ № 520, Росимущество
    'cdcf1a650': 'M&A',            # «Прайм Принт» Amedia, Росимущество
    'c7fd83d05': 'M&A',            # Danone Россия, Росимущество
    'ga142d8e0': 'M&A',            # Metro, «УК Торг РУС»
    'g64462179': 'M&A',            # Nestlé, «Л.Е.В. Менеджмент»
    'g2daf32fe': 'M&A',            # «Ашан», «Л.Е.В. Менеджмент»
    'g7fc9f764': 'Финансирование · структурная сделка',  # Fortum, указ № 302, Росимущество
    'gmru-razvitie-stroy-aktivov-akzo': 'M&A',  # Akzo Nobel, «Развитие строительных активов»
    'c2c719a9a': 'M&A',            # ЛОМО, указ № 139, «Калашников»
}

AKZO = 'gmru-razvitie-stroy-aktivov-akzo'
AKZO_LEAD = ('Указом президента локальные активы Akzo Nobel переданы во временное управление '
             'АО «Развитие строительных активов»; собственником остаётся Akzo Nobel. ')
AKZO_OLD_START = 'АО «Развитие строительных активов» зарегистрировано незадолго до того'

MANAGER = 'Временным управляющим назначено ООО «УК „Центр Капитал“»'
PENDING_CARDS = {
    'g8a599c40': MANAGER + '; право собственности к нему не переходит.',
    'g19410fc2': MANAGER + '; собственником остаётся шведская Sverige International Holdings AB, '
                           'право собственности к управляющему не переходит.',
    'gb3837d4d': MANAGER + '; собственником остаётся немецкая Menshen Beteiligungs-GmbH, '
                           'право собственности к управляющему не переходит.',
    'gfc3e1ae2': MANAGER + '; собственником остаётся бельгийская Ontex, право собственности '
                           'к управляющему не переходит.',
    'gf803c055': MANAGER + '; собственником остаётся группа Eviosys, с 2024 года принадлежащая '
                           'американской Sonoco Products Company, право собственности к управляющему '
                           'не переходит.',
}
LEAD = 'g8a599c40'
COVERS = list(PENDING_CARDS)


def link(cid, name):
    return '<a href="%s/#/deal/%s">%s</a>' % (SITE, cid, name)


JOINT_POST = '\n'.join([
    '<b>Пять иностранных компаний переданы во временное управление «Центр Капиталу»</b>',
    '',
    'Указом президента № 738 от 15 октября 2026 года российские активы пяти иностранных '
    'компаний переданы во временное управление ООО «УК „Центр Капитал“». Собственники не '
    'меняются: управляющая компания на время получает полномочия владельца, но не саму '
    'собственность. Пресс-секретарь президента Дмитрий Песков связал решение не со сменой '
    'собственника, а с тем, что компании — из стран, которые Москва считает недружественными.',
    '',
    '<b>Временный управляющий:</b> ООО «УК „Центр Капитал“»',
    '<b>Компании и их собственники:</b>',
    '• %s — напольные покрытия (АО «Таркетт», АО «Таркетт Рус», ООО «Таркетт Соммер»); '
    'собственник — французская Tarkett' % link('g8a599c40', 'Tarkett'),
    '• %s — упаковка; собственник — шведская Sverige International Holdings AB'
    % link('g19410fc2', '«Каппа Рус»'),
    '• %s — пластиковая упаковка; собственник — немецкая Menshen Beteiligungs-GmbH'
    % link('gb3837d4d', '«Менсен Пакаджинг СНГ»'),
    '• %s — подгузники и бренд Helen Harper; собственник — бельгийская Ontex'
    % link('gfc3e1ae2', '«Онтэкс РУ»'),
    '• %s — металлическая тара; собственник — группа Eviosys американской Sonoco'
    % link('gf803c055', '«Эвиосис Пэкэджинг Кубань»'),
    '<b>Статус:</b> указ подписан 15 октября 2026 года',
    '',
    '<b>Источники:</b> <a href="https://www.vedomosti.ru/business/news/2026/10/16/1237536-aktivi-tarkett">'
    'Ведомости</a>, <a href="https://ura.news/news/1053136498">URA.RU</a>',
    'Подробности о каждой компании — в карточках по ссылкам выше',
    '',
    '#промышленность #упаковка #потребрынок #временное_управление',
])


def absorb(card, field, old_value):
    """Запись FIXES, чей `new` совпадал с прежним текстом поля, остаётся
    применённой: её отпечаток — в `proofread_absorbed` (docs/card_editing.md)."""
    fps = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
    for fix in review.load_fixes():
        if fix.get('id') == card['id'] and fix.get('field') == field:
            if fix.get('new') == old_value or review.fix_fingerprint(fix.get('new')) in fps:
                fp = review.fix_fingerprint(fix['new'])
                if fp not in fps:
                    fps.append(fp)


def convert(card, expected_type, log):
    assert card.get('type') == expected_type, (card['id'], card.get('type'))
    card['type'] = NEW_TYPE
    card['kind'] = 'custody'
    removed = []
    for field in PARTY_FIELDS:
        value = card.get(field)
        if value:
            removed.append('%s=%r' % (field, value))
            if field in ('buyer_name', 'seller'):
                gone = card.setdefault('retracted', {}).setdefault(field, [])
                if value not in gone:
                    gone.append(value)
        card.pop(field, None)
    card.pop('seller_src', None)
    evidence = card.get('party_evidence')
    if isinstance(evidence, dict):
        for role in ('buyer', 'seller'):
            evidence.pop(role, None)
    card['no_parties'] = NO_PARTIES
    log.append('%s: тип %r → %r; снято: %s' % (card['id'], expected_type, NEW_TYPE,
                                               ', '.join(removed) or 'сторон не было'))


def main(write):
    raw_data = open(DATA, encoding='utf-8').read()
    raw_pending = open(PENDING, encoding='utf-8').read()
    data = json.loads(raw_data)
    pending = json.loads(raw_pending)
    log = []
    by_id = {d['id']: d for d in data['deals']}
    rolf = by_id['g69a22dab']
    assert rolf['type'] == 'M&A' and rolf.get('seller_id'), 'Рольф — M&A, его не трогаем'
    for cid, expected in BASE_CARDS.items():
        convert(by_id[cid], expected, log)
    akzo = by_id[AKZO]
    old = akzo['law']['struct']
    assert old.startswith(AKZO_OLD_START), old[:80]
    akzo['law']['struct'] = AKZO_LEAD + old
    absorb(akzo, 'law.struct', old)
    log.append('%s: law.struct начинается с управляющего' % AKZO)

    cards = {c['id']: c for c in pending['cards']}
    for cid, sentence in PENDING_CARDS.items():
        card = cards[cid]
        assert card.get('buyer_name') == '«Центр Капитал»', (cid, card.get('buyer_name'))
        assert card.get('kind') == 'custody' and not card.get('no_post'), cid
        convert(card, 'M&A', log)
        old = card['law']['struct']
        assert 'Центр Капитал' not in old, cid
        card['law']['struct'] = old.rstrip() + ' ' + sentence
        absorb(card, 'law.struct', old)
        if cid == LEAD:
            assert not card.get('post_override'), cid
            card['post_override'] = JOINT_POST
            card['post_covers'] = COVERS
            # Прежний одиночный снимок не должен уехать вместо общего поста:
            # снимок нового текста пишет показ в консоли.
            card.pop('post_preview', None)
            log.append('%s: общий пост на %d карточек (post_override, post_covers)' % (cid, len(COVERS)))
        else:
            card['no_post'] = True
            log.append('%s: на сайт без отдельного поста (no_post)' % cid)
    assert cards['g38bdff94']['type'] == 'M&A'   # «Гидроиндустрия» — обычная сделка, не трогаем

    print('\n'.join(log))
    print('\nОбщий пост:\n' + JOINT_POST)
    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0
    # Перечитать прямо перед записью и применить к свежему файлу
    # (docs/card_editing.md: json.dump старого снимка стирает чужой пуш).
    if open(DATA, encoding='utf-8').read() != raw_data \
            or open(PENDING, encoding='utf-8').read() != raw_pending:
        print('Файлы изменились во время прогона — запустите заново.')
        return 1
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nЗаписано.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
