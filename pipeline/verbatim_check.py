# -*- coding: utf-8 -*-
"""Одна политика дословности: чем текст карточки может совпадать с источником.

Решение владельца 31 октября 2026 (H10, дословно): «давай одну политику.
Вспомни последние обсуждения как мы решили. Мы делаем полный пересказ, то
есть там не чтобы 1 слово отличалось и потом 11 подряд из источника. Но если
цитата чья-то, то пересказывать, конечно, не надо, но нужно тогда на
источник ссылаться.»

До этого дня дословность считали четыре алгоритма с разными порогами и
разным отношением к прямой речи (замер в docs/sources_legal.md, раздел «Одна
политика дословности»): `prose_gate.prose_problems` — 8 обычных слов подряд
из цитаты, прямая речь с автором разрешена; `accept_card.verbatim_runs` — 12
любых слов подряд с текстом на диске, а рядом `proofread.long_quotes`
объявлял находкой ЛЮБУЮ цитату длиннее 6 слов, даже с автором;
`proofread.check` — то же для вычитки; `pipeline/verbatim_check.py` — 12 слов
по заголовку, предмету и прозе без поправки на кавычки. Теперь правило одно и
живет здесь; те четыре места его вызывают.

Политика
--------
1. **Прозаические поля** (`PROSE_FIELDS`: «Дополнительно», все текстовые
   поля «Экономиста» и «Юриста», заметки этапов) — полный пересказ. Нарушение
   `verbatim_run`: общая с источником цепочка от `MIN_WORDS` обычных слов
   (имена, названия в кавычках, латиница и числа — факты, они не считаются:
   `plain_words`), по основам слов (первые 5 букв — падеж и число не
   спасают) и с «дыркой»: одно замененное, вставленное или выброшенное слово
   цепочку не рвет — так «1 слово отличалось и потом 11 подряд» считается.
   Нарушение `near_copy`: предложение карточки повторяет построение
   предложения источника — от `NEAR_MIN` значимых основ, из них `NEAR_SHARE`
   в том же порядке (14 октября 2026, «Азимут»: три замененных слова).
2. **Прямая речь** — в «елочках» от `QUOTE_MIN_WORDS` слов. Не нарушение,
   если назван говорящий («— сказал гендиректор Иван Петров», «заявили в
   компании», `SPEAKER_RE`) или издание («— сообщает «Коммерсантъ»», либо
   издание из `src` карточки в том же поле). Цитата без того и другого —
   нарушение `quote_without_source`. Из сравнения по п. 1 кавычки вынуты:
   чужие слова в кавычках и есть дословность, за которую отвечает ссылка.
   С `quotes_in_texts=True` (запись по цитате: `review.py`, `write_card.py`)
   слова в кавычках обязаны лежать в источнике буква в букву — иначе
   `quote_altered` (владелец, 14 октября 2026: чужие слова не правят).
3. **Структурные поля** (заголовок, стороны, предмет, суммы, даты, статус) —
   вне политики: имя и число дословны по определению, для них `review.check`
   проверяет только, что цитата настоящая, заголовок сверяют
   `title_problems` и `accept_card.title_copied_from`.

API: `check_card(card, texts, companies=None) -> [Finding]` и
`check_text(field, text, texts, ...) -> [Finding]`; `Finding(field, kind,
span, words, share)`. `texts` — строки источников или уже подготовленные
`prepare(texts)` (приемка сверяет много карточек с одним сырьем).
Политика ничего из пайплайна не импортирует (`from pipeline import
verbatim_check`): ее берут review/prose_gate (запись по цитате), accept_card
(приемка), proofread (вычитка). Ниже, после политики, — очередь рутины
качества (источники качаются из сети, агрегаторы не качаются: их текст сам
пересказ):

    python3 pipeline/verbatim_check.py --queue [N]     # свежие карточки с находками
    python3 pipeline/verbatim_check.py --card <id>     # одна карточка подробно
    python3 pipeline/verbatim_check.py --sample 80     # замер по случайной выборке
    python3 pipeline/verbatim_check.py --from-fixes [N]  # без сети: проза против цитат FIXES
"""
import re
from collections import namedtuple

