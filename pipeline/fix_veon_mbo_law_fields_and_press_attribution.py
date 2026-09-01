# -*- coding: utf-8 -*-
"""Карточка MBO «ВымпелКома» (g64a94e27) по замечаниям владельца 31 августа 2026 —
и класс «рассказ от имени газеты» по всей базе.

Что чинит:
1. `law.struct` у g64a94e27 описывал не структуру сделки, а расчёты по
   еврооблигациям («будто бы это для вкладки экономист, тут ничего
   юридического нет») — факт переносится в `eco.fin` нашим текстом, поле
   «Структура» очищается.
2. `law.terms` там же цитировал газету от нашего имени: «Сделка, как и
   предполагал «Ъ» 6 октября, не предусматривает … и «означает полный уход
   Veon с российского рынка»». Владелец: «Нельзя цитату выдавать за наш
   текст. Надо просто написать наш текст». Переписано своими словами.
3. Консультанты той же карточки: АЛРУД стоял дважды (кириллицей и
   латиницей, из двух прогонов обогащения), роли — то в поле роли, то в
   заметке. Оставлен один АЛРУД, роли записаны единообразно со стороной.
   То же у gc3ab0c7d («Арнест»/Avon): Baker McKenzie и Melling, Voitishkin
   & Partners (ex-Baker McKenzie) — одна фирма, российский офис Baker
   McKenzie с 2022 года работает под вторым именем; для сделки 2026 года
   верно второе.
4. Класс по всей базе: обороты «как писал Коммерсантъ», «, пишет РБК»,
   «Как сообщает Интерфакс со ссылкой на …,» внутри текстов eco/law
   («и это везде править надо»). Замер 31 августа: 40 полей. Источник и
   так стоит в `src`; оборот снимается механически по узким правилам ниже,
   сам факт не трогается. Правила проверены на себе: `assert` на примерах.
   Обороты «по данным ЕГРЮЛ/отчётности/аналитика» — НЕ этот класс (это
   честная атрибуция числа, а не пересказ газеты), их не трогаем.

Запуск:
    python3 pipeline/fix_veon_mbo_law_fields_and_press_attribution.py          # сухой прогон с diff
    python3 pipeline/fix_veon_mbo_law_fields_and_press_attribution.py --write
"""
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'

PRESS = (r"(?:«?Ъ»?|«?Коммерсант[ъа-яё]*»?|РБК|«?Ведомост[а-яё]*»?|Интерфакс[а-яё]*|ТАСС|Forbes|«?Известия[а-яё]*»?|"
         r"Reuters|Bloomberg|Financial Times|The Bell|Frank Media|Frank\s*RG|CNews|TAdviser|vc\.ru|Vademecum|"
         r"РИА\s*Новости|«?Газета\.ru»?|«?Фонтанк[а-яё]*»?|«?Деловой Петербург»?|«?ДП»?|AdIndex|Shopper'?s|«?Фармацевтический вестник»?)")
VERB = r"(?:сообщает|сообщал[а-яё]*|писал[а-яё]*|пишет|отмечал[а-яё]*|отмечает|предполагал[а-яё]*|уточнял[а-яё]*|уточняет|указывал[а-яё]*|указывает|подтверждал[а-яё]*|ожидал[а-яё]*|напоминал[а-яё]*|напоминает)"
TAIL = r"(?:\s+со\s+ссылкой\s+на\s+[^,.;]{2,80})?(?:\s+в\s+[а-яё]+\s+\d{4}\s*(?:г\.|года)?)?(?:\s+\d{1,2}\s+[а-яё]+(?:\s+\d{4}\s*(?:г\.|года)?)?)?"

R_LEAD = re.compile(r"(?:^|(?<=[.;!?]\s))Как\s+(?:и\s+)?" + VERB + r"\s+" + PRESS + TAIL + r",\s*(\S)")
R_MID = re.compile(r",\s*как\s+(?:и\s+)?" + VERB + r"\s+" + PRESS + TAIL + r",\s*")
R_TAIL = re.compile(r",\s*(?:об\s+этом\s+)?" + VERB + r"\s+" + PRESS + TAIL + r"(?=[.;]|$)")
R_HEAD_CHTO = re.compile(r"(?:^|(?<=[.;!?]\s))" + PRESS + r"\s+" + VERB + r",?\s+что\s+(\S)")


def strip_press(text: str) -> str:
    t = text
    t = R_MID.sub(" ", t)
    t = R_TAIL.sub("", t)
    t = R_LEAD.sub(lambda m: m.group(1).upper(), t)
    t = R_HEAD_CHTO.sub(lambda m: m.group(1).upper(), t)
    if t == text:
        return text
    # Только пробелы: в многострочных полях переносы строк — часть текста.
    t = re.sub(r"[ \t]{2,}", " ", t).replace(" ,", ",").replace(" .", ".").strip()
    return t


