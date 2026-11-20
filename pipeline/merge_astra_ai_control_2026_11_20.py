# -*- coding: utf-8 -*-
"""Карточка `g2777a4b6» («Группа Астра» купила 26% разработчика ИИ AiB,
собрана 15 мая 2026) описывала только ПЕРВЫЙ транш — вход «Группы Астра» в
капитал ООО «АИБ» (бренд AiB, позже переименовано в ООО «Астра ИИ»,
datanewton FULL_NAME, смена 22.07.2026) с долей 26%. Сегодняшний приток
принес вторую новость об этой же сделке: «Группа Астра» нарастила долю до
80% (Ведомости, draft_id=d98123273; CNews, draft_id=d80736095 — тот же
сюжет, второе издание).

Ворота не пропустили ни одну из двух статей автоматически («не установлен
предмет сделки») — обе легли в `data/inbox/hold/2026-11-20.json`, в
pending.json не попали. Это не новая сделка, а второй этап уже описанной
(тот же покупатель, тот же профиль-предмет `gb02cbc20`, тот же механизм —
«Астра инвестиции»; прецедент слияния этапов — `g85e07f6d`/НПО «РТС»,
19 ноября 2026, `pipeline/merge_npo_rts_cnti_result_2026_11_19.py`): карточку
правим, вторую отдельную не заводим.

Почему не через таблицу FIXES (review.py): проза ниже — пересказ, а не
дословная цитата источника, и дописывается `events[]`, которого review.py не
читает (та же причина, что в merge_npo_rts_cnti_result_2026_11_19.py и
более старых слияниях этапов). Правка — прямым скриптом с assert на старое
значение каждого поля; факты (`title`, `date`, `eco.share`, `seller`) несут
цитату в `fact_log` (правило владельца 11 ноября 2026, `fact_edit_guard.py`).

ЧТО ПОДТВЕРЖДЕНО. Обе статьи (Ведомости, CNews) сходятся: «Группа Астра»
через «Астра инвестиции» увеличила долю в «Астра ИИ» с 26% до 80%;
Владимир Нелюб (директор по науке и ИИ «Группы Астра», гендиректор
«Астра ИИ») сохранил 20%. Кто продал — явно не названо ни в одной статье,
дочитано по ЕГРЮЛ (datanewton, ОГРН 1227700112485, api/v2/history,
OWNERS): запись от 2026-11-09 — Андрей Гантимуров (24,64%) полностью вышел
из состава участников, номинал доли Владимира Нелюба снизился с 6670 до
2703 ₽ (с 49,36% до 20%), номинал «Астра инвестиций» выросл с 3513 до
10810 ₽ (с 26% до 80%). Иностранных или подсанкционных лиц в истории нет —
`accepted_notes.checked.registry_owners`.

Сумма транша не названа ни в одном источнике: по CNews, расчет прошел
акциями самой ПАО «Группа Астра» из квазиказначейского пакета (а не
деньгами), с ограничением на их перепродажу, которое снимается поэтапно в
2027 году — это записано в `eco.val`/`law.struct`, а не в `sum`/`eco.sum`
(оставлены «Не раскрыта», как и было).

Тип сделки меняется с «Инвестиция» на «M&A»: 26% были миноритарным
вложением (cash_in), 80% — контрольный пакет (control_change); так же
типизированы другие консолидации «Группы Астра» (`g83bd07f6` — «купила
контроль в разработчиках ISPsystem, Knomary и GitFlic»). После записи — `python3
pipeline/facts_derive.py --write`: «facts» карточки пересчитаются с новым
`type`/`eco.share`.

Источники второго транша:
  Ведомости — https://www.vedomosti.ru/investments/news/2026/11/20/1413616-gruppa-astra
  CNews     — https://www.cnews.ru/news/line/2026-11-20_gruppa_astra_uvelichila
(тексты забраны целиком, на диске — data/inbox/raw/2026-11-20-articles.jsonl).

Запуск:
    python3 pipeline/merge_astra_ai_control_2026_11_20.py            # сухой прогон
    python3 pipeline/merge_astra_ai_control_2026_11_20.py --write    # применить
"""
import json
import os
import sys

