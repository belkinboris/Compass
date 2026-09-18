# -*- coding: utf-8 -*-
"""18 сентября 2026 — карточки временного управления Nestlé/«Ашан» (g64462179,
g2daf32fe) несли гарантированно неверную структуру.

Владелец увидел черновик «Ашана» на живом телефоне (карточки уже прошли
приёмку и ждали решения в pending.json) и написал прямо: «это какой-то
абсурд, мы разве не вычитываем карточки перед тем как их выкладывать?...
Когда национализируют активы там нет покупателя и продавца, там только
может быть предмет и бывший владелец и новый владелец... но что за позор
вообще находится в блоке «Команда сделки»? Я вижу, что ты недоработал».

Два отдельных дефекта, один источник.

1. `eco.finadv` («Финансовый консультант») нёс не имя консультанта, а
   предложение из расследования The Insider о том, что АО «Л.Е.В.
   Менеджмент» (сам временный управляющий) числится у регистратора в
   разделе «Готовые акционерные общества» — дословно верный факт О
   КАСТОДИАНЕ, поставленный не в своё поле (родня уже записанного класса
   «дословная цитата в НЕ СВОЁМ поле», HeadHunter/Happy Job). На экране это
   рендерилось как «Финансовый консультант · Со стороны продавца» —
   бессмыслица, которую владелец и увидел. Факт не выдуман и не потерян:
   он дописывается к уже стоящему в `eco.context` абзацу про регистрацию
   и руководство «Л.Е.В. Менеджмент» (та же тема, тот же абзац, только
   раньше не туда положенный), а `eco.finadv` возвращается к «—».

2. `d.target` был проставлен (управляемая компания), а `d.buyer`/`d.seller`
   — нет: плашка «Структура сделки» веткой `acquisition` в
   static/index.html честно, но неверно рисовала «Продавец: Не раскрыт» и
   «Покупатель: Не раскрыт» — не потому, что источник не назвал стороны, а
   потому что у указа о временном управлении таких ролей нет вовсе (ветка
   не знала другого способа описать сделку). Починено с двух сторон: в
   static/index.html заведена третья форма плашки, `kindKey==="custody"»
   (роли «Временный управляющий» / «Актив под управлением», без
   «Продавца» вовсе), а здесь — `d.kind = "custody"` на обеих карточках и
   `d.buyer` привязан к уже существующему профилю управляющего
   (`g9ba426b0`, АО «Л.Е.В. Менеджмент») вместо пустоты: имя управляющего
   уже дословно названо в `law.struct` обеих карточек, никакой новый факт
   не утверждается, только связывается уже известное.

Побутно: у самого профиля `g9ba426b0` описание оканчивалось служебным
хвостом автогенератора «; описание компании пока не добавлено» — при том,
что описание перед ним настоящее, не заглушка. Хвост снят.

Запуск: python3 pipeline/fix_auchan_nestle_custody_cards.py [--write]
"""
import json
import sys

PENDING_PATH = 'static/data/pending.json'
BASE_PATH = 'static/data/deals_promoted.json'
CUSTODIAN_ID = 'g9ba426b0'

CARDS = ['g64462179', 'g2daf32fe']

FINADV_GARBAGE = (
    'На сайте этого же регистратора The Insider обнаружил «Л.Е.В. '
    'Менеджмент» в разделе «Готовые акционерные общества».'
)

OLD_DESC = (
    'Временный управляющий, назначенный указом президента для управления '
    'активами Nestlé, Auchan, FM Logistic и «Леманы Про»; описание '
    'компании пока не добавлено.'
)
NEW_DESC = (
    'Временный управляющий, назначенный указом президента для управления '
    'активами Nestlé, Auchan, FM Logistic и «Леманы Про».'
)


def main(write):
    pending = json.load(open(PENDING_PATH, encoding='utf-8'))
    by_id = {c['id']: c for c in pending['cards']}
    for cid in CARDS:
        assert cid in by_id, 'карточки %r нет в pending.json' % cid
        card = by_id[cid]
        assert card.get('kind') == 'acquisition', \
            '%s: kind уже другой (%r)' % (cid, card.get('kind'))
        assert card.get('eco', {}).get('finadv') == FINADV_GARBAGE, \
            '%s: eco.finadv уже другой' % cid
        assert 'buyer' not in card, '%s: buyer уже проставлен' % cid
        context = card.get('eco', {}).get('context', '')
        assert FINADV_GARBAGE not in context, \
            '%s: этот факт уже дописан в context кем-то ещё' % cid

        card['eco']['context'] = context + ' ' + FINADV_GARBAGE
        card['eco']['finadv'] = '—'
        card['kind'] = 'custody'
        card['buyer'] = CUSTODIAN_ID

        print('%s: eco.finadv очищен, факт перенесён в eco.context' % cid)
        print('%s: kind acquisition -> custody' % cid)
        print('%s: buyer -> %s (АО «Л.Е.В. Менеджмент»)' % (cid, CUSTODIAN_ID))

    base = json.load(open(BASE_PATH, encoding='utf-8'))
    custodian = base['companies'][CUSTODIAN_ID]
    assert custodian['desc'] == OLD_DESC, 'desc профиля управляющего уже другой'
    custodian['desc'] = NEW_DESC
    print('%s: снят служебный хвост «описание пока не добавлено»' % CUSTODIAN_ID)

    if write:
        json.dump(pending, open(PENDING_PATH, 'w', encoding='utf-8'),
                   ensure_ascii=False, indent=1)
        json.dump(base, open(BASE_PATH, 'w', encoding='utf-8'),
                   ensure_ascii=False, indent=1)
        print('ЗАПИСАНО')
    else:
        print('сухой прогон — для записи передайте --write')


if __name__ == '__main__':
    main('--write' in sys.argv)
