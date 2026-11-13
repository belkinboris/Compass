# -*- coding: utf-8 -*-
"""Вычитка, партия m106a (13 ноября 2026), часть 1: отложенные спорные случаи —
семь карточек-повторов сливаются этапами в карточки самих сделок.

Владелец, 13 ноября 2026: «если после вычитки у тебя будут вопросы или отложенное
что-то, не жди моего ответа и постарайся сам все решить». Решения — по
docs/base_duplicates.md («Одна сделка — одна карточка с этапами»; слух и его исход —
одна сделка) через merge_duplicate_deals_batch.Merge: merged[drop] = keep, источники,
этап, снятие записей таблицы правок дубля (у всех семи они только в архиве
fixes_archive/*.json — живых чужих файлов правок скрипт не трогает).

  * c6fd3a848 и c49c9d8b0 → g1caed4b7 («ЕАС Групп» купила «Волга-Днепр», 30.12.2025).
    Обе — предложение владельцев передать группу государству: 24.08.2025 Алексей Исайкин
    объявил о возможной передаче (Коммерсантъ 7988696: «основатель «Волга-Днепр» Алексей
    Исайкин объявил о перспективах скорой передачи грузовой группы государству»), 29.08.2025
    акционеры направили в правительство заявление об отказе от прав собственности
    (Коммерсантъ 8005070). Передача не состоялась, группу купила «ЕАС Групп» — исход того же
    сюжета; у g1caed4b7 в eco.context уже есть «В августе 2025 года владельцы предложили
    передать группу государству». Два этапа с точным днем.
  * cf6de2938 → gd73fd825 (фонд «Консорциум.Первый» купил «Яндекс» у Yandex N.V.): та же
    сделка — 475 млрд ₽, 15.07.2024, тот же покупатель; из дубля — источники (Коммерсантъ
    06.10.2023 об условиях раздела, Ведомости 15.07.2024 о закрытии).
  * c33a55069 → gd73fd825: иск миноритариев Yandex N.V. (Nebius Group) о признании продажи
    недействительной — не сделка, а поздняя судьба этой сделки. В eco.context — одна
    фраза-мост с датой (BES.media 19.12.2024: «В сентябре 2024 года миноритарии … обратились
    с иском в суд Калининграда с требованием признать продажу … недействительной»;
    «Арбитражный апелляционный суд в Санкт-Петербурге отказал в удовлетворении иска
    миноритариев Yandex N.V.»).
  * c09e39da9 → absolut-strah (ЦАНЦ купил «Абсолют Страхование», 26.06.2026): объявление о
    продаже (Коммерсантъ 26.06.2024) — этап той же сделки; у выжившей в eco.context уже есть
    «Актив выставили на продажу еще в июне 2024 года».
  * c1d0f3d54 → g96b1cdaf (ЛУКОЙЛ купил 56,43% «ЭЛ5-Энерго», бывшая «Энел Россия»; тот же
    профиль предмета ge2a1dca0): заморозка продажи Enel указом № 520 (Neftegaz.RU 09.08.2022:
    «Сделка по продаже итальянской генерирующей компанией Enel 56,43% в Энел Россия ЛУКОЙЛу и
    фонду Газпромбанк-Фрезия приостановлена на неопределенное время») — этап. Fortum в той же
    заметке — у ее карточки g7fc9f764 своя история (временное управление 2023 года), туда
    этап не нужен: продажу Fortum так и не провели.
  * c51777ade → c7fd83d05 (временное управление активами Danone): назначение Якуба Закриева
    гендиректором — часть того же указа; в c7fd83d05 оно уже описано в eco.context. Из
    дубля — источник (Financial Times). Сумма дубля «До 1 млрд € (списание стоимости
    активов)» — не цена, не переносится.

    python3 pipeline/archive/2026-11/reread_deferred_m106a.py           # сухой прогон
    python3 pipeline/archive/2026-11/reread_deferred_m106a.py --write   # запись

Повторный запуск ничего не ломает: слитое пропускается, правка, которая уже стоит,
пропускается.
"""
import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
DISCREP = os.path.join(ROOT, 'pipeline', 'facts_discrepancies.json')
SIGNALS = os.path.join(ROOT, 'static', 'data', 'signals.json')
MISSING = object()

