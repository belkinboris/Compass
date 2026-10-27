"""Карточка так, как ее видит читатель на сайте: три экрана и пост, текстом.

Нужна второму читателю (`second_reading.py --queue`): до 27 октября 2026 он
получал поля с вопросом к каждому и не видел карточку целиком — «Обзор» с
«Не раскрыта» рядом с «Экономистом» с 1,427 млрд ₽ («Агропромкредит») по
полям читался нормально. Порядок и подписи — как в `static/index.html`
(renderDeal: «Обзор», «Экономист», «Юрист»); пустые значения («—») не
показываются, как и на экране.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'publish'))
import format_post  # noqa: E402

EMPTY = {'', '—', '-', '–', 'None'}


def has(v):
    return isinstance(v, str) and v.strip() not in EMPTY


def _row(label, v):
    return ['%s: %s' % (label, v.strip())] if has(v) else []


def _norm(v):
    return re.sub(r'\s+', '', str(v or '')).lower()


def render_screens(card, companies):
    seller, asset, buyer = format_post.party_names(card, companies)
    eco, law = card.get('eco') or {}, card.get('law') or {}
    listing = card.get('type') == 'Продажа с торгов' and card.get('status') != 'Закрыта'
    out = ['ШАПКА', '%s · %s · %s' % (card.get('date') or 'дата не указана', card.get('status') or 'статус не указан', card.get('ind') or ''),
           '%s → %s' % (buyer or '?', asset or '?'), card.get('title') or '', 'Тип: %s' % (card.get('type') or ''), '',
           'ОБЗОР', 'Сумма: %s' % (card.get('sum') if has(card.get('sum')) else 'Не раскрыта')]
    out += _row('Продавец', seller) + _row('Предмет сделки', card.get('asset') or asset) + _row('Покупатель', buyer)
    out += _row('Как устроена сделка', law.get('struct')) + _row('Статус', card.get('status')) + ['', 'ЭКОНОМИСТ']
    if has(eco.get('sum')) and (listing or _norm(eco.get('sum')) != _norm(card.get('sum'))):
        out += _row('Начальная цена лота' if listing else 'Сумма сделки', eco.get('sum'))
    advs = [a for a in (law.get('adv') or []) if isinstance(a, list) and len(a) > 1 and re.search(r'финанс|инвест', str(a[0]), re.I)]
    out += (_row('Предмет / доля', eco.get('share')) + _row('Оценка и дисконт', eco.get('val')) + _row('Показатели компании', eco.get('target_fin'))
            + _row('Форма расчетов', eco.get('fin'))
            + _row('Финансовые консультанты', '; '.join(str(a[1]) for a in advs) if advs else eco.get('finadv'))
            + _row('Цель сделки', eco.get('rationale')) + _row('Контекст', eco.get('context')) + _row('Дополнительно', card.get('extra')))
    # «Юрист» на сайте — согласования, условия, юридические консультанты;
    # структура (law.struct) живет на «Обзоре» как «Как устроена сделка» и
    # здесь не повторяется. Вкладка есть, только если есть что показать.
    legal = [a for a in (law.get('adv') or []) if isinstance(a, list) and len(a) > 1 and a not in advs]
    if has(law.get('appr')) or has(law.get('terms')) or legal:
        out += ['', 'ЮРИСТ'] + _row('Согласования', law.get('appr'))
        if legal:
            out.append('Консультанты: ' + '; '.join('%s — %s' % (a[1], a[0]) for a in legal))
        out += _row('Условия сделки', law.get('terms'))
    out += ['', 'ПОСТ В КАНАЛ']
    try:
        post = format_post.render(card, companies)
        post = re.sub(r'<a href="([^"]*)">([^<]*)</a>', r'\2 (\1)', post)
        out.append(re.sub(r'<[^>]+>', '', post))
    except Exception as e:  # noqa: BLE001
        out.append('Пост не собирается: %s' % e)
    return '\n'.join(out)
