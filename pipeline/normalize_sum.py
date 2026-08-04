# -*- coding: utf-8 -*-
"""Единообразная запись суммы сделки.

ЧТО БЫЛО НЕ ТАК. Сумма — самое заметное число на карточке, и записана она была
как придётся: «руб.» у 435 карточек, «рублей» у 182, «₽» у 11; доллар — «$»,
«USD» и «долл.». Пометка «это оценка, а не раскрытая цена» встречалась в
десятке формулировок: «(оценка)», «(оценка аналитиков)», «(по оценкам
экспертов)», «(экспертная оценка с учётом долга)», «оценочно».

Хуже того, у 135 карточек на обложке стояло «Не раскрыта», хотя в линзе
«Экономист» число было. Пользователь листал ленту и не видел суммы, которая у
нас есть.

ЧТО ДЕЛАЕМ.
  * Валюта — только значком: `₽` после числа (русская традиция), `$` и `€`
    перед числом (как в деловой прессе и как уже записано в большинстве
    карточек). Слова «рублей», «руб.», «USD», «долл.», «евро» уходят.
  * Пометка оценки — всегда «(по оценке)». Кто именно оценил, на обложке не
    нужно: это видно по ссылке на источник, а подробность сохраняется в поле
    «Оценка и дисконт» (`eco.val`), если её там ещё не было.
  * `sum` (обложка и лента) — короткая строка: число, единица, значок валюты и
    при необходимости «(по оценке)». `eco.sum` (линза «Экономист») — та же
    нормализация, но с сохранением содержательных оговорок.
  * Если на обложке «Не раскрыта», а число есть — число выносится на обложку.

ЧЕГО НЕ ДЕЛАЕМ. Не выбрасываем скобки, которые объясняют само число, а не его
достоверность: «$2 млрд (по $59 за акцию)», «230 млн ₽ (имплицитная оценка
100% компании — 469 млн ₽)». Признак — в скобках есть цифры или расчёт.
Не сочиняем сумму там, где её нет: строка должна содержать число, единицу
(тыс./млн/млрд/трлн) И валюту, иначе карточка остаётся без суммы.

Запуск:
    python3 pipeline/normalize_sum.py            # сухой прогон
    python3 pipeline/normalize_sum.py --write    # записать
"""
import collections
import json
import re
import sys

PATH = 'static/data/deals_promoted.json'

UNDISCLOSED = 'Не раскрыта'
PLACEHOLDER = re.compile(r'^(?:—|-|нет\s+данных)\s*$', re.I)
# ВНИМАНИЕ: без завершающего \b. С ним правило молча не работало: «не раскры»
# в слове «раскрыта» продолжается буквой, границы слова там нет, и ни одна
# карточка с «Не раскрыта» под правило не попадала.
NO_SUM = re.compile(r'^(?:не\s+раскры|официально\s+не|публично\s+не|не\s+сообщал|'
                    r'сумма\s+не|нет\s+данных|[—-]\s*$)', re.I)

# Валюта: как пишут в базе -> как пишем везде
RUB = r'(?:₽|руб\.?|рубл(?:ей|я|ь|ями)|RUB)'
USD = r'(?:\$|USD|долл(?:\.|аров(?:\s+США)?|ара)?)'
EUR = r'(?:€|EUR|евро)'

UNIT = r'(?:тыс\.?|млн|млрд|трлн|тысяч)'
NUM = r'\d[\d\s ]*(?:[.,]\d+)?'
# «около 4», «более 3», «не менее 21,2», «~1», «до $150»
PRE = r'(?:около|порядка|более|свыше|примерно|до|от|не\s+менее|не\s+более|~|≈)'

