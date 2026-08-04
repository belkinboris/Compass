# -*- coding: utf-8 -*-
"""Партия 8 @LawFirms: две новости канала, которые не объявления фирм.

ЗАЧЕМ. После того как правило консультанта перестало давать новые
срабатывания, в потоке канала остались новости о сделках без имени фирмы.
Их немного и почти все уже в базе, но две — нет.

ЛУКОЙЛ / CARLYLE. Карточка в базе была, и в ней стояли ДВЕ неверные вещи.
Во-первых, дата 2022-01-01 — заглушка из компактного импорта: сама карточка
говорит о согласовании с OFAC и о Carlyle, а соседние карточки того же
сюжета (предложение Gunvor и его отказ) датированы 2025 годом. Сделка,
поставленная в 2022 год, попадает не в тот год ленты и аналитики.
Во-вторых, статус «Обсуждается» при том, что канал 29 января 2026 года
сообщил о состоявшейся продаже.

ГРАНИЦА. Дата ставится не «по памяти», а по сообщению: 29 января 2026 года —
день, когда о завершении сделки сообщили. Это прямо написано в «Контексте»,
чтобы читатель не принял её за день подписания договора.

Запуск:
    python3 pipeline/enrich_from_lawfirms_batch8.py            # сухой прогон
    python3 pipeline/enrich_from_lawfirms_batch8.py --write    # записать
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SRC_LABEL = 'РУЛЬФЫ, ИЛЬФЫ И ИНХАУСЫ (@LawFirms)'
URL = 'https://t.me/LawFirms/10330'
DEAL_ID = 'g20d4cc38'

WAS = {'date': '2022-01-01', 'status': 'Обсуждается',
       'title': 'ЛУКОЙЛ продаёт зарубежные активы компании Carlyle'}
NOW = {'date': '2026-01-29', 'status': 'Закрыта',
       'title': 'ЛУКОЙЛ продал зарубежные активы (LUKOIL International GmbH) компании Carlyle'}
CONTEXT = ('Канал «РУЛЬФЫ, ИЛЬФЫ И ИНХАУСЫ» 29 января 2026 года сообщил о состоявшейся '
           'продаже: «Лукойл продала свои зарубежные активы, которыми владела LUKOIL '
           'International GmbH, американской инвестиционной компании Carlyle». Активы в '
           'Республике Казахстан в предмет сделки не входят и остаются в собственности группы '
           '«ЛУКОЙЛ». Дата карточки — день этого сообщения, а не день подписания договора: '
           'дату подписания источник не называет. Прежняя дата карточки (1 января 2022 года) '
           'была заглушкой компактного импорта.')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'карточки %s нет в базе' % DEAL_ID
    for key, value in WAS.items():
        assert deal.get(key) == value, \
            '%s: поле %s сейчас %r, а не %r — решение принимать заново' % (
                DEAL_ID, key, deal.get(key), value)
    assert str((deal.get('eco') or {}).get('context') or '').strip() in ('', '—'), \
        'поле «Контекст» уже заполнено — перепроверьте'
    assert URL not in {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}, \
        'объявление уже стоит в источниках'

    print('%s  %s' % (DEAL_ID, deal['title'][:64]))
    for key in NOW:
        print('    %-7s %r -> %r' % (key, WAS[key], NOW[key]))
    print('    «Контекст» заполняется цитатой сообщения')

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    deal.update(NOW)
    deal.setdefault('eco', {})['context'] = CONTEXT
    deal.setdefault('src', []).append([SRC_LABEL, URL])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nЗАПИСАНО в %s' % os.path.relpath(DATA, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
