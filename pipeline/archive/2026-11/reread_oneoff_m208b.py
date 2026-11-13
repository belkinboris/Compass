# -*- coding: utf-8 -*-
"""Разовые правки вычитки, партия m208, вторая часть (марафон 12 ноября 2026): то, что не ложится в FIXES.

Что и почему — в комментарии у каждой правки. Дата по реестру review.py не принимает
(в цитате нет дня прописью), элемент списка events[] он не адресует.

    python3 pipeline/archive/2026-11/reread_oneoff_m208b.py [--write]

Повторный запуск ничего не ломает: правка, у которой поле уже равно новому значению,
пропускается («уже применено»); иначе — assert на старое значение.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY, DAY = 'reread_oneoff_m208b', '2026-11-12'
FACT = {'date', 'title', 'status', 'sum', 'eco.sum', 'seller', 'buyer', 'buyer_name', 'target',
        'asset', 'asset_id', 'seller_id', 'stake_acquired', 'eco.share', 'law.adv', 'eco.finadv'}

# (id, путь, старое, новое, цитата, адрес)
EDITS = [
    # KD Pay: «(основатели)» в поле стороны — неверная роль (Леонид Дубов вошел в 2022 году, он гендиректор)
    ('gmru-mtsbank-kdpay', 'seller', 'Олег Пономарев и Леонид Дубов (основатели)', 'Олег Пономарев и Леонид Дубов',
     'Финальное изменение произошло 20 июля 2026 г., когда МТС Банк приобрел у Олега Пономарева его большую часть доли (49%), а у Леонида Дубова - 2%.',
     'https://www.comnews.ru/content/246503/2026-07-22/2026-w30/1008/mts-bank-kupil-platezhnyy-servis-kd-pay'),
    # «Милфудс»: предмет — заложенная доля, а не «партнерство»
    ('gmru-sucden-poetti', 'asset', 'партнерство с «Милфудс» (бренд Poetti)', '35% доли в ООО «Милфудс»',
     'В обеспечение товарного кредита в залог передана миноритарная часть доли в ООО «МилФудс» в размере 35%.',
     'https://www.retail.ru/news/sdelka-poetti-i-sucden-ne-yavlyaetsya-skrytoy-peredachey-aktivov-16-iyulya-2026-279949/'),
    # KD Pay: 50–150 млн ₽ — оценка аналитика «Финама» Ярослава Кабакова, стороны цену не раскрыли
    # (docs/card_money.md, «Что идет в сумму», 13 ноября 2026); оценка остается в eco.val.
    ('gmru-mtsbank-kdpay', 'sum', '50–150 млн ₽ (по оценке)', 'Не раскрыта',
     'Финансовые условия сделки не раскрываются.',
     'https://www.akm.ru/press/mts_bank_priobretaet_platezhnyy_servis_kd_pay/'),
    ('gmru-mtsbank-kdpay', 'eco.sum', '50–150 млн ₽ (по оценке)', 'Не раскрыта',
     'Финансовые условия сделки не раскрываются.',
     'https://www.akm.ru/press/mts_bank_priobretaet_platezhnyy_servis_kd_pay/'),
    ('gmru-mtsbank-kdpay', '+retracted.sum', None, '50–150 млн ₽ (по оценке)', None, None),
    # этап «Сделка завершена» — день записи в ЕГРЮЛ (20 июля), а не публикации ComNews
    ('gmru-mtsbank-kdpay', 'events.0.date', '2026-07-22', '2026-07-20', None, None),
    # ВНТ: «Предмет / доля» описывал терминал (емкость, танкеры) — это есть в профиле; размер пакета статья не называет.
    ('gmru-roshim-vnt', 'eco.share',
     'Резервуарный парк ВНТ вмещает 94 тыс. куб. м, танкеры терминал принимает дедвейтом до 50 тыс. т; через него идут нефтепродукты и нефтехимические грузы.',
     '—', 'Как выяснил “Ъ”, холдинг может выкупить Восточный нефтехимический терминал в бухте Врангеля', 'https://www.kommersant.ru/doc/8829978'),
    # «Золотоноша»: доля перешла 27 мая 2026 года по ЕГРЮЛ («в конце мая» у «Коммерсанта»); в карточке
    # стоял день публикации статьи.
    ('gmru-geopromining-zabaikalie', 'date', '2026-07-20', '2026-05-27',
     '2026-05-27: ООО "КРЯЖ ИНВЕСТ" вошел в участники (доля до None%, после 25.0%). Входящее в группу «ГеоПроМайнинг» ООО «Кряж Инвест» в конце мая получило 25% ООО «Золотоноша»',
     'https://projectcompass.ru/api/companies/g93fc66c3/fns'),
    # «Ростех»: заголовок по стандарту для обсуждаемой сделки, о которой объявили сами стороны
    # («Ростех» подтвердил обсуждение) — «собирается»; прежнюю запись заголовка (written_titles_g3)
    # закрывает отпечаток в proofread_absorbed.title (см. TITLE_ABSORB ниже).
    ('gmru-rostech-avia-holding', 'title',
     '«Ростех» объединяет Red Wings, SkyGates и другие авиаактивы в новый холдинг',
     '«Ростех» собирается объединить Red Wings, SkyGates и другие авиаактивы в холдинг',
     'В «Ростехе» подтвердили “Ъ”, что консолидация активов «в единый холдинг обсуждается на уровне корпорации»',
     'https://www.kommersant.ru/doc/8829970'),
    # Коми: $30 млн — цена в объявлении о продаже (покупателя нет), а не цена сделки
    # (docs/card_money.md, «Что идет в сумму»: стартовая цена — не цена); цифра остается в eco.val и в заголовке.
    ('gmru-vysochaishy-komi-oil', 'sum', '$30 млн', 'Не раскрыта',
     'Стоимость долей в двух компаниях — $30 млн, «Нефтегеосервис» оценен в $13 млн, НК «Севергеофизика» — в $17 млн.',
     'https://www.kommersant.ru/doc/8816591'),
    ('gmru-vysochaishy-komi-oil', 'eco.sum', '$30 млн', 'Не раскрыта',
     'Стоимость долей в двух компаниях — $30 млн, «Нефтегеосервис» оценен в $13 млн, НК «Севергеофизика» — в $17 млн.',
     'https://www.kommersant.ru/doc/8816591'),
    ('gmru-vysochaishy-komi-oil', '+retracted.sum', None, '$30 млн', None, None),
    # «Милфудс»: залог оформлен и виден в ЕГРЮЛ (договор — в июне 2026 года), партнерство заключено —
    # финансирование состоялось; «Обсуждается» стояло от версии о будущей покупке.
    ('gmru-sucden-poetti', 'status', 'Обсуждается', 'Закрыта',
     'Соответствующий договор был заключен в июне 2026 года, следует из данных СПАРК. Это обеспечение по товарному кредиту, пояснили “Ъ” в Sucden.',
     'https://www.kommersant.ru/doc/8815172'),
]


def _get(card, path):
    cur = card
    for p in path.split('.'):
        if cur is None:
            return None
        cur = cur[int(p)] if isinstance(cur, list) else cur.get(p)
    return cur


def _set(card, path, value):
    parts = path.split('.')
    cur = card
    for p in parts[:-1]:
        cur = cur[int(p)] if isinstance(cur, list) else cur.setdefault(p, {})
    last = parts[-1]
    if isinstance(cur, list):
        cur[int(last)] = value
    else:
        cur[last] = value


def apply(data, verbose=False):
    sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
    import review
    by = {d['id']: d for d in data['deals']}
    done = 0
    for cid, path, old, new, quote, url in EDITS:
        c = data['companies'][cid[1:]] if cid.startswith('@') else by[cid]
        if path.startswith('+'):
            # дописать в список (retracted.<поле>): снятое значение не вернется обогащением
            box = c.setdefault('retracted', {}).setdefault(path.split('.', 1)[1], [])
            if new not in box:
                box.append(new)
                done += 1
            continue
        cur = _get(c, path)
        if cur == new:
            if verbose:
                print('  уже применено  %s %s' % (cid, path))
            continue
        assert cur == old, (cid, path, cur)
        _set(c, path, new)
        if (path.startswith(('eco.', 'law.', 'extra')) and path not in FACT or path == 'title') and isinstance(old, str):
            # поле правили записи FIXES (у заголовка «Ростеха» — written_titles_g3): отпечаток прежнего текста — в proofread_absorbed
            fp = review.fix_fingerprint(old)
            box = c.setdefault('proofread_absorbed', {}).setdefault(path, [])
            if fp not in box:
                box.append(fp)
        if quote and path in FACT:
            fact_edit_guard.log(c, path, new, quote, url or '', BY, DAY)
        done += 1
        if verbose:
            print('  ПРАВИМ  %s %s: %r -> %r' % (cid, path, str(old)[:50], str(new)[:60]))
    return done


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = apply(data, verbose=True)
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    if not write:
        print('Сухой прогон: %d правок. Запись — с ключом --write.' % n)
        return 0
    if not n:
        print('Все правки уже применены.')
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО: %d правок.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
