# -*- coding: utf-8 -*-
"""Качество, 19 сентября 2026 — все три уровня очереди дочитывания пусты,
взят пункт G8 из бэклога («Собственники компании на её странице»).

`gebf162ee` («Атакайцемент») — карточка `gef7d4e54» («Атакайцемент»
продан на торгах компании «Бизнес-Инвест») уже называла бенефициара в
тексте («Бизнес-Инвест», бенефициар — Алексей Леонидович Филин), но
независимо от карточки WebFetch по «Блокнот Новороссийск»
(https://bloknot-novorossiysk.ru/news/vladelets-odnogo-iz-tsementnykh-zavodov-novorossiy)
подтвердил дословно: «Новый владелец завода «Атакайцемент» - теперь
брянский бизнесмен Алексей Филин, сделка обошлась ему в 4,39 млрд.
рублей.» — источник называет НОВОГО ВЛАДЕЛЬЦА напрямую по имени, это и
записано (100% — по самой сделке, торги были на все доли).

Второй кандидат этого прогона, `g23a1df20» (АО «УК «Белая скала»»),
проверялся тем же способом — оказалось, что тот же факт уже стоит в базе
(добавлен раньше, другим прогоном); собственный `assert` скрипта поймал
совпадение до записи. Дубль не создан, скрипт правит только Атакайцемент.

Запуск:
    python3 pipeline/fix_g8_ownership_atakaicement_belaya_skala.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_atakaicement_belaya_skala.py --write    # запись
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit('/pipeline', 1)[0]
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

BLOKNOT_SRC = ['Блокнот Новороссийск',
               'https://bloknot-novorossiysk.ru/news/vladelets-odnogo-iz-tsementnykh-zavodov-novorossiy']

OWNERSHIP = {
    'gebf162ee': [
        dict(name='Алексей Филин', id=None, share='100%',
             as_of='2022-11', source=BLOKNOT_SRC),
    ],
}


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    companies = data['companies']

    for cid, ownership in OWNERSHIP.items():
        assert cid in companies, f"нет профиля {cid}"
        assert not companies[cid].get('ownership'), f"{cid} уже несёт ownership: {companies[cid].get('ownership')!r}"
        print(f"{cid} ({companies[cid]['name']}): += ownership")
        for o in ownership:
            print(f"    {o['name']} — {o.get('share', '(доля не названа)')} (на {o['as_of']})")
        companies[cid]['ownership'] = ownership

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
