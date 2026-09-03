# -*- coding: utf-8 -*-
"""Вычитка карточек: применить редакторские правки, не дав им изменить факты.

ЧТО ЧИНИТ. Просьба владельца 2 сентября 2026: тексты карточек должны читаться
как грамотный, понятный, человеческий русский язык — без пересказа «по
информации от Ъ», без дословных цитат из статей, без канцелярита, одинаково
на всех карточках. Главное условие — «правки не меняют суть написанного и не
искажают информацию». Это условие здесь не пожелание редактору, а проверка
скриптом: правка, которая потеряла или добавила число, добавила имя, которого
не было, или оставила ссылку на газету, ОТКЛОНЯЕТСЯ с причиной.

ПОЧЕМУ ЭТО СЛОМАНО. Тексты карточек собирались разбором статей, и разбор
переносил в поля не факт, а фразу: «По его словам, в периметр сделки вошли…»
(чьим словам?), «сообщают «Ведомости» со ссылкой на данные отчётности»
(источник и так стоит в `src`), «Генеральным директором … стал Николай
Разуваев» (ploschadnews.ru, 29 января 2026 года) — цитата в кавычках вместо
своего предложения. `review.py` такое пропускает верно: он проверяет, что
значение РЕАЛЬНО лежит в источнике дословно (защита от выдумки), — но ничего
не говорит о том, КАК это написано. Вычитка — обратная задача: текст меняется
целиком, а факты обязаны остаться ровно те же. Отсюда две разные границы:
у `review.py` — «новое значение выводимо из цитаты», здесь — «старое и новое
значение несут одни и те же числа, имена и утверждения».

КАКИЕ ПОЛЯ МОЖНО ВЫЧИТЫВАТЬ — закрытый список `PROOFREAD_FIELDS`: только
прозаические поля, которые читатель видит абзацем. Заголовок, сумма, предмет,
имена сторон, консультанты, источники, даты и статус — структурные, у них
свои правила (`review.py`), и вычитка к ним не допускается: скрипт отказывает.

ПРОВЕРКИ НА КАЖДУЮ ПРАВКУ (все — под `assert` в `_self_check()`):
  * `old` дословно равен текущему значению поля — иначе база уже другая;
    если поле уже равно `new`, правка считается применённой (идемпотентность);
  * числа: ни одно число из `new` не может отсутствовать в `old` (нельзя
    досочинить цифру); число из `old` может исчезнуть из поля, только если
    оно стояло внутри пресс-атрибуции («(Retail.ru, 30 июня 2025 года)») или
    остаётся в ДРУГОМ поле той же карточки — так снимаются дубли между
    «Целью сделки» и «Дополнительной информацией», не теряя ни одной цифры;
  * валюты: набор валют (₽/$/€/£) в `new` равен набору в `old`;
  * имена: каждое слово с заглавной буквы в `new` не в начале предложения
    обязано встречаться в `old` с точностью до окончания (`name_match`: общее
    начало от 5 знаков, у коротких имён — до одной буквы окончания, иначе
    «Иванов» ляжет на «Иван»); имя из `old`, пропавшее из `new`, допустимо,
    только если это название издания, оно осталось в другом поле карточки
    или стояло внутри иноязычной цитаты, которую пересказали;
  * длина `new` — от 0,5 до 1,35 длины `old`;
  * нет пресс-атрибуции (`press_attribution`): оборот «сообщает/пишет/как
    сообщал/по данным/со ссылкой на» рядом с названием издания, издание в
    скобках, «Источник: …», «Ъ», «ИФ», «как сообщалось», «в статье», «издание».
    При этом атрибуция ЧИСЛА к реестру, отчётности или названному аналитику
    («по данным ЕГРЮЛ», «по оценке аналитика X», «по данным СПАРК») —
    РАЗРЕШЕНА: это честная квалификация числа, а не ссылка на прессу (та же
    граница, что в fix_veon_mbo_law_fields_and_press_attribution.py);
  * нет прямых кавычек `"` и английских “ ”, кавычки « » и „ “ сбалансированы
    и стоят только вокруг названий (до 6 слов внутри) — длинная цитата
    обязана стать пересказом;
  * нет служебных скобок разбора («(МТС-банк (покупатель))», «(на тот
    момент — ИФ)»), первого лица («мы», «наш»), внутреннего жаргона
    («гендиректор цели», «линза»), «undefined/null/NaN», обрыва без точки,
    висящего разделителя в конце, « - » вместо тире;
  * юридические поля начинаются с заглавной, «Согласования» не теряют
    названия органа — те же инварианты, что держит test_data.py.

ЗАПИСЬ — ПО КАРТОЧКЕ ЦЕЛИКОМ. Карточка записывается и получает штамп
`proofread: "YYYY-MM-DD"`, только если ВСЕ её правки приняты; карточка с хотя
бы одним отказом не трогается вовсе — вычитывающий переделывает правку или
снимает её из файла. Штамп идемпотентен: повторный прогон с теми же правками
ничего не меняет и дату не освежает (`stamp_proofread`). Карточку, которую
прочитали и править нечего, помечают `--mark-clean <id>`.

СОВМЕСТИМОСТЬ С ТАБЛИЦЕЙ ПРАВОК `review.py`. Записи `FIXES` сравнивают поле
с `new` дословно (`review.already_applied`), и вычитанное поле перестало бы
совпадать — тест `test_review_table_is_applied_and_not_pending` счёл бы
правку неприменённой. Три варианта рассмотрены:
  (а) считать применённой ЛЮБУЮ запись на вычитанное поле карточки со
      штампом — просто, но опасно: запись, добавленную ПОСЛЕ вычитки, тот же
      признак объявил бы применённой, и `review.py --write` молча пропустил
      бы её навсегда;
  (б) переписывать `new=` в файлах `fixes/*.py` (как делает
      sync_fixes_table_after_cleanup.py) — каждый час правит десятки файлов и
      конфликтует с партиями дочитывания, которые пишутся параллельно;
  (в) ВЫБРАНО: перед записью скрипт проверяет через `review.already_applied`,
      что у карточки нет ни одной неприменённой записи `FIXES` (иначе отказ:
      «сначала review.py --write»), и кладёт в карточку `proofread_absorbed`
      — по вычитанному полю список отпечатков (`review.fix_fingerprint`)
      тех записей, которые были применены ДО вычитки. `already_applied`
      считает запись применённой, если её отпечаток есть в этом списке.
      Запись, добавленная позже, отпечатка не имеет — и проверяется как
      обычно (её `old` обязан быть вычитанным текстом).

Запуск:
    python3 pipeline/proofread.py правки.json            # только проверка
    python3 pipeline/proofread.py --check правки.json    # то же самое
    python3 pipeline/proofread.py --write правки.json    # применить принятое
    python3 pipeline/proofread.py --write --mark-clean g1234567 g2345678
    python3 pipeline/proofread.py --self-check           # правила на себе
    python3 pipeline/proofread.py --queue [N]            # кто ещё не вычитан

Формат файла правок: список объектов {"id", "field", "old", "new"}; поле
`events[i].note` адресуется как "events.0.note".
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, 'ingest'))

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

PROOFREAD_FIELDS = ('extra', 'eco.share', 'eco.val', 'eco.target_fin', 'eco.fin',
                    'eco.rationale', 'eco.context', 'law.struct', 'law.terms',
                    'law.appr')
EVENT_NOTE = re.compile(r'^events\.(\d+)\.note$')
# Структурные поля названы явно, чтобы отказ объяснял, ПОЧЕМУ нельзя, а не
# просто «поле не из списка».
STRUCTURAL = {'title': 'заголовок', 'sum': 'сумма', 'eco.sum': 'сумма', 'asset': 'предмет',
              'buyer_name': 'покупатель', 'seller': 'продавец', 'law.adv': 'консультанты',
              'eco.finadv': 'финансовый консультант', 'src': 'источники', 'date': 'дата',
              'status': 'статус', 'type': 'тип сделки', 'ind': 'отрасль'}

MIN_RATIO, MAX_RATIO = 0.5, 1.35

# Тот же предикат заглушки, что на экране (`PLACEHOLDER` в static/index.html)
# и в test_data.py (`LAW_PLACEHOLDER`).
PLACEHOLDER = re.compile(
    r"^(?:[—-]|н/д|нет\s+данных|(?:публично|официально)\s+(?:об?\s+\S+\s+)?не\s+(?:раскры|сообщал|разглаш)[а-яё]*"
    r"|не\s+(?:раскры|сообщал|привлекал|указан|назван|разглаш)[а-яё]*"
    r"(?:\s+(?:официально|публично))?)[.\s]*$", re.I)

# ---------------------------------------------------------------------------
# Числа и валюты

# Единица может стоять через дефис и по-английски («$300-million loss» в
# пересказанной цитате) — приводится к русской, иначе честный перевод «$300 млн»
# получал бы отказ «число 300млн не из old».
NUMBER = re.compile(r'(?<![\w])(\d[\d ]*(?:[.,]\d+)?)\s*-?\s*(%|млрд|млн|тыс\.?|трлн|million|billion|thousand|mln|bn)?(?![A-Za-zА-Яа-я])', re.I)
UNIT_ALIAS = {'million': 'млн', 'mln': 'млн', 'billion': 'млрд', 'bn': 'млрд', 'thousand': 'тыс'}
CURRENCY = [('RUB', re.compile(r'₽|\bруб\b|\bруб\.|\bрубл[а-яё]*', re.I)),
            ('USD', re.compile(r'\$|\bдолл[а-яё.]*|\bUSD\b', re.I)),
            ('EUR', re.compile(r'€|\bевро\b|\bEUR\b', re.I)),
            ('GBP', re.compile(r'£|\bфунт[а-яё]*|\bGBP\b', re.I))]


def numbers(text):
    """Множество числовых токенов: «6,5 млрд» → «6.5млрд», «27,5%» → «27.5%»,
    «41 500» → «41500», «2024 году» → «2024», «70-е» → «70»."""
    out = set()
    for num, unit in NUMBER.findall(str(text or '')):
        core = num.replace(' ', '').replace(',', '.').rstrip('.')
        unit = (unit or '').lower().rstrip('.')
        out.add(core + UNIT_ALIAS.get(unit, unit))
    return out


def currencies(text):
    return {code for code, rx in CURRENCY if rx.search(str(text or ''))}


# ---------------------------------------------------------------------------
# Имена

# Слово: с буквы, дальше буквы/цифры/дефис/апостроф/точка/амперсанд («M&A»,
# «Retail.ru», «Агро-Белогорье», «Shopper's»).
WORD = re.compile(r"[A-Za-zА-ЯЁа-яё][A-Za-zА-ЯЁа-яё0-9&'’.\-]*")
# Граница предложения: начало текста или знак конца/двоеточие/точка с запятой,
# после которых могут стоять закрывающие кавычки/скобки, пробелы и открывающие
# кавычки/скобки/тире. Слово сразу после неё — не имя, а начало фразы.
SENT_START = re.compile(r'(?:^|[.!?:;]\s*[»"“”)]*\s+[«„"“(\-—–]*\s*|^[«„"“(\-—–]*\s*)$', re.S)
# Кириллические буквы, неотличимые от латинских: «МIUZ» с русской М — тот же
# бренд, что «MIUZ». Приводим только СМЕШАННЫЕ токены, чисто русские не трогаем.
HOMOGLYPHS = str.maketrans('аеорсухкмтнвАЕОРСУХКМТНВ', 'aeopcyxkmthbAEOPCYXKMTHB')


def name_key(word):
    w = word.strip(".'’-").replace('ё', 'е').replace('Ё', 'Е')
    if re.search(r'[A-Za-z]', w) and re.search(r'[А-Яа-я]', w):
        w = w.translate(HOMOGLYPHS)
    return w.lower()


def name_match(a, b):
    """Одно ли это имя с точностью до окончания.

    «Иванов» на «Иван» ложиться не должен (урок про `same_word` в
    assistant_retrieval): общее начало от 5 знаков, хвосты не длиннее 3.
    У коротких имён («Юрий/Юрия», «Ким/Кима», «Ольга/Ольги») окончание в одну
    букву — отдельная, более узкая ветка."""
    a, b = name_key(a), name_key(b)
    if a == b:
        return True
    p = 0
    for x, y in zip(a, b):
        if x != y:
            break
        p += 1
    ra, rb = len(a) - p, len(b) - p
    if p >= 5 and ra <= 3 and rb <= 3:
        return True
    return p >= 3 and ra <= 1 and rb <= 1


def capitalised_words(text, skip_sentence_start=True):
    """Слова с заглавной буквы (не в начале предложения), длиннее одной буквы."""
    text = str(text or '')
    out = []
    for m in WORD.finditer(text):
        w = m.group(0).rstrip(".'’-")
        if len(name_key(w)) < 2 or not w[0].isupper():
            continue
        if skip_sentence_start and SENT_START.search(text[:m.start()]):
            continue
        out.append(w)
    return out


def all_words(text):
    return [m.group(0).rstrip(".'’-") for m in WORD.finditer(str(text or ''))]


# ---------------------------------------------------------------------------
# Пресс-атрибуция

OUTLET = (r"(?:Коммерсант[ъа-яё]*|Kommersant|Ведомост[а-яё]*|Vedomosti|РБК|RBC|Интерфакс[а-яё]*|Interfax"
          r"|ТАСС|TASS|Forbes|Reuters|Bloomberg|Financial\s+Times|РИА\s+Новости|РИА|TAdviser|CNews|ComNews"
          r"|mergers\.ru|Frank\s*(?:Media|RG|Медиа)|The\s+Bell|Извести[яйюе][а-яё]*|Газета\.ru|Фонтанк[а-яё]*"
          r"|Деловой\s+Петербург|DP\.ru|Vademecum|AdIndex|Retail\.ru|vc\.ru|Lenta\.ru|Лента\.ру"
          r"|Бизнес\s+Online|БИЗНЕС\s+Online|Абирег[а-яё]*|Право\.ru|Pravo\.ru|BFM|Banki\.ru|Банки\.ру|Sostav|Rusbase"
          # Издания, на которых спотыкались прогоны вычитки 1-9 (3 сентября
          # 2026): их не было в списке, и снять «по данным X» без потери
          # имени редактор не мог. Добавляются с падежными хвостами там, где
          # имя склоняется («Нового проспекта», «АСН-новостей»).
          r"|Хабр[а-яё]*|Нов[а-яё]+\s+проспект[а-яё]*|АСН[- ]новост[а-яё]*|ADPASS|PrimaMedia|Прайм"
          r"|АК\s*&\s*М|АКМ|AKM|Ъ-[А-ЯЁA-Za-zа-яё]+|НГ\.ru|РИА\s+Недвижимост[а-яё]*|Реальное\s+врем[яени][а-яё]*"
          r"|Октагон|Октагон\.Медиа|Фармвестник|Медвестник|Эксперт\s+РА|Sperant|Shopper[’\']?s"
          r"|Yahoo\s+Finance|Wall\s+Street\s+Journal|WSJ|New\s+York\s+Times|Handelsblatt|The\s+Insider"
          r"|Shopper'?s|Фармацевтическ[а-яё]+\s+вестник|Мясной\s+эксперт|Milknews|Агроинвестор"
          r"|Секрет\s+фирмы|Инк\.|Inc\.\s*Russia|Ъ)")
OUTLET_RX = re.compile(OUTLET)
# Домен издания — и латиницей, и кириллицей: «УФА1.ру» и «МР7.ру» не ложились
# ни на список изданий, ни на латинский шаблон, и их исчезновение из текста
# читалось как потеря имени (прогоны вычитки 5 и 6, 3 сентября 2026).
DOMAIN = (r"\b(?:[a-z0-9-]+\.(?:ru|com|org|net|io|media|su|kz|by|ua)"
          r"|[а-яёa-z0-9-]+\.(?:ру|рф))\b")
ATTR_VERB = (r"(?:по\s+(?:данным|информации|сведениям|словам|оценк[а-яё]*|подсч[её]там)"
             r"|как\s+(?:и\s+)?(?:ранее\s+)?(?:писал|сообщ|отмеч|передав|уточн|указыв|напомин|подтвержд|рассказ)[а-яё]*"
             r"|(?:сообщ|пи[сш]|переда[юёе]|отмеча|уточня|указыва|напомина|подтвержда|рассказыва|утвержда|цитиру"
             r"|подсчита|выясни|узна|знае)[а-яё]*"
             r"|со\s+ссылкой\s+на|собеседник[а-яё]*|источник[а-яё]*|опрошенн[а-яё]*|говорится\s+в|следует\s+из"
             r"|об\s+этом|информаци[а-яё]*|материал[а-яё]*|стать[яией][а-яё]*)")

# Честная атрибуция числа — реестр, отчётность, названный аналитик — не
# пресс-атрибуция. Маскируется ДО проверки, чтобы «по данным рейтинга
# «Интерфакс-100»» и «по оценке директора … Strategy Partners» проходили.
ALLOWED_ATTRIBUTION = [
    re.compile(r"(?:по|согласно)\s+(?:данным|информации|сведениям)\s+(?:(?:рейтинга|рэнкинга|базы|реестра|картотеки"
               r"|системы|агрегатора|сервиса|аудированной|консолидированной|годовой|официальной|финансовой)\s+)?"
               r"[«„“\"]?(?:ЕГРЮЛ|ЕГРН|ЕГРИП|СПАРК[\w\-]*|Rusprofile|Контур[\w.\-]*|Интерфакс-100|Интерфакс-ЦРКИ"
               r"|Росстат[а-яё]*|ФНС|ЦБ\b|Банка\s+России|Мосбирж[а-яё]*|Минфин[а-яё]*|отч[её]тност[а-яё]*"
               r"|раскрыти[а-яё]*|Росимуществ[а-яё]*|Росреестр[а-яё]*|Федресурс[а-яё]*|Казначейств[а-яё]*"
               r"|компани[ия]|самой\s+компании|сторон\b|участников\s+рынка|аналитик[а-яё]*|эксперт[а-яё]*"
               r"|проспект[а-яё]*|презентаци[а-яё]*|годов[а-яё]+\s+отч[её]т[а-яё]*)[^,.;]{0,60}", re.I),
    re.compile(r"следует\s+из\s+(?:данных\s+)?(?:СПАРК[\w\-]*|ЕГРЮЛ|ЕГРН|отч[её]тност[а-яё]*|раскрыти[а-яё]*"
               r"|проспект[а-яё]*|Rusprofile|Контур[\w.\-]*)[^,.;]{0,60}", re.I),
    re.compile(r"по\s+(?:оценк[а-яё]*|расч[её]там|подсч[её]там|мнению|словам|прогноз[а-яё]*)\s+[^,.;]{0,90}", re.I),
    re.compile(r"в\s+(?:рейтинге|рэнкинге)\s+[«„]?Интерфакс-100[»“]?", re.I),
    re.compile(r"(?:говорится|сказано|указано|отмечается)\s+в\s+(?:аудированной\s+|консолидированной\s+|годовой\s+)?"
               r"(?:отч[её]тности|проспекте|презентации|сообщении|пресс-релизе|раскрытии|материалах\s+к\s+собранию)"
               r"[^,.;]{0,60}", re.I),
]

PRESS_RULES = [
    ('«Ъ» — обозначение газеты', re.compile(r'(?<![А-Яа-яЁё\w])Ъ(?![а-яё\w])')),
    ('«ИФ» — пометка агентства', re.compile(r'\bИФ\b')),
    ('«Источник:» в тексте', re.compile(r'Источник[а-яё]*\s*:', re.I)),
    ('издание в скобках', re.compile(r'\([^()]*(?:' + OUTLET + r'|' + DOMAIN + r')[^()]*\)')),
    ('пресс-атрибуция: оборот + издание', re.compile(r'(?i:' + ATTR_VERB + r')[^.;:!?]{0,60}?(?:' + OUTLET + r'|' + DOMAIN + r')')),
    ('пресс-атрибуция: издание + оборот', re.compile(r'(?:' + OUTLET + r')[^.;:!?]{0,40}?(?i:' + ATTR_VERB + r')')),
    ('безличный пересказ прессы', re.compile(r'\bкак\s+(?:ранее\s+|уже\s+)?(?:сообщалось|писалось|отмечалось|указывалось)|ранее\s+сообщалось', re.I)),
    ('ссылка на статью вместо факта', re.compile(r'\bв\s+(?:статье|материале|публикации|заметке)\b|\bиздани(?:е|я|ю|ем|и|ий)\b'
                                                r'|\bгазет[а-яё]*\s+(?:пишет|сообща)|\bжурналист[а-яё]*', re.I)),
]

# «1-я ювелирная сеть» — не первое лицо: дефис перед «я» исключён из границы.
FIRST_PERSON = re.compile(r'(?<![«„"“\w\-–])(?:мы|нас|нам|нами|наш(?:а|е|и|его|ей|их|им|ими|у|ем|ею)?|я)\b', re.I)
# Правовая форма — не имя: «АО» перед «Экспобанком» можно опустить, если
# компания названа; дописать форму, которой в old не было, по-прежнему нельзя.
LEGAL_FORMS = {'АО', 'ООО', 'ПАО', 'ЗАО', 'ОАО', 'НАО', 'ГК', 'ИП', 'ТОО', 'АНО', 'ФГУП', 'ГУП', 'МУП', 'НПАО'}
JARGON = [
    re.compile(r'\b(?:знаменател|линз[аеыу]|дочитыван|дочита[лн]|инвариант|идемпотент|штамп|прогон)[а-яё]*|\bbulk\b', re.I),
    re.compile(r'\b(?:гендиректор|директор|владел|выручк|прибыл|активы|акци|дол[яи]|капитал|бенефициар|сотрудник'
               r'|завод|бизнес|менеджмент|учредител|руководств)[а-яё]*\s+цели\b', re.I),
]
SERVICE_PARENS = re.compile(r'\((?:[^()]*\([^()]*\)|\s*(?:покупател|продав|инвестор|управляющ|цель|актив\b|источник)[^()]*|'
                            r'[^()]*—\s*ИФ\s*)\)', re.I)
BAD_TOKEN = re.compile(r'\b(?:undefined|null|NaN|None)\b')
HANGING_TAIL = re.compile(r'[;,:—–\-]$')
HYPHEN_AS_DASH = re.compile(r'[\wа-яё0-9%»)] - [\wа-яё0-9«(]', re.I)
BODY = re.compile(
    r"ФАС\b|антимонопольн|правительственн[а-яё]*\s+(?:под)?комисси|правкомисси|подкомисси|Банк[а-яё]*\s+России"
    r"|ЦБ\s+РФ|Центробанк|президент[а-яё]*|правительств[а-яё]*|премьер|власт[а-яё]*|Минцифр|Минпромторг|Минсельхоз"
    r"|Минфин|Минюст|Роскомнадзор|Росимуществ|Росжелдор|регулятор|UOKiK|Rekabet|Еврокомисси|CFIUS|OFAC|OFSI|BIS|EMRA"
    r"|министерств[а-яё]*|Minist|совет[а-яё]*\s+директоров|собрани[а-яё]*\s+акционеров|акционер|указ|распоряжени"
    r"|предписани|\bсуд[а-яё]*|прокуратур[а-яё]*|орган[а-яё]*\s+власти|регулирующ[а-яё]*\s+орган|кабмин|Роскосмос"
    r"|Генпрокуратур[а-яё]*|ЦНИИМаш", re.I)


def mask_allowed(text):
    for rx in ALLOWED_ATTRIBUTION:
        text = rx.sub(lambda m: ' ' * len(m.group(0)), text)
    return text


def press_attribution(text):
    """Список (правило, найденный кусок) — пусто, если пресс-атрибуции нет."""
    masked = mask_allowed(str(text or ''))
    found = []
    for name, rx in PRESS_RULES:
        m = rx.search(masked)
        if m:
            found.append((name, m.group(0).strip()))
    return found


def quote_spans(text):
    """Пары « » и „ “ (с вложенностью) — список (начало, конец, содержимое)."""
    stack, out = [], []
    for i, ch in enumerate(text):
        if ch in '«„':
            stack.append((ch, i))
        elif ch in '»“' and stack:
            opener, start = stack.pop()
            out.append((start, i, text[start + 1:i]))
    return out, [s for s in stack]


def long_quotes(text, limit=6):
    text = str(text or '')
    spans, _ = quote_spans(text)
    return [inner for _, _, inner in spans if len(re.findall(r'\w+', inner)) > limit]


def quotes_balanced(text):
    text = str(text or '')
    _, unclosed = quote_spans(text)
    return not unclosed and text.count('«') == text.count('»') and text.count('„') == text.count('“')


# Аббревиатуры изданий («ФВ» — «Фармацевтический вестник», «ДП» — «Деловой
# Петербург») и общеупотребительные сокращения («ЧП» — чистая прибыль, «СМИ»)
# писались с заглавных и потому считались именами собственными: снять их из
# текста было нельзя. Именами они не являются — список закрытый и короткий.
SHORT_OUTLET = {'ИФ', 'Ъ', 'ФВ', 'ДП', 'НГ', 'АСН', 'ASN', 'AKM', 'РГ', 'ЕЖ'}
COMMON_ABBR = {'ЧП', 'СМИ', 'ЕГРЮЛ', 'ЕГРН', 'СПАРК', 'МСФО', 'РСБУ', 'НДС', 'ФЗ'}


def outlet_like(word):
    return bool(OUTLET_RX.fullmatch(word) or re.fullmatch(DOMAIN, word.lower())
                or word in SHORT_OUTLET or word in COMMON_ABBR)


def strip_press(text):
    """`old` без кусков пресс-атрибуции — по ним считается, что ПОТЕРЯНО.

    Число или имя внутри «(Retail.ru, 30 июня 2025 года)» — дата заметки, не
    факт сделки, и её исчезновение из `new` — не потеря."""
    text = str(text or '')
    for _, rx in PRESS_RULES[3:6]:
        text = rx.sub(' ', text)
    return text


# ---------------------------------------------------------------------------
# Поля карточки

def field_allowed(field):
    return field in PROOFREAD_FIELDS or bool(EVENT_NOTE.match(str(field)))


def get_field(card, field):
    m = EVENT_NOTE.match(str(field))
    if m:
        events = card.get('events') or []
        i = int(m.group(1))
        return events[i].get('note') if i < len(events) and isinstance(events[i], dict) else None
    obj = card
    for part in str(field).split('.'):
        if not isinstance(obj, dict):
            return None
        obj = obj.get(part)
    return obj


def set_field(card, field, value):
    m = EVENT_NOTE.match(str(field))
    if m:
        card['events'][int(m.group(1))]['note'] = value
        return
    parts = str(field).split('.')
    obj = card
    for part in parts[:-1]:
        obj = obj.setdefault(part, {})
    obj[parts[-1]] = value


def card_texts(card, companies=None, skip_field=None):
    """Все тексты карточки, кроме одного поля, — чтобы понять, остался ли
    снятый факт где-то ещё на той же карточке."""
    out = []
    for k in ('title', 'extra', 'seller', 'buyer_name', 'asset', 'sum'):
        if k != skip_field and isinstance(card.get(k), str):
            out.append(card[k])
    for grp in ('eco', 'law'):
        for k, v in (card.get(grp) or {}).items():
            if grp + '.' + k == skip_field:
                continue
            if isinstance(v, str):
                out.append(v)
            elif isinstance(v, list):
                for row in v:
                    out.extend(x for x in (row if isinstance(row, list) else [row]) if isinstance(x, str))
    for i, ev in enumerate(card.get('events') or []):
        if isinstance(ev, dict) and 'events.%d.note' % i != skip_field and isinstance(ev.get('note'), str):
            out.append(ev['note'])
    if companies:
        for k in ('buyer', 'target', 'seller_id', 'asset_id'):
            prof = companies.get(card.get(k) or '')
            if isinstance(prof, dict) and isinstance(prof.get('name'), str):
                out.append(prof['name'])
    return ' \n '.join(out)


def apply_edits(card, edits):
    """Копия карточки с применёнными правками — «после» для проверки потерь."""
    after = json.loads(json.dumps(card, ensure_ascii=False))
    for e in edits:
        if field_allowed(e.get('field')):
            try:
                set_field(after, e['field'], e['new'])
            except (KeyError, IndexError, TypeError):
                pass
    return after


# ---------------------------------------------------------------------------
# Проверка одной правки

def check(edit, card, after=None, companies=None):
    """Список причин отказа (пусто — принято) и список замечаний (не блокируют)."""
    bad, notes = [], []
    field, old, new = edit.get('field'), edit.get('old'), edit.get('new')
    if not field_allowed(field):
        why = STRUCTURAL.get(field)
        bad.append('поле %r не вычитывается%s' % (field, ' — это %s, у него свои правила (review.py)' % why if why else
                                                  '; разрешены: %s и events.N.note' % ', '.join(PROOFREAD_FIELDS)))
        return bad, notes
    current = get_field(card, field)
    if not isinstance(new, str) or not isinstance(old, str):
        bad.append('old и new обязаны быть строками')
        return bad, notes
    if current != old:
        bad.append('поле уже другое: в базе %r, ожидали %r' % (str(current)[:60], old[:60]))
        return bad, notes
    if PLACEHOLDER.match(old.strip()) or not old.strip():
        bad.append('поле пустое или заглушка — вычитывать нечего')
        return bad, notes
    if PLACEHOLDER.match(new.strip()) or not new.strip():
        bad.append('new пуст или заглушка — вычитка не удаляет поля')
        return bad, notes
    if new == old:
        bad.append('new совпадает с old — правки нет')
        return bad, notes
    if new != new.strip():
        bad.append('пробелы в начале или конце new')
    if '  ' in new:
        bad.append('двойной пробел в new')

    # Числа: досочинить нельзя вовсе; потерять — только если число остаётся
    # в другом поле карточки или стояло внутри пресс-атрибуции.
    old_nums, new_nums = numbers(old), numbers(new)
    added = new_nums - old_nums
    if added:
        bad.append('в new есть числа, которых не было в old: %s' % ', '.join(sorted(added)))
    kept_nums = numbers(strip_press(old))
    lost = kept_nums - new_nums
    if lost:
        elsewhere = numbers(card_texts(after or card, companies, skip_field=field))
        really_lost = lost - elsewhere
        if really_lost:
            bad.append('из new пропали числа: %s' % ', '.join(sorted(really_lost)))
        if lost - really_lost:
            notes.append('числа %s сняты как повтор — остаются в других полях карточки'
                         % ', '.join(sorted(lost - really_lost)))
    if currencies(new) != currencies(old):
        bad.append('набор валют изменился: было %s, стало %s'
                   % (sorted(currencies(old)) or '—', sorted(currencies(new)) or '—'))

    # Имена: в new — только те, что были в old; из old пропасть может лишь
    # издание, имя из пересказанной иноязычной цитаты или то, что осталось в
    # другом поле карточки.
    old_words = all_words(old)
    unknown = [w for w in capitalised_words(new)
               if not any(name_match(w, o) for o in old_words)]
    if unknown:
        bad.append('в new есть имена, которых не было в old: %s' % ', '.join(sorted(set(unknown))))
    new_words = all_words(new)
    foreign_quoted = set()
    for inner in long_quotes(old):
        if re.search(r'[A-Za-z]', inner) and not re.search(r'[А-Яа-яЁё]', inner):
            foreign_quoted.update(name_key(w) for w in all_words(inner))
    elsewhere_words = None
    for w in capitalised_words(strip_press(old)):
        if any(name_match(w, n) for n in new_words):
            continue
        if outlet_like(w.strip(".'’-")) or name_key(w) in foreign_quoted or w in LEGAL_FORMS:
            continue
        if elsewhere_words is None:
            elsewhere_words = all_words(card_texts(after or card, companies, skip_field=field))
        if any(name_match(w, o) for o in elsewhere_words):
            notes.append('имя «%s» снято из поля — остаётся в других полях карточки' % w)
            continue
        bad.append('из new пропало имя «%s»' % w)

    ratio = len(new) / max(len(old), 1)
    if not MIN_RATIO <= ratio <= MAX_RATIO:
        bad.append('длина new — %.2f от old (допустимо %.2f–%.2f)' % (ratio, MIN_RATIO, MAX_RATIO))

    for name, snippet in press_attribution(new):
        bad.append('%s: «%s»' % (name, snippet[:60]))
    if '"' in new or '”' in new:
        bad.append('прямые или английские кавычки — используйте « » и „ “')
    if not quotes_balanced(new):
        bad.append('кавычки « » / „ “ не сбалансированы')
    for inner in long_quotes(new):
        bad.append('длинная цитата в кавычках вместо пересказа: «%s…»' % inner[:50])
    m = SERVICE_PARENS.search(new)
    if m:
        bad.append('служебные скобки разбора: %s' % m.group(0)[:50])
    m = FIRST_PERSON.search(new)
    if m and not (m.group(0)[0].isupper() and m.start() and new[m.start() - 1] in '«„'):
        bad.append('первое лицо: «%s»' % m.group(0))
    for rx in JARGON:
        m = rx.search(new)
        if m:
            bad.append('внутренний жаргон: «%s»' % m.group(0))
    m = BAD_TOKEN.search(new)
    if m:
        bad.append('служебное значение в тексте: %s' % m.group(0))
    if '...' in new:
        bad.append('троеточие из точек — знак обрыва, вычитанный текст обрывов не несёт')
    if HANGING_TAIL.search(new.rstrip('»)')):
        bad.append('new обрывается на разделителе')
    tail = new.rstrip('»)" ')
    if old.rstrip('»)" ').endswith(('.', '!', '?')) and not tail.endswith(('.', '!', '?')):
        bad.append('old заканчивался точкой, new — нет (обрыв?)')
    if HYPHEN_AS_DASH.search(new):
        bad.append('« - » вместо тире « — »')
    if field.startswith('law.'):
        first = re.search(r'[\wА-ЯЁа-яё]', new)
        if first and not (first.group(0).isupper() or first.group(0).isdigit()):
            bad.append('юридическое поле начинается со строчной буквы')
    if field == 'law.appr' and BODY.search(old) and not BODY.search(new):
        bad.append('из «Согласований» пропало название органа')
    return bad, notes


# ---------------------------------------------------------------------------
# Штамп, очередь, таблица правок review.py

def stamp_proofread(card, day=None):
    """Отметка «вычитано» — один раз, повторный прогон дату не освежает."""
    if card.get('proofread'):
        return False
    card['proofread'] = day or datetime.now(timezone.utc).date().isoformat()
    return True


def _review():
    import review  # noqa: E402 — тяжёлый импорт (таблица FIXES), поэтому лениво
    return review


def unapplied_fixes(card, fields=None):
    """Записи FIXES этой карточки, которых ещё нет в базе, — по вычитываемым полям."""
    review = _review()
    return [f for f in review.FIXES
            if f['id'] == card['id'] and field_allowed(f['field'])
            and (fields is None or f['field'] in fields)
            and not review.already_applied(f, card)]


def absorb_fixes(card, fields):
    """Запомнить отпечатки записей FIXES по вычитанным полям — см. докстринг,
    вариант (в). Возвращает число записей."""
    review = _review()
    n = 0
    for f in review.FIXES:
        if f['id'] != card['id'] or f['field'] not in fields:
            continue
        absorbed = card.setdefault('proofread_absorbed', {}).setdefault(f['field'], [])
        fp = review.fix_fingerprint(f['new'])
        if fp not in absorbed:
            absorbed.append(fp)
            n += 1
    if 'proofread_absorbed' in card and not card['proofread_absorbed']:
        del card['proofread_absorbed']
    return n


def queue(data, limit=None):
    """Карточки без штампа, видимые на сайте, — самые читаемые первыми."""
    review = _review()
    cards = [c for c in data['deals'] if not c.get('proofread') and review.site_visible(c)]

    def weight(c):
        text = ''.join(str(get_field(c, f) or '') for f in PROOFREAD_FIELDS)
        return (len(c.get('src') or []), len(text))
    cards.sort(key=weight, reverse=True)
    return cards[:limit] if limit else cards


# ---------------------------------------------------------------------------
# Прогон

def run(edits, data, write=False, mark_clean=(), day=None, out=print):
    cards = {d['id']: d for d in data['deals']}
    companies = data.get('companies') or {}
    by_card = {}
    for e in edits:
        by_card.setdefault(str(e.get('id')), []).append(e)

    accepted, refused, done, notes_all = [], [], 0, []
    ready_cards = []
    for cid, group in by_card.items():
        card = cards.get(cid)
        if not card:
            for e in group:
                refused.append((e, ['карточки %s нет в базе' % cid]))
            continue
        after = apply_edits(card, group)
        seen_fields, card_ok = set(), True
        for e in group:
            field = e.get('field')
            if field in seen_fields:
                refused.append((e, ['второе изменение одного поля в одном файле']))
                card_ok = False
                continue
            seen_fields.add(field)
            if field_allowed(field) and isinstance(e.get('new'), str) and get_field(card, field) == e['new']:
                done += 1
                continue
            bad, notes = check(e, card, after, companies)
            if bad:
                refused.append((e, bad))
                card_ok = False
            else:
                accepted.append((e, notes))
        pending_fixes = unapplied_fixes(card, seen_fields)
        if pending_fixes:
            for f in pending_fixes:
                refused.append((dict(id=cid, field=f['field']),
                                ['у карточки есть неприменённая правка review.py по этому полю — '
                                 'сначала review.py --write']))
            card_ok = False
        if card_ok and any(e['id'] == cid for e, _ in accepted):
            ready_cards.append(cid)

    for e, notes in accepted:
        out('  ПРИНЯТО  %s %-16s %r -> %r' % (e['id'], e['field'], str(e['old'])[:30], str(e['new'])[:36]))
        for n in notes:
            out('           замечание: %s' % n)
    for e, bad in refused:
        out('  ОТКАЗ    %s %-16s %s' % (e.get('id'), e.get('field'), '; '.join(bad)))
    if done:
        out('  уже применено раньше: %d' % done)

    clean = []
    for cid in mark_clean:
        if cid not in cards:
            refused.append((dict(id=cid, field='proofread'), ['карточки %s нет в базе' % cid]))
            out('  ОТКАЗ    %s proofread         карточки нет в базе' % cid)
        elif unapplied_fixes(cards[cid]):
            refused.append((dict(id=cid, field='proofread'), ['есть неприменённые правки review.py']))
            out('  ОТКАЗ    %s proofread         есть неприменённые правки review.py' % cid)
        else:
            clean.append(cid)

    skipped = sorted({e['id'] for e, _ in accepted} - set(ready_cards))
    out('\nпринято %d, отклонено %d; карточек к записи %d%s'
        % (len(accepted), len(refused), len(ready_cards) + len(clean),
           ', не записываются из-за отказов по соседнему полю: %s' % ', '.join(skipped) if skipped else ''))
    if not write:
        out('Проверка. Запись — с ключом --write.')
        return 1 if refused else 0

    changed = 0
    for cid in ready_cards:
        card = cards[cid]
        fields = set()
        for e, _ in accepted:
            if e['id'] != cid:
                continue
            assert get_field(card, e['field']) == e['old'], 'состояние поля изменилось'
            set_field(card, e['field'], e['new'])
            fields.add(e['field'])
        absorb_fixes(card, fields)
        stamp_proofread(card, day)
        changed += 1
    for cid in clean:
        if stamp_proofread(cards[cid], day):
            changed += 1
    if not changed:
        out('Записывать нечего.')
        return 1 if refused else 0
    return changed


def main(argv):
    if '--self-check' in argv:
        _self_check()
        print('Самопроверка вычитки пройдена.')
        return 0
    if '--queue' in argv:
        rest = [a for a in argv if a != '--queue']
        limit = int(rest[0]) if rest and rest[0].isdigit() else 60
        data = json.load(open(DATA, encoding='utf-8'))
        q = queue(data)
        print('Не вычитано (видимых на сайте): %d' % len(q))
        for c in q[:limit]:
            print('  %s  %s  %s' % (c['id'], c.get('date'), str(c.get('title'))[:70]))
        return 0
    write = '--write' in argv
    mark_clean, ids_mode, path = [], False, None
    for a in argv:
        if a == '--mark-clean':
            ids_mode = True
        elif a in ('--write', '--check'):
            ids_mode = False
        elif ids_mode:
            mark_clean.append(a)
        elif a.endswith('.json'):
            path = a
    _self_check()
    edits = json.load(open(path, encoding='utf-8')) if path else []
    if not isinstance(edits, list):
        print('Файл правок обязан быть списком объектов {id, field, old, new}.')
        return 1
    data = json.load(open(DATA, encoding='utf-8'))
    print('Правок в файле: %d, карточек: %d%s'
          % (len(edits), len({str(e.get('id')) for e in edits}),
             ', пометить чистыми: %d' % len(mark_clean) if mark_clean else ''))
    result = run(edits, data, write=write, mark_clean=mark_clean)
    if write and result not in (0, 1):
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        print('ЗАПИСАНО: %d карточек со штампом proofread в %s' % (result, os.path.relpath(DATA, ROOT)))
        return 0
    return result


# ---------------------------------------------------------------------------
# Правила проверяются на себе

def _self_check():
    # Числа: досочинить нельзя, потерять из поля — только с сохранением на карточке.
    assert numbers('выручка 10,4 млрд руб., рост на 27,5%, 41 500 млн ₽ в 2024 году, 70-е место') == \
        {'10.4млрд', '27.5%', '41500млн', '2024', '70'}
    assert numbers('$300-million loss') == numbers('$300 млн') == {'300млн'} and numbers('топ-30 банков') == {'30'}
    assert numbers('4–5 млрд руб. и 2021–2024 гг.') == {'4', '5млрд', '2021', '2024'}
    assert currencies('12,5 млрд руб.') == currencies('12,5 млрд ₽') == {'RUB'}
    assert currencies('$4,1 млрд') == {'USD'} and currencies('€1 млн и 2 млрд руб.') == {'EUR', 'RUB'}
    # Имена: с точностью до окончания, но не «Иванов» на «Иван».
    assert name_match('Левицкого', 'Левицкий') and name_match('Шишкаревым', 'Шишкарев')
    assert name_match('Юрия', 'Юрий') and name_match('Кима', 'Ким') and name_match('Ольги', 'Ольга')
    assert not name_match('Иванов', 'Иван') and not name_match('Вера', 'Вета')
    assert not name_match('Ростех', 'Ростелеком') and not name_match('Медси', 'Медскан')
    assert name_match('МIUZ', 'MIUZ')            # русская М в латинском бренде
    assert capitalised_words('Сеть «Адамас» создана Андреем Сидоренко. Сейчас она работает.') == \
        ['Адамас', 'Андреем', 'Сидоренко']
    assert capitalised_words('Торги начались: «С 1 июля торги идут». Продавец — АО «Форум Капитал».') == \
        ['АО', 'Форум', 'Капитал']
    # Пресс-атрибуция: газета — отказ, реестр и аналитик — нет.
    assert press_attribution('Сумма могла составить 5 млрд руб., пишет Forbes.')
    assert press_attribution('Как сообщал “Ъ” 29 сентября 2020 года, управляющий продал акции.')
    assert press_attribution('сообщают «Ведомости» со ссылкой на данные отчётности')
    assert press_attribution('Торги начались (Retail.ru, 30 июня 2025 года).')
    assert press_attribution('Банк переименован (profbanking.com).')
    assert press_attribution('Продавец — Михаил Несветайло. Источник: Kommersant.')
    assert press_attribution('владельца доли 22,5% (на тот момент — ИФ)')
    assert press_attribution('Как сообщалось, в 2019 году группа купила 22,5%.')
    assert press_attribution('собеседники «Ъ» на ювелирном рынке называли претендентом MIUZ')
    assert press_attribution('опрошенные «Ведомостями» эксперты считают условия выгодными')
    assert press_attribution('В статье говорится, что сделка закрыта.')
    assert press_attribution('План утвердил кабмин, передают ТАСС и «РИА Новости».')
    assert not press_attribution('По данным ЕГРЮЛ, смена собственника зафиксирована в марте.')
    assert not press_attribution('По данным Rusprofile, балансовая стоимость невысока.')
    assert not press_attribution('чистая прибыль выросла втрое (по данным СПАРК).')
    assert not press_attribution('По оценке аналитика Ивана Пешкова, капитализация составляет 38 млрд ₽.')
    assert not press_attribution('По данным рейтинга «Интерфакс-100», активы составляли 89,2 млрд ₽.')
    assert not press_attribution('активы составляли 89,2 млрд ₽ — 70-е место в рэнкинге «Интерфакс-100».')
    assert not press_attribution('По данным аудированной отчётности за первое полугодие 2025 года, компания заплатила 31 млрд ₽.')
    assert not press_attribution('По неофициальным данным, дисконт ожидался существенным.')
    assert not press_attribution('ФАС одобрила ходатайство; гендиректор сообщил о планах инвестировать 10 млрд ₽.')
    assert not press_attribution('Об этом говорится в аудированной отчётности компании.')
    # Издание как сторона сделки без оборота атрибуции проходит.
    assert not press_attribution('Издатель продал Forbes новому владельцу.')
    # Кавычки: название — можно, цитата — нет.
    assert not long_quotes('ООО «Белгородский ювелирный завод „Арт-Карат“»')
    assert long_quotes('«Отменить решение, производство прекратить, утвердить мировое соглашение», — говорится')
    assert quotes_balanced('«Русагро» и ООО «ГК „Агро-Белогорье“»') and not quotes_balanced('«Русагро и «Дело»')
    # Служебные скобки разбора, первое лицо, жаргон.
    assert SERVICE_PARENS.search('текст (АО «РСА» (временный управляющий, инициатор выкупа))')
    assert SERVICE_PARENS.search('текст (МТС-банк (покупатель))') and SERVICE_PARENS.search('доля 22,5% (на тот момент — ИФ)')
    assert not SERVICE_PARENS.search('стоимость (около 396 млн ₽ на конец 2024 года)')
    assert FIRST_PERSON.search('мы считаем') and FIRST_PERSON.search('в нашей базе')
    assert not FIRST_PERSON.search('сеть «Наш дом» продана') and not FIRST_PERSON.search('намерен купить')
    assert not FIRST_PERSON.search('АО «1-я ювелирная сеть» и 2-я очередь')
    assert JARGON[1].search('Гендиректор цели сменился') and not JARGON[1].search('цель сделки — синергия')

    # Правка целиком: хорошая проходит, плохие получают отказ по своей причине.
    card = {'id': 'x', 'title': 'Тест', 'sum': '31 млрд ₽',
            'eco': {'val': 'Эксперты оценивают сделку до 6,5 млрд руб., подсчитал директор BGP Capital Юрий Левицкий. '
                           'Тогда же собеседники «Ъ» называли претендентом MIUZ и оценивали сумму в 3–5 млрд руб.',
                    'fin': 'РУСАГРО заплатила 31 млрд рублей за 77,5%, сообщают «Ведомости».',
                    'context': '—'},
            'law': {'appr': 'Сделку одобрила ФАС в марте 2024 года.',
                    'struct': 'Покупка 77,5% долей компании, следует из данных ЕГРЮЛ, сообщает «Интерфакс».'}}
    good = dict(id='x', field='eco.val',
                old=card['eco']['val'],
                new='Эксперты оценивают сделку в сумму до 6,5 млрд ₽; по расчётам директора BGP Capital Юрия '
                    'Левицкого, участники рынка называли претендентом MIUZ и оценивали сумму в 3–5 млрд ₽.')
    bad, notes = check(good, card)
    assert not bad, bad
    bad, _ = check(dict(good, new=good['new'].replace('6,5', '7,5')), card)
    assert any('числа, которых не было' in b for b in bad), bad          # чужое число
    bad, _ = check(dict(good, new=good['new'].replace('MIUZ и оценивали сумму в 3–5 млрд ₽', 'MIUZ')), card)
    assert any('пропали числа' in b for b in bad), bad                   # потерянное число
    bad, _ = check(dict(good, new=good['new'].replace('Юрия Левицкого', 'Ивана Петрова')), card)
    assert any('имена, которых не было' in b for b in bad), bad          # новое имя
    assert any('пропало имя' in b for b in bad), bad                     # и старое исчезло
    bad, _ = check(dict(good, new=good['new'] + ' Об этом сообщает «Коммерсантъ».'), card)
    assert any('пресс-атрибуция' in b for b in bad), bad
    bad, _ = check(dict(good, new=good['new'].replace('MIUZ', '"MIUZ"')), card)
    assert any('кавычки' in b for b in bad), bad
    bad, _ = check(dict(good, new=good['new'][:40]), card)
    assert any('длина' in b for b in bad), bad
    bad, _ = check(dict(good, old='другое'), card)
    assert any('поле уже другое' in b for b in bad), bad
    bad, _ = check(dict(good, field='sum', old='31 млрд ₽', new='31 млрд ₽.'), card)
    assert any('не вычитывается' in b for b in bad), bad
    bad, _ = check(dict(id='x', field='eco.context', old='—', new='Текст.'), card)
    assert any('заглушка' in b for b in bad), bad
    # Число, снятое как повтор, остаётся в другом поле — принято с замечанием.
    fin = dict(id='x', field='eco.fin', old=card['eco']['fin'],
               new='Компания заплатила 31 млрд ₽ за пакет по данным отчётности.')
    bad, notes = check(fin, card)
    assert not bad and any('77.5%' in n for n in notes), (bad, notes)
    assert 'RUB' in currencies(fin['new'])
    bad, _ = check(dict(fin, new='Компания заплатила 31 млрд ₽ за 77,5% и ещё $5 млн.'), card)
    assert any('валют' in b for b in bad), bad
    # «Согласования» не теряют орган; юридическое поле — с заглавной.
    bad, _ = check(dict(id='x', field='law.appr', old=card['law']['appr'], new='Сделку одобрили в марте 2024 года.'), card)
    assert any('органа' in b for b in bad), bad
    bad, _ = check(dict(id='x', field='law.struct', old=card['law']['struct'],
                        new='покупка 77,5% долей компании (по данным ЕГРЮЛ).'), card)
    assert any('строчной' in b for b in bad), bad
    # Разрешённая атрибуция числа проходит и в правке, не только в регулярке;
    # газета из old снимается без отказа — это издание, а не факт.
    bad, _ = check(dict(id='x', field='law.struct', old=card['law']['struct'],
                        new='Покупка 77,5% долей компании (по данным ЕГРЮЛ).'), card)
    assert not bad, bad
    # А вот дописать «по данным ЕГРЮЛ» туда, где реестра не было, нельзя:
    # это новое имя, а значит — новое утверждение.
    bad, _ = check(dict(id='x', field='law.appr', old=card['law']['appr'],
                        new='Сделку одобрила ФАС в марте 2024 года (по данным ЕГРЮЛ).'), card)
    assert any('имена, которых не было' in b for b in bad), bad
    # Штамп идемпотентен.
    c = {'id': 'y'}
    assert stamp_proofread(c, '2026-09-02') and c['proofread'] == '2026-09-02'
    assert not stamp_proofread(c, '2026-09-03') and c['proofread'] == '2026-09-02'


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