ROOT = '/home/user/Compass'
sys.path.insert(0, os.path.join(ROOT, 'pipeline', 'ingest'))
import enrich  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

CARD_ID = 'g2777a4b6'

SRC_VED = ['Ведомости', 'https://www.vedomosti.ru/investments/news/2026/11/20/1413616-gruppa-astra']
SRC_CNEWS = ['CNews', 'https://www.cnews.ru/news/line/2026-11-20_gruppa_astra_uvelichila']
SRC_VED_MAY = ['Ведомости',
               'https://www.vedomosti.ru/technology/articles/2026/05/26/1199902-gruppa-astra-vikupila-26-kompanii-razrabotchika-iskusstvennogo-intellekta']
REGISTRY_URL = 'https://datanewton.ru/api/v2/history?ogrn=1227700112485&startDate=2000-01-01&attributes=OWNERS'

OLD_TITLE = '«Группа Астра» купила 26% разработчика ИИ AiB'
NEW_TITLE = '«Группа Астра» выкупила контроль в «Астра ИИ»'

OLD_TYPE = 'Инвестиция'
NEW_TYPE = 'M&A'

OLD_DATE = '2026-05-15'
NEW_DATE = '2026-11-09'

NEW_SELLER = 'Андрей Гантимуров и Владимир Нелюб'

OLD_SHARE = '26% долей в ООО «АИБ» (бренд AiB).'
NEW_SHARE = ('80% долей в ООО «Астра ИИ» (прежнее название — ООО «АИБ», бренд AiB). В мае 2026 года '
             '«Группа Астра» получила 26% компании; в ноябре 2026 года через «Астра инвестиции» выкупила еще '
             '54% и довела долю до контрольной. Директор по науке и искусственному интеллекту «Группы Астра» '
             'и гендиректор «Астра ИИ» Владимир Нелюб сохранил 20% в капитале компании.')

OLD_VAL = ('Официально сумму не раскрывали. По оценке сооснователя «МойОфис» Дмитрия Комиссарова, сделка могла '
           'обойтись примерно в 100 млн ₽; другие эксперты оценивают ее в 80–100 млн ₽.')
NEW_VAL = (OLD_VAL + '\n\nЦену ноябрьского транша стороны не назвали; по данным CNews, оплата прошла акциями '
           'самой «Группы Астра» из квазиказначейского пакета, а ограничение на их перепродажу будет сниматься '
           'по частям в течение 2027 года.')

OLD_CONTEXT = ('AiB (ООО «АИБ») основана в Москве в марте 2022 года. Ее главный продукт — Razum AI: на этой '
               'платформе модели машинного обучения готовят и запускают без программирования, в визуальном '
               'редакторе; продукт внесен в реестр российского ПО. В команде более 50 специалистов.\n\n'
               'Гендиректором AiB в марте 2026 года стал Владимир Нелюб, до этого директор по науке и ИИ '
               '«Группы Астра»; тогда же к нему перешли 66,7% компании, которые принадлежали Евгению Лысенко.'
               '\n\nПо данным источников в «Группе Астра», группа может довести долю в AiB до контрольной — '
               'это будет зависеть от результатов компании.')
NEW_CONTEXT = ('AiB (ООО «АИБ») основана в Москве в марте 2022 года. Ее главный продукт — Razum AI: на этой '
               'платформе модели машинного обучения готовят и запускают без программирования, в визуальном '
               'редакторе; продукт внесен в реестр российского ПО. В команде более 50 специалистов.\n\n'
               'Гендиректором AiB в марте 2026 года стал Владимир Нелюб, до этого директор по науке и ИИ '
               '«Группы Астра»; тогда же к нему перешли 66,7% компании, которые принадлежали Евгению Лысенко.'
               '\n\nК ноябрю 2026 года план реализовался: «Группа Астра» нарастила долю до 80%, а по сведениям '
               'компании, в «Астра ИИ» на прежних местах остались свыше 60 человек команды.')

