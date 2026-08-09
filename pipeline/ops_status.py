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
]


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


def render_quality(did='', left=0):
    """Качество: одна понятная фраза о сделанном плюс сколько осталось."""
    lines = ['🔧 <b>Компас · качество</b>', '']
    lines.append(did.strip() if did and did.strip() else 'Проверили платформу — всё в порядке, чинить нечего.')
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
    return render_quality(args.did, args.left), None


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
