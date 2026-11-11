# -*- coding: utf-8 -*-
"""«Ренессанс Капитал» / «Онэксим» (g995f83cf): покупатель в схеме — АО «РКИП», как в ЕГРЮЛ.

ПОЧЕМУ. В схеме покупателем стояли «Максим Орловский, Владимир Куров и Игорь
Даниленко» — так сделку описал совместный пресс-релиз сторон (Frank Media,
Интерфакс, 13.11.2024). Владелец, 11 ноября 2026: «там же РКИП был… как вообще
покупателем стал не настоящий покупатель? В схеме четко должно быть, кто купил,
кто продал, кто таргет… В названии менеджеров тоже убери, это можно только в
дополнительном контексте написать».

ЧТО В РЕЕСТРЕ. ЕГРЮЛ, участники ООО «Ренессанс Капитал — Финансовый консультант»
(ИНН 7703261640, ОГРН 1027739121871), запись 13.11.2024: ООО «Группа Онэксим»
99,9995% вышло, вошло АО «РКИП» (ОГРН 1247700361149, ИНН 9702067348) с той же
долей. Два источника: история участников на Датаньютоне (api/v2/history, OWNERS)
и ЕГРЮЛ по API-ФНС на нашем сайте (/api/companies/rencap/fns — текущий состав и
история). Акционеров АО реестр не показывает: то, что за РКИП стоят трое
топ-менеджеров, известно только со слов сторон — это и пишется в контексте.

Профиль g30de903e (был «Максим Орловский, Владимир Куров и Игорь Даниленко»,
стоит только в этой сделке) становится профилем АО «РКИП».

    python3 pipeline/archive/2026-11/rencap_buyer_rkip_g995f83cf_2026_11_11.py [--write]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import fact_edit_guard  # noqa: E402
import mass_edit_guard  # noqa: E402
import fns_registry  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
REG = os.path.join(ROOT, 'pipeline', 'fns_registry.py')
DEAL, PROFILE, DAY, BY = 'g995f83cf', 'g30de903e', '2026-11-11', 'rencap_buyer_rkip_g995f83cf_2026_11_11'
INN, OGRN = '9702067348', '1247700361149'
HISTORY = 'https://datanewton.ru/api/v2/history?ogrn=1027739121871&startDate=2023-01-01&attributes=OWNERS'
QUOTE = ('ЕГРЮЛ, участники ООО «Ренессанс Капитал — Финансовый консультант» (Датаньютон, OWNERS), запись от '
         '2024-11-13: ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "ГРУППА ОНЭКСИМ" (ОГРН: 1057749737341) 99.9995% '
         'удалено, добавлено АКЦИОНЕРНОЕ ОБЩЕСТВО "РКИП" (ОГРН: 1247700361149) 99.9995%; (49 999 750 руб.).')
OLD_TITLE = 'Максим Орловский, Владимир Куров и Игорь Даниленко купили «Ренессанс Капитал» у «Онэксима»'
NEW_TITLE = '«РКИП» купил «Ренессанс Капитал» у «Онэксима»'
OLD_NAME = 'Максим Орловский, Владимир Куров и Игорь Даниленко'
NEW_STRUCT = ('АО «РКИП» купило у ООО «Группа Онэксим» российские компании группы: «Ренессанс Капитал — '
              'Финансовый консультант», «Ренессанс Брокер» и недавно учрежденную управляющую компанию «РенКап». '
              'В ЕГРЮЛ переход доли 99,9995% в «Ренессанс Капитал — Финансовый консультант» от «Группы Онэксим» '
              'к АО «РКИП» записан 13 ноября 2024 года. Стороны сообщили, что получили все нужные согласования, '
              'и закрыли сделку.')
MANAGERS = ('Стороны в совместном сообщении назвали сделку продажей менеджменту: по их словам, компании группы '
            'выкупили топ-менеджеры «Ренессанс Капитала» Максим Орловский, Владимир Куров и Игорь Даниленко; '
            'по словам Орловского, ему досталось 36%, Курову и Даниленко — по 32%. Покупатель по реестру — '
            'АО «РКИП»; акционеров акционерного общества ЕГРЮЛ не показывает.')
OLD_ROLE = 'Юридический консультант покупателя («Ренессанс Капитал»: Максим Орловский, Владимир Куров и Игорь Даниленко)'
NEW_ROLE = 'Юридический консультант покупателя (АО «РКИП»)'
REASON = ('Покупатель сделки g995f83cf. АО «РКИП», ИНН 9702067348, ОГРН 1247700361149. Два независимых источника: '
          '(1) ЕГРЮЛ по API-ФНС (карточка ООО «Ренессанс Капитал — ФК», ИНН 7703261640, на нашем сайте): текущий '
          'участник — АО "РКИП", ИНН 9702067348, ОГРН 1247700361149, доля 99,9995%, вошел 13.11.2024 вместо ООО '
          '«Группа Онэксим»; (2) история участников на Датаньютоне по ОГРН 1027739121871 (api/v2/history, OWNERS) — '
          'запись 13.11.2024: АКЦИОНЕРНОЕ ОБЩЕСТВО "РКИП" (ОГРН: 1247700361149) 99.9995%. Контрольная сумма ИНН сходится.')


def apply(data):
    comps, mk = data['companies'], data.setdefault('match_keys', {})
    card = next(x for x in data['deals'] if x['id'] == DEAL)
    assert card['title'] == OLD_TITLE, card['title']
    assert card['buyer'] == PROFILE and comps[PROFILE]['name'] == OLD_NAME
    assert [x['id'] for x in data['deals'] if PROFILE in (x.get('buyer'), x.get('seller_id'), x.get('target'), x.get('asset_id'))] == [DEAL]
    assert card['law']['adv'][0][0] == OLD_ROLE and card['law']['struct'].startswith('Три топ-менеджера выкупили')
    assert card['eco']['context'].startswith('Сделка завершила двухлетний план')
    assert fns_registry.inn_is_valid(INN)
    comps[PROFILE] = dict(comps[PROFILE], name='РКИП', legal_short='АО «РКИП»',
                          desc=('Акционерное общество, зарегистрировано в 2024 году. С 13 ноября 2024 года — участник '
                                'ООО «Ренессанс Капитал — Финансовый консультант» с долей 99,9995%. По сообщению '
                                'сторон сделки, за компанией стоят топ-менеджеры «Ренессанс Капитала».'))
    comps[PROFILE].pop('fns_asked', None)
    mk[PROFILE] = ['ркип', 'ао «ркип»', 'ао ркип']
    card['title'] = NEW_TITLE
    card['law']['struct'] = NEW_STRUCT
    card['law']['adv'][0][0] = NEW_ROLE
    card['eco']['context'] = MANAGERS + '\n\n' + card['eco']['context']
    for f, v in (('title', NEW_TITLE), ('buyer', PROFILE), ('law.adv', card['law']['adv'])):
        fact_edit_guard.log(card, f, v, QUOTE, HISTORY, BY, DAY)
    return card


def main(write):
    raw = open(DATA, encoding='utf-8').read()
    reg_src = open(REG, encoding='utf-8').read()
    assert INN not in reg_src and ("'%s'" % PROFILE) not in reg_src and ('"%s"' % PROFILE) not in reg_src
    old, data = json.loads(raw), json.loads(raw)
    card = apply(data)
    print(card['title']); print(data['companies'][PROFILE])
    mass_edit_guard.check(old, data, os.environ.get('MASS_OK'))
    bad = fact_edit_guard.unbacked(old, data)
    assert not bad, bad
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    fresh_raw = open(DATA, encoding='utf-8').read()
    fresh = json.loads(fresh_raw)
    apply(fresh)
    marker = "\n\ndef by_company_id() -> dict[str, dict]:"
    assert marker in reg_src and open(REG, encoding='utf-8').read() == reg_src
    block = ('\n\n# Покупатель сделки g995f83cf (АО «РКИП») — %s (pipeline/archive/2026-11/%s.py).\nREGISTRY += [\n'
             '    {"company_id": %r, "decision": "confirmed", "inn": %r,\n     "reason": %r,\n     "date": %r},\n]'
             % (DAY, BY, PROFILE, INN, REASON, DAY))
    with open(DATA, 'w', encoding='utf-8') as f:
        f.write(json.dumps(fresh, ensure_ascii=False, indent=1) + ('\n' if fresh_raw.endswith('\n') else ''))
    with open(REG, 'w', encoding='utf-8') as f:
        f.write(reg_src.replace(marker, block + marker, 1))
    print('ЗАПИСАНО.')
    return 0


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv[1:]))
