# -*- coding: utf-8 -*-
"""Вычитка базы, партии l–u (2 ноября 2026, вечерний прогон): то, что таблица FIXES не умеет.
Пара к pipeline/ingest/fixes/reread_2026_11_02_{l..u}.py.

Даты (review.py принимает дату, только если день и месяц названы в цитате словами):
- g015e2da2 («Медси»/«Александрия»): 2026-03-15 → 2026-03-25, registry — вход «Медси»
  в ООО «Рост-клиник» с 80% по ЕГРЮЛ 25.03.2026.
- g373c03ad, ge6e9c77a, g097e34b2: источники называют только месяц («в июне»,
  «в апреле 2026 года актив сменил владельца») — по docs/card_status_dates.md
  «нет дня — только год»: дата → «2026».
- g0bbc9e9e (Точка/Mpstats): 2026-06-15 → 2026-03-25, registry — АО «Точка» записано
  единственным акционером АО «МПСТАТС ТЕХ» (datanewton, includeDate). Отрасль
  Банки → ИТ и интернет: предмет — сервис аналитики маркетплейсов.
- gedfd4c1e (Herbalife/Bioniq): статус «Закрыта», а дата 26 марта — объявление;
  закрытие 30 апреля 2026 (пресс-релиз Herbalife 6 мая, 8-K; 10-Q) → closing.
- gcc677615 (Рижский вокзал): статус «Не состоялась», дата 13 февраля — распоряжение;
  четвертый аукцион признан несостоявшимся 6 октября 2026 (РИА: «6 окт») → announcement.

Суммы, которых нет ни в одном источнике (снятое — в retracted.sum, иначе enrich.py вернет):
- g489b4309-2 (казначейский пакет X5): «≈65–72 млрд ₽ (по оценке)» → «Не раскрыта».
- g8bc7aacf («Е1 Групп»/«Энгельс Электроинструменты»): «804 млн ₽ (по оценке)» — это
  стоимость активов завода на конец 2023 года (BFM), а не цена → «Не раскрыта».
- gf12c6323 (RWB/«Еаптека»): прежнее «8–10 млрд ₽ (по оценке)» уже заменено таблицей
  (партия o) на оценку RNC Pharma 7–12 млрд ₽ — снятое в retracted.sum.

Стороны:
- gf5c8e14e («Филанко»): «Структуры Александра Клячина» снято таблицей (партия n) —
  в retracted.seller (Клячина нет ни в одной статье и реестре).
- g4e692f4b (ОМК/НВК): продавец «Менеджмент НВК» → ООО «Викар»: по ЕГРЮЛ 70% перешли
  от ООО «Викар» (ОГРН 1237700614535) к АО «Инвестоптима» 26.02.2026.
- g796316fe («Делимобиль»): покупатель — профиль g3ff23b62 «Делимобиля» (сама
  компания, в родительном падеже) → Винченцо Трани (g33023870): Ведомости, CNews,
  vc.ru, Эксперт — выкупил сам Трани; его косвенная доля 53,25% → 66,15%.
  (Отменено fix_reread_2026_11_02_lu2.py: архивная запись аудита снимала Трани в пользу
  ООО «Делимобиль Холдинг» — спор оставлен до статьи.)
- gc3ab0c7d (Avon): продавец «natura&co» → «Natura&Co» (регистр; review.py считает
  правку уже примененной).
- g1125c0ec (Wink/«Смотрешка»): отрасль E-commerce → Медиа (онлайн-кинотеатр и IPTV);
  словарь review.py этих слов не знает.

Темы: g52a9b068 («Врач на дом») — «Продажа с торгов» снята: прямой выкуп у партнеров
(tag_themes.add_themes только дописывает).

Источник: gea799efc — снята ссылка РИА о торгах здания цирка в Уссурийске
(tsirk-2126450240): об Ижевском заводе в ней ни слова.

Профили (описание попадает в пост и на сайт):
- ga3c5b4db «Кронос»: «2011–2015» и «Транслом продал» неверны (по ЕГРЮЛ доли 50/50 со
  «Сбербанк Инвестициями» 04.2021–11.2025, продал сам «Кронос»).
- g504a7eab «Рокет Сити»: «купила у «Транслома»» неверно.
- g0e10bcc3 «Уфабурмаш»: описание действия снято, остается описание компании.

legal_short вручную — party_legal_names.py искажает имя или профиль привязан к
другому юрлицу группы:
- gae376dd7 → АО «Группа компаний «Медси»»; g690e043b → АО «Издательство «Просвещение»»;
  gd51874a0 → ПАО МКК «Займер»; gee79811a → ООО «РБЕ» (по ЕГРЮЛ покупатель — ООО «РБЕ»,
  ИНН 7717798160; у профиля ИНН дочки — вопрос в бэклог).

    python3 pipeline/archive/2026-11/fix_reread_2026_11_02_lu.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import review  # noqa: E402

BASE = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')


def set_val(obj, key, old, new):
    assert obj.get(key) == old, (obj.get('id'), key, obj.get(key), old)
    obj[key] = new


def retract(card, field, value):
    lst = card.setdefault('retracted', {}).setdefault(field, [])
    if value not in lst:
        lst.append(value)


def absorb(card, field):
    """Поле правится мимо таблицы, а у него есть запись FIXES: ее отпечаток —
    в proofread_absorbed (docs/card_editing.md), иначе запись сочтут непримененной."""
    for f in review.FIXES:
        if f['id'] == card['id'] and f['field'] == field and f.get('new') is not None:
            marks = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
            fp = review.fix_fingerprint(f['new'])
            if fp not in marks:
                marks.append(fp)


def setf(card, field, old, new):
    absorb(card, field)
    set_val(card, field, old, new)


def main(argv):
    raw = open(BASE, encoding='utf-8').read()
    data = json.loads(raw)
    D = {d['id']: d for d in data['deals']}
    C = data['companies']
    log = []

    def date(i, old, new, basis):
        c = D[i]
        setf(c, 'date', old, new)
        if basis is not None:
            absorb(c, 'date_basis')
            c['date_basis'] = basis
        log.append('%s: дата %s → %s%s' % (i, old, new, (' (%s)' % basis) if basis else ''))

    date('g015e2da2', '2026-03-15', '2026-03-25', 'registry')
    date('g373c03ad', '2026-06-15', '2026', None)
    date('ge6e9c77a', '2026-06-16', '2026', None)
    date('g097e34b2', '2026-04-15', '2026', None)
    date('g0bbc9e9e', '2026-06-15', '2026-03-25', 'registry')
    date('gedfd4c1e', '2026-03-26', '2026-04-30', 'closing')
    date('gcc677615', '2026-02-13', '2026-10-06', 'announcement')

    setf(D['g0bbc9e9e'], 'ind', 'Банки', 'ИТ и интернет')
    setf(D['g1125c0ec'], 'ind', 'E-commerce', 'Медиа')
    log.append('g0bbc9e9e: отрасль Банки → ИТ и интернет; g1125c0ec: E-commerce → Медиа')

    for i, old in [('g489b4309-2', '≈65–72 млрд ₽ (по оценке)'), ('g8bc7aacf', '804 млн ₽ (по оценке)')]:
        c = D[i]
        setf(c, 'sum', old, 'Не раскрыта')
        eco = c.get('eco') or {}
        if eco.get('sum') not in (None, '', '—', 'Не раскрыта'):
            absorb(c, 'eco.sum')
            assert eco['sum'] == old, (i, eco['sum'])
            eco['sum'] = 'Не раскрыта'
        retract(c, 'sum', old)
        log.append('%s: сумма %s → Не раскрыта' % (i, old))
    assert D['gf12c6323']['sum'] == '7–12 млрд ₽ (по оценке)'
    retract(D['gf12c6323'], 'sum', '8–10 млрд ₽ (по оценке)')

    assert D['gf5c8e14e'].get('seller') in (None, '', '—'), D['gf5c8e14e'].get('seller')
    retract(D['gf5c8e14e'], 'seller', 'Структуры Александра Клячина')

    c = D['g4e692f4b']
    setf(c, 'seller', 'Менеджмент НВК', 'ООО «Викар»')
    assert c.get('seller_id') is None
    retract(c, 'seller', 'Менеджмент НВК')

    c = D['g796316fe']
    absorb(c, 'buyer')
    set_val(c, 'buyer', 'g3ff23b62', 'g33023870')
    assert C['g33023870']['name'] == 'Винченцо Трани'

    setf(D['gc3ab0c7d'], 'seller', 'natura&co', 'Natura&Co')
    log.append('стороны: g4e692f4b продавец → ООО «Викар»; g796316fe покупатель → Винченцо Трани; '
               'gc3ab0c7d продавец Natura&Co; retracted: gf5c8e14e seller, gf12c6323 sum')

    c = D['g52a9b068']
    assert c['themes'] == ['Продажа с торгов', 'Консолидация доли'], c['themes']
    c['themes'] = ['Консолидация доли']

    c = D['gea799efc']
    bad = 'https://realty.ria.ru/20261023/tsirk-2126450240.html'
    n = len(c['src'])
    c['src'] = [s for s in c['src'] if (s[1] if isinstance(s, list) else s) != bad]
    assert len(c['src']) == n - 1, c['src']
    log.append('g52a9b068: тема «Продажа с торгов» снята; gea799efc: ссылка о цирке снята')

    set_val(C['ga3c5b4db'], 'desc',
            'Структура, владевшая финтех-сервисом «Вториум» вместе со «Сбербанк Инвестициями» в 2011–2015 '
            'годах; в 2026-м «Транслом» (структура «Кроноса») продал «Вториум» ООО «Рокет Сити».',
            'Компания Алексея Золотарева, владелец «Транслома», крупнейшего в России заготовителя лома.')
    set_val(C['g504a7eab'], 'desc',
            'В 2026 году купила у «Транслома» финтех-сервис «Вториум»; аналитики оценивали актив от 640 млн ₽.',
            'Компания Анастасии Усковой, бывшего гендиректора Рокетбанка.')
    set_val(C['g0e10bcc3'], 'desc',
            'Уфимский производитель бурового инструмента (долота PDC, элементы бурильных колонн); выручка '
            '409 млн ₽ (2025). В 2026 году 51% купил «Бурсервис», 49% остались за прежним совладельцем.',
            'Уфимский производитель бурового инструмента (долота PDC, элементы бурильных колонн); выручка '
            '409 млн ₽ (2025).')
    log.append('профили: описания «Кроноса», «Рокет Сити», «Уфабурмаша»')

    for cid, ls in [('gae376dd7', 'АО «Группа компаний «Медси»»'),
                    ('g690e043b', 'АО «Издательство «Просвещение»»'),
                    ('gd51874a0', 'ПАО МКК «Займер»'),
                    ('gee79811a', 'ООО «РБЕ»'),
                    # дописано после party_legal_names.py --write (у него «Семейная Аптека "апрель»;
                    # у «Кама Капитал» продавцу EKE форма не ставится — профиль привязан к чужому ИНН)
                    ('ge96b97f1', 'ООО «Семейная аптека «Апрель»»'),
                    ('g77f87dcc', 'АО «Кама Капитал»'),
                    ('g9d2e4c88', 'ООО «Евростройконсалт»')]:
        C[cid]['legal_short'] = ls
    log.append('legal_short вручную: Медси, Просвещение, Займер, РБЕ')

    print('\n'.join(log))
    if '--write' not in argv:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    assert open(BASE, encoding='utf-8').read() == raw, 'база изменилась во время прогона — перезапустите'
    out = json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else '')
    open(BASE, 'w', encoding='utf-8').write(out)
    print('записано')


if __name__ == '__main__':
    main(sys.argv[1:])
