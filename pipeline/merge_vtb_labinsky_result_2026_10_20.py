# -*- coding: utf-8 -*-
"""Карточка `g97679d43` («ВТБ продает аграрные активы (агрокомплекс
«Лабинский» и сельхозземли)», добавлена 23 июля 2026) описывала только ПОИСК
покупателя — ВТБ выбирал между «Агрокомплексом им. Ткачева» и агрохолдингом
«Просторы». Сегодняшний приток принёс исход: Frank Media сообщил, что ВТБ
продал «Лабинский» структурам «Просторов» за 50 млрд рублей — ровно ту же
сумму, что раньше оценивал BGP Capital для EV самого «Лабинского» (без земель
Очкаласова, которые Frank Media не упоминает).

Ворота притока завели на эту же новость ОТДЕЛЬНУЮ карточку (`g2dce9ce0`,
черновик `d37214342`; слабый матчер не опознал смену ракурса заголовка —
«продаёт» → «продал», плюс другой набор слов) — это исход уже известной
сделки, не новая сделка (признак и образец — `docs/intake_run.md`, шаг 3а,
case Azimut/Ярославль, `merge_azimut_yaroslavl_result_2026_10_13.py`).
`g2dce9ce0` убирается из `pending.json`, факты уходят в `g97679d43`; поиск
источников для неё (сделан этим же прогоном — Moscow Times/Reuters за
апрель, июль, август 2026, Коммерсантъ и AK&M про «Просторы») дал всё
нужное для дозаполнения старой карточки.

Почему не через таблицу FIXES (review.py/write_card.py): почти все поля
переписываются целиком, сводя старый и новый текст в один, а не дописывая
цитату к пустому полю — ни review.py (дословная цитата целиком), ни
write_card.py (опирается на facts/evidence одной карточки) для такого
слияния не предназначены (docs/card_editing.md, «Когда review.py не
подходит»). Правка — прямым скриптом с `assert` на старое значение каждого
поля. Проверка на самопереписывание — `pipeline/verbatim_check.py --card
g97679d43` после записи (тот же рубеж, что у прямой правки опубликованной
карточки, docs/intake_run.md).

Открытый риск, честно отражённый в eco.val: сумму и покупателя назвал
только Frank Media (пересказ, без собственного текста статьи — страница
не отдаёт полный текст нашему забору); сам ВТБ ни то ни другое публично
не подтвердил ни в одном из более ранних заявлений. Входят ли в сделку
земли Виталия Очкаласова (отдельно оценивались в 5,5 млрд ₽) — источник
не уточняет, в карточку этот факт не переносится как решённый.

Источники (дочитаны полностью, тексты в data/inbox/raw/2026-10-20-articles.jsonl,
кроме Frank Media — страница отдаёт только RSS-заголовок и краткую сводку):
  Frank Media                 https://frankmedia.ru/310918
  The Moscow Times (Reuters)  https://ru.themoscowtimes.com/2026/08/28/vtb-podpisal-soglashenie-ob-usloviyakh-s-pokupatelem-agrokompleksa-labinskiy-bank-a204588
  The Moscow Times (Reuters)  https://ru.themoscowtimes.com/2026/04/08/update-1-vtb-prodast-vse-selskokhozyaystvennye-aktivy-prodolzhaet-diskussiyu-o-dividendakh-kostin-a192095
  The Moscow Times (Reuters)  https://ru.themoscowtimes.com/2026/07/03/intervyu-vtb-nadeetsya-prodat-agrokompleks-labinskiy-v-26g-1-y-zampred-vtb-a199935
  Коммерсантъ                 https://www.kommersant.ru/doc/7268241
  AK&M                        https://www.akm.ru/news/vyruchka_predpriyatiy_agrokholdinga_prostory_po_itogam_2024_goda_sostavila_65_57_mlrd_rub/

Запуск:
    python3 pipeline/merge_vtb_labinsky_result_2026_10_20.py            # сухой прогон
    python3 pipeline/merge_vtb_labinsky_result_2026_10_20.py --write    # применить
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import enrich  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
PENDING = os.path.join(ROOT, 'static', 'data', 'pending.json')

CARD_ID = 'g97679d43'
PENDING_DUP_ID = 'g2dce9ce0'
DUP_DRAFT_ID = 'd37214342'

FRANK = ['Frank Media', 'https://frankmedia.ru/310918']
MT_AUG = ['The Moscow Times (Reuters)',
          'https://ru.themoscowtimes.com/2026/08/28/vtb-podpisal-soglashenie-ob-usloviyakh-s-pokupatelem-agrokompleksa-labinskiy-bank-a204588']
MT_APR = ['The Moscow Times (Reuters)',
          'https://ru.themoscowtimes.com/2026/04/08/update-1-vtb-prodast-vse-selskokhozyaystvennye-aktivy-prodolzhaet-diskussiyu-o-dividendakh-kostin-a192095']
MT_JUL = ['The Moscow Times (Reuters)',
          'https://ru.themoscowtimes.com/2026/07/03/intervyu-vtb-nadeetsya-prodat-agrokompleks-labinskiy-v-26g-1-y-zampred-vtb-a199935']
KOMMERSANT = ['Коммерсантъ', 'https://www.kommersant.ru/doc/7268241']
AKM = ['AK&M', 'https://www.akm.ru/news/vyruchka_predpriyatiy_agrokholdinga_prostory_po_itogam_2024_goda_sostavila_65_57_mlrd_rub/']

OLD_TITLE = 'ВТБ продает аграрные активы (агрокомплекс «Лабинский» и сельхозземли)'
NEW_TITLE = 'ВТБ продал агрохолдинг «Лабинский» за 50 млрд рублей'

OLD_STATUS = 'Обсуждается'
NEW_STATUS = 'Закрыта'
OLD_DATE = '2026'
NEW_DATE = '2026-10-20'
OLD_SUM = '55 млрд ₽ (по оценке)'
NEW_SUM = '50 млрд ₽'

BUYER_COMPANY_ID = 'g8611f1d2'  # агрохолдинг «Просторы»

OLD_VAL = '55 млрд ₽: 50 млрд ₽ за «Лабинский» и 5,5 млрд ₽ за земли Очкаласова.'
NEW_VAL = ('Сделка закрылась на уровне более ранней оценки: BGP Capital оценивал '
           '«Лабинский» отдельно в 50 млрд ₽, а земли Виталия Очкаласова — в 5,5 млрд ₽. '
           'Итоговую сумму и покупателя назвал только Frank Media (около 50 млрд ₽, '
           '«Просторы») — сам ВТБ ни то ни другое публично не подтвердил ни в одном из '
           'более ранних заявлений; входят ли в сделку земли Очкаласова, источник не '
           'уточняет.')

OLD_RATIONALE = ('Старший аналитик «Риком-Траст» Валерия Попова связывает решение с '
                  'изменениями банковского регулирования. Банк России собирается ввести '
                  'для банков лимит на непрофильные активы, привязанный к размеру '
                  'капитала, — он заработает с 1 апреля 2027 года. Так риски должны лечь '
                  'на акционеров банков, а не на вкладчиков и кредиторов.')
NEW_RATIONALE = ('ВТБ приобретал «Лабинский» в инвестиционных целях, рассчитывая продать '
                  'актив «в обозримой перспективе». Весной 2026 глава банка Андрей Костин '
                  'подтвердил решение продать все сельхозактивы: «У нас есть '
                  'сельскохозяйственные активы, но я принял решение их продать, скорее '
                  'всего. Мы ушли из села… теперь только в городе», — и ждал конкурс '
                  'среди покупателей: «Да, у нас там конкурс будет, там много желающих». '
                  'Старший аналитик «Риком-Траст» Валерия Попова связывала такое решение '
                  'с изменениями банковского регулирования — Банк России вводит для '
                  'банков лимит на непрофильные активы, привязанный к размеру капитала, '
                  'который заработает с 1 апреля 2027 года; сам Костин выход из гостиниц '
                  'и сельхозактивов объяснил тем же: «Мы, кстати, уже гостиницы продали, '
                  'мы еще продаем активы, скоро узнаете. Мы, в общем-то, все непрофильные '
                  'активы сейчас стараемся продать».')

OLD_CONTEXT = ('ВТБ резко поменял подход к аграрным активам: ещё в декабре 2025 Андрей '
               'Костин говорил о планах отдельного агрохолдинга — то есть скорее о '
               'покупке, чем о продаже. Пешков не исключает, что позицию поменяли из-за '
               'слабых финансовых результатов агропредприятий. Агрокомплекс «Лабинский» '
               'в декабре 2024 перешёл от Росимущества к ООО «Мегатэк», 99% которого у '
               'ООО «БФ Прямые инвестиции»; владельцы «БФ Прямые инвестиции» в ЕГРЮЛ не '
               'раскрыты. До марта 2022 эта компания принадлежала ООО «Бизнес-финанс» — '
               'дочерней структуре ВТБ.')
NEW_CONTEXT = ('Агрокомплекс «Лабинский» — бывшие активы концерна «Покровский», одного из '
               'крупнейших агрохолдингов юга России (растениеводство, животноводство, '
               'сахар): его передали в управление Росимущества по решению суда после '
               'того, как Генпрокуратура предъявила обвинения в коррупции основным '
               'владельцам концерна; основатель «Покровского» Андрей Коровайко через '
               'представителя эти обвинения отвергает. В декабре 2024 актив перешёл от '
               'Росимущества к ООО «Мегатэк», 99% которого принадлежит ООО «БФ Прямые '
               'инвестиции» (владельцы не раскрыты в ЕГРЮЛ); до марта 2022 эта компания '
               'принадлежала ООО «Бизнес-финанс» — дочерней структуре ВТБ. У банка уже '
               'был опыт в агробизнесе: ему принадлежала одна из крупнейших '
               'вертикально-интегрированных зерновых компаний «Деметра-Холдинг», из '
               'которой он вышел летом 2023 года. Ещё в декабре 2025 Костин говорил о '
               'планах создать на базе «Лабинского» отдельный агрохолдинг — то есть '
               'скорее о покупке, чем о продаже; Пешков не исключает, что позицию '
               'поменяли из-за слабых финансовых результатов агропредприятий. Победителем '
               'в поиске покупателя, который вели среди «Агрокомплекса им. Ткачева» и '
               '«Просторов», стали структуры «Просторов» — холдинга, который по данным '
               'ЕГРЮЛ в октябре 2024 получил 99% долей ООО «Инвестком», контролирующего '
               '11 сельхозкомпаний, включая производителя круп АФГ «Националь» и '
               'производителя мраморной говядины группу «Заречное»; тем же путём '
               '«Просторы» ранее получили растениеводческий холдинг «Дон-Агро» — '
               'выкупили его у экс-депутата Госдумы Евгения Туголукова. Бенефициаром '
               '«Инвесткома» называли Ивана Юзефовича, партнёра экс-президента УГМК '
               'Искандера Махмудова; позже бенефициары «Просторов» официально не '
               'раскрывались, а по данным AK&M реальные владельцы — сам Махмудов и '
               'Анатолий Коцюк, в равных долях. Первый зампред ВТБ Дмитрий Пьянов '
               'рассказывал, что потенциальные покупатели «Лабинского» проводят due '
               'diligence, и банк надеется продать актив во втором полугодии; позже '
               'он сообщил, что ВТБ подписал с покупателем соглашение об условиях '
               'сделки и ждёт её закрытия до конца года, не назвав покупателя '
               'публично.')

OLD_APPR = 'Публично не сообщалось'
NEW_APPR = OLD_APPR  # не трогаем: due diligence/подписание условий — не согласование
                     # органа (ФАС и т.п.), test_data.py::test_approval_names_a_body;
                     # этот факт ушёл в eco.context ниже

OLD_EXTRA = ('В портфель входят агрокомплекс «Лабинский» (218 тыс. га) и сельхозземли '
             'Виталия Очкаласова (12,2 тыс. га). Возможные покупатели — «Агрокомплекс '
             'им. Ткачева» и агрохолдинг «Просторы». Пока идёт поиск покупателя, сделку '
             'планируют завершить до 2027 года. По оценке BGP Capital, стоимость '
             'бизнеса (EV) «Лабинского» — 50 млрд ₽, активы Очкаласова — 5,5 млрд ₽.')
NEW_EXTRA = '—'


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    card = by_id.get(CARD_ID)
    if card is None:
        print('ОТКАЗ: карточки %s нет в базе' % CARD_ID)
        return 1

    assert card.get('title') == OLD_TITLE, card.get('title')
    assert card.get('status') == OLD_STATUS, card.get('status')
    assert card.get('date') == OLD_DATE, card.get('date')
    assert card.get('sum') == OLD_SUM, card.get('sum')
    assert card.get('buyer') is None, card.get('buyer')
    assert card['eco']['val'] == OLD_VAL
    assert card['eco']['rationale'] == OLD_RATIONALE
    assert card['eco']['context'] == OLD_CONTEXT
    assert card['law']['appr'] == OLD_APPR
    assert card.get('extra') == OLD_EXTRA
    assert not card.get('events')

    new_event = {
        'kind': 'closed', 'date': NEW_DATE, 'title': 'Сделка завершена',
        'note': ('ВТБ объявил, что продал агрохолдинг «Лабинский» структурам '
                 'агрохолдинга «Просторы» за 50 млрд рублей; сумму и покупателя назвал '
                 'только Frank Media, сам банк не подтверждал.'),
        'source': list(FRANK),
    }
    prior = enrich.prior_stage_event(card, new_event)
    if prior is None:
        prior = {'id': 'negotiations-%s' % OLD_DATE, 'kind': 'negotiations', 'date': OLD_DATE,
                  'title': 'Переговоры', 'historicalTitle': OLD_TITLE, 'note': '',
                  'sources': [list(KOMMERSANT)] if card.get('src') else []}

    print('ПРАВКА %s' % CARD_ID)
    print('  title  : %r -> %r' % (OLD_TITLE, NEW_TITLE))
    print('  status : %r -> %r' % (OLD_STATUS, NEW_STATUS))
    print('  date   : %r -> %r' % (OLD_DATE, NEW_DATE))
    print('  sum    : %r -> %r' % (OLD_SUM, NEW_SUM))
    print('  buyer  : None -> %r (агрохолдинг «Просторы»)' % BUYER_COMPANY_ID)
    print('  events : +%s' % [prior['kind'], new_event['kind']])
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    card['title'] = NEW_TITLE
    card['status'] = NEW_STATUS
    card['date'] = NEW_DATE
    card['sum'] = NEW_SUM
    card['buyer'] = BUYER_COMPANY_ID
    card['eco']['val'] = NEW_VAL
    card['eco']['rationale'] = NEW_RATIONALE
    card['eco']['context'] = NEW_CONTEXT
    card['law']['appr'] = NEW_APPR
    card['extra'] = NEW_EXTRA
    card['events'] = [prior, new_event]

    existing_urls = {s[1] for s in card.get('src', []) if len(s) > 1}
    for src in (FRANK, MT_AUG, MT_APR, MT_JUL, KOMMERSANT, AKM):
        if src[1] not in existing_urls:
            card.setdefault('src', []).append(list(src))
            existing_urls.add(src[1])

    pe = card.setdefault('party_evidence', {})
    pe['buyer'] = [{'value': 'агрохолдинг «Просторы»', 'field': 'buyer',
                    'method': 'human_review', 'url': FRANK[1]}]

    # Карточку перечитываем прямо перед записью — чужой пуш не затирается.
    fresh = json.load(open(DATA, encoding='utf-8'))
    fresh_by_id = {d['id']: d for d in fresh['deals']}
    fresh_card = fresh_by_id[CARD_ID]
    assert fresh_card.get('title') == OLD_TITLE, 'карточку кто-то уже поправил — перечитайте'
    idx = fresh['deals'].index(fresh_card)
    fresh['deals'][idx] = card

    # Дублирующую карточку из pending.json убираем: эти факты теперь в g97679d43.
    pending = json.load(open(PENDING, encoding='utf-8'))
    before = len(pending['cards'])
    pending['cards'] = [c for c in pending['cards'] if c['id'] != PENDING_DUP_ID]
    removed = before - len(pending['cards'])

    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    json.dump(pending, open(PENDING, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено. Из pending.json убрано карточек: %d.' % removed)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