# Правила проверены на себе — на фразах, которые видел владелец, и на тех, что трогать нельзя.
assert strip_press("Сделка, как и предполагал «Ъ» 6 октября, не предусматривает соглашений.") == \
    "Сделка не предусматривает соглашений."
assert strip_press("Как сообщает Интерфакс со ссылкой на портал ГИС «Торги», стартовый платеж составлял 1 млрд.") == \
    "Стартовый платеж составлял 1 млрд."
assert strip_press("Сумма сделки могла составить до 5 млрд рублей, пишет Forbes. Дальше текст.") == \
    "Сумма сделки могла составить до 5 млрд рублей. Дальше текст."
assert strip_press("Получил 12% в капитале, об этом сообщал РБК. Затем купил ещё.") == \
    "Получил 12% в капитале. Затем купил ещё."
assert strip_press("По данным ЕГРЮЛ, смена собственника зафиксирована в марте.") == \
    "По данным ЕГРЮЛ, смена собственника зафиксирована в марте."          # честная атрибуция числа — не трогаем
assert strip_press("О том, что VK ведет переговоры, «Ъ» сообщал в ноябре 2023 года.") == \
    "О том, что VK ведет переговоры, «Ъ» сообщал в ноябре 2023 года."      # факт о хронологии — не трогаем

VEON = 'g64a94e27'
ARNEST = 'gc3ab0c7d'
FIELDS = [('eco', k) for k in ('sum', 'share', 'val', 'target_fin', 'fin', 'finadv', 'rationale', 'context')] + \
         [('law', k) for k in ('struct', 'appr', 'terms')]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    # --- 1–3. VEON ---
    v = by_id[VEON]
    assert v['law']['struct'].startswith('«Вымпелком» выкупает еврооблигации Veon'), v['law']['struct']
    assert v['law']['terms'].startswith('Сделка, как и предполагал «Ъ»'), v['law']['terms']
    assert v['eco']['fin'].startswith('ВымпелКом погасил путём выкупа еврооблигаций VEON'), v['eco']['fin']
    assert [a[1] for a in v['law']['adv']] == ['LEVEL Legal Services', 'АЛРУД', 'ALRUD', 'Aspring Capital'], v['law']['adv']
    v['eco']['fin'] = ('ВымпелКом погасил путём выкупа еврооблигаций VEON у российских держателей (выкуп проходил '
                       'с февраля по сентябрь 2023 г., выкуплено более 96% бондов); взамен держатели получили '
                       'замещающие облигации самого «Вымпелкома» на сопоставимую сумму с более длительным сроком погашения.')
    v['law']['struct'] = '—'
    v['law']['terms'] = 'Сделка не предусматривает соглашений об обратном выкупе и означает полный уход Veon с российского рынка.'
    aspring = v['law']['adv'][3]
    v['law']['adv'] = [
        ['Юридический консультант покупателя (топ-менеджмент ВымпелКома)', 'LEVEL Legal Services', ''],
        ['Юридический консультант продавца (холдинг VEON)', 'АЛРУД', ''],
        ['Финансовый консультант продавца (холдинг VEON)', 'Aspring Capital', aspring[2]],
    ]
    print('VEON: struct → —, terms переписан, fin дополнен, консультантов 4 → 3')

    # --- 3. Арнест/Avon: одна фирма под двумя именами ---
    a = by_id[ARNEST]
    names = [x[1] for x in a['law']['adv']]
    assert names == ['Baker McKenzie', 'Melling, Voitishkin & Partners',
                     'Меллинг, Войтишкин и Партнеры (ex-Baker McKenzie)', 'Althaus'], names
    keep = [a['law']['adv'][1], a['law']['adv'][3]]
    keep[0] = [keep[0][0], 'Melling, Voitishkin & Partners (бывший российский офис Baker McKenzie)', keep[0][2]]
    a['law']['adv'] = keep
    print('Арнест/Avon: консультантов 4 → 2 (Baker McKenzie и Меллинг… — одна фирма)')

    # --- 4. класс «рассказ от имени газеты» ---
    # gecf3eca5 eco.val: после снятия оборота осталась бы голая цитата собеседника
    # газеты и «по оценкам собеседников газеты» без самой газеты — это чтение, не механика.
    SKIP = {('gecf3eca5', 'eco', 'val')}
    changed = 0
    for d in data['deals']:
        for scope, key in FIELDS:
            if (d['id'], scope, key) in SKIP:
                continue
            obj = d.get(scope) or {}
            val = obj.get(key)
            if not isinstance(val, str) or not val.strip():
                continue
            new = strip_press(val)
            if new != val:
                changed += 1
                print(f'\n[{d["id"]}] {scope}.{key}\n  - {val}\n  + {new}')
                obj[key] = new
    print(f'\nполей с оборотом «как писал …» переписано: {changed}')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('ЗАПИСАНО в', PATH)


if __name__ == '__main__':
    main(write='--write' in sys.argv)