# Сумма целиком: [приставка] число[–число] единица валюта  (валюта может стоять
# и перед числом: «$150-200 млн»)
AMOUNT = re.compile(
    r'(?P<pre>' + PRE + r')?\s*'
    # Значок ПЕРЕД числом: у доллара и евро это норма, а «₽25 млрд» —
    # чужая запись, попавшая из англоязычного источника. Узнаём её здесь,
    # чтобы правило перевернуло значок назад, а не прошло мимо суммы.
    r'(?P<cur_pre>' + USD + r'|' + EUR + r'|₽)?\s*'
    r'(?P<n1>' + NUM + r')'
    r'(?:\s*[–—-]\s*(?P<n2>' + NUM + r'))?'
    r'\s*(?P<unit>' + UNIT + r')?'
    r'\s*(?P<cur_post>' + RUB + r'|' + USD + r'|' + EUR + r')?',
    re.I)

# Оговорка «это оценка», а не раскрытая цена
ESTIMATE = re.compile(
    r'оценк|оценив|оценочн|эксперт|предположительн|расчётн|расчетн|прикид|'
    r'по\s+мнению|аналитик', re.I)

# Скобка помечает недостоверность, только если С НЕЁ И НАЧИНАЕТСЯ разговор об
# оценке. Иначе под правило попадала оговорка совсем о другом: «(CarPrice и доли
# в компаниях переданы сверх этой суммы, их отдельная оценка не указана)» —
# здесь оценка отсутствует у ДРУГИХ активов, а 8 млрд ₽ вполне достоверны.
EST_PAREN = re.compile(r'^\s*(?:по\s+)?(?:оценк|оценочн|экспертн|предположительн|'
                       r'расчётн|расчетн|эксперт)', re.I)

# Числа, которые ценой сделки НЕ являются: стартовая цена торгов, запрашиваемая
# цена, взятый долг, упущенная прибыль. Такие на обложку не выносим — иначе
# «не раскрыта (менеджмент берёт долг 45,9 млрд руб.)» превратится в сумму сделки.
NOT_PRICE = re.compile(r'стартов|начальн|запрашива|минимальн\w*\s+(?:цен|стоимост|оценочн)|упущенн|'
                       r'берёт\s+долг|берет\s+долг|долг\b|обязательств', re.I)

# Скобка объясняет ЧИСЛО (расчёт, курс, доля), а не его достоверность —
# такие оставляем как есть.
EXPLAINS = re.compile(r'\d')

# Диапазон «от 40 до 100 млн руб.»: без отдельного правила регулярка цеплялась
# за «до 100 млн» и нижняя граница молча пропадала.
FROM_TO = re.compile(
    r'\bот\s+(?P<n1>' + NUM + r')\s*(?:' + UNIT + r')?\s*(?:' + RUB + r'|' + USD + r'|' + EUR + r')?'
    r'\s+до\s+(?P<n2>' + NUM + r')\s*(?P<unit>' + UNIT + r')\s*'
    r'(?P<cur>' + RUB + r'|' + USD + r'|' + EUR + r')', re.I)


def outside_parens(text):
    return re.sub(r'\([^()]*\)', ' ', text)


def is_estimate(text):
    """Оценка ли это — про САМО число, а не про соседнее.

    Скобка с цифрами объясняет другое число («230 млн ₽ (имплицитная оценка
    100% компании — 469 млн ₽)») и пометкой недостоверности не является: иначе
    раскрытая в отчётности сумма поехала бы на обложку как «по оценке».
    """
    if ESTIMATE.search(outside_parens(text)):
        return True
    for m in re.finditer(r'\(([^()]*)\)', text):
        if EST_PAREN.match(m.group(1)):
            return True
    return False


def norm(s):
    return re.sub(r'[\s ]+', ' ', s or '').strip()


def currency_of(text):
    if re.search(USD, text, re.I):
        return '$'
    if re.search(EUR, text, re.I):
        return '€'
    if re.search(RUB, text, re.I):
        return '₽'
    return None


def tidy_number(n):
    """Убираем неразрывные пробелы внутри числа, оставляя разряды читаемыми."""
    return re.sub(r'[\s ]+', ' ', n).strip()


def context_ok(t, start):
    """Число рядом со словом «стартовая цена» или «долг» — не цена сделки."""
    # Смотрим и вперёд: «280,8 млрд руб. (стартовая цена аукциона)» — пометка
    # стоит ПОСЛЕ числа, и окна только назад не хватало.
    return not NOT_PRICE.search(t[max(0, start - 60):start + 60])