MIN_WORDS = 8            # общих обычных слов подряд (с одной «дыркой») — нарушение
HOLES = 1                # сколько замен/вставок прощается внутри одной цепочки
NEAR_MIN = 8             # значимых основ в предложении, с которого смотрим скелет
NEAR_SHARE = 0.7         # доля основ в том же порядке — предложение списано
QUOTE_MIN_WORDS = 5      # кавычки от стольких слов — чужая речь, а не название
ANCHOR = 3               # длина якоря при поиске общих цепочек

PROSE_FIELDS = frozenset(('extra', 'eco.share', 'eco.val', 'eco.target_fin', 'eco.fin',
                          'eco.rationale', 'eco.context', 'law.struct', 'law.terms', 'law.appr'))
STRUCTURAL_FIELDS = frozenset(('title', 'asset', 'target', 'seller', 'buyer_name', 'buyer', 'sum', 'eco.sum',
                               'date', 'status', 'type', 'ind', 'stake_acquired', 'date_basis', 'sum_basis',
                               'src', 'eco.advisors', 'law.advisors'))

Finding = namedtuple('Finding', 'field kind span words share')
Finding.__new__.__defaults__ = (None,)

KINDS = {
    'verbatim_run': 'слов подряд как в источнике — пересказать своими словами',
    'near_copy': 'предложение повторяет предложение источника с заменой отдельных слов — пересказать по-своему',
    'quote_without_source': 'чужие слова в кавычках без указания, кто сказал или какое издание сообщает',
    'quote_altered': 'в кавычках не дословные слова источника — цитату нельзя менять',
}

_STOP = set('и в во на с со к ко по о об от до из за для при у не но а же что как это его ее их она он они было были '
            'был была также который которая которые которое этот эта эти том той тот года году лет млн млрд руб'.split())
_QUOTED = re.compile(r'«[^«»]*(?:«[^«»]*»[^«»]*)*»|„[^“]*“|"[^"]*"')
_UNIT = re.compile(r'(?i)\b(?:млн|млрд|трлн|тыс|руб|т|кг|га|кв|м|км|г|гг|год[ау]?|лет)\b\.?|[%₽$€]')
_TOKEN = re.compile(r'[^\s]+')
_SPEECH = re.compile(r'«((?:[^«»]|«[^«»]*»)*)»')
SPEAKER_RE = re.compile(r'(?i)\b(?:сказал|сказала|заявил|заявила|отметил|отметила|пояснил|пояснила|'
                        r'считает|говорит|по\s+(?:его\s+|ее\s+|их\s+)?словам|рассказал|рассказала|добавил|добавила|'
                        r'подчеркнул|подчеркнула|написал|написала|уточнил|уточнила|объявил|объявила|сообщил|сообщила|'
                        # «заявили в правительстве», «сообщили в компании» — 16 октября 2026
                        r'сказали|заявили|отметили|пояснили|рассказали|добавили|подчеркнули|написали|уточнили|объявили|сообщили|'
                        # «как заявило «Авито»» — компания среднего рода, 16 октября 2026
                        r'сказало|заявило|отметило|пояснило|рассказало|добавило|подчеркнуло|написало|уточнило|объявило|сообщило|'
                        r'говорится|сказано|отмечается|указано)\b')
# «…», — сообщает «Коммерсантъ» / пишет РБК / передает ТАСС: издание после
# закрывающей кавычки (правило 1 docs/sources_legal.md, 3 октября 2026).
OUTLET_AFTER_QUOTE = re.compile(r'»\s*,?\s*[—–-]\s*(?:как\s+)?(?:сообщ\w+|пиш\w+|переда\w+|писал\w*|'
                                r'отмеча\w+|уточня\w+|говорится|по\s+данным|по\s+информации)\b')


