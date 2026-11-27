# -*- coding: utf-8 -*-
"""Проверка правки даты по цитате для review.py (вынесено 26 ноября 2026:
review.py у потолка test_fix_batches_live_in_separate_files)."""
import re

MONTHS = {'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
          'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12}

EN_MONTHS = ['Jan(?:uary)?', 'Feb(?:ruary)?', 'Mar(?:ch)?', 'Apr(?:il)?', 'May', 'June?', 'July?',
             'Aug(?:ust)?', 'Sep(?:t(?:ember)?)?', 'Oct(?:ober)?', 'Nov(?:ember)?', 'Dec(?:ember)?']


def date_is_supported(old, new, quote):
    """Дату можно уточнить внутри известного года, но не перенести в другой.

    Менять год — значит утверждать новое; тот же порог, что у
    `fix_placeholder_dates.py`. День и месяц обязаны быть названы в цитате
    прописью («закрыта 4 мая»), иначе это не перенос, а догадка.
    """
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', str(new or '')):
        return 'новая дата не в формате ГГГГ-ММ-ДД'
    if str(old or '')[:4] != new[:4]:
        return 'год не совпадает: уточнять день можно, переносить год — нет'
    day, month, year = int(new[8:10]), int(new[5:7]), int(new[:4])
    for word, num in MONTHS.items():
        if num == month and re.search(r'(?<!\d)0?%d\s+%s' % (day, word), quote, re.I):
            return None
    # Та же дата цифрами («02.12.2025», «2026-07-07» в реестре) или по-английски
    # («31 May», «May 31») — 26 ноября 2026: даты из реестра и отчетов иностранных
    # продавцов не проходили, хотя день и месяц в источнике названы.
    if re.search(r'(?<!\d)0?%d\.0?%d\.%d(?!\d)' % (day, month, year), quote) \
            or re.search(r'(?<!\d)%d-%02d-%02d(?!\d)' % (year, month, day), quote):
        return None
    en = EN_MONTHS[month - 1]
    if re.search(r'(?<!\d)0?%d(?:st|nd|rd|th)?\s+%s' % (day, en), quote, re.I) \
            or re.search(r'%s\.?\s+0?%d(?:st|nd|rd|th)?(?!\d)' % (en, day), quote, re.I):
        return None
    return 'в цитате нет «%d %s»' % (day, [w for w, n in MONTHS.items() if n == month][0])
