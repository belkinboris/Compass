"""Продавцы двух карточек очереди — 19 октября 2026 (партнёр владельца:
«продавец не раскрыт, хотя его можно найти в СМИ и в реестрах»).

g28941fd8 — VEON покупает 100% Rubicon Wireless Communication (Perfectum).
  Пресс-релиз VEON и Интерфакс продавца не называют, но покупка 100% ООО —
  это покупка долей ВСЕХ его участников, а участников показывает госреестр
  Узбекистана (ЕГРПО): Spot.uz 19.10.2026 — «Согласно ЕГРПО, сейчас основным
  учредителем Rubicon Wireless Communication является Маматджанов Фарход
  Фахритдинович с долей в 50%… 41,23% — иностранной компании IMC-Capital,
  8,77% — Камрону Акбарову»; Gazeta.uz 19.08.2026 — тот же состав («Сейчас
  среди учредителей числятся Мамаджанов (50%), IMC-Capital (41,23%) и Камрон
  Акбаров (8,77%)») и прежний (Иминов 50%, IMC-Capital 37,5%, Акбаров 12,5%).
  Написание фамилии — «Мамаджанов», как у Интерфакса и Gazeta.uz (Spot.uz
  транслитерирует «Маматджанов»). orginfo.uz отдаёт устаревший срез (на
  27.05.2024: Иминов 100%) — как источник не годится. Заодно отрасль карточки
  «Не определена» → «Телеком» (профили обеих сторон — «Телеком»).

ga09376f6 — «Экспанта» купила 25% ООО «СиЭс Технологии» («Стаксель»).
  ОГРН 1137746030982 / ИНН 7706787671 (rusprofile, list-org, saby, rbc; в истории
  участников ЕГРЮЛ общество само держало долю под этим ИНН в 2017 году). История участников ЕГРЮЛ
  (datanewton, проверено 19.10.2026): последняя запись 25.05.2018 —
  Владимир Скороход 100%, капитал 10 000 ₽; перехода к «Экспанте» в реестре
  ещё нет. Продал ли долю Скороход или «Экспанта» вошла в капитал новой
  долей — ни Коммерсантъ, ни перепечатки (Investfuture, Mergers.ru, Runet)
  не говорят. По `docs/card_parties.md` продавца не вписываем и не утверждаем,
  что его нет: записываем, что показал реестр. Кроме того, «300 млн ₽» в
  поле суммы — не цена: источник говорит «средневзвешенная оценка по двум
  траншам составит 300 млн руб.» (`docs/card_money.md`, «Что не цена»), —
  число уходит в `eco.val`, в `retracted.sum`, сумма — «Не раскрыта».

У обеих карточек сбрасывается `post_draft_sent` (`draft_sent` не трогаем):
`send_drafts.py --write` пришлёт в консоль новый проект поста.
Без ключа — сухой прогон; `--write` перечитывает pending.json и пишет.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'static', 'data', 'pending.json')
REG = os.path.join(ROOT, 'pipeline', 'fns_registry.py')

SPOT = 'https://www.spot.uz/ru/2026/10/19/perfectum'
GAZ_AUG = 'https://www.gazeta.uz/ru/2026/08/19/veon-perfectum/'
GAZ_OCT = 'https://www.gazeta.uz/ru/2026/10/19/veon-perfectum/'
VEON_SELLER = 'Фарход Мамаджанов, IMC-Capital и Камрон Акбаров'
VEON_STRUCT = (
    'VEON покупает 100% ООО Rubicon Wireless Communication — то есть доли всех трёх его участников. '
    'По данным госреестра Узбекистана, которые 19 октября 2026 года привёл Spot.uz, 50% принадлежат '
    'предпринимателю Фарходу Мамаджанову (крупнейший акционер InfinBank), 41,23% — иностранной компании '
    'IMC-Capital, 8,77% — Камрону Акбарову; IMC-Capital и Акбаров — акционеры процессингового центра Uzcard. '
    'Мамаджанов получил согласие Комитета по развитию конкуренции на покупку 50% в июле 2026 года; до этого '
    'половина компании принадлежала Абдумалику Иминову, которому после приватизации в начале 2024 года '
    'принадлежал весь Perfectum. Сами VEON и продавцы имена продавцов в объявлении о сделке не называли.')
VEON_NOTE = ('три продавца (физлица и иностранная компания), один профиль не ставится; найдены по госреестру '
             'Узбекистана (ЕГРПО) — состав участников привели Spot.uz 19.10.2026 и Gazeta.uz 19.08.2026; '
             'пресс-релиз VEON и Интерфакс продавцов не называют')

DN = 'https://datanewton.ru/contragents/1137746030982/history/timeline'
STAX_STRUCT = (
    'По истории участников ЕГРЮЛ (проверено 19 октября 2026 года) единственный участник ООО «СиЭс Технологии» — '
    'Владимир Скороход: ему принадлежат 100% с 25 мая 2018 года, уставный капитал — 10 тыс. ₽. Перехода 25% к '
    '«Экспанте» в реестре пока нет. Продаёт ли долю Скороход или «Экспанта» входит в капитал новой долей, '
    'компания не сообщила. Сделка рассчитана на два транша: после второго доля «Экспанты» дойдёт до 50%.')
STAX_VAL = ('«Экспанта» называет средневзвешенную оценку по двум траншам — 300 млн ₽. Цену самой доли '
            'компания не раскрыла.')
STAX_NOTE = ('продавец не назван ни в одном источнике (Коммерсантъ, Investfuture, Mergers.ru, Runet); история '
             'участников ЕГРЮЛ (datanewton, ОГРН 1137746030982, проверено 19.10.2026): последняя запись '
             '25.05.2018 — Владимир Скороход 100%, перехода доли к «Экспанте» ещё нет. Продажа его доли или вход '
             'в капитал новой долей — источник не говорит, поэтому продавец не вписан и не утверждается, что его нет')

REG_MARK = "'gba3ec0cd', \"decision\": 'confirmed', \"inn\": '7706787671'"
REG_BLOCK = '''

# Предмет карточки ga09376f6 — 2026-10-19 (pipeline/fix_sellers_veon_expanta_2026_10_19.py).
REGISTRY += [
    {"company_id": 'gba3ec0cd', "decision": 'confirmed', "inn": '7706787671',
     "reason": 'Предмет карточки ga09376f6 (2026-10-19): разработчик «Стаксель» — ООО «СиЭс Технологии» (Коммерсантъ), ОГРН 1137746030982, ИНН 7706787671 (история участников ЕГРЮЛ на datanewton: ИНН общества в записи 2017 года; rusprofile, list-org, saby совпадают).',
     "date": '2026-10-19'},
]
'''


def add_src(c, label, url):
    if url not in {s[1] for s in c.get('src') or [] if len(s) > 1}:
        c.setdefault('src', []).append([label, url])


def apply(pending):
    cards = {c['id']: c for c in pending['cards']}
    out = []

    v = cards['g28941fd8']
    if v.get('seller') != VEON_SELLER:
        assert not v.get('seller') and not v.get('seller_id'), v.get('seller')
        assert v['law'].get('struct') in ('—', '', None), v['law'].get('struct')
        assert v.get('ind') == 'Не определена', v.get('ind')
        v['seller'] = VEON_SELLER
        v['law']['struct'] = VEON_STRUCT
        v['ind'] = 'Телеком'
        v.setdefault('party_evidence', {})['seller'] = [
            {'value': VEON_SELLER, 'method': 'manual_source_review', 'url': SPOT},
            {'value': VEON_SELLER, 'method': 'manual_source_review', 'url': GAZ_AUG}]
        add_src(v, 'Spot.uz', SPOT)
        add_src(v, 'Gazeta.uz', GAZ_OCT)
        add_src(v, 'Gazeta.uz', GAZ_AUG)
        v.setdefault('accepted_notes', {}).setdefault('no_profile', {})['seller'] = VEON_NOTE
        v['post_draft_sent'] = False
        v.pop('post_preview', None)
        out.append('g28941fd8 продавец: %s; отрасль: Телеком' % VEON_SELLER)

    s = cards['ga09376f6']
    if s['law'].get('struct') != STAX_STRUCT:
        assert not s.get('seller') and not s.get('seller_id'), s.get('seller')
        assert s['law'].get('struct') in ('—', '', None), s['law'].get('struct')
        assert s.get('sum') == '300 млн ₽', s.get('sum')
        assert s['eco'].get('val') in ('—', '', None), s['eco'].get('val')
        s['law']['struct'] = STAX_STRUCT
        s['eco']['val'] = STAX_VAL
        s['sum'] = 'Не раскрыта'
        r = s.setdefault('retracted', {}).setdefault('sum', [])
        if '300 млн ₽' not in r:
            r.append('300 млн ₽')
        add_src(s, 'ЕГРЮЛ: история участников ООО «СиЭс Технологии»', DN)
        notes = s.setdefault('accepted_notes', {})
        notes.setdefault('no_profile', {})['seller'] = STAX_NOTE
        (notes.get('no_inn') or {}).pop('target', None)
        if 'no_inn' in notes and not notes['no_inn']:
            notes.pop('no_inn')
        s['post_draft_sent'] = False
        s.pop('post_preview', None)
        out.append('ga09376f6 продавец не вписан (реестр: Скороход 100% с 25.05.2018); сумма 300 млн ₽ → eco.val')
    return out


def main():
    write = '--write' in sys.argv
    raw = open(P, encoding='utf-8').read()     # перечитываем прямо перед записью
    pending = json.loads(raw)
    out = apply(pending)
    print('\n'.join(out) or 'уже применено')
    reg = open(REG, encoding='utf-8').read()
    need_reg = REG_MARK not in reg
    print('реестр ИНН: %s' % ('+ gba3ec0cd 7706787671' if need_reg else 'уже есть'))
    if write:
        if out:
            open(P, 'w', encoding='utf-8').write(
                json.dumps(pending, ensure_ascii=False, indent=1) + ('\n' if raw.endswith('\n') else ''))
        if need_reg:
            open(REG, 'w', encoding='utf-8').write(reg.rstrip('\n') + '\n' + REG_BLOCK)
        print('записано')


if __name__ == '__main__':
    main()