K_VD1 = 'https://www.kommersant.ru/doc/7988696'
K_VD2 = 'https://www.kommersant.ru/doc/8005070'
BES_1 = 'https://bes.media/news/aktsioneri-bivshey-yandex-nv-podali-isk-s-trebovaniem-priznat-nedeystvitelnoy-prodazhu-niderladskoy-chasti-biznesa-bbf412/'
BES_2 = 'https://bes.media/news/aktsioneri-bivshey-yandex-nv-proigrali-sud-ob-osparivanii-prodazhi-niderladskoy-chasti-biznesa-575833/'
K_ABS = 'https://www.kommersant.ru/doc/6790872'
NG_EN = 'https://neftegaz.ru/news/companies/746492-sdelki-po-prodazhe-enel-i-fortum-rossiyskikh-aktivov-zamorozheny-na-neopredelennyy-srok/'

MERGES = [
    {'keep': 'g1caed4b7', 'drop': 'c6fd3a848',
     'reason': '«Волга-Днепр»: объявление основателя о передаче группы государству (24.08.2025) — этап сюжета, исход которого — продажа «ЕАС Групп».',
     'add_src': [['Коммерсантъ', K_VD1]],
     'events': [{'kind': 'other', 'date': '2025-08-24', 'title': 'Основатель предложил передать группу государству',
                 'note': 'Основатель «Волга-Днепр» Алексей Исайкин объявил, что группу могут передать государству.',
                 'source': ['Коммерсантъ', K_VD1]}]},
    {'keep': 'g1caed4b7', 'drop': 'c49c9d8b0',
     'reason': '«Волга-Днепр»: заявление акционеров об отказе от акций в пользу государства (29.08.2025) — этап того же сюжета.',
     'add_src': [['Коммерсантъ', K_VD2]],
     'events': [{'kind': 'other', 'date': '2025-08-29', 'title': 'Акционеры заявили об отказе от акций в пользу государства',
                 'note': 'Акционеры «Волга-Днепр» направили в правительство заявление об отказе от акций в пользу государства.',
                 'source': ['Коммерсантъ', K_VD2]}]},
    {'keep': 'gd73fd825', 'drop': 'cf6de2938',
     'reason': '«Яндекс»: раздел активов между российской и международной структурами — та же продажа фонду «Консорциум.Первый» (475 млрд ₽, 15.07.2024).',
     'add_src': [['Коммерсантъ', 'https://www.kommersant.ru/doc/6254171'],
                 ['Ведомости', 'https://www.vedomosti.ru/investments/news/2024/07/15/1050031-yandex-nv']]},
    {'keep': 'gd73fd825', 'drop': 'c33a55069',
     'reason': '«Яндекс»: иск миноритариев Yandex N.V. о признании продажи недействительной — поздняя судьба той же сделки, не сделка.',
     'add_src': [['Forbes', 'https://www.forbes.ru/investicii/520567-minoritarii-byvsej-yandex-n-v-podali-vtoroj-isk-k-konsorciumu-investorov']]},
    {'keep': 'absolut-strah', 'drop': 'c09e39da9',
     'reason': '«Абсолют Страхование»: объявление о продаже (26.06.2024) — этап продажи ЦАНЦ (26.06.2026).',
     'add_src': [['Коммерсантъ', K_ABS]],
     'events': [{'kind': 'announced', 'date': '2024-06-26', 'title': 'Компанию выставили на продажу',
                 'note': 'Александр Светаков выставил «Абсолют Страхование» на продажу.',
                 'source': ['Коммерсантъ', K_ABS]}]},
    {'keep': 'g96b1cdaf', 'drop': 'c1d0f3d54',
     'reason': 'Enel: заморозка продажи указом № 520 (август 2022) — этап продажи 56,43% «Энел Россия» ЛУКОЙЛу.',
     'add_src': [['Neftegaz.RU', NG_EN]],
     'events': [{'kind': 'other', 'date': '2022-08-05', 'title': 'Продажу приостановил указ № 520',
                 'note': 'Продажу российских активов Enel приостановили из-за указа Президента № 520 о временном порядке сделок с недружественными инвесторами.',
                 'source': ['Neftegaz.RU', NG_EN]}]},
    {'keep': 'c7fd83d05', 'drop': 'c51777ade',
     'reason': 'Danone: назначение Якуба Закриева гендиректором «Данон Россия» — часть временного управления по указу № 520 (16.07.2023).',
     'add_src': [['Financial Times', 'https://www.ft.com/content/d5234953-cddf-4b64-8a55-dc749843ab5c']]},
]

