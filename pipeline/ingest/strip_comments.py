# -*- coding: utf-8 -*-
"""Отрезать комментарии читателей от текста статьи перед сохранением.

ЗАЧЕМ. Проверка цитат (`review.quote_is_real()`) ищет цитату подстрокой во
ВСЕМ сохраненном тексте страницы и не знает, где кончилась статья. Если в
кэш попали комментарии под статьей, обрывок чужого мнения проходит проверку
как факт источника: так в карточку g004a92b7 (КРТ в Воронеже) попал «Грин
парк» из читательской поправки под статьей Абирега (known_issues/card.md,
«Выдуманный факт прошел проверку дословности»; бэклог A30, п. 1). Владелец:
«комментарии читателей конечно отрезаем».

ДВА ЯРУСА.
1. По разметке (`strip_comment_html`): из HTML вырезаются элементы, у
   которых класс или id называют блок комментариев (`comments`,
   `commentList`, `comment-item`, `disqus_thread`, `hypercomments`,
   `mc-container` у Cackle, `#respond` у WordPress, `reply_to_<n>`…). Режем
   ВЕСЬ элемент вместе с вложенным; остальной HTML не трогаем, поэтому
   страница без комментариев дает ровно тот же текст, что и раньше.
   Одинокое `comment` (без «s» и без слова-контейнера) не режем: так на
   части сайтов называют врезку «Комментарий эксперта» — это текст статьи.
2. По готовому тексту (`cut_comment_text`): когда разметки нет (текст из
   WebFetch для `save_source.py`) или сайт назвал классы невнятно, хвост
   отрезается по надежным словам начала блока: «Комментариев пока нет»,
   «Обсуждение закрыто», «Комментарии 5 Гость…», серия «имя / дата /
   Ответить»; слова-кнопки («Написать комментарий», «Комментарии (5)»)
   режут, только если сразу за ними форма или чужие сообщения. Только в хвосте:
   до метки должна стоять большая часть текста (`_tail_ok`), иначе метка —
   это шапка или меню сайта, а не конец статьи.

«Читайте также» НЕ режем: у 93.ru и сайтов той же сети этот блок стоит
ПОСРЕДИ статьи, и все, что ниже, — тоже статья.
"""
import re
from html.parser import HTMLParser

# Слова, по которым класс/id — точно блок комментариев. Сравнение по
# токену класса в нижнем регистре, после выкидывания всего, кроме букв:
# «commentList_tcD0l» → «commentlisttcdl», «comment-item_comment-item__pGafo»
# → «commentitemcommentitempgafo».
_CONTAINER = re.compile(
    r'comments'                      # comments, commentsBlock, b-comments, pin-comments
    r'|comment(?:list|form|item|wrapper|block|body|header|footer|thread|area|box|reply|txt|text|author|title|meta|card)'
    r'|disqus|hypercomment|cackle|mccontainer|mccomment'
    r'|replyto|commentreply'
    r'|kommentari|obsuzhdeni'          # транслит: id="kommentarii" у Абирега
)
# WordPress: <div id="respond"> — форма ответа; токен целиком, иначе
# «correspondent» (подпись корреспондента) сойдет за комментарий.
_EXACT = {'respond', 'cmlist'}
# Токены-признаки состояния, а не блока: «has-comments» на <article>
# означает «у статьи есть комментарии», а внутри — сама статья.
_STATE = re.compile(r'^(?:has|with|no|is|allow|show)[-_]|[-_](?:open|closed|enabled|disabled|on|off|count|counter)$')
# Врезка эксперта называется похоже, но это текст статьи.
_KEEP = re.compile(r'expert|quote|citat|opinion|interview|commentator|commentary')
# Обертки страницы целиком: даже с «comments» в классе их не режем.
_NEVER = {'html', 'body', 'main', 'article', 'head'}
_VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
         'meta', 'param', 'source', 'track', 'wbr'}


def _is_comment_block(tag, attrs):
    if tag in _NEVER:
        return False
    for name, value in attrs:
        if not value:
            continue
        if tag == 'form' and name in ('action', 'data-form') and 'comment' in value.lower():
            return True             # форма комментария: «Подпись», «Почта», согласия
        if name not in ('class', 'id'):
            continue
        for token in value.split():
            low = token.lower()
            if low in _EXACT:
                return True
            if _STATE.search(low) or _KEEP.search(low):
                continue
            if _CONTAINER.search(re.sub(r'[^a-z]', '', low)):
                return True
    return False


class _Spans(HTMLParser):
    """Находит [начало, конец) каждого блока комментариев верхнего уровня."""

    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.raw = raw
        self.lines = [0]
        for m in re.finditer('\n', raw):
            self.lines.append(m.end())
        self.spans = []
        self.open = None            # (тег, начало, глубина)

    def _offset(self):
        line, col = self.getpos()
        return self.lines[line - 1] + col

    def handle_starttag(self, tag, attrs):
        if tag in _VOID:
            return
        if self.open:
            if tag == self.open[0]:
                self.open[2] += 1
            return
        if _is_comment_block(tag, attrs):
            self.open = [tag, self._offset(), 1]

    def handle_endtag(self, tag):
        if not self.open or tag != self.open[0]:
            return
        self.open[2] -= 1
        if self.open[2] == 0:
            pos = self._offset()
            end = self.raw.find('>', pos)
            self.spans.append((self.open[1], len(self.raw) if end < 0 else end + 1))
            self.open = None

    def close(self):
        super().close()
        if self.open:               # блок не закрыт до конца файла — режем до конца
            self.spans.append((self.open[1], len(self.raw)))
            self.open = None


