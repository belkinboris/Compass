# -*- coding: utf-8 -*-
"""Вычитка 12 ноября 2026, марафон, партия m008: правки, которые review.py не делает.

ЧТО И ПОЧЕМУ (каждая правка — с цитатой источника, сохраненного save_source.save(..., day='2026-11-12_m008')):
  g0be691b7 «Бери заряд!» — date 2024-05-01 → 2024: «1 мая» — заглушка; Habr, vc.ru и Investfunds называют только
            «май 2024 года», дня нет (docs/card_status_dates.md, «Нет дня — только год»); review.py день до года не снимает.
            eco.finadv: «Публично не сообщалось» → «Альфа-банк — агент по размещению» (Habr: «Агентом по размещению
            сделки выступил «Альфа-банк»»).
  gaa7602e7 «Цифровые привычки» — date 2024-11-11 (день заметки «Ъ» о плане) → 2025-05-19: pre-IPO прошло двумя
            раундами, второй и последний завершился 19 мая 2025 года (CNews 11.06.2025). Перенос года review.py не
            делает. eco.finadv: фраза → «ИФК «Солид» — организатор размещения» (тот же источник).
  g6a453b19 Ultimate Education — eco.finadv: «Публично не сообщалось» → «Альфа-Инвестиции» — агент по привлечению
            капитала (Ведомости 11.12.2024).
  g3ed36abe «Европлан» — продавец пуст, а акции в IPO продавал единственный владелец, холдинг SFI (Интерфакс
            953060): seller «SFI» + seller_id g83db9336 (профиль SFI, уже продавец «Европлана» в g78986e22).

    python3 pipeline/archive/2026-11/reread_oneoff_m008.py [--write]

Повторный запуск ничего не ломает: уже стоящее значение пропускается («уже применено»).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_m008', '2026-11-12'

HABR = 'https://habr.com/en/articles/838622'
Q_BZ = ('Агентом по размещению сделки выступил «Альфа-банк». Изначально участники ориентировались на диапазон '
        '500-700 млн рублей и срок в один месяц для сбора поручений.')
Q_BZ_DATE = 'В мае 2024 года сервис по аренде пауэрбанков «Бери заряд!» закрыл книгу заявок'
CNEWS = 'https://www.cnews.ru/news/line/2025-06-11_gk_tsifrovye_privychki_rezultaty'
Q_CP = ('Объем привлечения по итогам двух раундов, завершившихся пятого марта и 19 мая соответственно, составил '
        '900 млн руб.')
Q_CP2 = 'А также нашему организатору ИФК «Солид»'
VED_UE = 'https://www.vedomosti.ru/investments/news/2024/12/11/1080745-ultimate-education-privlek'
Q_UE = ('Об этом сообщили представители платформы «Альфа-инвестиции», которая выступила агентом по привлечению '
        'капитала в рамках сделки.')
IFX_E = 'https://www.interfax.ru/business/953060'
Q_E = ('Предложение в рамках размещения состояло из 15 млн акций, принадлежащих единственному владельцу компании – '
       'инвестиционному холдингу SFI (ПАО "ЭсЭфАй", бывшее "Сафмар финансовые инвестиции", контролируется Саидом '
       'Гуцериевым), что соответствует 13,1 млрд рублей по цене IPO.')
SFI = 'g83db9336'

# (карточка, путь поля, старое, новое, цитата, адрес)
EDITS = [
    ('g0be691b7', 'date', '2024-05-01', '2024', Q_BZ_DATE, HABR),
    ('g0be691b7', 'eco.finadv', 'Публично не сообщалось', 'Альфа-банк — агент по размещению', Q_BZ, HABR),
    ('gaa7602e7', 'date', '2024-11-11', '2025-05-19', Q_CP, CNEWS),
    ('gaa7602e7', 'eco.finadv', 'Организатором размещения выступила ИФК «Солид».', 'ИФК «Солид» — организатор размещения',
     Q_CP2, CNEWS),
    ('g6a453b19', 'eco.finadv', 'Публично не сообщалось', '«Альфа-Инвестиции» — агент по привлечению капитала', Q_UE, VED_UE),
    ('g3ed36abe', 'seller', None, 'SFI', Q_E, IFX_E),
    ('g3ed36abe', 'seller_id', None, SFI, Q_E, IFX_E),
]


def getp(card, path):
    if '.' in path:
        a, k = path.split('.', 1)
        return (card.get(a) or {}).get(k)
    return card.get(path)


def setp(card, path, value):
    if '.' in path:
        a, k = path.split('.', 1)
        card.setdefault(a, {})[k] = value
    else:
        card[path] = value


def apply(data):
    by = {d['id']: d for d in data['deals']}
    assert data['companies'][SFI]['name'] == 'SFI'
    done = []
    for cid, path, old, new, quote, url in EDITS:
        card = by[cid]
        cur = getp(card, path)
        if cur == new:
            print('  уже применено: %s %s' % (cid, path))
            continue
        assert cur == old, (cid, path, cur)
        setp(card, path, new)
        if cid == 'g0be691b7' and path == 'date':
            for ev in card.get('events') or []:
                if ev.get('date') == old:
                    ev['date'] = new
        fact_edit_guard.log(card, path, new, quote, url, BY, DAY)
        done.append((cid, path, old, new))
    return done


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    done = apply(data)
    for d in done:
        print('  %s %s: %r → %r' % d)
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()          # перечитать прямо перед записью
    fresh = json.loads(fresh_raw)
    if apply(fresh):
        with open(DATA, 'w', encoding='utf-8') as f:
            f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
        print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