# (id карточки, поле через точку, старое значение, новое значение)
EDITS = [
    ('gd73fd825', 'eco.context', '—',
     'В сентябре 2024 года 15 миноритариев Yandex N.V. (теперь Nebius Group) потребовали в арбитражном суде '
     'Калининграда признать продажу недействительной: по их словам, после сделки они не могли продать акции по '
     'справедливой цене. В декабре 2024 года суд в иске отказал.'),
]
ADD_SRC = [('gd73fd825', ['BES.media', BES_1]), ('gd73fd825', ['BES.media', BES_2])]


def get(obj, path):
    for k in path.split('.'):
        if not isinstance(obj, dict) or k not in obj:
            return MISSING
        obj = obj[k]
    return obj


def put(obj, path, value):
    keys = path.split('.')
    for k in keys[:-1]:
        obj = obj.setdefault(k, {})
    obj[keys[-1]] = value


def merge_step(data, write):
    import merge_duplicate_deals_batch as mdb
    known_ind = mdb.industries()
    known_themes = {t for d in data['deals'] for t in (d.get('themes') or [])}
    todo, errors = [], []
    for spec in MERGES:
        if (data.get('merged') or {}).get(spec['drop']) == spec['keep']:
            continue
        m = mdb.Merge(data, spec, known_ind, known_themes)
        m.check()
        for line in m.plan:
            print(line)
        errors += m.errors
        todo.append(m)
    if errors:
        raise SystemExit('ОТКАЗ слияния: %s' % '; '.join(errors))
    for m in todo:
        m.apply()
        print('  слито %s -> %s' % (m.drop_id, m.keep_id))
    if todo:
        mdb.strip_fixes({m.drop_id for m in todo}, write=write)
    return len(todo)


def edit_step(data):
    cards = {d['id']: d for d in data['deals']}
    done = 0
    for cid, field, old, new in EDITS:
        card = cards[cid]
        cur = get(card, field)
        if cur == new:
            continue
        assert cur == old, '%s %s: в базе %r, ожидали %r' % (cid, field, cur, old)
        put(card, field, new)
        done += 1
        print('  %s %s → %r' % (cid, field, str(new)[:70]))
    for cid, item in ADD_SRC:
        src = cards[cid].setdefault('src', [])
        if item[1] not in [s[1] for s in src if isinstance(s, list) and len(s) > 1]:
            src.append(item)
            done += 1
            print('  %s src += %s' % (cid, item[1]))
    return done


def side_files(gone, write):
    """Строки facts_discrepancies и признаки signals.json на слитые id."""
    for path, key in ((DISCREP, None), (SIGNALS, 'signals')):
        if not os.path.exists(path):
            continue
        raw = open(path, encoding='utf-8').read()
        store = json.loads(raw)
        rows = store[key] if key else store
        idf = 'deal_id' if key else 'id'
        kept = [r for r in rows if r.get(idf) not in gone]
        if len(kept) != len(rows):
            print('  %s: снять %d строк' % (os.path.basename(path), len(rows) - len(kept)))
            if write:
                if key:
                    store[key] = kept
                else:
                    store = kept
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(store, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))


def run(data, write):
    n = merge_step(data, write)
    n += edit_step(data)
    side_files({m['drop'] for m in MERGES}, write)
    return n


def main(argv):
    write = '--write' in argv
    data = json.load(open(DATA, encoding='utf-8'))
    n = run(copy.deepcopy(data), write=False)
    if not n:
        print('Уже применено.')
        return 0
    if not write:
        print('Сухой прогон: %d изменений. Запись — с ключом --write.' % n)
        return 0
    import mass_edit_guard
    raw = open(DATA, encoding='utf-8').read()     # перечитать прямо перед записью
    old = json.loads(raw)
    data = copy.deepcopy(old)
    run(data, write=True)
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
    print('Записано изменений: %d' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
