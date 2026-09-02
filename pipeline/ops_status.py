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
    python3 pipeline/ops_status.py вычитка --proofread 58 --refused 3 --left 1334 --ids g1,g2,g3
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
    # Только словоформы «тишина/тишины/тишине/тишину/тишиной» — не
    # `\w+` без границы: он совпадал внутри имени сделки («ТВК
    # «Тишинка»», «Тишинки», «Тишинской площади») и 23 августа 2026
    # отклонил честный отчёт о карточке Capital Group. Тот же класс
    # дефекта, что уже записан в CLAUDE.md («ствол словаря без границы
    # слова ловится внутри чужого слова»), только здесь — в отчётах
    # рутин, а не в разборе притока.
    (r'\bтишин(?:а|е|ы|у|ой)\b', '«выйдут сами, если не трогать»'),
    (r'\bдрафт\w*|\bпромоут\w*|\bмёрдж\w*|\bbulk\b', 'разработческий жаргон'),
    (r'дочитан\w+\s+карточк', '«дополнили карточку»'),
    # 9 августа владелец прочитал в консоли «восемь заводских и биржевых
    # сделок» и «показатели компаний и терминалов» и спросил, что это значит.
    # Ответа не было: таких категорий у нас нет. Партия из двенадцати
    # РАЗНОРОДНЫХ карточек (завод, приватизация, фонд, торговый комплекс)
    # не сводится к одному ярлыку, и попытка свести рождает выдумку.
    # «сделк\w*» не совпадает с «сделок» — там «о» перед «к» (сдел-О-к, не
    # сдел-к), а не суффикс после общего «сделк»; тот же класс дефекта, что
    # уже записан в CLAUDE.md про стемы без учёта конкретной словоформы.
    # Оба варианта — явно, а не понадеявшись на общий стем.
    (r'заводск\w+\s+(и\s+\w+\s+)?(?:сделок|сделк\w*)', 'такого типа сделок у нас нет — назовите компании по именам'),
    (r'биржев\w+\s+(?:сделок|сделк\w*)', 'у нас есть «Продажа с торгов», а «биржевых сделок» нет'),
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


def render_intake(looked=0, found=0, cards=0, screened=0):
    """Приток: что просмотрели за сутки и что из этого вышло.

    `screened` — сколько сомнительного сырья отсеяно автоматически ДО
    консоли (шаг D, `raw_screen.py --drop`/`--enrich`): владелец 21 августа
    жаловался на поток мусора вроде свадебных заметок в «сомнительных» —
    печатается ВСЕГДА, включая ноль, чтобы «отсеивали и просто нечего было»
    и «шаг не сработал» не выглядели одинаково молчанием."""
    lines = ['🌅 <b>Компас · утренний обзор рынка</b>', '']
    if looked:
        lines.append('Просмотрели %d %s.' % (looked, _plural(looked, 'новость', 'новости', 'новостей')))
    lines.append('Отсеяли как явный мусор ещё до консоли — %d.' % screened)
    if not cards:
        lines.append('Новых сделок сегодня нет — бывают тихие дни, это нормально.')
        return '\n'.join(lines)
    if found:
        lines.append('Похожих на сделки — %d.' % found)
    lines.append('')
    lines.append('📋 <b>%d %s ждут вашей проверки</b> — с кнопками, ниже в этой группе.'
                 % (cards, _plural(cards, 'карточка', 'карточки', 'карточек')))
    return '\n'.join(lines)