def words(text):
    """Слова текста строчными, без «ё»; HTML и сущности сняты."""
    text = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', str(text or ''), flags=re.S | re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    for a, b in (('&nbsp;', ' '), ('&laquo;', '«'), ('&raquo;', '»'), ('&mdash;', '—'), ('&quot;', '"'), ('&amp;', '&')):
        text = text.replace(a, b)
    text = re.sub(r'&#\d+;', ' ', text)
    return re.findall(r'[0-9a-zа-яё]+', text.lower().replace('ё', 'е'))


def plain_words(text):
    """Текст без имен, названий в кавычках, латиницы, чисел и единиц;
    границы предложений сохраняются. Списанное предложение узнается по
    ОБЫЧНЫМ словам — их и сравниваем (проба на «Карате», 14 октября 2026:
    без этого отказ получали честные пересказы с теми же юрлицами)."""
    text = _QUOTED.sub(' ', str(text or ''))
    text = re.sub(r'\d[\d\s .,–-]*', ' ', text)
    text = _UNIT.sub(' ', text)
    out, start = [], True
    for tok in _TOKEN.findall(text):
        core = tok.strip('()«»„“"—–-:,;')
        if core and re.match(r'[A-Za-z]', core):
            pass                                   # латиница — имя
        elif core and core[0].isupper() and not start:
            pass                                   # заглавная внутри предложения — имя
        else:
            out.append(tok)
        if tok:
            start = tok.endswith(('.', '!', '?', ';')) or (start and not core)
    return ' '.join(out)


def stem(w):
    return w[:5]


def stems(word_list):
    """Основы всех слов — для цепочек."""
    return [stem(w) for w in word_list]


def key_stems(word_list):
    """Основы значимых слов (без служебных и коротких) — для скелета предложения."""
    return [stem(w) for w in word_list if len(w) >= 3 and w not in _STOP]


def flat(text):
    return re.sub(r'[^0-9a-zа-я]+', ' ', str(text or '').lower().replace('ё', 'е')).strip()


def sentences(text):
    # Граница — знак конца и заглавная буква следом: «12 тыс. кв. метров» —
    # одно предложение, а не три.
    return [x.strip() for x in re.split(r'(?<=[.!?;])\s+(?=[А-ЯЁA-Z«"(])', str(text or '')) if x.strip()]


class Source(object):
    """Текст источника, подготовленный к сравнению один раз."""
    __slots__ = ('raw', 'plain', 'stems', 'index', 'keys', 'flat')

    def __init__(self, text):
        self.raw = words(text)
        self.plain = words(plain_words(text))
        self.stems = stems(self.plain)
        self.index = {}
        for i in range(len(self.stems) - ANCHOR + 1):
            self.index.setdefault(tuple(self.stems[i:i + ANCHOR]), []).append(i)
        self.keys = key_stems(self.plain)
        self.flat = flat(text)


def prepare(texts):
    """[Source] из строк; уже подготовленные проходят как есть."""
    return [t if isinstance(t, Source) else Source(t) for t in texts or ()]


def _extend(a, b, i, j, holes=HOLES):
    """Длина общей цепочки от (i, j): сколько слов `a` совпало с `b` по
    основам, одна «дырка» (замена, лишнее или пропущенное слово) прощается.
    Возвращает (совпавших слов, пройдено слов в `a`)."""
    k = m = matched = 0
    used = 0
    while i + k < len(a) and j + m < len(b):
        if a[i + k] == b[j + m]:
            matched += 1
            k += 1
            m += 1
            continue
        if used >= holes or matched < ANCHOR:
            break                     # дырка — только внутри цепочки, не на ее краю
        # замена слова (или слова на два), лишнее слово в карточке, лишнее в источнике
        for da, db in ((1, 1), (1, 0), (0, 1), (2, 1), (1, 2)):
            if i + k + da < len(a) and j + m + db < len(b) and a[i + k + da] == b[j + m + db]:
                k += da
                m += db
                break
        else:
            break
        used += 1
    return matched, k


