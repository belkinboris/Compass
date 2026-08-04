# -*- coding: utf-8 -*-
"""40 из 41 оставшейся карточки с «голым доменом» вместо ссылки на статью.

ЧТО СЛОМАНО. Тот же класс дефекта, что уже чинил `fix_broken_source_links.py`
(10 карточек, прогон 1 августа): первый источник — не ссылка на статью, а
домен без пути (`http://Price.ru/`, `http://ВЭБ.РФ/`, `http://Mail.ru/` и
т. п.), похожий на компанию из текста самой карточки, а не на реальный
адрес. Открыв такую ссылку, читатель не находит ни слова о сделке. Список
41 оставшейся карточки был записан в `PRODUCT_ROADMAP.md`/CLAUDE.md как
неразобранный («отдельная сессия, не на один присест»).

ЧТО СДЕЛАНО. 40 из 41 карточки проверены живым поиском (WebSearch), для
каждой найдена статья, которая описывает ИМЕННО эту сделку, а не просто
компанию упомянутую в заголовке — факты (стороны, предмет, сумма, период)
сверены с уже записанными в карточке. Одна карточка (`ge760cc08`, «Malina VC
инвестировал в Агредатор») осталась непочиненной: несколько разных запросов
нашли только те же формулировки, что уже в самой карточке, ни одной
независимой статьи с адресом — оставлена как есть, честнее не гадать.

КАК ПРИМЕНЯЕТСЯ. В отличие от `fix_broken_source_links.py` (который менял
только URL, а подпись поручал последующему прогону `relabel_dealsma_sources.py`
по всей базе), здесь подпись меняется СРАЗУ в этом же скрипте — через ту же
таблицу `DOMAIN_NAMES` и ту же функцию `display_name()`, импортированные из
`relabel_dealsma_sources.py`, а не скопированные заново. Так подпись сразу
называет издание, а не «@dealsma (Telegram)» ещё на один прогон дольше;
`relabel_dealsma_sources.py` устроен так, что «голые» домены он сам
принципиально пропускает (`is_bare()`), поэтому конфликта между скриптами
нет — каждый чинит свою часть, и повторный прогон relabel эти записи не
заденет (label уже не будет содержать «dealsma»/«Telegram»).

Запуск:
    python3 pipeline/fix_bare_domain_sources_batch2.py            # сухой прогон
    python3 pipeline/fix_bare_domain_sources_batch2.py --write    # записать
"""
import json
import os
import sys
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from relabel_dealsma_sources import display_name  # noqa: E402

PATH = 'static/data/deals_promoted.json'

