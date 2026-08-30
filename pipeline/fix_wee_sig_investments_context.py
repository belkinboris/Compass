# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка g6d719087
(Wee привлёк $12 млн в pre-Series A раунде финансирования) — карточка
держалась на иностранном источнике (Wamda.com) без проверки, что это
за инвестор и что известно о дальнейших планах компании. Проверено
лично прямым WebFetch трёх источников.

1) `eco.context` (сохранено дословно, источник расширен) — запуск и
основатели Wee, теперь подтверждено дополнительно техническим
описанием, что сама компания зарегистрирована в ОАЭ и работает на
рынке Дубая (technode.global называет её «UAE marketplace»,
CEO/сооснователь — Анастасия Ким) — это тот же самый факт, не новая
компания: основатели с российским бэкграундом (Logsis, AML, DTS,
«Яндекс Доставка») запустили маркетплейс в Дубае.

2) `eco.context` (дополнено) — инвестор SIG Investments и планы IPO.
Дословно (technode.global): цитата гендиректора SIG Investments Сами
Аль-Мохаммада — «WEE has entered the UAE market recently but has
already been able to win over the audience and offer a unique fast
delivery service in the selected time slots»; компания «actively
exploring the possibility of an initial public offering (IPO) in the
Middle East and North Africa (MENA) region».
https://technode.global/2024/04/26/uae-marketplace-wee-secures-10m-funding-from-sig-investment/

3) `eco.context` (дополнено) — направления использования средств и план
оборота. Дословно (rb.ru): «инвестиции пойдут на укрепление
логистических возможностей и команды, а также на продвижение категории
fashion»; компания рассчитывает на «оборот в $150 млн (выкупленные
заказы)» в следующем году.
https://rb.ru/news/wee-deal/

НЕ ВКЛЮЧЕНО: цифра фактического оборота ~$3,5 млн за 2025-2026 годы
(резко расходящаяся с планом в $150 млн) — встретилась только в
резюме поисковика по Forbes.ru, прямой WebFetch статьи заблокирован
защитой сайта, дословная цитата не получена — не включается без
подтверждения личным чтением; консультанты раунда — не найдены ни в
одном источнике; независимая оценка компании — не найдена, кроме
заявленных $40 млн post-money.

Запуск: python3 pipeline/fix_wee_sig_investments_context.py
        python3 pipeline/fix_wee_sig_investments_context.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'g6d719087'

OLD_CONTEXT = (
    'Wee был запущен в 2022 году основателем компании Logsis (доставка '
    'товаров из интернет-магазинов и розничных сетей) Олегом '
    'Дашкевичем, Сергеем Коликовым (отвечал за развитие складов и '
    'коммерции в AML, DTS, «Яндекс Доставке») и Анастасией Ким (в '
    '«Яндекс Маркете» отвечала за развитие сервиса «Яндекс Доставка»).'
)
NEW_CONTEXT = OLD_CONTEXT + (
    ' Гендиректор инвестора, SIG Investments, Сами Аль-Мохаммад: «WEE '
    'has entered the UAE market recently but has already been able to '
    'win over the audience and offer a unique fast delivery service in '
    'the selected time slots» — компания «actively exploring the '
    'possibility of an initial public offering (IPO) in the Middle East '
    'and North Africa (MENA) region» (technode.global). По данным rb.ru, '
    '«инвестиции пойдут на укрепление логистических возможностей и '
    'команды, а также на продвижение категории fashion»; компания '
    'рассчитывала на «оборот в $150 млн (выкупленные заказы)» в '
    'следующем году.'
)

NEW_SRC = [
    ['technode.global', 'https://technode.global/2024/04/26/uae-marketplace-wee-secures-10m-funding-from-sig-investment/'],
    ['rb.ru', 'https://rb.ru/news/wee-deal/'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['context'] == OLD_CONTEXT
    for label, url in NEW_SRC:
        assert not any(s[1] == url for s in deal['src']), f'{url} уже в src'

    print('=== eco.context: станет ===')
    print(NEW_CONTEXT)
    print('\n=== src добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['eco']['context'] = NEW_CONTEXT
        deal['src'].extend(NEW_SRC)
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
