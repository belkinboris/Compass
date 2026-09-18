# -*- coding: utf-8 -*-
"""Карточка g404c3459 «Тодд Бёли продал свою долю в «Челси»» прошла ворота
притока 18.09.2026 (часовой прогон 10:20 МСК) до того, как в том же прогоне
был исправлен корень проблемы: `russian_evidence()` в promote.py принимала
слова «Челси», «Бёли» и «Тодд» — транслитерации иностранного футбольного
клуба и имени/фамилии его совладельца — за «имя собственное кириллицей»,
то есть за возможный признак российского рынка. Третий день подряд с той
же историей (Бёли/Уолтер продают долю в лондонском «Челси» инвесткомпании
Clearlake Capital Group — сделка целиком иностранная, ни одна сторона к
российскому рынку отношения не имеет) наконец дал достаточно материала для
осознанной, измеренной правки: все три слова добавлены в существующие
списки-исключения NOT_RUSSIAN_PLACE/NOT_RUSSIAN_PERSON тем же прогоном
(замер по всей базе — ни одно из трёх слов не встречается ни в одной из
1586 карточек, значит добавление никого не лишает единственного
доказательства). Эта карточка успела попасть в pending.json ДО правки —
снимаем её тем же способом, что и двух предыдущих (17 и 18 сентября,
`fix_remove_chelsea_no_russian_nexus.py`/`_2.py`), но в третий раз это уже
не заплатка поверх симптома, а уборка одной последней карточки после
починки самой причины.

Карточка ещё не отправлена в консоль (send_drafts не запускался после
promote.py) — снимаем из pending.json, а не через модерацию.

Запуск: python3 pipeline/fix_remove_chelsea_no_russian_nexus_3.py [--write]
"""
import json
import sys

PENDING_PATH = 'static/data/pending.json'


def main(write):
    data = json.load(open(PENDING_PATH, encoding='utf-8'))
    cards = data['cards']
    before = len(cards)
    target = [c for c in cards if c['id'] == 'g404c3459']
    assert len(target) == 1, target
    assert target[0]['title'] == 'Тодд Бёли продал свою долю в «Челси»'
    assert not target[0].get('draft_sent'), 'карточка уже отправлена в консоль — снимать нельзя этим скриптом'
    data['cards'] = [c for c in cards if c['id'] != 'g404c3459']
    assert len(data['cards']) == before - 1

    if write:
        json.dump(data, open(PENDING_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('Снято: g404c3459. ЗАПИСАНО.')
    else:
        print('Сухой прогон: снял бы g404c3459. Повторите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