def render_publish(posted=0, edited=0, applied=0, soon=0, held=0, unread=0, nothing=False):
    """Публикация: что вышло в канал и что ещё ждёт.

    `soon` и `unread` — РАЗНЫЕ причины ждать, и путать их нельзя: `soon` —
    карточка уже прочитана против источника, тишина через сутки её опубликует
    сама; `unread` — карточку ещё никто не сверил со статьёй, и по молчанию
    она не выйдет НИКОГДА, сколько бы часов ни прошло (защита от каркасных
    дефектов черновика, approve.py/`plan_actions`). До 18 августа обе группы
    считались одним числом «soon» — и владелец час за часом получал «карточка
    выйдет сама», хотя она была не прочитана и не могла выйти: «Ленобласть»/
    «М.видео» простояли так больше суток без единого изменения в отчёте.
    """
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
    if soon or held or unread:
        lines.append('')
        if soon:
            # Согласуется и существительное, и ГЛАГОЛ: «1 карточка выйдет»,
            # «6 карточек выйдут». Первая версия писала «1 карточка выйдут» —
            # поймано своим же тестом, а не глазами.
            lines.append('⏳ %d %s %s сами в ближайшие сутки, если не трогать'
                         % (soon, _plural(soon, 'карточка', 'карточки', 'карточек'),
                            _plural(soon, 'выйдет', 'выйдут', 'выйдут')))
        if unread:
            lines.append('📖 %d %s ждут прочтения — сами не выйдут, пока их не сверят со статьёй'
                         % (unread, _plural(unread, 'карточка', 'карточки', 'карточек')))
        if held:
            lines.append('✋ %d %s вы придержали — %s вашего слова'
                         % (held, _plural(held, 'карточку', 'карточки', 'карточек'),
                            _plural(held, 'ждёт', 'ждут', 'ждут')))
    return '\n'.join(lines)


def _trim(s, limit=45):
    """Обрезать по границе слова, не разрубая слово и не оставляя повисшую
    открывающую скобку — профили компаний нередко несут пояснение в скобках
    («CanPack Group, Inc. (владелец активов, американская компания)»), и
    обрезка ровно посередине такого пояснения выглядит сломанной."""
    s = str(s or '').strip()
    if len(s) <= limit:
        return s
    cut = s[:limit].rsplit(' ', 1)[0]
    if '(' in cut and ')' not in cut:
        cut = cut[:cut.rindex('(')].rstrip()
    return cut


def short_name(deal, companies=None):
    """Короткое узнаваемое имя сделки для отчёта — по СТРУКТУРНЫМ полям, а
    не по первому попавшемуся капитализированному слову заголовка.

    ПОЧЕМУ ПЕРЕПИСАНО. В русском предложении с заглавной буквы начинается
    ЛЮБОЕ первое слово, а не только имя собственное. Прежняя версия брала
    первое слово заголовка с заглавной буквы как «имя» — и получала
    «Продажа», «Слияние», «Российские», «Государственный» у трёх десятков
    заголовков, начинающихся с описания типа сделки, а не со стороны или
    предмета («Продажа Veeam Software фонду Insight Partners…», «Слияние
    Whoosh и МТС Юрент…»). Владелец 16 августа прислал два таких отчёта и
    назвал это «безумными косяками».

    Порядок источников — от самого надёжного к самому слабому:
    1. название в кавычках из заголовка (почти всегда точное и короткое);
    2. профиль предмета сделки (`target`) или его текст (`asset`);
    3. профиль покупателя (`buyer`) или его текст (`buyer_name`);
    4. продавец текстом (`seller`);
    5. первые три слова заголовка — честно урезанный заголовок, а не
       выдуманное «имя», для редких карточек без единого структурного поля
       (кураторские записи).
    Ничего не сочиняем: каждый источник — то, что уже стоит в базе фактом.
    """
    companies = companies or {}
    title = re.sub(r'\s+', ' ', str(deal.get('title') or '')).strip()
    quoted = re.findall(r'[«"]([^»"]{2,40})[»"]', title)
    if quoted:
        return '«%s»' % quoted[0]
    target = companies.get(deal.get('target') or '', {}).get('name')
    if target:
        return _trim(target)
    if deal.get('asset'):
        return _trim(deal['asset'])
    buyer = companies.get(deal.get('buyer') or '', {}).get('name')
    if buyer:
        return _trim(buyer)
    if deal.get('buyer_name'):
        return _trim(deal['buyer_name'])
    if deal.get('seller'):
        return _trim(deal['seller'])
    return ' '.join(title.split()[:3]) if title else '(без названия)'


def load_base():
    path = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
    return json.load(open(path, encoding='utf-8'))


def deal_names(ids, base=None):
    """Короткие имена карточек по их id — из базы, а не из головы."""
    if base is None:
        base = load_base()
    by_id = {d['id']: d for d in base.get('deals', [])}
    companies = base.get('companies', {})
    return [short_name(by_id[i], companies) for i in ids if i in by_id]