def strip_comment_html(raw_html):
    """HTML без блоков комментариев; остальное — байт в байт как было."""
    if not raw_html:
        return raw_html
    # Внутри <script> встречаются строки с «<div class="comments">» —
    # парсер их не трогает (это CDATA), позиции остаются верными.
    parser = _Spans(raw_html)
    try:
        parser.feed(raw_html)
        parser.close()
    except Exception:               # кривой HTML — лучше старое поведение, чем падение забора
        return raw_html
    if not parser.spans:
        return raw_html
    out, pos = [], 0
    for start, end in parser.spans:
        if start < pos:
            continue
        out.append(raw_html[pos:start])
        out.append(' ')
        pos = end
    out.append(raw_html[pos:])
    return ''.join(out)


# --- ярус 2: по готовому тексту ------------------------------------------

# Метки, которые сами по себе — начало блока комментариев: в тексте
# статьи так не пишут.
_STRONG = re.compile(
    r'Комментариев(?: к материалу)? (?:пока )?нет'
    r'|Пока никто не оставил'
    r'|Комментарии\s+\d{1,5}\s+(?:Гость|Читать все|все комментарии|Сначала)'
    r'|Ctrl\+Enter\s+Комментарии\s+\d'
    r'|(?:Читать|Показать) все комментарии'
    r'|Обсуждение закрыто'
    r'|Чтобы участвовать в дискуссии'
    r'|Будьте первым,? кто (?:оставит )?комментари',
    re.I)
# Метки-кнопки: «Написать комментарий» у старой «Фонтанки» стоит ПОД
# ЗАГОЛОВКОМ, до статьи; «Комментарии (0)» бывает счетчиком у даты. Такая
# метка режет, только если рядом за ней — форма или чужие сообщения
# (`_NEAR`) либо еще одна метка.
_WEAK = re.compile(
    r'Ваш комментарий'
    r'|(?:Добавить|Оставить|Написать|Отправить) комментарий'
    r'|Комментари(?:и|ев)\s*\(\s*\d{1,5}\s*\)'
    r'|ссылка на комментарий'
    r'|Обсудить с другими читателями'
    r'|Чтобы оставить комментарий'
    r'|Правила (?:комментирования|комментариев)\b',
    re.I)
_NEAR = re.compile(
    r'Ответить|\bГость\b|Отправить|модерац|персональных данных'
    r'|авторизуйтесь|Войдите|зарегистрируйтесь|Сначала (?:новые|старые)'
    r'|\bИмя\b|\+\d+ –\d+', re.I)
_NEAR_WINDOW = 600
# «Ответить» после имени и даты — карточка читательского комментария
# (bnkomi, ura, chelny-biz, smart-lab, business-gazeta). В тексте из
# WebFetch это отдельные строки, в тексте `article_text()` — одна строка.
_REPLY_LINE = re.compile(r'^\s*Ответить\s*$', re.M | re.I)
_DATE_LINE = re.compile(r'\d{1,2}[ .](?:\d{2}|[а-я]+)[ .,]*(?:\d{4})?[ г.,]*\d{1,2}:\d{2}', re.I)
_DATE_REPLY = re.compile(
    r'(?:\(?\d{1,2}[ .](?:\d{2}|[А-Яа-я]+)[ .,]*(?:\d{4})?[ г.,]*)?'
    r'\d{1,2}:\d{2}(?::\d{2})?\)?\s+Ответить', re.I)


def _tail_ok(text, pos):
    """Метка годится как начало комментариев, только если статья уже
    позади: перед меткой не меньше 500 знаков и не меньше пятой части
    текста. Пятая, а не половина: у 93.ru, «Фонтанки», E1 и других сайтов
    той же сети после комментариев идет еще длинная лента чужих новостей,
    и комментарии начинаются на 20–30% текста страницы."""
    return pos >= 500 and pos >= len(text) / 5


def cut_comment_text(text):
    """(текст без хвоста комментариев, сколько знаков отрезано)."""
    text = text or ''
    cut = None
    for m in _STRONG.finditer(text):
        if _tail_ok(text, m.start()):
            cut = m.start()
            break
    for m in _WEAK.finditer(text):
        if cut is not None and m.start() >= cut:
            break
        after = text[m.end():m.end() + _NEAR_WINDOW]
        if _tail_ok(text, m.start()) and (_NEAR.search(after) or _WEAK.search(after)
                                          or _STRONG.search(after)):
            cut = m.start()
            break
    replies = list(_REPLY_LINE.finditer(text))
    if len(replies) >= 2:
        first = replies[0].start()
        # шаг назад на «имя» и «дату» над первой «Ответить»
        head = text[:first].rstrip('\n')
        lines = head.split('\n')
        back = 0
        for i in range(1, min(4, len(lines)) + 1):
            if _DATE_LINE.search(lines[-i]):
                back = i + 1 if len(lines) > i else i
                break
        start = len('\n'.join(lines[:len(lines) - back])) if back else first
        if _tail_ok(text, start) and (cut is None or start < cut):
            cut = start
    pairs = list(_DATE_REPLY.finditer(text))
    if len(pairs) >= 2 and _tail_ok(text, pairs[0].start()) and (cut is None or pairs[0].start() < cut):
        cut = pairs[0].start()
    if cut is None:
        return text, 0
    head = text[:cut].rstrip()
    # заголовок блока («Комментарии», «Обсуждение») перед меткой — тоже блок
    head = re.sub(r'(?:Комментарии|Обсуждение)\s*(?:\(?\s*\d+\s*\)?)?\s*$', '', head, flags=re.I).rstrip()
    return head, len(text) - len(head)
