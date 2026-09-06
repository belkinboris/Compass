# -*- coding: utf-8 -*-
"""Правки оставшихся карточек после второй партии слияний дублей (6 сентября
2026) — то, что читатели пар нашли в самих оставшихся карточках, а не в дублях.

Слияние (`pipeline/merge_duplicate_deals_batch.py`) по устройству только
ДОПОЛНЯЕТ пустые поля; здесь — замены, каждая под assert на исходное
состояние, и каждая взята из прочитанного источника или из удалённого дубля:

- `g38129341` (МТС / «Проектная среда»): заголовок «приобрела 15%» описывал
  первое из двух закрытий одной сделки; после слияния с карточкой о контроле
  заголовок берётся у дубля — сделка в итоге о контрольном пакете (51%,
  27 апреля 2023, пресс-релиз МТС и Интерфакс 898045).
- `gc660ac38` (ТРЦ «Саларис»): дата «2023» → 2023-12-14 — день, когда продавец
  подтвердил закрытие (РИА Недвижимость, 14.12.2023; эту же дату нёс дубль);
  покупатель — компания «Первый» семьи Ракшина (профиль есть), а не бренд
  «Мария-Ра»: РИА — «Новым владельцем актива станет компания «Первый»».
  Профиль АО «Лаут» описывал компанию как покупателя — по той же статье это
  собственник здания, у которого сменился гендиректор; описание исправлено.
- `gdb2a120f` («Директ Кредит»): покупатель не был привязан к профилю —
  «М.Видео» (`g444cac01`) в базе есть.
- `g64141daa` («Домиленд»/Яндекс): «купил оставшуюся долю» неверно — доли у
  Яндекса не было, куплено 100% ООО «Клиентский сервис» (бывш. «Домиленд») у
  «Самолета» и основателей (Интерфакс 1025082, Право.ru 256974); дата «2025» →
  2025-05-06 по ЕГРЮЛ (тот же источник); отрасль — ИТ-платформа, не
  недвижимость.
- `g3fb43064` (МЭЗ «Исток»): «Согласования» держали «на согласовании в ФАС»
  при закрытой сделке; предложение об одобрении ФАС пришло из дубля в
  «Дополнительную информацию» — оно и становится значением поля.

Не сделано намеренно: покупатель ALD Automotive (`g2d653619`) остаётся
профилем «Структуры Игоря Кима» — читатель предложил АО «ЦК», но профиль
`gc0638d38` в базе назван ООО «ЦК» с другой сделкой 2024 года, и без
проверки ИНН это могли бы оказаться два разных юрлица.

Запуск:
    python3 pipeline/fix_audit_round2_after_merges.py           # сухой прогон
    python3 pipeline/fix_audit_round2_after_merges.py --write
"""
import json
import re
import sys

DATA = 'static/data/deals_promoted.json'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    for drop in ('g43c78df8', 'g6f8c1a94', 'gbaf3c565', 'g809f9155'):
        assert drop not in deals and data['merged'].get(drop), f'сначала слияние: {drop}'

    d = deals['g38129341']
    new_title = 'МТС приобрела контроль в разработчике телематических решений СКАУТ-КР'
    if d['title'] != new_title:
        assert d['title'].startswith('МТС приобрела 15% ООО «Проектная среда»'), d['title']
        print('g38129341: title ->', new_title)
        if write:
            d['title'] = new_title

    d = deals['gc660ac38']
    if d.get('date') != '2023-12-14':
        assert d.get('date') == '2023', d.get('date')
        assert any(e.get('date') == '2023-12-14' for e in d.get('events') or []), 'нет события закрытия 14.12.2023'
        print('gc660ac38: date 2023 -> 2023-12-14')
        if write:
            d['date'] = '2023-12-14'
    if d.get('buyer') != 'ge438bc54':
        assert d.get('buyer') == 'gc6091c34', d.get('buyer')
        assert comps['ge438bc54']['name'] == 'Первый'
        print('gc660ac38: buyer gc6091c34 (%s) -> ge438bc54 (Первый)' % comps['gc6091c34']['name'])
        if write:
            d['buyer'] = 'ge438bc54'
    laut = comps['glautao']
    laut_desc = ('Компания — собственник ТРЦ «Саларис» в Москве; в декабре 2023 года комплекс перешёл '
                 'к компании «Первый» семьи Александра Ракшина, основателя сети «Мария-Ра».')
    if laut.get('desc') != laut_desc:
        assert 'купила ТРЦ «Саларис»' in (laut.get('desc') or ''), laut.get('desc')
        print('glautao: desc -> собственник ТРЦ, а не покупатель')
        if write:
            laut['desc'] = laut_desc

    d = deals['gdb2a120f']
    if d.get('buyer') != 'g444cac01':
        assert not d.get('buyer') and not d.get('buyer_name'), (d.get('buyer'), d.get('buyer_name'))
        assert comps['g444cac01']['name'] == 'М.Видео'
        print('gdb2a120f: buyer -> g444cac01 (М.Видео)')
        if write:
            d['buyer'] = 'g444cac01'

    d = deals['g64141daa']
    new_title = 'Яндекс купил 100% «Домиленд» (ООО «Клиентский сервис») у «Самолета» и основателей'
    if d['title'] != new_title:
        assert d['title'] == 'Яндекс купил оставшуюся долю в Домиленд', d['title']
        assert d.get('date') == '2025' and d.get('ind') == 'Недвижимость', (d.get('date'), d.get('ind'))
        assert d.get('seller_id') == 'g12111389' and 'Самолет' in comps['g12111389']['name'], comps['g12111389']['name']
        print('g64141daa: title, date 2025 -> 2025-05-06, ind -> ИТ и интернет')
        if write:
            d['title'] = new_title
            d['date'] = '2025-05-06'
            d['ind'] = 'ИТ и интернет'

    d = deals['g3fb43064']
    appr = (d.get('law') or {}).get('appr') or ''
    if re.search(r'на согласовании', appr):
        sentences = re.split(r'(?<=[.!?])\s+', d.get('extra') or '')
        fas = [s for s in sentences if re.search(r'ФАС', s) and re.search(r'одобр|согласова', s)]
        assert fas, 'в extra нет предложения об одобрении ФАС'
        print('g3fb43064: law.appr %r -> %r' % (appr[:50], fas[0][:80]))
        if write:
            d['law']['appr'] = fas[0]
    # связка «Тем не менее …» — хвост предыдущего предложения, полю она не нужна;
    # остаток — подстрока исходного предложения, ничего не сочинено
    appr = (d.get('law') or {}).get('appr') or ''
    if appr.startswith('Тем не менее '):
        fixed = appr[len('Тем не менее '):]
        fixed = fixed[0].upper() + fixed[1:]
        assert fixed.lower() in appr.lower()
        print('g3fb43064: law.appr без связки ->', fixed[:60])
        if write:
            d['law']['appr'] = fixed

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return 0
    json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