OLD_STRUCT = ('«Группа Астра» вошла в ООО «АИБ» через дочернюю компанию «Астра Инвестиции» новым участником с '
              'долей 26%. По ЕГРЮЛ ее доля номиналом 3 513 ₽ добавилась к прежним: номинал долей Владимира '
              'Нелюба (6 670 ₽) и Андрея Гантимурова (3 330 ₽) остался тем же, а в процентах их доли снизились '
              'с 66,7% до 49,36% и с 33,3% до 24,64%.')
NEW_STRUCT = (OLD_STRUCT + '\n\n«Астра инвестиции» нарастила долю в ООО «Астра ИИ» (бывшее ООО «АИБ») с 26% до '
              '80%. По данным ЕГРЮЛ, 9 ноября 2026 года Андрей Гантимуров полностью вышел из состава участников '
              '(ранее владел 24,64%), а номинал доли Владимира Нелюба снизился с 6 670 до 2 703 ₽ — с 49,36% до '
              '20%. Оплата прошла акциями самой «Группы Астра» из квазиказначейского пакета; ограничение на их '
              'перепродажу снимается поэтапно в 2027 году.')


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))
    by_id = {d['id']: d for d in data['deals']}
    card = by_id.get(CARD_ID)
    if card is None:
        print('ОТКАЗ: карточки %s нет в базе' % CARD_ID)
        return 1

    assert card.get('title') == OLD_TITLE, card.get('title')
    assert card.get('type') == OLD_TYPE, card.get('type')
    assert card.get('date') == OLD_DATE, card.get('date')
    assert card.get('status') == 'Закрыта', card.get('status')
    assert card.get('seller') is None, card.get('seller')
    assert card['eco']['share'] == OLD_SHARE, card['eco']['share']
    assert card['eco']['val'] == OLD_VAL, card['eco']['val']
    assert card['eco']['context'] == OLD_CONTEXT, card['eco']['context']
    assert card['law']['struct'] == OLD_STRUCT, card['law']['struct']
    assert not card.get('events')
    assert not card.get('accepted_notes')

    new_event = {
        'kind': 'closed', 'date': NEW_DATE, 'title': 'Сделка завершена',
        'note': ('«Группа Астра» увеличила долю в «Астра ИИ» с 26% до 80%, выкупив дополнительные 54% через '
                 '«Астра инвестиции»; Владимир Нелюб сохранил 20%.'),
        'source': list(SRC_VED),
    }
    # `enrich.prior_stage_event` здесь ничего не вернет: статус не менялся
    # (оба транша — «Закрыта», один и тот же STAGE_KIND), поэтому прежний
    # этап дописываем вручную, тем же каркасом, что строит сама функция.
    prior = {'id': 'closed-%s' % OLD_DATE, 'kind': 'closed', 'date': OLD_DATE, 'title': 'Сделка завершена',
             'historicalTitle': OLD_TITLE, 'note': '', 'sources': [list(SRC_VED_MAY)]}
    assert enrich.prior_stage_event(card, new_event) is None  # подтверждает, что ветка выше верна

    print('ПРАВКА %s' % CARD_ID)
    print('  title  : %r -> %r' % (OLD_TITLE, NEW_TITLE))
    print('  type   : %r -> %r' % (OLD_TYPE, NEW_TYPE))
    print('  date   : %r -> %r' % (OLD_DATE, NEW_DATE))
    print('  seller : None -> %r' % NEW_SELLER)
    print('  events : +closed %s, +closed %s' % (OLD_DATE, NEW_DATE))
    print('  src    : +%s +%s' % (SRC_VED[0], SRC_CNEWS[0]))
    if not write:
        print('\nСухой прогон. Применение — с ключом --write.')
        return 0

    card['title'] = NEW_TITLE
    card['type'] = NEW_TYPE
    card['date'] = NEW_DATE
    card['seller'] = NEW_SELLER
    card['eco']['share'] = NEW_SHARE
    card['eco']['val'] = NEW_VAL
    card['eco']['context'] = NEW_CONTEXT
    card['law']['struct'] = NEW_STRUCT
    card['events'] = [prior, new_event]

    existing_urls = {s[1] for s in card.get('src', []) if len(s) > 1}
    for s in (SRC_VED, SRC_CNEWS):
        if s[1] not in existing_urls:
            card.setdefault('src', []).append(list(s))

    pe = card.setdefault('party_evidence', {})
    pe['seller'] = [{'value': NEW_SELLER, 'field': 'seller',
                      'method': 'registry_history', 'url': REGISTRY_URL}]

    notes = card.setdefault('accepted_notes', {})
    checked = notes.setdefault('checked', {})
    checked['registry_owners'] = (
        'история участников ЕГРЮЛ (datanewton, ОГРН 1227700112485): запись от 2026-11-09 — Андрей Гантимуров '
        '(ИНН 772791526626) полностью вышел из состава участников (ранее 24,64%), номинал доли Владимира '
        'Нелюба (ИНН 772878584904) снизился с 6 670 до 2 703 ₽ (с 49,36% до 20%), номинал «Астра инвестиций» '
        'вырос с 3 513 до 10 810 ₽ (с 26% до 80%); иностранных или подсанкционных лиц в истории нет')

    fact_log = card.setdefault('fact_log', [])
    fact_log.append({'field': 'title', 'new': NEW_TITLE,
                      'quote': ('Получив контроль над «Астра ИИ», мы можем эффективнее развивать эти технологии '
                                'вместе с нашим инфраструктурным софтом, средствами защиты информации и предлагать '
                                'их заказчикам как единое решение'),
                      'url': SRC_CNEWS[1], 'by': 'приток, 20.11.2026', 'date': '2026-11-20'})
    fact_log.append({'field': 'date', 'new': NEW_DATE,
                      'quote': 'OWNERS updated_at 2026-11-09: доля "АСТРА ИНВЕСТИЦИИ" выросла с 26.0% до 80.0%',
                      'url': REGISTRY_URL, 'by': 'приток, 20.11.2026 (ЕГРЮЛ)', 'date': '2026-11-20'})
    fact_log.append({'field': 'eco.share', 'new': NEW_SHARE,
                      'quote': ('«Группа Астра» нарастила долю в «Астра ИИ» с 26% до 80%... Владимир Нелюб... '
                                'сохранил 20% в капитале «Астра ИИ»'),
                      'url': SRC_CNEWS[1], 'by': 'приток, 20.11.2026', 'date': '2026-11-20'})
    fact_log.append({'field': 'seller', 'new': NEW_SELLER,
                      'quote': ('OWNERS updated_at 2026-11-09: "ГАНТИМУРОВ АНДРЕЙ ПАВЛОВИЧ ... 24.64%" -> null; '
                                '"НЕЛЮБ ВЛАДИМИР АЛЕКСАНДРОВИЧ ... 49.36%" -> "... 20.0%"'),
                      'url': REGISTRY_URL, 'by': 'приток, 20.11.2026 (ЕГРЮЛ)', 'date': '2026-11-20'})

    # Карточку перечитываем прямо перед записью — чужой пуш не затирается.
    fresh = json.load(open(DATA, encoding='utf-8'))
    fresh_by_id = {d['id']: d for d in fresh['deals']}
    fresh_card = fresh_by_id[CARD_ID]
    assert fresh_card.get('title') == OLD_TITLE, 'карточку кто-то уже поправил — перечитайте'
    idx = fresh['deals'].index(fresh_card)
    fresh['deals'][idx] = card

    json.dump(fresh, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('\nПрименено.')
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
