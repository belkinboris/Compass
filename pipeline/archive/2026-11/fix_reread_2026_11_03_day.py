# -*- coding: utf-8 -*-
"""Вычитка 3 ноября 2026 (партии da–dj): правки, которых review.py не умеет.

Каждая правка — с assert на прежнее значение; основания — в ONE_OFF файлов партий
`pipeline/ingest/fixes/reread_2026_11_03_<партия>.py` и в докстроках ниже.
Порядок: сначала `review.py --write`, потом этот скрипт, потом `facts_derive.py --write`.

Даты (review.py год не переносит, `date_is_supported` берет день только из русской цитаты):
- g3c46e216 (Mondi → «Готэк»): 2022-12-15 (подписание) → 2023-07-03 (закрытие; Ведомости, Mondi).
- gbe0ffe61 (PPF): 2022-12-07 (заметка об отчете) → 2023-04-04 (ЕГРЮЛ: Home Credit N.V. вышла
  из СК «Хоум Кредит Страхование»).
- gd01de1ad («Стокманн» / Podium Market): 2022-11-16 — день отмененного решения суда; сама покупка
  2017 года, а база начинается с 2022-го — дата не перенесена, вопрос владельцу.
  (Ведомости: магазины «перешедших «Стокманну» в 2017 г.»).
- g2d525daa (Nokian Tyres → «Татнефть»): 2022-10-28 (подписание) → 2023-03-24 (регистрация
  в ЕГРЮЛ; Neftegaz, Ведомости), основание registry.
- g8559b920 (Rubbles): 2022-08-01 → 2022 (в статьях только «в августе 2022 года», день выдуман).
- g2b9c2d45 (VK / MGL Wallet): 2023-07-31 → 2023 (только «в июле 2023 года»).
- ga9aa543c (CVS / Oak Street): 2023-02-08 (объявление) → 2023-05-02 (закрытие по 8-K CVS),
  основание closing; источник — SEC 8-K, английский, поэтому мимо review.py.

Прочее:
- ga9aa543c eco.finadv по-английски → по-русски (поле переносится дословно, перевод
  review.py не пропустит); extra — снято последнее пустое предложение.
- gedfd4c1e eco.context: «Gazprom-Media Technologies» нет ни в одной статье (Коммерсантъ:
  «Газпром-медиа»), «последний раунд» неверен (в феврале 2025 года вложился Диогу Далот,
  The Next Web); числа раунда — The Next Web («$15 million»), prose_gate английских чисел не видит.
- gf23149cf law.adv: снят ALUMNI Partners (не найден ни в статьях, ни в поиске).
- gf2c13b88 eco.finadv: фраза → имя консультанта; отпечаток прежней архивной записи —
  в proofread_absorbed.
- g7fc9f764 sum €1,7 млрд — списание Fortum, а не цена (временное управление) → пусто, в retracted.
- g22000f22 sum 54 млрд ₽ — верх расчета Ведомостей, цена не раскрыта → пусто, в retracted;
  снят источник t.me/BIRCHLEGAL/512 (подборка без этой сделки).
- g2b9c2d45: описание профиля gd2346bb9, где искали покупателя (accepted_notes.no_profile.buyer).
- g4b26b011: описание профиля gd096d9d8 пересказывало сделку.
- ga402c91b: покупатель — профиль g130b6d10 («Росспиртпром»), а не текст.
- g4feb5ec3: kind ipo → financing (pre-IPO раунд, тип уже «Инвестиция»).
- g042073c4 law.adv: снят Better Chance (нет ни в одной статье и в поиске).
- legal_short: g98105961 «Татнефть», mid «Мать и дитя», g23a1df20 «Белая скала»,
  g17f6794a «Подиум маркет» — party_legal_names.py эти реестровые имена не разбирает.

    python3 pipeline/archive/2026-11/fix_reread_2026_11_03_day.py            # сухой прогон
    python3 pipeline/archive/2026-11/fix_reread_2026_11_03_day.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DATES = [  # id, старая дата, новая дата, новое основание (None — не трогать)
    ('g3c46e216', '2022-12-15', '2023-07-03', None),
    ('gbe0ffe61', '2022-12-07', '2023-04-04', None),
    # gd01de1ad → 2017 откатан: база начинается с 2022 года (test_base_starts_in_2022), вопрос владельцу
    ('g2d525daa', '2022-10-28', '2023-03-24', 'registry'),
    ('g8559b920', '2022-08-01', '2022', None),
    ('g2b9c2d45', '2023-07-31', '2023', None),
    ('ga9aa543c', '2023-02-08', '2023-05-02', 'closing'),
]

MISSING = object()


def get(obj, path):
    for k in path:
        if not isinstance(obj, dict) or k not in obj:
            return MISSING
        obj = obj[k]
    return obj


def put(obj, path, value):
    for k in path[:-1]:
        obj = obj.setdefault(k, {})
    if value is MISSING:
        obj.pop(path[-1], None)
    else:
        obj[path[-1]] = value


def main(write=False):
    import review
    data = json.load(open(DATA, encoding='utf-8'))   # перечитать прямо перед записью
    deals = {d['id']: d for d in data['deals']}
    comps = data['companies']
    changes = []   # (объект, путь, старое, новое)

    def ch(obj, path, old, new):
        cur = get(obj, path)
        assert cur == old, '%s: %r, ожидали %r' % ('.'.join(path), cur, old)
        changes.append((obj, path, old, new))

    for did, old, new, basis in DATES:
        d = deals[did]
        assert not any(e.get('date') == old for e in d.get('events') or []), '%s: этап с той же датой' % did
        ch(d, ['date'], old, new)
        if basis:
            changes.append((d, ['date_basis'], d.get('date_basis'), basis))

    d = deals['ga9aa543c']
    ch(d, ['eco', 'finadv'],
       'Credit Suisse Securities (USA) LLC — co-financial advisor CVS Health; Lazard Ltd — co-financial '
       'advisor CVS Health; Centerview Partners — financial advisor Oak Street Health (гонорар ~$79,3 млн)',
       'Credit Suisse Securities (USA) LLC и Lazard Ltd — финансовые консультанты CVS Health; Centerview '
       'Partners — финансовый консультант Oak Street Health (гонорар около $79,3 млн)')
    old_extra = d.get('extra')
    tail = ' Финансирование сделки и обязательства крупных акционеров Oak Street Health описаны в разделах о финансировании и предмете сделки.'
    assert old_extra.endswith(tail), old_extra
    ch(d, ['extra'], old_extra, old_extra[:-len(tail)])

    ch(deals['gedfd4c1e'], ['eco', 'context'],
       'Bioniq была основана в 2019 году в Лондоне бывшим топ-менеджером Gazprom-Media Technologies Вадимом '
       'Федотовым; последний раунд финансирования (Series B, $15 млн, июль 2024) был проведен под руководством '
       'HV Capital и Unbound при оценке $75 млн, которая выросла до $82 млн после входа Криштиану Роналду в '
       'октябре 2024 года.',
       'Bioniq основал в 2019 году в Лондоне Вадим Федотов — бывший баскетболист и топ-менеджер «Газпром-медиа». '
       'В июле 2024 года компания привлекла $15 млн в раунде B, его возглавили фонды HV Capital и Unbound, и '
       'Bioniq тогда оценили в $75 млн. После того как в октябре 2024 года в компанию инвестировал Криштиану '
       'Роналду, оценка выросла до $82 млн.')

    ch(deals['gf23149cf'], ['law', 'adv'],
       [['Юридический консультант', 'ALUMNI Partners', 'юридический советник VK Group (сторона покупателя)']],
       [['Стороны сделки', 'Не раскрывались', 'Консультанты сделки в публичных источниках не названы']])

    d = deals['gf2c13b88']
    ch(d, ['eco', 'finadv'], 'Финансовым консультантом по сделке выступал Advance Capital', 'Advance Capital')
    prev = [f for f in review.FIXES if (f['id'], f['field']) == ('gf2c13b88', 'eco.finadv')]
    marks = list((d.get('proofread_absorbed') or {}).get('eco.finadv') or [])
    for f in prev:
        fp = review.fix_fingerprint(f['new'])
        if fp not in marks:
            marks.append(fp)
    changes.append((d, ['proofread_absorbed', 'eco.finadv'], None, marks))

    for did, val in (('g7fc9f764', '€1,7 млрд'), ('g22000f22', '54 млрд ₽')):
        d = deals[did]
        ch(d, ['sum'], val, MISSING)
        assert get(d, ['eco', 'sum']) in (val, '—'), get(d, ['eco', 'sum'])
        changes.append((d, ['eco', 'sum'], get(d, ['eco', 'sum']), '—'))
        retr = list(get(d, ['retracted', 'sum']) if get(d, ['retracted', 'sum']) is not MISSING else [])
        if val not in retr:
            retr.append(val)
        changes.append((d, ['retracted', 'sum'], None, retr))

    d = deals['g22000f22']
    bad = ['Telegram-канал фирмы', 'https://t.me/BIRCHLEGAL/512']
    src = [s for s in d['src'] if s[1] != bad[1]]
    assert len(src) == len(d['src']) - 1, 'нет источника %s' % bad[1]
    ch(d, ['src'], d['src'], src)

    ch(comps['gd2346bb9'], ['desc'],
       'Кипрская финтех-компания, лицензированная ЦБ Кипра; в 2023 году VK продала контроль в ней неназванному '
       'покупателю за €1 млн.',
       'Кипрская финтех-компания: онлайн-платежи для частных лиц и бизнеса в Европейской экономической зоне.')
    ch(deals['g2b9c2d45'], ['accepted_notes', 'no_profile', 'buyer'], MISSING,
       'Покупатель не назван: искали в отчете VK по пересказам Интерфакса, ПРАЙМ, Finversia, Interfax (EN) и в '
       'WebSearch по MGL Wallet (3 ноября 2026); иностранная компания, реестра ФНС нет')
    ch(comps['gd096d9d8'], ['desc'],
       'Холдинг, владевший казахстанскими активами Beeline («КаР-Тел», «КазЕвроМобайл»); в 2022 году '
       '«Вымпелком» продал 75% акций VEON за 54 млрд ₽.',
       'Холдинг, которому принадлежат казахстанские операторы ТОО «КаР-Тел» и ТОО «КазЕвроМобайл».')

    d = deals['ga402c91b']
    assert d.get('buyer') in (None, ''), d.get('buyer')
    assert (d.get('buyer_name') or '').find('Росспиртпром') >= 0, d.get('buyer_name')
    changes.append((d, ['buyer'], None, 'g130b6d10'))
    changes.append((d, ['buyer_name'], d.get('buyer_name'), MISSING))

    ch(deals['g4feb5ec3'], ['kind'], 'ipo', 'financing')

    d = deals['g042073c4']
    names = [a[1] for a in d['law']['adv']]
    assert names == ['Better Chance (Вадим Турцев, Булат Жамбалнимбуев)', 'ККМП (Кучер Кулешов Максименко и партнеры)'], names
    ch(d, ['law', 'adv'], d['law']['adv'], [a for a in d['law']['adv'] if not a[1].startswith('Better Chance')])

    for cid, name_part, short in (('g98105961', 'Татнефть', 'ПАО «Татнефть» им. В. Д. Шашина'),
                                  ('mid', 'Мать и дитя', 'МКПАО «МД Медикал Груп»'),
                                  ('g23a1df20', 'Белая скала', 'АО «УК «Белая скала»'),
                                  ('g17f6794a', None, 'ООО «ИПК «Атлас»')):
        c = comps[cid]
        assert name_part is None or name_part in c['name'], c['name']
        ch(c, ['legal_short'], MISSING, short)

    for obj, path, old, new in changes:
        print('%s %s: %s → %s' % (obj.get('id') or obj.get('name'), '.'.join(path),
                                  str(old if old is not MISSING else '∅')[:70], str(new if new is not MISSING else '∅')[:70]))
    if not write:
        print('Сухой прогон: %d изменений. Запись — с ключом --write.' % len(changes))
        return
    for obj, path, old, new in changes:
        put(obj, path, new)
    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('Записано: %d изменений.' % len(changes))


if __name__ == '__main__':
    main('--write' in sys.argv)
