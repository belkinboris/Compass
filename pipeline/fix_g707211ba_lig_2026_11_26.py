# -*- coding: utf-8 -*-
"""Карточка g707211ba (консорциум Тодда Боэли / зарубежные активы ЛУКОЙЛа),
дополнение 26 ноября 2026 по сообщению самого консорциума (бэклог G41) — то,
что не ложится в таблицу FIXES:

1. Предмет привязан к профилю g6b0b26d9 «LUKOIL International GmbH».
   25 ноября предмет был лотом («Зарубежные активы ЛУКОЙЛа»): юрлицо-держатель
   источники о соглашении не называли, а общий профиль g199de75d («иностранные
   активы ЛУКОЙЛа», со строчной буквы) второе чтение отвязало — его имя шло в
   строку «Предмет» поста вместо текста (archive/2026-11/
   fix_g707211ba_second_reading_2026_11_25.py). Теперь консорциум сам назвал
   покупаемую компанию: 100% LUKOIL International GmbH (Frank Media, РИА
   Новости, ПРАЙМ, Коммерсантъ). У профиля g6b0b26d9 имя — юрлицо с заглавной,
   строка поста «Предмет: LUKOIL International GmbH» читается верно. Текст
   `asset` меняет таблица (fixes/g707211ba_boehly_lukoil_2026_11_25.py) —
   этот скрипт запускается ПОСЛЕ `review.py --write`.
2. «Команда сделки»: Citi — финансовый консультант (Коммерсантъ по сообщению
   Eldridge). Чью сторону он ведет, издание не уточняет; клиента не
   выводим: сообщение консорциума могло назвать и консультанта продавца.
   `law.adv` элементом списка review.py не пишет (docs/card_editing_scripts.md).
3. Профиль g6b0b26d9: из описания снят устаревший хвост «в 2026 году его
   продажу американской Carlyle согласовывает ЛУКОЙЛ» — соглашение с Carlyle
   лицензию OFAC не получило (Frank Media), а описание — о компании, не о
   сделке (docs/company_profiles.md, «Новая сделка — перечитать описания
   сторон»). Первая часть описания не тронута.
4. Источник поста — первым в src: Коммерсантъ doc/9130738 (сообщение
   консорциума об окончательном соглашении), а не doc/9130604.
5. accepted_notes: снята причина «нет профиля предмета» и отметка о имени
   продавца в предмете (предмет теперь юрлицо); заметки о прочитанном и о
   консультантах — по новым источникам; причина «нет профиля покупателя» —
   по составу консорциума из сообщения (во главе Eldridge, не физлицо);
   «соглашение подписано 25 ноября» -> «объявлено» (замечания приемки).

Запуск: python3 pipeline/fix_g707211ba_lig_2026_11_26.py [--write]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CARD_ID = 'g707211ba'
PROFILE = 'g6b0b26d9'
BY, DAY = 'fix_g707211ba_lig_2026_11_26', '2026-11-26'

FRANK = 'https://frankmedia.ru/318105'
KOM = 'https://www.kommersant.ru/doc/9130738'
Q_TARGET = ('Консорциум во главе с компанией Eldridge американского миллиардера Тодда Боули заключил '
            'окончательное соглашение о покупке LUKOIL International GmbH (LIG), которой принадлежат '
            'зарубежные активы Лукойла, говорится в сообщении консорциума.')
Q_CITI = ('Консорциум во главе с Eldridge Тодда Боэли заключил соглашение о приобретении LUKOIL '
          'International GmbH (LIG), объединяющую зарубежные активы ЛУКОЙЛа, сообщила Eldridge. В '
          'консорциум также входят Корпорация финансирования международного развития США (DFC), Catena '
          'Investment Holding из ОАЭ и американская Xtellus Partners. Финансовым консультантом выступает Citi.')
ADV_ROW = ['Финансовый консультант', 'Citi',
           'Назван в сообщении консорциума; чью сторону он консультирует, источник не уточняет']

DESC_OLD = ('Дочернее общество ЛУКОЙЛа, владеющее зарубежными активами группы (кроме казахстанских); в 2026 '
            'году его продажу американской Carlyle согласовывает ЛУКОЙЛ, сделка зависит от одобрения OFAC США.')
# Первый проход 26 ноября оставил «(кроме казахстанских)»; приемка (два чтения подряд) нашла, что
# источники этой сделки включают в зарубежный портфель месторождения в Казахстане (Reuters, Ведомости),
# а исключение Казахстана в источниках — условие прежней сделки с Carlyle (оно записано в ее карточке,
# eco.context g20d4cc38), а не состав LIG. Неподтвержденная оговорка снята.
DESC_MID = 'Дочернее общество ЛУКОЙЛа, владеющее зарубежными активами группы (кроме казахстанских).'
DESC_NEW = 'Дочернее общество ЛУКОЙЛа, которому принадлежат зарубежные активы группы.'

NOTE_TARGET_OLD_START = 'предмет — лот: совокупность зарубежных активов продавца'
NOTE_SELLER_OLD_START = 'предмет — зарубежные активы самого продавца'
ADVISER_CHECK_NEW = ('совпадение у Global Banking & Finance Review — не консультант сделки, а юридическая '
                     'оговорка сайта под статьей («References to a market rising or falling… third-party '
                     'views»). Консультант сделки назван один: Citi — финансовый консультант (Коммерсантъ '
                     '26 ноября по сообщению Eldridge), сторона не уточняется; другие семь источников '
                     'консультантов не называют')
NOTES_ADD = (' 26 ноября дочитаны сообщение консорциума (сайт Eldridge) в пересказе РИА Новости и ПРАЙМ, '
             'Frank Media и второй материал Коммерсанта: соглашение окончательное, покупаемая компания — '
             '100% LUKOIL International GmbH (профиль g6b0b26d9), обмен на акции ПАО «ЛУКОЙЛ» и других '
             'российских компаний; Citi — финансовый консультант, сторона не названа.')

BUYER_NOTE_NEW = ('покупатель — консорциум из четырех участников без общего юрлица и названия: во главе — '
                  'американский холдинг Eldridge Тодда Боэли, в составе также DFC, Catena Investment Holding (ОАЭ) '
                  'и Xtellus Partners (сообщение консорциума на сайте Eldridge по РИА Новости и ПРАЙМ; Frank Media; '
                  'Коммерсантъ 26 ноября). По словам Боэли, совместное предприятие переименуют. Профиль Eldridge '
                  'покупателем не ставится: покупает не он один, а консорциум четырех участников с нераскрытыми '
                  'долями. Искали общее юрлицо консорциума в Reuters (перепечатка Global Banking & Finance Review), '
                  'Коммерсанте, Ведомостях (25 и 3 ноября), Frank Media, РИА Новости, ПРАЙМ, веб-поиском по '
                  '«Boehly Lukoil consortium» — не названо. Участники перечислены в «Структуре сделки»')
DUP_OLD = 'соглашение подписано 25 ноября 2026 года'
DUP_NEW = 'об окончательном соглашении объявлено 25 ноября 2026 года'
# Первым источником (его берет пост) — пересказ сообщения самого консорциума об окончательном
# соглашении на покупку 100% LIG; Коммерсантъ doc/9130604 писал «соглашение ... о создании
# консорциума» (замечание приемки 26 ноября).
FIRST_SRC = 'https://www.kommersant.ru/doc/9130738'


def main(write):
    old_data = json.load(open(PATH, encoding='utf-8'))
    data = json.load(open(PATH, encoding='utf-8'))
    card = next(d for d in data['deals'] if d['id'] == CARD_ID)
    prof = data['companies'][PROFILE]
    assert prof['name'] == 'LUKOIL International GmbH', prof['name']
    n = 0

    if card.get('target') != PROFILE:
        assert not card.get('target'), 'target уже другой: %r' % card.get('target')
        assert card.get('asset') == 'LUKOIL International GmbH', \
            'сначала review.py --write: asset должен уже быть LUKOIL International GmbH, сейчас %r' % card.get('asset')
        card['target'] = PROFILE
        fact_edit_guard.log(card, 'target', PROFILE, Q_TARGET, FRANK, BY, DAY)
        print('%s: target -> %s (%s)' % (CARD_ID, PROFILE, prof['name']))
        n += 1

    adv = card.setdefault('law', {}).setdefault('adv', [])
    if not any(r[1] == 'Citi' for r in adv if isinstance(r, list) and len(r) > 1):
        assert adv == [], 'law.adv не пуст: %r' % adv
        adv.append(list(ADV_ROW))
        # fact_edit_guard сверяет значение поля целиком — весь список, а не строку.
        fact_edit_guard.log(card, 'law.adv', [list(r) for r in adv], Q_CITI, KOM, BY, DAY)
        print('%s: law.adv += %r' % (CARD_ID, ADV_ROW))
        n += 1

    if prof.get('desc') != DESC_NEW:
        assert prof.get('desc') in (DESC_OLD, DESC_MID), 'desc профиля другой: %r' % prof.get('desc')
        prof['desc'] = DESC_NEW
        print('%s: desc -> %s' % (PROFILE, DESC_NEW))
        n += 1

    notes = card.setdefault('accepted_notes', {})
    np_ = notes.get('no_profile') or {}
    if str(np_.get('target', '')).startswith(NOTE_TARGET_OLD_START):
        np_.pop('target')
        n += 1
    nok = notes.get('name_ok') or {}
    if str(nok.get('seller', '')).startswith(NOTE_SELLER_OLD_START):
        nok.pop('seller')
        if not nok:
            notes.pop('name_ok', None)
        n += 1
    checked = notes.setdefault('checked', {})
    if checked.get('adviser_in_source') != ADVISER_CHECK_NEW:
        checked['adviser_in_source'] = ADVISER_CHECK_NEW
        n += 1
    if NOTES_ADD.strip() not in str(notes.get('notes', '')):
        notes['notes'] = str(notes.get('notes', '')).rstrip() + NOTES_ADD
        n += 1

    np_ = notes.setdefault('no_profile', {})
    if np_.get('buyer') != BUYER_NOTE_NEW:
        np_['buyer'] = BUYER_NOTE_NEW
        n += 1
    dup = checked.get('duplicate_card', '')
    if DUP_OLD in dup:
        checked['duplicate_card'] = dup.replace(DUP_OLD, DUP_NEW)
        n += 1
    src = card.get('src') or []
    if src and src[0][1] != FIRST_SRC:
        row = next(r for r in src if r[1] == FIRST_SRC)
        card['src'] = [row] + [r for r in src if r is not row]
        print('%s: первым источником — %s' % (CARD_ID, FIRST_SRC))
        n += 1

    if not n:
        print('Уже применено — нечего делать.')
        return
    mass_edit_guard.check(old_data, data)
    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('ЗАПИСАНО (%d изменений).' % n)
    else:
        print('Сухой прогон: %d изменений. Запись — с ключом --write.' % n)


if __name__ == '__main__':
    main(write='--write' in sys.argv)