# id -> (старый URL, новый URL). Источник найден и проверен по фактам
# карточки живым поиском (WebSearch), издание в новой подписи определяется
# по домену новой ссылки — так же, как во всей остальной базе.
URL_FIXES = {
    'g68ebf773': ('http://vseinstrumenti.ru/', 'https://www.cnews.ru/news/top/2024-07-09_neizvestnyj_vladelets_giganta'),
    'g8a66f3c7': ('http://%D0%B4%D0%BE%D0%BC%D0%B5%D0%BD%D0%B5.ru/', 'https://www.comnews.ru/content/231550/2024-02-14/2024-w07/1010/regru-prinyal-obsluzhivanie-klientov-reddock'),
    'gf9932079': ('http://%D0%92%D0%AD%D0%91.%D0%A0%D0%A4/', 'https://www.kommersant.ru/doc/8009248'),
    'g577a83e0': ('http://%D0%90%D0%BF%D1%82%D0%B5%D0%BA%D0%B025.%D1%80%D1%84/', 'https://vademec.ru/news/2025/09/15/rigla-priobrela-vse-tochki-seti-apteka25-rf-iz-vladivostoka/'),
    'g4fc7af86': ('https://forwardlegal.com/', 'https://www.sostav.ru/publication/fas-odobrila-pokupku-ipsos-komkon-rossijskim-investorom-80996.html'),
    'gd3ba954d': ('http://%D0%92%D0%AD%D0%91.%D0%A0%D0%A4/', 'https://www.vedomosti.ru/media/articles/2025/03/17/1098299-veb-poluchil-dolyu-sbera-v-gruppe-kompanii-prosveschenie'),
    'g5b8fa758': ('http://Booking.com/', 'https://www.kommersant.ru/doc/8692225'),
    'gc7e0b5c9': ('http://Tutu.ru/', 'https://www.sostav.ru/publication/tutu-ru-kupil-domen-travel-ru-79706.html'),
    'g321bdead': ('http://%D0%9D%D0%B0%D1%88.%D0%94%D0%BE%D0%BC.%D0%A0%D0%A4/', 'https://mergers.ru/news/Jetalon-priobretaet-Biznes-Nedvizhimost-u-AFK-Sistema-za-14-1-mlrd-rublej-85793'),
    'g7ccf80f9': ('http://Mail.ru/', 'https://www.sostav.ru/publication/avito-kupil-reklamnye-servisy-adriver-i-soloway-72080.html'),
    'gbd5ad233': ('http://Sostav.ru/', 'https://www.sostav.ru/publication/sovladelets-kokoc-group-kupil-players-team-70860.html'),
    'g4a751f95': ('http://Price.ru/', 'https://www.kommersant.ru/doc/7198627'),
    'g4b447867': ('http://%D0%A1%D0%BE%D1%86%D0%B8%D0%B0%D0%BB%D0%BE%D1%87%D0%BA%D0%B0.%D1%80%D1%84/', 'https://www.kommersant.ru/doc/6836700'),
    'g39218eec': ('http://%D0%92%D0%AD%D0%91.%D0%A0%D0%A4/', 'https://www.kommersant.ru/doc/6727734'),
    'g807a5625': ('http://Intickets.ru/', 'https://www.kommersant.ru/doc/6686581'),
    'gc0ba024d': ('http://Telega.in/', 'https://www.kommersant.ru/doc/6835929'),
    'ga1152200': ('http://Mail.ru/', 'https://realty.ria.ru/20230417/vk-1865738053.html'),
    'g25db4ede': ('http://%D0%92%D0%AD%D0%91.%D0%A0%D0%A4/', 'https://www.cnews.ru/news/line/2025-11-01_ivideon_vykupil_dolyu_sk_capitalzavershiv'),
    'ga6924cc4': ('http://hh.ru/', 'https://www.vedomosti.ru/technologies/industries_and_markets/news/2025/10/09/1145756-headhunter-investiroval-v-moya-smena'),
    'g8ea6e559': ('http://%D0%92%D0%AD%D0%91.%D0%A0%D0%A4/', 'https://incrussia.ru/news/sk-capital-kupila-10-aktsij-softline-za-5-mlrd-rub/'),
    'g37737226': ('http://servers.ru/', 'https://www.rbc.ru/rbcfreenews/675fd25f9a7947b26cbfc66d'),
    'g96674c34': ('http://RB.RU/', 'https://frankmedia.ru/177816'),
    'g1e2b16c3': ('http://Price.ru/', 'https://www.rbc.ru/business/20/12/2023/6582a8d99a79470c6a2afa49'),
    'g19186bb9': ('http://T.one/', 'https://www.interfax.ru/business/933988'),
    'ga3afca6c': ('http://Kassir.ru/', 'https://www.rbc.ru/rbcfreenews/64d263059a7947180e74880b'),
    'g5809b7a2': ('http://%D0%BF%D0%BE%D0%BB%D0%B5.%D1%80%D1%84/', 'https://www.agroinvestor.ru/transaction/news/40928-demetra-kholding-priobrel-elevatory-v-ulyanovskoy-i-volgogradskoy-oblastyakh/'),
    'ged59a2eb': ('http://%D0%BF%D0%BE%D0%BB%D0%B5.%D1%80%D1%84/', 'https://www.kommersant.ru/doc/6096656'),
    'g78e14953': ('http://Price.ru/', 'https://lenta.ru/news/2023/06/05/shiny/'),
    'ga3ca0cde': ('http://%D0%92%D0%AD%D0%91.%D0%A0%D0%A4/', 'https://www.interfax.ru/business/894526'),
    'g2d075f03': ('http://Sravni.ru/', 'https://www.rbc.ru/finances/15/03/2023/640f5e929a794736319671f3'),
    'ga133cd89': ('http://INTICKETS.RU/', 'https://www.kommersant.ru/doc/6365658'),
    'gc3a6085a': ('http://Price.ru/', 'https://www.kommersant.ru/doc/6296459'),
    'g7d996243': ('http://Nebo.digital/', 'https://adpass.ru/russ-nakleil-poster-krupnejshij-rossijskij-operator-naruzhnoj-reklamy-kupil-chetvertogo/'),
    'gc6322659': ('http://Mail.ru/', 'https://www.interfax.ru/business/917057'),
    'g38ce6e22': ('http://%D0%BF%D0%BE%D0%BB%D0%B5.%D1%80%D1%84/', 'https://www.kommersant.ru/doc/6149973'),
    'ga7232033': ('http://%D0%BF%D0%BE%D0%BB%D0%B5.%D1%80%D1%84/', 'https://www.agroinvestor.ru/companies/news/40448-vtb-prodast-svoyu-dolyu-v-demetra-kholding/'),
    'gc4c76129': ('http://2be.lu/', 'https://www.kommersant.ru/doc/5861955'),
    'gafda8e29': ('http://Price.ru/', 'https://www.kommersant.ru/doc/5965150'),
    'g5cb74803': ('http://Mail.ru/', 'https://www.interfax.ru/business/886936'),
    'g688aa290': ('http://4tochki.ru/', 'https://www.interfax.ru/business/903364'),
}

# Проверена, но НЕ починена — независимого источника не нашлось (см. docstring).
NOT_FOUND = ['ge760cc08']


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    changes = []
    for did, (old_url, new_url) in URL_FIXES.items():
        d = by_id[did]
        src = d.get('src') or []
        idx = next((i for i, s in enumerate(src) if len(s) > 1 and s[1] == old_url), None)
        assert idx is not None, f'{did}: старый URL не найден в src — {old_url!r}'
        domain = urlparse(new_url).netloc.replace('www.', '')
        new_label = display_name(domain)
        changes.append((did, old_url, new_url, new_label))
        if write:
            src[idx] = [new_label, new_url]

    assert len(changes) == 40, f'ожидали 40 починок, собрали {len(changes)}'

    print(f'правок: {len(changes)}, не тронуто (источник не найден): {len(NOT_FOUND)} — {NOT_FOUND}')
    for did, old, new, label in changes:
        print(f'  {did}: {old[:60]!r} -> {label} / {new}')

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
        print('\nЗАПИСАНО в', PATH)
    return 0


if __name__ == '__main__':
    sys.exit(main(write='--write' in sys.argv))
