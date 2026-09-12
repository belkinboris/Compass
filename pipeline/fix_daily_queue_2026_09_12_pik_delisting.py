# -*- coding: utf-8 -*-
"""Приток, 12 сентября 2026: новая карточка — «Недвижимые активы» (98% ПИК)
проводит принудительный выкуп оставшихся акций ПАО «ПИК-специализированный
застройщик» при делистинге с Московской биржи. Источники — Коммерсантъ
(doc/8938431, цена выкупа 551,4 ₽/акция, исправленная с 537,9 ₽) и Интерфакс
(business/1113284, дата совета директоров 7 сентября, собрание акционеров
13 октября, реестр на 20 октября, честная неопределённость бенефициаров
«Недвижимых активов» — источник прямо говорит «не раскрываются», и
приписывать компанию Сергею Гордееву нельзя: известна только доля ~15% его
структур на конец 2024 года, а не контроль над самой «Недвижимые активы»).
Профиль ПИК заведён новый (в базе был только «ПИК-Инвестпроект», дочерняя
структура) с ИНН 7713011336 (ПАО «ПИК СЗ», rusprofile.ru/id/3645461,
подтверждено также spark-interfax.ru). Прочитано лично (WebFetch: Коммерсантъ,
Интерфакс) и WebSearch для проверки ИНН. Пишется в pending.json — карточку
должна пройти accept_card.py перед консолью.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEALS_PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING_PATH = os.path.join(ROOT, 'static', 'data', 'pending.json')
REGISTRY_PATH = os.path.join(ROOT, 'pipeline', 'fns_registry.py')

TARGET_ID = 'gfb08c766'
CARD_ID = 'g134cf416'

TARGET_PROFILE = {
    "name": "ПИК-специализированный застройщик",
    "ind": "Недвижимость",
    "desc": "Один из крупнейших российских девелоперов жилья, специализируется на строительстве жилья экономкласса в Москве, области и Санкт-Петербурге.",
    "kpi": ["Профиль", "Автоматический"],
}

CARD = {
    "id": CARD_ID,
    "date": "2026-09-07",
    "title": "«Недвижимые активы» выкупает оставшиеся акции ПИК при делистинге с Мосбиржи",
    "ind": "Недвижимость",
    "type": "M&A",
    "status": "Обсуждается",
    "src": [
        ["Коммерсантъ", "https://www.kommersant.ru/doc/8938431"],
        ["Интерфакс", "https://www.interfax.ru/business/1113284"],
    ],
    "from_ingest": True,
    "eco": {
        "sum": "—",
        "share": "«Недвижимые активы» владеет 98% акций ПАО «ПИК-специализированный застройщик» и намерена выкупить оставшиеся акции по цене 551,4 ₽ за бумагу (цена соответствует апрельской оферте акционерам ПИК). Совет директоров 7 сентября вынес вопрос о делистинге на внеочередное собрание акционеров 13 октября; реестр акционеров для выкупа составляется на 20 октября.",
        "val": "—",
        "target_fin": "—",
        "fin": "—",
        "rationale": "—",
        "context": "Бенефициары «Недвижимых активов» не раскрываются. Известно, что на конец 2024 года около 15% ПИК владели компании, аффилированные с Сергеем Гордеевым.",
        "finadv": "—",
    },
    "law": {
        "struct": "Принудительный выкуп акций у миноритариев в рамках делистинга: владельцы должны подать заявления в регистратор с реквизитами банковских счетов для получения средств.",
        "appr": "Первую оферту на выкуп «Недвижимые активы» направляли Банку России в феврале 2026 года — регулятор признал её параметры не соответствующими требованиям законодательства.",
        "adv": [],
        "terms": "—",
    },
    "buyer_name": "«Недвижимые активы»",
    "target": TARGET_ID,
    "asset": "ПИК-специализированный застройщик",
}


def main(write):
    with open(DEALS_PATH, encoding='utf-8') as f:
        deals_data = json.load(f)
    assert TARGET_ID not in deals_data['companies'], 'профиль уже существует'
    assert not any(d['id'] == CARD_ID for d in deals_data['deals']), 'карточка уже есть в базе'

    with open(PENDING_PATH, encoding='utf-8') as f:
        pending_data = json.load(f)
    assert not any(c['id'] == CARD_ID for c in pending_data['cards']), 'карточка уже в очереди'

    deals_data['companies'][TARGET_ID] = TARGET_PROFILE
    pending_data['cards'].append(CARD)

    print('Добавлен профиль:', TARGET_ID, '(ПИК)')
    print('Добавлена карточка в очередь:', CARD_ID)

    if write:
        with open(DEALS_PATH, 'w', encoding='utf-8') as f:
            json.dump(deals_data, f, ensure_ascii=False, indent=1)
            f.write('\n')
        with open(PENDING_PATH, 'w', encoding='utf-8') as f:
            json.dump(pending_data, f, ensure_ascii=False, indent=1)
            f.write('\n')

        registry_block = '''
# Приток — 12 сентября 2026: ИНН ПАО «ПИК СЗ» (карточка g134cf416, покупка
# «Недвижимыми активами» оставшихся акций при делистинге). Подтверждено
# двумя независимыми регистровыми источниками (rusprofile.ru/id/3645461,
# spark-interfax.ru), ОГРН 1027739137084.
REGISTRY += [
    {"company_id": 'gfb08c766', "decision": "confirmed", "inn": '7713011336',
     "reason": "Приток (12.09.2026): ИНН ПАО «ПИК СЗ» подтверждён rusprofile.ru и spark-interfax.ru, ОГРН 1027739137084.",
     "date": '2026-09-12'},
]
'''
        with open(REGISTRY_PATH, encoding='utf-8') as f:
            registry_src = f.read()
        marker = 'def by_company_id() -> dict[str, dict]:'
        assert marker in registry_src
        assert 'gfb08c766' not in registry_src
        registry_src = registry_src.replace(marker, registry_block.strip('\n') + '\n\n' + marker, 1)
        with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
            f.write(registry_src)

        print('Записано.')
    else:
        print('Сухой прогон — для записи передайте --write')


if __name__ == '__main__':
    import sys
    main('--write' in sys.argv)
