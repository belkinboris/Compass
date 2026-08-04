# -*- coding: utf-8 -*-
"""Партия 7 @LawFirms: правило узнало ещё две формы того же глагола.

ЗАЧЕМ. После первого расширения правила остался хвост: «сопроводила
приобретение» (совершенный вид) и «выступает консультантом» (настоящее
время). Знало правило только несовершенный вид и прошедшее время —
«сопровождала», «выступила». Это тот же урок, что уже записан про
`продавц\\w*`, который не совпадает со словом «Продавец»: любой шаблон по
русскому глаголу прогонять по ВСЕМ формам, а не по тем, что попались в
выборке.

ЗАМЕР: срабатываний было 128, стало 134. Все 6 добавившихся — настоящие
объявления (Delcredere/«Ниармедик», Delcredere/SolidSoft, АЛРУД/
«Академ-Онлайн», VERBA LEGAL/МТС Банк, АЛРУД/Qiwi, АЛРУД/Lundbeck).
Ложных ноль, потерянных ноль.

ЗАОДНО: «КА» перед именем — сокращение от «коллегия адвокатов», как «АБ» от
«адвокатское бюро». Без него в базе появился бы консультант с именем
«КА Delcredere».

ЧТО ЗДЕСЬ ПРАВИТСЯ. Из шести две сделки уже были в базе с той же фирмой
(«Академ-Онлайн»/АЛРУД, Qiwi/ALRUD), одна не сделка (трансформация
бизнес-модели Lundbeck — фильтр её и не пропустил), одна карточка получает
факт, две сделки заводятся отдельным прогоном.

ТОНКАЯ КАРТОЧКА «ЯНДЕКС»/SOLIDSOFT — ОСОБЫЙ СЛУЧАЙ. У неё в поле
консультанта одной строкой записаны ОБЕ фирмы: имя — «Melling, Voitishkin &
Partners», а в пояснении текстом «Delcredere — за SolidSoft». То есть факт в
базе был, но лежал не в своём поле: на экране «Консультанты» показывали одну
фирму из двух, а вторая пряталась в примечании. Строка разбивается на две —
это не новый факт, а тот же факт в правильном поле.

Запуск:
    python3 pipeline/enrich_from_lawfirms_batch7.py            # сухой прогон
    python3 pipeline/enrich_from_lawfirms_batch7.py --write    # записать
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

SRC_LABEL = 'РУЛЬФЫ, ИЛЬФЫ И ИНХАУСЫ (@LawFirms)'

DEAL_ID = 'cb30dbbc8'
URL = 'https://t.me/LawFirms/9294'

WAS = [['Юридический консультант', 'Melling, Voitishkin & Partners',
        'Delcredere — за SolidSoft, «Меллинг, Войтишкин и партнеры» — за Yandex B2B Tech; '
        '50% доли + опцион на увеличение у «Яндекса». Возможная сумма — 3–4 млрд ₽']]

NOW = [['Юридический консультант Yandex B2B Tech', 'Melling, Voitishkin & Partners',
        'Комплексная юридическая поддержка Yandex B2B Tech в проекте создания совместного '
        'предприятия с SolidSoft. Источник: https://t.me/LawFirms/9301'],
       ['Юридический консультант SolidSoft', 'Delcredere',
        'Сопровождение сделки со стороны SolidSoft силами M&A-направления коллегии. '
        'Источник: https://t.me/LawFirms/9294']]

# Факты из объявления, которых у тонкой карточки не было вовсе.
FILL = {
    'status': 'Подписана',
    'asset': 'Совместное предприятие Yandex B2B Tech и SolidSoft',
    'sum': 'Не раскрыта',
}
ECO = {
    'sum': 'Не раскрыта',
    'share': 'SolidSoft и Yandex B2B Tech создают совместное предприятие, которое будет '
             'разрабатывать сервисы и продукты для обеспечения кибербезопасности. По условиям '
             'сделки «Яндекс» также получит опцион на увеличение доли в будущем.',
    'context': 'Руководить совместным предприятием будут основатели SolidSoft; компания '
               'продолжит развивать собственные продукты, а все действующие соглашения '
               'SolidSoft с клиентами и партнёрами останутся в силе.',
}
EMPTY_ECO = {'sum': '—', 'share': '—', 'val': '—', 'target_fin': '—',
             'fin': '—', 'rationale': '—', 'context': '—', 'finadv': '—'}


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    deal = by_id.get(DEAL_ID)
    assert deal is not None, 'карточки %s нет в базе' % DEAL_ID
    assert (deal.get('law') or {}).get('adv') == WAS, \
        'поле «Консультанты» уже другое — решение принимать заново'
    for key in FILL:
        assert not deal.get(key), '%s: поле %s уже заполнено (%r)' % (DEAL_ID, key, deal.get(key))
    assert URL not in {str(s[1]) for s in (deal.get('src') or []) if len(s) > 1}, \
        'объявление уже стоит в источниках'

    print('%s  %s' % (DEAL_ID, (deal.get('title') or '')[:64]))
    print('    было : 1 строка «Юридический консультант» с двумя фирмами в пояснении')
    print('    стало: %s' % ' | '.join('%s — %s' % (a[0], a[1]) for a in NOW))
    for key, value in FILL.items():
        print('    %-7s -> %s' % (key, value))
    print('    заполняется: %s' % ', '.join(ECO))

    if not write:
        print('\nСухой прогон. Запись — с ключом --write.')
        return 0

    deal.update(FILL)
    deal['law']['adv'] = [list(a) for a in NOW]
    eco = dict(EMPTY_ECO, **(deal.get('eco') or {}))
    eco.update(ECO)
    deal['eco'] = eco
    law = deal['law']
    law.setdefault('struct', 'Создание совместного предприятия с опционом на увеличение доли.')
    for key in ('appr', 'terms'):
        law.setdefault(key, '—')
    deal.setdefault('src', []).append([SRC_LABEL, URL])
    deal['src'].append([SRC_LABEL, 'https://t.me/LawFirms/9301'])
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nЗАПИСАНО в %s' % os.path.relpath(DATA, ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