def common_runs(card_words, source, min_words=MIN_WORDS):
    """[(совпавших слов, кусок карточки)] — общие цепочки обычных слов от
    `min_words`, по основам, с одной «дыркой». `card_words` — список слов
    (plain), `source` — Source."""
    a = stems(card_words)
    b = source.stems
    out, i = [], 0
    while i <= len(a) - ANCHOR:
        key = tuple(a[i:i + ANCHOR])
        best = (0, 0)
        for j in source.index.get(key, ()):
            best = max(best, _extend(a, b, i, j))
        if best[0] >= min_words:
            out.append((best[0], ' '.join(card_words[i:i + best[1]])))
            i += best[1]
        else:
            i += 1
    return out


def longest_common_run(a, b, minw=MIN_WORDS):
    """Самая длинная общая цепочка слов двух списков слов БЕЗ дырок:
    (длина, текст). Остается для очереди рутины качества и старых скриптов;
    политика — `common_runs`."""
    if len(a) < minw or len(b) < minw:
        return 0, ''
    index = {}
    for i in range(len(b) - minw + 1):
        index.setdefault(tuple(b[i:i + minw]), []).append(i)
    best, best_text, i = 0, '', 0
    while i <= len(a) - minw:
        key = tuple(a[i:i + minw])
        if key in index:
            run = 0
            for j in index[key]:
                k = 0
                while i + k < len(a) and j + k < len(b) and a[i + k] == b[j + k]:
                    k += 1
                run = max(run, k)
            if run > best:
                best, best_text = run, ' '.join(a[i:i + run])
            i += max(1, run - minw + 1)
        else:
            i += 1
    return best, best_text


def _lcs(a, b):
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if x == y else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]


