# -*- coding: utf-8 -*-
"""Предмет сделки — в именительном падеже, а не в том, что диктует глагол.

ЧТО СЛОМАНО. `guess_parties()` в draft.py вырезает предмет ПОДСТРОКОЙ из
заголовка после глагола покупки/продажи — а русское управление ставит его не
в именительном: «купил X» — X в винительном («производственную базу»),
«присоединение X» — X в родительном («Дальневосточного банка»), «долю в X» —
X в предложном («производителе картошки для чипсов»). Владелец увидел это в
живых постах канала 9 августа: «Предмет: Дальневосточного банка» вместо
«Дальневосточный банк» — и так почти в каждой автособранной карточке.

ПОЧЕМУ НЕ ПРОСТО «ВЗЯТЬ НАЧАЛЬНУЮ ФОРМУ». pymorphy сводит слово к лемме
(«банка» -> «банк»), а не согласует всё словосочетание: прилагательное перед
существительным осталось бы в старом падеже («дальневосточного банк»). Нужно
согласовать род/число головы и её прилагательных вместе — и то только для
головы словосочетания, а не для всего хвоста: в «производитель картошки для
чипсов» после головы «производитель» идёт ЗАВИСИМЫЙ родительный оборот
(«картошки для чипсов»), и его трогать нельзя — это грамматически верно уже
сейчас.

ПОЧЕМУ ТАК МНОГО ОТКАЗОВ (ниже — специально, не жаль сработавших случаев).
Первая версия правила била и по хорошим случаям: «45% сети X» стало «45%
сеть X» (после «%» всегда родительный — числительное управляет, а не
сказуемое); «Группа компаний X» стало «Группа компании X» (голова — первое
слово «Группа», уже именительный, а «компаний» — зависимый родительный,
взятый по ошибке за голову); «Рив Гош» стало «Рив Гоши» (bare-слово без
контекста — pymorphy угадывает форму наугад, а это вообще имя бренда);
«права на СУБД «Персей»» стало «право на СУБД» (слово «права» —
самостоятельно неоднозначно: родительный ед. числа «права» И именительный/
винительный мн. числа «права» — одна и та же словоформа, и без контекста
предложения не разобрать, что имелось в виду; смена числа меняет смысл, а
не только падеж). Отсюда правила ниже: не трогаем то, что после «%»/числа
(там правит числительное, не позиция в предложении); голова — ПЕРВОЕ
существительное словосочетания, дальше не ищем; ничего после головы не
трогаем; слово с заглавной буквы не трогаем (похоже на имя/бренд); слово,
для которого есть другой разбор той же леммы с именительным падежом, не
трогаем (неоднозначно); всё, что в «кавычках» или граничит с ними, не
трогаем вовсе.

ЗАМЕР (9 августа, deals_promoted.json + pending.json, 183 карточки с
`asset`): 19 срабатываний, ни одного ложного — каждое проверено вручную и
описано в `pipeline/fix_asset_case.py`.
"""
import re

import pymorphy3

_morph = pymorphy3.MorphAnalyzer()

QUOTE_CHARS = '«»"“”„'


def to_nominative_asset(phrase):
    """(нормализованная строка, изменилось ли). Правило нарочно
    консервативное — см. docstring модуля: лучше пропустить сомнительный
    случай, чем сломать верный."""
    phrase = (phrase or '').strip()
    if not phrase or '%' in phrase:
        return phrase, False
    words = phrase.split(' ')
    if re.match(r'^\d', words[0]):
        return phrase, False

    head_idx = None
    for i, w in enumerate(words):
        if any(c in w for c in QUOTE_CHARS):
            return phrase, False
        if not w or not re.match(r'^[А-Яа-яЁё-]+$', w):
            return phrase, False
        p = _morph.parse(w)[0]
        if 'NOUN' in p.tag:
            head_idx = i
            break
        if not ('ADJF' in p.tag or 'PRTF' in p.tag):
            return phrase, False
    if head_idx is None:
        return phrase, False

    head_word = words[head_idx]
    if head_word[:1].isupper():
        return phrase, False                   # похоже на имя/бренд
    parses = _morph.parse(head_word)
    head = parses[0]
    if head.tag.case == 'nomn':
        return phrase, False
    if any(g in head.tag for g in ('Name', 'Surn', 'Patr', 'Geox')):
        return phrase, False
    if head.score < 0.1:
        return phrase, False
    if any(p.normal_form == head.normal_form and p.tag.case == 'nomn'
           for p in parses[1:]):
        return phrase, False                   # та же лемма даёт им. падеж — неоднозначно

    number = head.tag.number
    gender = head.tag.gender
    targets = {'nomn'}
    if number:
        targets.add(number)
    if gender and number != 'plur':
        targets.add(gender)
    head_infl = head.inflect(targets)
    if not head_infl or head_infl.word == head_word:
        return phrase, False

    def cased(new, orig):
        return new[:1].upper() + new[1:] if orig[:1].isupper() else new

    out = list(words)
    out[head_idx] = cased(head_infl.word, head_word)
    changed = out[head_idx].lower() != head_word.lower()

    for i in range(head_idx - 1, -1, -1):
        w = words[i]
        infl = _morph.parse(w)[0].inflect(targets)
        if infl and infl.word != w.lower():
            out[i] = cased(infl.word, w)
            changed = True

    return ' '.join(out), changed
