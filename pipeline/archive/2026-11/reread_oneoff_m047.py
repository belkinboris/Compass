# -*- coding: utf-8 -*-
"""Вычитка базы, марафон 12 ноября 2026, партия m047: правки, которые не ложатся в FIXES.

ЧТО ЧИНИТ И ПОЧЕМУ (доказательства — цитаты в OPS, статьи сохранены
save_source.py в data/inbox/triage/sources_2026-11-12_m047.json):
  g94dcc5cc («Газпром Тех»/Aurus) — дата стояла днем слуха (30.10.2023), а
      сделка закрыта летом 2025 года (Ведомости, Коммерсантъ): дата — год 2025.
      Профиль «Газпром Тех» описывал чужую сделку («Микран») — описание компании.
  g8f1fab29 («Русал»/HWNM) — дата стояла днем подписания (23.10.2023), а права
      на долю перешли в апреле 2024 года (Ведомости, Интерфакс): дата — год 2024.
  ga5b0724c («Лебеди») — в extra утверждения без опоры в источниках (AVG Capital
      Partners, цены и выручка 2024–2025); law.struct повторял мнение эксперта
      из eco.fin — снято.
  g4612b667 («МЗК Экспорт»/Viterra) — предметом стоял профиль-описание
      «операционный бизнес и зерновой терминал…»: переходила ООО «МЗК Экспорт»
      (Интерфакс по ЕГРЮЛ, отчет Viterra); профиль переименован. В extra снята
      статистика 2024–2025 годов без опоры в источниках (выручка 69,9 млрд ₽ —
      это 2021 год).

ПОЧЕМУ НЕ review.py: год даты он не переносит (date_is_supported), профили и
вырезание фраз из прозы — не поле карточки по цитате.

Запуск: python3 pipeline/archive/2026-11/reread_oneoff_m047.py [--write]
База перечитывается прямо перед записью; повторный запуск — «уже применено».
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import fact_edit_guard  # noqa: E402

DATA = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')
BY = 'reread m047 (12.11.2026)'
FACT_FIELDS = {'date', 'seller', 'buyer', 'target', 'title', 'sum', 'seller_id', 'buyer_name', 'asset'}

# (вид, id, путь поля, старое, новое, цитата, адрес). Путь — через точку.
# Вид 'deal' — поле карточки, 'co' — поле профиля компании,
# 'mk' — псевдонимы профиля в match_keys (путь — id профиля),
# 'cut' — вырезать подстроку из поля карточки (старое — вырезаемый текст, новое — замена).
OPS = [
 ('deal', 'g94dcc5cc', 'date', '2023-10-30', '2025',
  'Структура «Газпрома» летом 2025 г. приобрела контрольный пакет (51%) отечественного производителя автомобилей класса люкс Aurus.',
  'https://www.vedomosti.ru/auto/articles/2025/11/18/1155718-gazprom-stal-vladeltsem-kontrolnogo-paketa-aurus'),
 ('co', 'g6261c82c', 'desc',
  'В 2023 году выкупил 90% акций научно-производственной фирмы «Микран» за 5–10 млрд ₽ (по оценке), продавец — Владимир Вавилин.',
  'Дочерняя компания «Газпрома», созданная в 2023 году для объединения его активов в авиации, судостроении и автопроме.',
  'пакет был приобретен на « Газпром тех» – дочернюю компанию «Газпрома», учрежденную в 2023 г. для консолидации активов в сфере авиации, судостроения и автопрома.',
  'https://www.vedomosti.ru/auto/articles/2025/11/18/1155718-gazprom-stal-vladeltsem-kontrolnogo-paketa-aurus'),
 ('deal', 'g8f1fab29', 'date', '2023-10-23', '2024',
  'Переход права на долю произошел в апреле 2024 года, но оценка покупки еще может измениться в течение года с момента сделки.',
  'https://www.interfax.ru/world/978748'),
 ('cut', 'ga5b0724c', 'extra', 'управляющий партнер AVG Capital Partners Рустем Миргалимов владеет', 'Рустем Миргалимов владеет', None, None),
 ('cut', 'ga5b0724c', 'extra',
  ' Цены на рис обвалились из-за перепроизводства при запрете экспорта риса-сырца: с 2024 по 2025 год цена снизилась более чем вдвое, выручка «Лебедей» упала с 1,45 до 1,1 млрд ₽, «Лебеди-Агро» устойчиво убыточна.',
  '', None, None),
 ('deal', 'ga5b0724c', 'law.struct',
  'Продана только 51%-я доля, поэтому эксперт считает сделку, вероятно, частично cash in. Деньги могут пойти в том числе на развитие компании, возможно на покупку дополнительных рисовых чеков.',
  '—', None, None),
 ('co', 'g9fbd1431', 'name', 'операционный бизнес и зерновой терминал в Ростове-на-Дону', 'МЗК Экспорт',
  'Владельцем российской "дочки" зернотрейдера Viterra - ООО "МЗК Экспорт" (прежнее название "Витерра Рус") стала компания "Управление агробизнесом", следует из ЕГРЮЛ.',
  'https://www.interfax.ru/business/927099'),
 ('co', 'g9fbd1431', 'legal_short', None, 'ООО «МЗК Экспорт»', None, None),
 ('co', 'g9fbd1431', 'desc',
  'Операционный бизнес и зерновой терминал в Ростове-на-Дону; в 2023 году их выкупил российский менеджмент Viterra.',
  'Зерновой экспортер, бывшая российская дочерняя компания Viterra (прежде МЗК и «Витерра Рус»); торгует зерном в России с 2004 года.',
  None, None),
 ('mk', 'match_keys', 'g9fbd1431', ['операционный бизнес и зерновой терминал в ростове-на-дону'],
  ['мзк экспорт', 'витерра рус'], None, None),
 ('cut', 'g4612b667', 'extra',
  ' В 2024 году компания экспортировала 3,2 млн тонн зерна (5-е место среди российских экспортеров, выручка 69,9 млрд ₽), но в 2025 году резко просела: выручка упала до 1,15 млрд ₽, убыток составил 463,6 млн ₽, и компания выпала из топ-10 экспортеров пшеницы.',
  '', None, None),
 ('deal', 'g94dcc5cc', 'seller', None, 'ФГУП «НАМИ» и «Дедал»',
  'Издание уточняет, что в состав приобретенной доли вошла часть пакета госинститута ФГУП НАМИ (владело 63,5% Aurus), а также пакет, ранее принадлежавший арабском фонду Tawazun (36%), а затем российской компании «Дедал».',
  'https://www.kommersant.ru/doc/8211090'),
 ('deal', 'ga5b0724c', 'buyer', None, 'gbfbb6750',
  'В конце октября по 49% в ООО «Лебеди» и ООО «Лебеди-Агро» получило ООО «Управление агроактивами», еще по 2% — гендиректор и владелец последней Денис Майоров.',
  'https://www.kommersant.ru/doc/6311043'),
 ('deal', 'ga5b0724c', 'buyer_name', 'ООО «Управление агроактивами» (49%) и Денис Майоров (2%)', None,
  'В конце октября по 49% в ООО «Лебеди» и ООО «Лебеди-Агро» получило ООО «Управление агроактивами», еще по 2% — гендиректор и владелец последней Денис Майоров.',
  'https://www.kommersant.ru/doc/6311043'),
 ('deal', 'g8f1fab29', 'accepted_notes', None,
  {'no_profile': {'seller': 'Продавец 30% HWNM в открытых источниках не назван: искали в Коммерсанте, Ведомостях, Интерфаксе (рус. и англ.), AK&M, пресс-релизе «Русала» на rusal.ru, в выдаче по англоязычным изданиям (Reuters/Mining Weekly, DealStreetAsia, Alcircle). Интерфакс называет лишь контролирующего акционера HWNM — Hebei Wenfeng Industrial Group, но не как продавца.'}},
  None, None),
]


def get(obj, path):
    if isinstance(obj, dict) and path in obj:
        return obj[path]
    for p in path.split('.'):
        obj = (obj or {}).get(p)
    return obj


def put(obj, path, value):
    if path.startswith('g') and '.' not in path:
        obj[path] = value
        return
    parts = path.split('.')
    for p in parts[:-1]:
        obj = obj.setdefault(p, {})
    obj[parts[-1]] = value


def main(write=False):
    data = json.load(open(DATA, encoding='utf-8'))      # перечитать прямо перед записью
    deals = {d['id']: d for d in data['deals']}
    cos = data['companies']
    cos = cos if isinstance(cos, dict) else {c['id']: c for c in cos}
    changed = 0
    for kind, cid, path, old, new, quote, url in OPS:
        obj = cos.get(cid) if kind == 'co' else data['match_keys'] if kind == 'mk' else deals.get(cid)
        assert obj is not None, 'нет %s %s' % (kind, cid)
        cur = get(obj, path)
        if kind == 'cut':
            if old not in (cur or ''):
                assert new == '' or new in cur, '%s %s: нет ни старого, ни нового текста' % (cid, path)
                print('уже применено: %s %s (вырезка)' % (cid, path))
                continue
            assert (cur or '').count(old) == 1, '%s %s: вырезаемый текст не один' % (cid, path)
            value = cur.replace(old, new)
        else:
            if cur == new:
                print('уже применено: %s %s' % (cid, path))
                continue
            assert cur == old, '%s %s: в базе %r, ожидали %r' % (cid, path, cur, old)
            value = new
        print('%s %s: %r → %r' % (cid, path, str(cur)[:70], str(value)[:70]))
        changed += 1
        if write:
            put(obj, path, value)
            if kind == 'deal' and path in FACT_FIELDS and quote:
                fact_edit_guard.log(obj, path, value, quote, url, BY)
    if not write:
        print('Сухой прогон: %d правок. Запись — --write.' % changed)
        return
    if changed:
        json.dump(data, open(DATA, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('Записано: %d.' % changed)


if __name__ == '__main__':
    main('--write' in sys.argv)
