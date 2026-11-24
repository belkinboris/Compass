# -*- coding: utf-8 -*-
"""Карточка rosatom-mali (Росатом / литиевый проект Бугула, Мали): приемка 24 ноября
2026 нашла, что фраза о лицензии Moketi Mining SARL / Uranium One Group в
`eco.context` и `law.struct` (1) дублирует один факт в двух полях и (2) путает
направление передачи лицензии — и обе проверки подтверждают, что чинить
направление в тексте нельзя: факт не лежит ни в одном читаемом источнике карточки.

ЧТО БЫЛО. eco.context: «Права на Бугулу горное министерство Мали в июле 2024 года
разрешило передать Moketi Mining SARL из Uranium One Group.» law.struct: «Разрешение
на добычу на Бугуле с июля 2024 года принадлежит Moketi Mining SARL — дочерней
компании Uranium One Group, структуры Росатома.» Обе фразы говорят: лицензия у
Moketi Mining SARL, а Moketi Mining SARL — дочка Uranium One Group.

ПРОВЕРКА ПО ИСТОЧНИКАМ КАРТОЧКИ. `src` несет три адреса. ПРАЙМ (1prime.ru,
20261030/rosatom-874832259.html) — единственная статья о самой покупке; прочитан
целиком (WebFetch): Лихачев говорит о покупке малийской компании, но ни название
компании, ни Moketi Mining SARL, ни Uranium One Group, ни лицензию на Бугулу статья
не упоминает вовсе. Интерфакс (interfax.ru/business/1092728) — прочитан целиком;
дата публикации 29 мая 2026, статья пересказывает отчет АО «Атомэнергопром» за 2025
год о геологоразведке, тех же имен и лицензии в ней тоже нет. Neftegaz.ru — страница
рендерится JS (WebFetch вместо текста отдает закодированный gif-индикатор загрузки),
дословно непроверяема; это и есть ее заявленный статус в карточке приемки.
Значит фраза о Moketi Mining SARL/Uranium One Group не подтверждается НИ ОДНИМ
читаемым источником карточки — ни их дословным текстом, ни направлением передачи.

ПРОВЕРКА НЕЗАВИСИМЫМИ ИСТОЧНИКАМИ (не «ссылка вместо источника», а подтверждение,
что фраза фактически перепутана, а не просто неудачно сформулирована). Bloomberg Law
(news.bloomberglaw.com/mergers-and-acquisitions/russias-rosatom-acquires-license-for-mali-lithium-project)
и отраслевая пресса (Mining Weekly/Engineering News, «Bougouni lithium project mining
licence transfer completed») сходятся: малийская компания Moketi Mining SARL ДЕРЖАЛА
лицензию на Бугулу ДО июля 2024 года; в июле 2024 года правительство Мали одобрило
передачу лицензии ОТ Moketi Mining SARL К Uranium One Group — зарубежной урановой
структуре Росатома. То есть в обеих фразах карточки направление перепутано (после
июля 2024 лицензия у Uranium One Group, а не у Moketi Mining SARL) и отношение
компаний названо наоборот (Moketi Mining SARL — прежний самостоятельный держатель,
а не «дочка» Uranium One Group). Эта же проверка уже стоит в `accepted_notes.
no_profile.target` карточки (записана ранее и не меняется этой правкой) — там
направление названо верно; разойтись с собственной запиской — отдельный повод не
оставлять фразу как есть.

ПОЧЕМУ — СНЯТИЕ, А НЕ ПЕРЕФОРМУЛИРОВКА. Переписать фразу правильным направлением
значило бы внести факт, подтвержденный только недоступной(-ым) карточке источником
на английском, которого нет в `src`, а не исходным адресом карточки (Neftegaz.ru,
дословно не проверяемым). Правило CLAUDE.md «не подменять отсутствующие данные
правдоподобными; пустое поле честнее» — тот же случай: безопаснее снять факт,
который наши читаемые источники не несут и который в прежней форме был фактически
обратным, чем оставить его или переписать по источнику, не входящему в `src`.
eco.context и law.struct без этой фразы остаются полными и не противоречат ничему
— оставшийся текст подтвержден отдельно (ПРАЙМ — покупка и слова Лихачева;
Интерфакс и отчет «Атомэнергопрома» — геологоразведка).

ОДНОВРЕМЕННО, та же приемка: `eco.sum` — «Инвестиции не раскрывались» (нигде в базе
больше не встречается: 780 карточек несут стандартную форму «Не раскрыта», эта
одна — нет) заменено на стандартную форму; `src` переставлен — ПРАЙМ первым (пост
должен вести на статью о самой покупке, а не на отчет о геологоразведке).

Правка — разовым скриптом с assert на старое значение (review.py для «Не раскрыта»
в сумме не годится — его `sum_is_supported` ждет число; для `eco.context`/
`law.struct` его FIXES ждут цитату с диска, которой у Neftegaz.ru нет).

    python3 pipeline/fix_rosatom_mali_license_direction_2026_11_24.py [--write]

После записи карточка становится «stale» (accepted_hash не совпадет с отпечатком) —
нужна переприемка (accept_card.py).
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import pipeline.fact_edit_guard as fact_edit_guard  # noqa: E402
import pipeline.mass_edit_guard as mass_edit_guard  # noqa: E402
import review  # noqa: E402  (fix_fingerprint — отметить записи FIXES, обойденные этой правкой, поглощенными)

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
CID = 'rosatom-mali'

OLD_CONTEXT = (
    'Литиевый проект в малийском регионе Сикасо Россия и Мали ведут с марта 2023 года. Летом 2023 года '
    'Владимир Путин говорил, что дочерней компании Росатома принадлежат 75% активов проекта. Права на '
    'Бугулу горное министерство Мали в июле 2024 года разрешило передать Moketi Mining SARL из Uranium '
    'One Group.\n\nПо отчету АО «Атомэнергопром» за 2025 год, геологоразведка предварительно подтвердила '
    'потенциал участка. По словам Алексея Лихачева, первый этап изысканий удвоил запасы месторождения — '
    'до более чем 400 тыс. т литиевого концентрата. Строительство горно-обогатительного комбината в Мали '
    'Росатом намерен начать в 2028 году.')
NEW_CONTEXT = (
    'Литиевый проект в малийском регионе Сикасо Россия и Мали ведут с марта 2023 года. Летом 2023 года '
    'Владимир Путин говорил, что дочерней компании Росатома принадлежат 75% активов проекта.\n\nПо отчету '
    'АО «Атомэнергопром» за 2025 год, геологоразведка предварительно подтвердила потенциал участка. По '
    'словам Алексея Лихачева, первый этап изысканий удвоил запасы месторождения — до более чем 400 тыс. т '
    'литиевого концентрата. Строительство горно-обогатительного комбината в Мали Росатом намерен начать '
    'в 2028 году.')

OLD_STRUCT = (
    'Название купленной компании, ее прежних владельцев и долю Росатом не раскрыл. Разрешение на добычу '
    'на Бугуле с июля 2024 года принадлежит Moketi Mining SARL — дочерней компании Uranium One Group, '
    'структуры Росатома.')
NEW_STRUCT = 'Название купленной компании, ее прежних владельцев и долю Росатом не раскрыл.'

OLD_SUM = 'Инвестиции не раскрывались'
NEW_SUM = 'Не раскрыта'
PRIME_URL = 'https://1prime.ru/20261030/rosatom-874832259.html'
SUM_QUOTE = ('В "Росатоме" сообщили о приобретении малийской компании для проекта на месторождении Бугула, '
             'но не назвали ни ее имени, ни условий сделки — статья ПРАЙМ о покупке не называет сумму вовсе')

OLD_SRC = [['Интерфакс', 'https://www.interfax.ru/business/1092728'],
           ['Neftegaz.ru', 'https://neftegaz.ru/news/Geological-exploration/857026-mali-zhdet-geologov-iz-rossii'
                           '-dlya-razvedki-mestorozhdeniy-litiya-nefti-i-gaza/'],
           ['ПРАЙМ', PRIME_URL]]
NEW_SRC = [['ПРАЙМ', PRIME_URL],
           ['Интерфакс', 'https://www.interfax.ru/business/1092728'],
           ['Neftegaz.ru', 'https://neftegaz.ru/news/Geological-exploration/857026-mali-zhdet-geologov-iz-rossii'
                           '-dlya-razvedki-mestorozhdeniy-litiya-nefti-i-gaza/']]

NOTE = ('Приемка 24 ноября 2026: из eco.context и law.struct снята фраза о лицензии Moketi Mining SARL / '
        'Uranium One Group — она дублировала один факт в двух полях и несла его с перепутанным направлением '
        '(после июля 2024 лицензия на Бугулу у Uranium One Group, а не у Moketi Mining SARL, которая не '
        'дочка Uranium One Group, а прежний самостоятельный держатель — Bloomberg Law, Mining Weekly/'
        'Engineering News, «Bougouni lithium project mining licence transfer completed»; то же направление '
        'уже верно записано в accepted_notes.no_profile.target). Ни ПРАЙМ, ни Интерфакс (оба прочитаны '
        'целиком) этот факт не несут вовсе; Neftegaz.ru дословно не проверить (JS-рендер) — поэтому фраза '
        'снята, а не переписана по источнику, не входящему в src. eco.sum приведен к стандартной форме '
        '«Не раскрыта» (была единственной в базе формой «Инвестиции не раскрывались»); src переставлен — '
        'ПРАЙМ первым (единственная статья о самой покупке).')


def _card(data):
    return next(d for d in data['deals'] if d['id'] == CID)


def _absorb(card, field, old_value):
    """Прямая правка обошла review.py/proofread.py — таблица FIXES несет живую,
    не поглощенную запись на (CID, field) с тем же `new`, что было OLD_*
    (pipeline/ingest/fixes/reread_2026_11_12_m070.py). Без этой отметки
    test_no_duplicate_fix_for_one_field и test_review_table_is_applied_and_not_pending
    считают запись «живой, но не примененной» (review.already_applied). Возвращает
    True, если отметка была новой (посчитать как правку)."""
    fp = review.fix_fingerprint(old_value)
    marks = card.setdefault('proofread_absorbed', {}).setdefault(field, [])
    if fp in marks:
        return False
    marks.append(fp)
    return True


def _apply(data):
    c = _card(data)
    n = 0
    if c['eco'].get('context') == NEW_CONTEXT:
        n += _absorb(c, 'eco.context', OLD_CONTEXT)
    else:
        assert c['eco'].get('context') == OLD_CONTEXT, c['eco'].get('context')
        c['eco']['context'] = NEW_CONTEXT
        _absorb(c, 'eco.context', OLD_CONTEXT)
        n += 1
    if c['law'].get('struct') == NEW_STRUCT:
        n += _absorb(c, 'law.struct', OLD_STRUCT)
    else:
        assert c['law'].get('struct') == OLD_STRUCT, c['law'].get('struct')
        c['law']['struct'] = NEW_STRUCT
        _absorb(c, 'law.struct', OLD_STRUCT)
        n += 1
    if c['eco'].get('sum') != NEW_SUM:
        assert c['eco'].get('sum') == OLD_SUM, c['eco'].get('sum')
        c['eco']['sum'] = NEW_SUM
        fact_edit_guard.log(c, 'eco.sum', NEW_SUM, SUM_QUOTE, PRIME_URL, 'accept_card_rosatom_mali', '2026-11-24')
        n += 1
    if [s[0] for s in c['src']] != [s[0] for s in NEW_SRC]:
        assert c['src'] == OLD_SRC, c['src']
        c['src'] = NEW_SRC
        n += 1
    if NOTE not in str(c.get('notes') or ''):
        c['notes'] = (str(c.get('notes') or '').rstrip() + ('\n\n' if c.get('notes') else '') + NOTE).strip()
        n += 1
    return n


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    old, data = json.loads(raw), json.loads(raw)
    n = _apply(data)
    if not n:
        print('Уже применено.')
        return 0
    mass_edit_guard.check(old, data)
    print('%s: %d правок (eco.context, law.struct, eco.sum, src).' % (CID, n))
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    _apply(fresh)
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