def near_copies(text, article_keys, min_stems=NEAR_MIN, share=NEAR_SHARE):
    """[(доля, предложение)] — предложения `text`, повторяющие скелет статьи
    (`article_keys` — key_stems источника)."""
    out = []
    for sent in sentences(text):
        st = key_stems(words(sent))
        if len(st) < min_stems:
            continue
        n, best = len(st), 0
        span = 2 * n
        step = max(1, n // 2)
        first = set(st)
        for i in range(0, max(1, len(article_keys) - n + 1), step):
            win = article_keys[i:i + span]
            if len(first & set(win)) < share * len(first):
                continue
            best = max(best, _lcs(st, win))
            if best == n:
                break
        if best >= share * n:
            out.append((round(best / n, 2), sent))
    return out


def _nwords(frag):
    # Слова через пробел: «Эйч-эс-би-си банк (РР)» — три слова, название, а не речь.
    return len([t for t in str(frag or '').split() if re.search(r'[0-9a-zа-яё]', t, re.I)])


def speech_fragments(text):
    """Куски в «елочках» от QUOTE_MIN_WORDS слов — чужие слова, не названия."""
    out = []
    for m in _SPEECH.finditer(str(text or '')):
        frag = m.group(1)
        if _nwords(frag) >= QUOTE_MIN_WORDS:
            out.append(frag)
    return out


def quote_attributed(text, frag, src_names=()):
    """Назван ли у цитаты говорящий или издание."""
    text = str(text or '')
    if SPEAKER_RE.search(text):
        return True
    pos = text.find(frag)
    tail = text[pos + len(frag):pos + len(frag) + 120] if pos >= 0 else ''
    if OUTLET_AFTER_QUOTE.match(tail.lstrip()) or OUTLET_AFTER_QUOTE.search('»' + tail[1:] if tail else ''):
        return True
    for name in src_names or ():
        name = str(name or '').strip()
        if len(name) >= 3 and name.lower() in text.lower():
            return True
    return False


def _without_speech(text):
    """Текст без кусков прямой речи: на их месте точка, чтобы соседние слова
    не склеились в чужую цепочку."""
    def repl(m):
        return ' . ' if _nwords(m.group(1)) >= QUOTE_MIN_WORDS else m.group(0)
    return _SPEECH.sub(repl, str(text or ''))


def check_text(field, text, texts, min_words=MIN_WORDS, quotes_in_texts=False, src_names=()):
    """Находки политики по одному полю. `texts` — источники (строки или
    `prepare()`); без источников проверяется только прямая речь."""
    text = str(text or '')
    out = []
    sources = prepare(texts)
    for frag in speech_fragments(text):
        if quotes_in_texts and sources and not any(flat(frag) in s.flat for s in sources):
            out.append(Finding(field, 'quote_altered', frag, _nwords(frag)))
        elif not quote_attributed(text, frag, src_names):
            out.append(Finding(field, 'quote_without_source', frag, _nwords(frag)))
    if not sources:
        return out
    body = _without_speech(text)
    plain = words(plain_words(body))
    best_run = None
    for s in sources:
        for n, span in common_runs(plain, s, min_words):
            if not best_run or n > best_run.words:
                best_run = Finding(field, 'verbatim_run', span, n)
    if best_run:
        out.append(best_run)
    best_near = None
    for s in sources:
        for share, sent in near_copies(plain_words(body), s.keys):
            if not best_near or share > best_near.share:
                best_near = Finding(field, 'near_copy', sent, len(key_stems(words(sent))), share)
    if best_near:
        out.append(best_near)
    return out


def get_field(card, field):
    if '.' in field:
        a, b = field.split('.', 1)
        v = card.get(a)
        return v.get(b) if isinstance(v, dict) else None
    return card.get(field)


def card_prose(card):
    """(поле, текст) по прозаическим полям и заметкам этапов — то, к чему
    политика применяется."""
    for f in sorted(PROSE_FIELDS):
        v = get_field(card, f)
        if isinstance(v, str) and v.strip() not in ('', '—'):
            yield f, v
    for i, e in enumerate(card.get('events') or []):
        v = e.get('note') if isinstance(e, dict) else None
        if isinstance(v, str) and v.strip() not in ('', '—'):
            yield 'events[%d].note' % i, v


def src_names(card):
    """Имена изданий из `src` карточки — ими можно подписать цитату."""
    out = []
    for s in card.get('src') or []:
        if isinstance(s, (list, tuple)) and s and isinstance(s[0], str):
            out.append(s[0])
    return out


def check_card(card, texts, companies=None, min_words=MIN_WORDS):
    """Находки политики по всей карточке (структурные поля не смотрятся).
    `companies` принимается для единообразия вызова и пока не нужен."""
    out = []
    names = src_names(card)
    for field, text in card_prose(card):
        out.extend(check_text(field, text, texts, min_words=min_words, src_names=names))
    return out


def describe(f):
    """Строка находки для человека (приемка, отказ записи)."""
    if f.kind == 'verbatim_run':
        return '%d слов подряд как в источнике в %s: «%s…» — пересказать своими словами' % (f.words, f.field, f.span[:80])
    if f.kind == 'near_copy':
        return ('в %s предложение повторяет предложение источника с заменой отдельных слов (%d%% основ в том же '
                'порядке): «%s» — пересказать по-своему: другой порядок, своя мысль' % (f.field, round(100 * f.share), f.span[:90]))
    if f.kind == 'quote_without_source':
        return ('в %s чужие слова в кавычках («%s…») без того, кто это сказал, и без издания — назовите '
                'говорящего или издание либо перескажите без кавычек' % (f.field, f.span[:60]))
    if f.kind == 'quote_altered':
        return ('в %s в кавычках не дословные слова источника («%s…») — цитату нельзя менять: дословно '
                'или пересказом без кавычек' % (f.field, f.span[:60]))
    return '%s: %s' % (f.kind, f.span[:80])


def self_check():
    """Таблица примеров политики — вызывается тестом и `review._self_check`."""
    src = ('Покупателю придется учесть обременение: с 2021 года объект арендует управляющая '
           'компания «Azimut Hotels», договор рассчитан на 25 лет. Продажа состоялась по '
           'минимальной цене, поскольку других претендентов на актив не нашлось, сообщили в министерстве.')
    kinds = lambda t, **kw: [f.kind for f in check_text('extra', t, [src], **kw)]  # noqa: E731
    # Пересказ — ок.
    assert kinds('Гостиница продана вместе с арендой: ею управляет Azimut Hotels по договору на 25 лет, '
                 'а других покупателей не было, поэтому объект ушел по нижнему порогу цены.') == []
    # Копия — нарушение; одно замененное слово посреди цепочки ее не рвет.
    assert 'verbatim_run' in kinds('Продажа состоялась по минимальной цене, поскольку других претендентов на актив не нашлось.')
    assert 'verbatim_run' in kinds('Продажа состоялась по минимальной цене, потому что других претендентов на актив не нашлось.')
    assert 'near_copy' in kinds('Покупателю придется считаться с обременением: с 2021 года гостиницу арендует '
                                'управляющая компания «Azimut Hotels», договор заключен на 25 лет.')
    # Прямая речь с говорящим — ок; с изданием после кавычки — ок; без — нарушение.
    sp = '«Продажа состоялась по минимальной цене, поскольку других претендентов на актив не нашлось»'
    assert kinds(sp + ', — сказал министр Иван Петров.') == []
    assert kinds(sp + ', — сообщает «Коммерсантъ».') == []
    assert kinds('Министерство: ' + sp + '.') == ['quote_without_source']
    assert kinds('Министерство: ' + sp + '.', src_names=['Коммерсантъ']) == ['quote_without_source']
    assert kinds('Министерство сказало «Коммерсанту»: ' + sp + '.', src_names=['Коммерсантъ']) == []
    # Измененная цитата при записи по цитате — нарушение.
    assert kinds('«Продажа прошла по минимальной цене, поскольку других претендентов на актив не нашлось», '
                 '— сказал министр.', quotes_in_texts=True) == ['quote_altered']
    # Заголовок и стороны — вне политики.
    card = {'title': src[:60], 'seller': 'Минимущество', 'extra': 'Свой текст.', 'src': [['Ъ', 'http://x']]}
    assert check_card(card, [src]) == []
    assert {f.field for f in check_card(dict(card, extra=src), [src])} == {'extra'}


# ---------------------------------------------------------------------------
# Очередь рутины качества: источники из сети, отчет для человека.
# ---------------------------------------------------------------------------
import json  # noqa: E402
import os  # noqa: E402
import random  # noqa: E402
import sys  # noqa: E402
from concurrent.futures import ThreadPoolExecutor  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'


def fetch(url):
    import httpx
    try:
        r = httpx.get(url, headers={'User-Agent': UA}, timeout=20, follow_redirects=True)
        return r.status_code, r.text
    except Exception:                                       # noqa: BLE001
        return 0, ''


def check_card_online(deal, max_sources=3):
    """{'id', 'title', 'fetched': n, 'findings': [Finding]} — источники карточки
    качаются из сети (агрегаторы — нет), проза сверяется политикой."""
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    from pipeline import source_names
    res = {'id': deal['id'], 'title': deal.get('title', ''), 'fetched': 0, 'findings': []}
    srcs = [s for s in (deal.get('src') or []) if isinstance(s, list) and len(s) > 1
            and str(s[1]).startswith('http') and not source_names.is_aggregator(s[1])]
    texts = []
    for name, url in srcs[:max_sources]:
        code, html = fetch(url)
        if code != 200 or len(html) < 2000:
            continue
        res['fetched'] += 1
        texts.append(html)
    if texts:
        res['findings'] = check_card(deal, prepare(texts))
    return res


def report(rows):
    for r in rows:
        if not r['findings']:
            continue
        print('%s %s' % (r['id'], r['title'][:60]))
        for f in sorted(r['findings'], key=lambda f: (f.kind, -(f.words or 0))):
            print('   %s' % describe(f))


def copied_from_fixes(deals):
    """{id: [поля]} — проза, повторяющая цитату, по которой ее записали.

    Без сети: цитаты правок review.py (`fixes/`) — это и есть текст
    источника, из которого поле переносили. Мера та же, что у записи
    нового текста (политика выше). Замер 14 октября 2026 (старой мерой):
    1095 из 1481 карточки на сайте; 31 октября 2026 (политика: 8 обычных
    слов с одной заменой или скелет предложения): 318 из 1531.
    """
    sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
    import review
    quotes = {}
    for f in review.FIXES:
        q = f.get('quote')
        if isinstance(q, str) and len(q) > 40 and f.get('field') in PROSE_FIELDS:
            quotes.setdefault(f['id'], []).append(q)
    out = {}
    for d in deals:
        if d['id'] not in quotes:
            continue
        found = sorted({f.field for f in check_card(d, [' '.join(quotes[d['id']])])
                        if f.kind in ('verbatim_run', 'near_copy')})
        if found:
            out[d['id']] = found
    return out


def main(argv):
    data = json.load(open(DATA, encoding='utf-8'))
    deals = data['deals']
    if '--from-fixes' in argv:
        i = argv.index('--from-fixes')
        n = int(argv[i + 1]) if len(argv) > i + 1 and argv[i + 1].isdigit() else 10
        found = copied_from_fixes(deals)
        print('Проза повторяет цитату источника у %d карточек из %d (полей: %d).'
              % (len(found), len(deals), sum(map(len, found.values()))))
        fresh = sorted((d for d in deals if d['id'] in found),
                       key=lambda d: str(d.get('date') or ''), reverse=True)
        for d in fresh[:n]:
            print('%s  %s  %s — %s' % (d['id'], str(d.get('date') or '')[:10],
                                       d.get('title', '')[:70], ', '.join(found[d['id']])))
        return 0
    if '--card' in argv:
        deal = next(d for d in deals if d['id'] == argv[argv.index('--card') + 1])
        r = check_card_online(deal)
        print(json.dumps(dict(r, findings=[f._asdict() for f in r['findings']]), ensure_ascii=False, indent=1))
        return 0
    if '--sample' in argv:
        n = int(argv[argv.index('--sample') + 1])
        pool = [d for d in deals if d.get('src')]
        random.seed(7)
        random.shuffle(pool)
        chosen = pool[:n]
    else:
        n = int(argv[argv.index('--queue') + 1]) if '--queue' in argv and len(argv) > argv.index('--queue') + 1 \
            and argv[argv.index('--queue') + 1].isdigit() else 40
        chosen = sorted((d for d in deals if d.get('src')), key=lambda d: str(d.get('added') or d.get('date') or ''),
                        reverse=True)[:n]
    with ThreadPoolExecutor(max_workers=8) as ex:
        rows = list(ex.map(check_card_online, chosen))
    fetched = [r for r in rows if r['fetched']]
    hit = [r for r in fetched if r['findings']]
    by_kind = {k: sum(1 for r in fetched if any(f.kind == k for f in r['findings'])) for k in KINDS}
    print('Проверено карточек: %d, источник открылся у %d, с находками %d: дословные куски (от %d обычных слов, '
          'одна замена прощается) у %d, скелет чужого предложения у %d, цитата без автора у %d.'
          % (len(rows), len(fetched), len(hit), MIN_WORDS, by_kind['verbatim_run'], by_kind['near_copy'],
             by_kind['quote_without_source']))
    for th in (12, 20, 30):
        print('  от %d слов: %d' % (th, sum(1 for r in hit if any(f.kind == 'verbatim_run' and f.words >= th
                                                                   for f in r['findings']))))
    print()
    report(sorted(hit, key=lambda r: -max([f.words or 0 for f in r['findings']] or [0])))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