def hidden_ok(t, start):
    """Строка начинается с «не раскрыта» — число можно вынести, только если
    рядом сказано, что это оценка сделки. Иначе на обложку уедет чужое число:
    «не раскрыта (менеджмент берёт долг 45,9 млрд руб.)»."""
    if not NO_SUM.match(t):
        return True
    return bool(ESTIMATE.search(t[max(0, start - 80):start]))


def short_sum(text):
    """Короткая строка для обложки: число + единица + значок валюты.

    Возвращает None, если внятной суммы в тексте нет. Требуем и единицу, и
    валюту: без этого «до 30 июня 2026 года» превратилось бы в сумму.
    """
    t = norm(text)
    m = FROM_TO.search(t)
    if m and context_ok(t, m.start()) and hidden_ok(t, m.start()):
        sign = currency_of(m.group('cur'))
        unit = m.group('unit').lower().rstrip('.')
        unit = 'тыс.' if unit.startswith('тыс') else unit
        num = tidy_number(m.group('n1')) + '–' + tidy_number(m.group('n2'))
        head = num + ' ' + unit
        return f'{head} {sign}' if sign == '₽' else f'{sign}{head}'
    for m in AMOUNT.finditer(t):
        unit = m.group('unit')
        cur = m.group('cur_pre') or m.group('cur_post')
        if not cur:
            continue
        # Без единицы принимаем только крупное число: «$550 000» — сумма,
        # а «$5 за акцию» — нет.
        if not unit and len(re.sub(r'\D', '', m.group('n1'))) < 4:
            continue
        # Если ПЕРВОЕ число оказалось не ценой сделки, дальше не идём: следующее
        # в строке — уже про что-то другое. Иначе «Минимальная оценочная
        # стоимость проекта — 3,45 млрд руб.; оценка затрат на гостиницу…»
        # выносила на обложку 15–17 млн ₽ из второй половины фразы.
        if not context_ok(t, m.start()) or not hidden_ok(t, m.start()):
            return None
        sign = currency_of(cur)
        if not sign:
            continue
        if unit:
            unit = unit.lower().replace('тысяч', 'тыс.').rstrip('.')
            unit = 'тыс.' if unit.startswith('тыс') else unit
        num = tidy_number(m.group('n1'))
        if m.group('n2'):
            num += '–' + tidy_number(m.group('n2'))
        pre = (m.group('pre') or '').lower().strip()
        # «от»/«до» в паре с диапазоном избыточны, а поодиночке нужны
        if pre in ('~', '≈'):
            pre = '≈'
        head = (num + ' ' + unit) if unit else num
        out = f'{head} {sign}' if sign == '₽' else f'{sign}{head}'
        if not pre:
            return out
        # «≈» пишется вплотную к числу, слова-приставки — через пробел
        return pre + out if pre == '≈' else pre + ' ' + out
    return None


def normalize_full(text):
    """`eco.sum`: та же валюта значком, оговорка про оценку — одной формой."""
    t = norm(text)
    # «₽25 млрд» — значок ПЕРЕД числом: так пишут в англоязычных источниках, и
    # запись просачивается к нам. Переставляем значок назад, само число не
    # трогая. Обратной правки для $ и € здесь нет и быть не должно: у них
    # позиция перед числом — как раз наше соглашение.
    t = re.sub(r'₽\s*(?P<n>' + NUM + r')(?:\s*(?P<u>' + UNIT + r'))?',
               lambda m: m.group('n').strip() + (' ' + m.group('u') if m.group('u') else '') + ' ₽',
               t)
    # валюта -> значок
    t = re.sub(r'\s*(?:' + RUB + r')(?=$|[\s.,;)])', ' ₽', t)
    t = re.sub(r'(?<![\w])(?:USD|долл(?:\.|аров(?:\s+США)?|ара)?)', '$', t, flags=re.I)
    t = re.sub(r'(?<![\w])(?:EUR|евро)', '€', t, flags=re.I)
    t = re.sub(r'\s+([₽€])', r' \1', t)
    t = re.sub(r'\$\s+', '$', t)
    # Скобка, которая говорит только «это оценка такого-то», заменяется единой
    # пометкой: кто оценил, уходит в «Оценку и дисконт». Скобку с цифрами не
    # трогаем — она объясняет расчёт, а не достоверность.
    def one_form(m):
        inner = m.group(1)
        if EST_PAREN.match(inner) and not EXPLAINS.search(inner):
            return '(по оценке)'
        return m.group(0)
    t = re.sub(r'\(([^()]*)\)', one_form, t)
    return re.sub(r'\s{2,}', ' ', t).strip()


