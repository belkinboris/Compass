# -*- coding: utf-8 -*-
"""Отчёт рутины в консоль основателей — человеческим языком, а не жаргоном.

ЗАЧЕМ ВООБЩЕ. До 9 августа рутины писали в Telegram, только когда есть ЧТО
показать, — и «прогон был, ничего не нашлось» было неотличимо от «рутина
сломалась»: и то и другое выглядело молчанием. Так суточный приток простоял
несколько дней незамеченным. Теперь каждая рутина отчитывается в конце ЛЮБОГО
прогона, включая пустой.

ЗАЧЕМ ПЕРЕПИСАНО (в тот же день). Первая версия принимала готовую строку — и
рутины немедленно принесли в канал свою внутреннюю кухню: «G7: дочитана
карточка, 6 полей заполнено», «очередь решений пуста, 6 внутри 24ч тишины».
Партнёр такое читать не может: «G7» — наш код бэклога, «поля» — устройство
базы, «в тишине» — вообще не по-русски. Это тот же класс ошибки, что уже
записан в CLAUDE.md («пояснение объясняет смысл числа, а не устройство базы»),
только вылез в отчётах рутин.

КАК ЧИНИТСЯ. Рутина больше НЕ пишет текст — она передаёт цифры и факты, а
слова подбирает этот файл. Плюс `JARGON`: если во free-text описание работы
(единственное место, где рутина всё же пишет прозой) просочился внутренний
термин, отправка ОТКЛОНЯЕТСЯ с подсказкой, чем заменить. Проверка на себе —
в `_self_check()`.

Запуск (так его зовут рутины):
    python3 pipeline/ops_status.py приток --looked 1633 --found 32 --cards 6
    python3 pipeline/ops_status.py публикация --posted 3 --edited 1
    python3 pipeline/ops_status.py публикация --nothing --soon 6 --held 4
    python3 pipeline/ops_status.py качество --did "Дополнили карточку «Пеко»…" --left 57
    python3 pipeline/ops_status.py приток --broken "Источники не отвечают"
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import telegram_endpoint                                  # noqa: E402

# ВНУТРЕННЯЯ КУХНЯ, КОТОРОЙ НЕ МЕСТО В КОНСОЛИ. Слева — что писать нельзя,
# справа — чем сказать то же самое человеку. Список пополняется каждый раз,
# когда в канал прилетает очередная невнятица.
JARGON = [
    (r'\bG[1-9]\b', 'код нашего бэклога — скажите словами, что сделали'),
    (r'\bpending\b|предпросмотр', '«ждёт вашей проверки»'),
    (r'\bfrom_ingest\b|\breviewed\b|\beco\b|\blaw\b', 'название поля в базе — назовите факт, а не поле'),
    (r'полей\s+заполнено|поля\s+заполнены', '«перенесли N фактов из статьи»'),
    (r'очередь\s+решений', '«карточки, которые ждут вашей кнопки»'),
    (r'тишин\w+', '«выйдут сами, если не трогать»'),
    (r'\bдрафт\w*|\bпромоут\w*|\bмёрдж\w*|\bbulk\b', 'разработческий жаргон'),
    (r'дочитан\w+\s+карточк', '«дополнили карточку»'),
    # 9 августа владелец прочитал в консоли «восемь заводских и биржевых
    # сделок» и «показатели компаний и терминалов» и спросил, что это значит.
    # Ответа не было: таких категорий у нас нет. Партия из двенадцати
    # РАЗНОРОДНЫХ карточек (завод, приватизация, фонд, торговый комплекс)
    # не сводится к одному ярлыку, и попытка свести рождает выдумку.
    (r'заводск\w+\s+(и\s+\w+\s+)?сделк', 'такого типа сделок у нас нет — назовите компании по именам'),
    (r'биржев\w+\s+сделк', 'у нас есть «Продажа с торгов», а «биржевых сделок» нет'),
]

# ТИПЫ СДЕЛОК, КОТОРЫЕ У НАС ЕСТЬ. Всё остальное перед словом «сделка» —
# выдуманная категория: см. историю выше.
DEAL_TYPES = ('m&a', 'инвестиционн', 'инвестиц', 'ipo', 'торг', 'структурн',
              'финансирован')
# Слова, которые характеризуют сделку по величине или новизне, а не по типу, —
# они законны и категории не выдумывают.
SIZE_WORDS = ('крупн', 'нов', 'стар', 'свеж', 'мелк', 'небольш', 'закрыт',
              'объявленн', 'несостоявш', 'прошлогодн', 'недавн')
COUNTED_DEALS = re.compile(
    r'(?:\d+|дв[ае]|три|четыре|пять|шесть|семь|восемь|девять|десять|'
    r'одиннадцать|двенадцать)\s+((?:[а-яё]+(?:ых|их|ые|ие)\s+(?:и\s+)?){1,3})'
    r'(?:сделок|сделки|карточек|карточки)', re.I)


def find_invented_category(text):
    """«Восемь заводских и биржевых сделок» — категория, которой у нас нет.

    Признак узкий НАРОЧНО: ловим только попытку обобщить ПАРТИЮ одним
    прилагательным («N <каких-то> сделок»), потому что именно она и рождает
    выдумку — двенадцать разнородных карточек не сводятся к ярлыку. Обычные
    характеристики величины и новизны («восемь крупных сделок») проходят: они
    ничего не выдумывают.
    """
    m = COUNTED_DEALS.search(str(text or ''))
    if not m:
        return None
    words = [w for w in re.split(r'\s+|\bи\b', m.group(1)) if w.strip()]
    unknown = [w for w in words
               if not any(w.lower().startswith(t) for t in DEAL_TYPES + SIZE_WORDS)]
    if not unknown:
        return None
    return ('«%s» — такой категории сделок у нас нет. Партия из разных сделок '
            'не сводится к одному ярлыку: назовите две-три компании по именам, '
            'а про остальные скажите «и ещё N».' % m.group(0).strip())


def find_jargon(text):
    """Список (что нашли, чем заменить) — пусто, если текст человеческий."""
    found = []
    for pattern, hint in JARGON:
        m = re.search(pattern, str(text or ''), re.I)
        if m:
            found.append((m.group(0), hint))
    return found


def _plural(n, one, few, many):
    n = abs(int(n))
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def render_intake(looked=0, found=0, cards=0):
    """Приток: что просмотрели за сутки и что из этого вышло."""
    lines = ['🌅 <b>Компас · утренний обзор рынка</b>', '']
    if looked:
        lines.append('Просмотрели %d %s.' % (looked, _plural(looked, 'новость', 'новости', 'новостей')))
    if not cards:
        lines.append('Новых сделок сегодня нет — бывают тихие дни, это нормально.')
        return '\n'.join(lines)
    if found:
        lines.append('Похожих на сделки — %d.' % found)
    lines.append('')
    lines.append('📋 <b>%d %s ждут вашей проверки</b> — с кнопками, ниже в этой группе.'
                 % (cards, _plural(cards, 'карточка', 'карточки', 'карточек')))
    return '\n'.join(lines)


def render_publish(posted=0, edited=0, applied=0, soon=0, held=0, nothing=False):
    """Публикация: что вышло в канал и что ещё ждёт."""
    lines = []
    if nothing or not (posted or edited or applied):
        lines += ['😴 <b>Компас · публикация</b>', '', 'Сейчас публиковать нечего.']
    else:
        lines += ['📣 <b>Компас · публикация</b>', '']
        done = []
        if posted:
            done.append('опубликовали %d %s' % (posted, _plural(posted, 'сделку', 'сделки', 'сделок')))
        if edited:
            done.append('обновили %d %s' % (edited, _plural(edited, 'пост', 'поста', 'постов')))
        if applied:
            done.append('применили %d %s' % (applied, _plural(applied, 'ваше решение', 'ваших решения', 'ваших решений')))
        lines.append('Готово: %s.' % ', '.join(done))
    if soon or held:
        lines.append('')
        if soon:
            # Согласуется и существительное, и ГЛАГОЛ: «1 карточка выйдет»,
            # «6 карточек выйдут». Первая версия писала «1 карточка выйдут» —
            # поймано своим же тестом, а не глазами.
            lines.append('⏳ %d %s %s сами в ближайшие сутки, если не трогать'
                         % (soon, _plural(soon, 'карточка', 'карточки', 'карточек'),
                            _plural(soon, 'выйдет', 'выйдут', 'выйдут')))
        if held:
            lines.append('✋ %d %s вы придержали — %s вашего слова'
                         % (held, _plural(held, 'карточку', 'карточки', 'карточек'),
                            _plural(held, 'ждёт', 'ждут', 'ждут')))
    return '\n'.join(lines)


def short_name(title):
    """Из заголовка сделки — короткое узнаваемое имя для отчёта.

    Берём первое название в кавычках, иначе первые два слова с заглавной,
    иначе первые три слова. Ничего не сочиняем: имя приходит из базы.
    """
    t = re.sub(r'\s+', ' ', str(title or '')).strip()
    quoted = re.findall(r'[«"]([^»"]{2,40})[»"]', t)
    if quoted:
        return '«%s»' % quoted[0]
    caps = re.findall(r'(?-i:[А-ЯЁA-Z][\w.&-]+)', t)
    if caps:
        return ' '.join(caps[:2]) if len(caps) > 1 and len(caps[0]) < 5 else caps[0]
    return ' '.join(t.split()[:3])


def deal_names(ids, base=None):
    """Заголовки карточек по их id — из базы, а не из головы."""
    if base is None:
        path = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
        base = json.load(open(path, encoding='utf-8'))
    by_id = {d['id']: d for d in base.get('deals', [])}
    return [short_name(by_id[i].get('title')) for i in ids if i in by_id]


def render_quality(did='', left=0, ids=(), facts=0):
    """Качество: что именно дополнили — ИМЕНАМИ, а не ярлыком партии.

    ПОЧЕМУ ИМЕНАМИ. Пока рутина читала одну карточку за прогон, обобщать было
    нечего — её называли по имени. С переходом на партии из двенадцати
    РАЗНОРОДНЫХ сделок фраза «что сделал» стала требовать ярлыка на всех, и
    ярлык получался выдуманным: «восемь заводских и биржевых сделок»,
    «показатели компаний и терминалов». Владелец 9 августа спросил, что это
    значит, — и правильного ответа не было. Теперь скрипт строит первую фразу
    сам из заголовков карточек, а `did` описывает НАХОДКИ, где обобщение
    уместно и ничего не выдумывает («независимые оценки экспертов», «кто
    владел активом до сделки»).
    """
    lines = ['🔧 <b>Компас · качество</b>', '']
    names = deal_names(ids) if ids else []
    if names:
        head = 'Дополнили %d %s: %s' % (
            len(ids), _plural(len(ids), 'карточку', 'карточки', 'карточек'),
            ', '.join(names[:3]))
        if len(names) > 3:
            head += ' и ещё %d' % (len(names) - 3)
        if facts:
            head += '. Перенесли из статей %d %s, %s на сайте не было' % (
                facts, _plural(facts, 'факт', 'факта', 'фактов'),
                _plural(facts, 'которого', 'которых', 'которых'))
        lines.append(head + '.')
        if did and did.strip():
            lines.append('')
            lines.append(did.strip())
    else:
        lines.append(did.strip() if did and did.strip()
                     else 'Проверили платформу — всё в порядке, чинить нечего.')
    if left:
        lines.append('')
        lines.append('📚 Ещё не дополнены по источникам: %d %s'
                     % (left, _plural(left, 'карточка', 'карточки', 'карточек')))
    return '\n'.join(lines)


def render_broken(routine, why):
    return ('🚨 <b>Компас · сбой</b>\n\nНе сработало: %s.\n\n<i>%s</i>\n\n'
            'Платформа продолжает работать, но этот шаг сегодня не выполнен.'
            % (routine, why))


def queue_keyboard(soon=0, held=0):
    """Кнопки «показать, что там» — чтобы не идти искать руками."""
    row = []
    if soon:
        row.append({'text': '👀 Что скоро выйдет', 'callback_data': 'show:soon'})
    if held:
        row.append({'text': '✋ Что придержано', 'callback_data': 'show:held'})
    return {'inline_keyboard': [row]} if row else None


def post_status(client, token, chat, text, keyboard=None):
    """(отправлено?, причина отказа). Сеть недоступна — не бросаем: отчёт о
    прогоне не должен ронять сам прогон."""
    body = {'chat_id': chat, 'text': text, 'parse_mode': 'HTML',
            'disable_web_page_preview': True}
    if keyboard:
        body['reply_markup'] = keyboard
    try:
        r = client.post(telegram_endpoint.method_url(token, 'sendMessage'), json=body)
        data = r.json()
    except Exception as e:                                 # noqa: BLE001
        return False, '%s: %s' % (type(e).__name__, e)
    if data.get('ok'):
        return True, None
    return False, data.get('description') or str(data)


def build(args):
    """(текст, клавиатура) по разобранным аргументам."""
    if args.broken:
        return render_broken(args.routine, args.broken), None
    if args.routine == 'приток':
        return render_intake(args.looked, args.found, args.cards), None
    if args.routine == 'публикация':
        text = render_publish(args.posted, args.edited, args.applied,
                              args.soon, args.held, args.nothing)
        return text, queue_keyboard(args.soon, args.held)
    ids = [i.strip() for i in args.ids.split(',') if i.strip()]
    return render_quality(args.did, args.left, ids, args.facts), None


def main(argv):
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('routine', choices=['приток', 'публикация', 'качество'])
    p.add_argument('--looked', type=int, default=0)
    p.add_argument('--found', type=int, default=0)
    p.add_argument('--cards', type=int, default=0)
    p.add_argument('--posted', type=int, default=0)
    p.add_argument('--edited', type=int, default=0)
    p.add_argument('--applied', type=int, default=0)
    p.add_argument('--soon', type=int, default=0)
    p.add_argument('--held', type=int, default=0)
    p.add_argument('--nothing', action='store_true')
    p.add_argument('--did', default='')
    p.add_argument('--left', type=int, default=0)
    p.add_argument('--ids', default='',
                   help='id карточек партии через запятую — имена скрипт возьмёт из базы')
    p.add_argument('--facts', type=int, default=0,
                   help='сколько фактов перенесено из статей')
    p.add_argument('--broken', default='')
    try:
        args = p.parse_args(argv)
    except SystemExit:
        print(__doc__)
        return 1

    bad = find_jargon(args.did) + find_jargon(args.broken)
    if bad:
        print('НЕ ОТПРАВЛЕНО: в тексте внутренний жаргон, партнёр его не поймёт.')
        for word, hint in bad:
            print('   «%s» -> %s' % (word, hint))
        return 1
    invented = find_invented_category(args.did) or find_invented_category(args.broken)
    if invented:
        print('НЕ ОТПРАВЛЕНО: %s' % invented)
        return 1

    text, keyboard = build(args)
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat = os.environ.get('TELEGRAM_REVIEW_GROUP_ID')
    if not token or not chat:
        print('TELEGRAM_BOT_TOKEN/TELEGRAM_REVIEW_GROUP_ID не заданы — вот что ушло бы:')
        print(re.sub(r'<[^>]+>', '', text))
        return 1
    import httpx
    with httpx.Client(timeout=20) as client:
        ok, why = post_status(client, token, chat, text, keyboard)
    if not ok:
        print('Отчёт не ушёл (%s).' % why)
        return 1
    print('Отчёт отправлен в консоль.')
    return 0


def _self_check():
    """Правила проверяются на себе — иначе жаргон снова уедет в канал."""
    # Ровно те две фразы, которые владелец прислал как непонятные.
    assert find_jargon('G7 — дочитана карточка, 6 полей заполнено')
    assert find_jargon('очередь решений пуста, 6 внутри 24ч тишины')
    # Человеческий текст проходит.
    assert not find_jargon('Дополнили карточку «Родные поля» — перенесли 6 фактов из статьи.')
    # ВЫДУМАННАЯ КАТЕГОРИЯ ПАРТИИ. Владелец 9 августа прислал два вопроса:
    # «что значит „восемь заводских и биржевых сделок"» и «что значит
    # „показатели компаний и терминалов"». Ответа не было — таких категорий у
    # нас нет; их породила попытка свести двенадцать разнородных карточек к
    # одному ярлыку.
    assert find_jargon('Дополнили восемь заводских и биржевых сделок')
    assert find_invented_category('Дополнили восемь заводских и биржевых сделок')
    assert find_invented_category('шесть портовых и складских сделок')
    # А величина и наши настоящие типы сделок — проходят: они ничего не выдумывают.
    assert not find_invented_category('восемь крупных сделок')
    assert not find_invented_category('12 инвестиционных сделок')
    assert not find_invented_category('Дополнили двенадцать карточек')
    # Имена берутся из базы, а не из головы: короткое имя — из заголовка.
    assert short_name('«Росхим» может приобрести Восточный нефтехимический терминал') == '«Росхим»'
    assert short_name('ВЭБ.РФ объявила о приобретении ГТЛК') == 'ВЭБ.РФ'
    # Склонения, ради которых всё и затевалось.
    assert 'карточка' in render_publish(nothing=True, soon=1)
    assert 'карточки' in render_publish(nothing=True, soon=3)
    assert 'карточек' in render_publish(nothing=True, soon=6)
    # Пустой прогон обязан быть внятным, а не молчаливым.
    assert 'публиковать нечего' in render_publish(nothing=True).lower()
    assert 'тихие дни' in render_intake(looked=1633)
    # Кнопки появляются только там, где есть что показать.
    assert queue_keyboard(0, 0) is None
    assert queue_keyboard(6, 4)['inline_keyboard'][0][0]['callback_data'] == 'show:soon'
    print('Самопроверка отчётов пройдена.')


if __name__ == '__main__':
    if '--self-check' in sys.argv:
        _self_check()
        sys.exit(0)
    sys.exit(main(sys.argv[1:]))
