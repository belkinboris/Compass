# -*- coding: utf-8 -*-
"""Дневная очередь (REVISION_BRIEF, первый уровень — полный обыск в
течение суток после появления), карточка `gddb34475` («"Газпромбанк-
инвест" продал торговый центр "Город Косино"», закрыта, 2026-09-04) —
приток построил карточку по одной статье Коммерсанта; полный обыск
нашёл вторую статью с оценками стоимости, финансами предмета и
причиной продажи.

Проверено ЛИЧНО прямым WebFetch (дословные цитаты,
mergers.ru/news/Gazprombank-invest-prodal-torgovyj-centr-Gorod-Kosino-
na-vostoke-Moskvy-87475 — перепечатка Finance.Mail.Ru со ссылкой на ту
же статью Коммерсанта плюс комментарии экспертов):
- «за "Город Косино" новый владелец мог заплатить 6,5-7 млрд руб.»
  (Ольга Шлычкова, CMWP);
- «рыночную стоимость объекта в 8-10 млрд руб.» — Станислав Ахмедзянов
  (IBC Global), при этом ежегодный арендный поток он же оценивает «в
  1-1,3 млрд руб.»;
- «Долгосрочные обязательства [ООО "Строй инвест"] на конец 2025 года:
  5,9 млрд руб. Краткосрочные обязательства: 278,2 млн руб.»; «Выручка
  в 2025 году выросла на 16% год к году, до 972,1 млн руб. Чистый
  убыток сократился на 26%, до 449,6 млн руб.»;
- «для "Газпромбанк-инвеста" торгцентр "Город Косино" является
  непрофильным активом» (Микаэл Казарян, IBC Real Estate);
- состав AF Holding: «азербайджанские строительные компании UGUR 97 и
  Everton, производство пластиковых изделий Afsan Plastik, бизнес-
  центры, торгцентры и аквапарки в Баку, а также сеть магазинов
  стройматериалов AF Euro Home».

НЕ ВНЕСЕНО: (1) более ранние российские активы AF Holding (торгово-
складской комплекс на Варшавском шоссе) — саб-агент нашёл это только
через WebSearch-агрегацию (interfax.az недоступен, ENOTFOUND), прямым
чтением не подтверждено; (2) консультанты сделки — ноль по обоим
источникам, названные лица (Шлычкова, Ахмедзянов, Казарян) — сторонние
комментаторы для прессы, а не консультанты сторон; (3) планы
«Газпромбанк-инвеста» по другим активам — целевой поиск дал ноль,
официальных комментариев банк и AF Holding не дали («не ответили на
запрос "Ъ"», уже в карточке).

Запуск: python3 pipeline/fix_afkap_gorod_kosino_fullscan.py
        python3 pipeline/fix_afkap_gorod_kosino_fullscan.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gddb34475'

OLD_ECO_VAL = '—'
NEW_ECO_VAL = (
    'Независимые оценки расходятся: Ольга Шлычкова (CMWP) полагает, что '
    'новый владелец мог заплатить 6,5–7 млрд ₽; Станислав Ахмедзянов '
    '(IBC Global) оценивает рыночную стоимость объекта в 8–10 млрд ₽, '
    'но отмечает, что сумма самой сделки могла быть существенно ниже '
    'из-за долга на балансе компании.'
)

OLD_ECO_TARGET_FIN = '—'
NEW_ECO_TARGET_FIN = (
    'Долгосрочные обязательства ООО «Строй инвест» на конец 2025 года '
    '— 5,9 млрд ₽, краткосрочные — 278,2 млн ₽. Выручка в 2025 году '
    'выросла на 16% до 972,1 млн ₽, чистый убыток сократился на 26% до '
    '449,6 млн ₽. Ежегодный арендный поток эксперты оценивают в '
    '1–1,3 млрд ₽.'
)

OLD_ECO_RATIONALE = '—'
NEW_ECO_RATIONALE = (
    'Для «Газпромбанк-инвеста» торговый центр «Город Косино» был '
    'непрофильным активом, считает Микаэл Казарян (IBC Real Estate).'
)

OLD_ECO_CONTEXT = (
    'Новым владельцем компании стало ООО «Афкап» Агиля Мохнатова — сына '
    'Азая Мохнатова, основателя азербайджанской AF Holding.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Группа AF Holding также владеет строительными '
    'компаниями UGUR 97 и Everton, производством пластиковых изделий '
    'Afsan Plastik, бизнес-центрами, торговыми центрами и аквапарками в '
    'Баку и сетью магазинов стройматериалов AF Euro Home.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['val'] == OLD_ECO_VAL
    assert deal['eco']['target_fin'] == OLD_ECO_TARGET_FIN
    assert deal['eco']['rationale'] == OLD_ECO_RATIONALE
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    print('=== eco.val: станет ===')
    print(NEW_ECO_VAL)
    print('\n=== eco.target_fin: станет ===')
    print(NEW_ECO_TARGET_FIN)
    print('\n=== eco.rationale: станет ===')
    print(NEW_ECO_RATIONALE)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)

    if write:
        deal['eco']['val'] = NEW_ECO_VAL
        deal['eco']['target_fin'] = NEW_ECO_TARGET_FIN
        deal['eco']['rationale'] = NEW_ECO_RATIONALE
        deal['eco']['context'] = NEW_ECO_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