def estimate_detail(text):
    """Кусок с указанием, кто оценил, — его место в «Оценке и дисконте»."""
    for m in re.finditer(r'\(([^()]{0,200})\)', text):
        inner = m.group(1)
        if ESTIMATE.search(inner) and len(inner) > 12:
            return inner.strip()
    return None


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)

    stats = collections.Counter()
    changes = []

    for d in data['deals']:
        eco = d.setdefault('eco', {})
        cover_old = norm(d.get('sum'))
        full_old = norm(eco.get('sum'))

        source = full_old if (full_old and not PLACEHOLDER.match(full_old)) else cover_old
        if not source or PLACEHOLDER.match(source):
            continue

        is_est = is_estimate(source)
        full_new = normalize_full(source)
        short = short_sum(source)

        # Обложку не пересобираем из числа: в скобках может стоять оговорка,
        # меняющая смысл («140 млрд ₽ (заявлено как объём инвестиций в проект)»).
        # Нормализуем запись, а короткую форму строим только там, где на обложке
        # суммы нет вовсе, — чтобы вынести известное число из линзы.
        if not cover_old or NO_SUM.match(cover_old):
            cover_new = (short + (' (по оценке)' if is_est else '')) if short else UNDISCLOSED
        else:
            cover_new = normalize_full(cover_old)

        # «Сумма сделки» на линзе — крупное число, а не абзац. Если исходная
        # строка длиннее короткой формы, оставляем в поле только число, а всё
        # остальное (кто оценил, альтернативные оценки, оговорки) переносим в
        # «Оценку и дисконт» — поле ровно для этого и предназначено.
        val_new = norm(eco.get('val'))
        val_empty = not val_new or PLACEHOLDER.match(val_new)
        if short:
            full_new = short + (' (по оценке)' if is_est else '')
            tail = normalize_full(source)
            if norm(tail) != norm(full_new):
                piece = tail[0].upper() + tail[1:]
                if val_empty:
                    val_new = piece
                elif piece not in val_new:
                    val_new = val_new.rstrip(' .;') + '; ' + piece[0].lower() + piece[1:]
                stats['подробность суммы перенесена в «Оценку и дисконт»'] += 1

        if cover_new != cover_old:
            stats['обложка: сумма приведена к единому виду'] += 1
            if NO_SUM.match(cover_old or UNDISCLOSED) and short:
                stats['  из них: число вынесено на обложку из линзы'] += 1
        if full_new != full_old:
            stats['линза: валюта и оговорка приведены к единому виду'] += 1

        if (cover_new, full_new, val_new) != (cover_old, full_old, norm(eco.get('val'))):
            changes.append((d['id'], cover_old, cover_new, full_old, full_new, val_new))
            if write:
                d['sum'] = cover_new
                eco['sum'] = full_new
                if val_new:
                    eco['val'] = val_new

    print('РЕЗУЛЬТАТ:')
    for k, n in stats.most_common():
        print(f'  {n:5}  {k}')
    print(f'\nкарточек затронуто: {len(changes)}')

    print('\nПРИМЕРЫ:')
    for did, co, cn, fo, fn, _ in changes[:15]:
        print(f'  {did}')
        print(f'    обложка: {co[:70]!r} -> {cn[:70]!r}')
        if fo != fn:
            print(f'    линза:   {fo[:80]!r}\n          -> {fn[:80]!r}')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в', PATH)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