def _esc(text):
    return (str(text).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;'))


def deal_links(ids, base=None):
    """Имена карточек как ссылки на сами карточки — просьба владельца
    21 августа: из отчёта «дополнили X» должно быть видно, ЧТО именно
    дополнили, в один клик, а не поиском по сайту."""
    if base is None:
        base = load_base()
    by_id = {d['id']: d for d in base.get('deals', [])}
    companies = base.get('companies', {})
    site = os.environ.get('APP_BASE_URL', 'https://projectcompass.ru').rstrip('/')
    return ['<a href="%s/#/deal/%s">%s</a>'
            % (site, i, _esc(short_name(by_id[i], companies)))
            for i in ids if i in by_id]


def reading_queues(base=None, today=None):
    """(первый проход, недельная, месячная) — размеры трёх очередей
    дочитывания, посчитанные ЗДЕСЬ, а не переданные рутиной.

    Просьба владельца 21 августа: отчёт «дополнили 3 карточки» не
    отвечал на вопрос «а сколько ещё осталось». Рутина передавала
    `--left` только по уровню, по которому работала, — закрыла дневной в
    ноль, и строка исчезала, хотя недельная и месячная очереди не пусты.
    Число, которое печатается каждый раз, надёжнее числа, которое надо
    не забыть передать (тот же принцип, что имена карточек из базы, а не
    из головы). Формулы — дословно из REVISION_BRIEF.md («Три уровня
    очереди»)."""
    from datetime import date
    if base is None:
        base = load_base()
    if today is None:
        today = date.today()

    def age_days(c):
        try:
            y, m, d = map(int, str(c.get('added', '')).split('-'))
            return (today - date(y, m, d)).days
        except Exception:
            return None

    deals = base.get('deals', [])
    day = sum(1 for c in deals
              if c.get('reviewed') and not c.get('deep_researched')
              and (age_days(c) or 0) >= 1)
    week = sum(1 for c in deals
               if c.get('deep_researched') and not c.get('weekly_researched')
               and (age_days(c) or 0) >= 7)
    month = sum(1 for c in deals
                if c.get('weekly_researched') and not c.get('followup_researched')
                and (age_days(c) or 0) >= 30)
    return day, week, month


def render_quality(did='', left=0, ids=(), facts=0, base=None, fns_budget=''):
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
    if base is None:
        try:
            base = load_base()
        except Exception:
            base = None
    names = deal_links(ids, base) if ids and base else (deal_names(ids) if ids else [])
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
    # Остаток очередей считает сам скрипт и печатает ВСЕГДА — «закрыли
    # уровень» без общей картины читалось как «всё готово», хотя две
    # другие очереди не пусты (замечание владельца 21 августа).
    if base:
        day, week, month = reading_queues(base)
        lines.append('')
        if day or week or month:
            parts = []
            if day:
                parts.append('%d — первое полное чтение источников' % day)
            if week:
                parts.append('%d — недельная сверка, что вышло нового' % week)
            if month:
                # Не «837 постов за месяц» — владелец 22 августа прочитал
                # именно так. Это старые карточки (обычно давно в базе, не
                # вышедшие недавно), у которых уже была первая и недельная
                # проверка, и раз в месяц им полагается лёгкая сверка: не
                # изменилось ли что-то с тех пор (сделка закрылась, сорвалась,
                # вышли новые цифры). Число выросло разом, когда опустела
                # недельная очередь, — не потому что за месяц вышло 837 постов.
                parts.append('%d — повторная сверка старых карточек на новые факты' % month)
            lines.append('📚 Ещё в очереди на проверку: %s.' % '; '.join(parts))
        else:
            lines.append('📚 Все карточки проверены по своим срокам — очередь пуста.')
    elif left:
        lines.append('')
        lines.append('📚 Ещё не дополнены по источникам: %d %s'
                     % (left, _plural(left, 'карточка', 'карточки', 'карточек')))
    # Строку остатка квоты ФНС печатаем, только если рутина сегодня реально
    # ходила в API-ФНС и передала готовую строку (format_stat_summary из
    # fns_client.py) — ops_status.py сам живых запросов не делает, чтобы
    # отчёт не превращался в источник побочных трат.
    if fns_budget:
        lines.append('')
        lines.append('💳 %s' % fns_budget)
    return '\n'.join(lines)


def render_proofread(done=0, refused=0, left=0, ids=(), base=None):
    """Вычитка (2 сентября 2026): сколько карточек переписано понятным языком.

    Владельцу важно одно обещание — «факты, цифры и имена не менялись»: это
    не вежливая фраза, а то, что proofread.py проверяет на каждой правке, и
    отчёт повторяет его каждый раз, чтобы партнёр знал, ЧТО именно делает
    рутина с базой. Отказы — не тревога, а норма: правка, не прошедшая
    проверку, просто не записана, текст остался прежним."""
    lines = ['✍️ <b>Компас · вычитка</b>', '']
    if base is None:
        try:
            base = load_base()
        except Exception:
            base = None
    names = deal_links(ids, base) if ids and base else (deal_names(ids) if ids else [])
    if done:
        head = 'Переписали понятным языком %d %s' % (
            done, _plural(done, 'карточку', 'карточки', 'карточек'))
        if names:
            head += ': ' + ', '.join(names[:3])
            if len(names) > 3:
                head += ' и ещё %d' % (len(names) - 3)
        lines.append(head + '. Факты, цифры и имена не менялись — только язык.')
    else:
        lines.append('За этот час вычитать ничего не удалось.')
    if refused:
        lines.append('')
        lines.append('%d %s не %s проверку и не %s — тексты этих полей остались как были.' % (
            refused, _plural(refused, 'правка', 'правки', 'правок'),
            _plural(refused, 'прошла', 'прошли', 'прошли'),
            _plural(refused, 'записана', 'записаны', 'записаны')))
    lines.append('')
    if left:
        lines.append('📚 Ещё не вычитаны: %d %s.'
                     % (left, _plural(left, 'карточка', 'карточки', 'карточек')))
    else:
        lines.append('📚 Все карточки вычитаны — очередь пуста.')
    return '\n'.join(lines)


def render_broken(routine, why):
    return ('🚨 <b>Компас · сбой</b>\n\nНе сработало: %s.\n\n<i>%s</i>\n\n'
            'Платформа продолжает работать, но этот шаг сегодня не выполнен.'
            % (routine, why))


def queue_keyboard(soon=0, held=0, unread=0):
    """Кнопки «показать, что там» — чтобы не идти искать руками."""
    row = []
    if soon:
        row.append({'text': '👀 Что скоро выйдет', 'callback_data': 'show:soon'})
    if unread:
        row.append({'text': '📖 Что ждёт прочтения', 'callback_data': 'show:unread'})
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
        return render_intake(args.looked, args.found, args.cards, args.screened), None
    if args.routine == 'публикация':
        text = render_publish(args.posted, args.edited, args.applied,
                              args.soon, args.held, args.unread, args.nothing)
        return text, queue_keyboard(args.soon, args.held, args.unread)
    ids = [i.strip() for i in args.ids.split(',') if i.strip()]
    if args.routine == 'вычитка':
        return render_proofread(args.proofread, args.refused, args.left, ids), None
    return render_quality(args.did, args.left, ids, args.facts, fns_budget=args.fns_budget), None


def main(argv):
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('routine', choices=['приток', 'публикация', 'качество', 'вычитка'])
    p.add_argument('--proofread', type=int, default=0,
                   help='вычитка: сколько карточек переписано и получило штамп proofread')
    p.add_argument('--refused', type=int, default=0,
                   help='вычитка: сколько правок не прошли проверку proofread.py')
    p.add_argument('--looked', type=int, default=0)
    p.add_argument('--found', type=int, default=0)
    p.add_argument('--cards', type=int, default=0)
    p.add_argument('--screened', type=int, default=0,
                   help='сомнительного сырья отсеяно автоматически (raw_screen.py) до консоли')
    p.add_argument('--posted', type=int, default=0)
    p.add_argument('--edited', type=int, default=0)
    p.add_argument('--applied', type=int, default=0)
    p.add_argument('--soon', type=int, default=0)
    p.add_argument('--held', type=int, default=0)
    p.add_argument('--unread', type=int, default=0,
                   help='ждут прочтения против источника — не выйдут по молчанию')
    p.add_argument('--nothing', action='store_true')
    p.add_argument('--did', default='')
    p.add_argument('--left', type=int, default=0)
    p.add_argument('--ids', default='',
                   help='id карточек партии через запятую — имена скрипт возьмёт из базы')
    p.add_argument('--facts', type=int, default=0,
                   help='сколько фактов перенесено из статей')
    p.add_argument('--fns-budget', default='',
                   help='готовая строка format_stat_summary() из fns_client.py — только если '
                        'рутина сегодня реально ходила в API-ФНС; сам ops_status.py в API не ходит')
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
    # Имена берутся из базы, а не из головы. Название в кавычках — точнее
    # всего, берётся первым, даже когда структурных полей тоже хватает.
    assert short_name({'title': '«Росхим» может приобрести Восточный нефтехимический терминал',
                       'target': 'x'}, {'x': {'name': 'АО «Росхим»'}}) == '«Росхим»'
    # ГЛАВНАЯ ЗАЩИТА ЭТОЙ ПРАВКИ: заголовок начинается с описания ТИПА
    # сделки («Продажа», «Слияние»), а не со стороны — старая версия взяла
    # бы именно это слово с заглавной. Профиль предмета сделки перебивает
    # такое заглавное слово и даёт настоящее имя.
    assert short_name({'title': 'Продажа Veeam Software фонду Insight Partners за $5 млрд',
                       'target': 'v'}, {'v': {'name': 'Veeam Software'}}) == 'Veeam Software'
    assert short_name({'title': 'Слияние Whoosh и МТС Юрент (ЮрентБайк.ру)'}) \
        != 'Слияние'
    assert short_name({'title': 'Российские активы CanPack переданы во временное управление'}) \
        != 'Российские'
    # Ни кавычек, ни структурных полей — честно урезанный заголовок, а не
    # выдуманное «имя» по первой заглавной букве.
    assert short_name({'title': 'ВЭБ.РФ объявила о приобретении ГТЛК'}) == 'ВЭБ.РФ объявила о'
    # Склонения, ради которых всё и затевалось.
    assert 'карточка' in render_publish(nothing=True, soon=1)
    assert 'карточки' in render_publish(nothing=True, soon=3)
    assert 'карточек' in render_publish(nothing=True, soon=6)
    # Пустой прогон обязан быть внятным, а не молчаливым.
    assert 'публиковать нечего' in render_publish(nothing=True).lower()
    assert 'тихие дни' in render_intake(looked=1633)
    # Отсев сырья (раздел D) печатается даже нулём — иначе «отсеивать
    # нечего» и «шаг отсева не запускался» снова неотличимы в отчёте.
    assert 'Отсеяли' in render_intake(looked=100, screened=0)
    assert '7' in render_intake(looked=100, screened=7)
    # Кнопки появляются только там, где есть что показать.
    assert queue_keyboard(0, 0) is None
    assert queue_keyboard(6, 4)['inline_keyboard'][0][0]['callback_data'] == 'show:soon'
    # «Скоро выйдет» и «ждёт прочтения» — РАЗНЫЕ утверждения, путать их
    # нельзя (18 августа так и застряли «Ленобласть»/«М.видео»): у карточки,
    # которую ещё не прочитали, текст не должен обещать, что она выйдет сама.
    unread_text = render_publish(nothing=True, unread=2)
    assert 'выйдут сами' not in unread_text and 'ждут прочтения' in unread_text
    assert queue_keyboard(0, 0, 3)['inline_keyboard'][0][0]['callback_data'] == 'show:unread'
    # Вычитка: обещание «факты не менялись» — в каждом отчёте, отказы названы
    # по-человечески, пустой час не выглядит как молчание.
    text = render_proofread(58, 3, 1334, base={'deals': []})
    assert '58 карточек' in text and 'не менялись' in text and '3 правки не прошли' in text
    assert '1334' in text and not find_jargon(text)
    assert 'ничего не удалось' in render_proofread(0, 0, 10, base={'deals': []})
    assert 'очередь пуста' in render_proofread(5, 0, 0, base={'deals': []})
    print('Самопроверка отчётов пройдена.')


if __name__ == '__main__':
    if '--self-check' in sys.argv:
        _self_check()
        sys.exit(0)
    sys.exit(main(sys.argv[1:]))
