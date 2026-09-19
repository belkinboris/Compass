# -*- coding: utf-8 -*-
"""Качество, 19 сентября 2026 (ежедневный прогон 21:37 МСК) — все три уровня
очереди дочитывания снова измерены (по site_visible-карточкам) и снова
пусты, продолжение пункта G8 из бэклога («Собственники компании на её
странице»). Три закрытые сделки, факт — о структуре ПОКУПАТЕЛЯ после
сделки, проверка независимым чтением источников (саб-агент). Четвёртый
кандидат этого же захода (Vizant/Аркадий Ротенберг, `g016f1b13`) НЕ
подтвердился — см. новую запись в CLAUDE.md, «Известные проблемы»: ни один
из источников САМОЙ карточки не называет ни ЗПИФ «Терс», ни Ротенберга.

1) `g30bc92fd` (ООО «Гермес», прямой покупатель сети гипермаркетов OBI,
   позже актив перешёл к «Ленте»/«Севергрупп») — карточка `gcdd2b6de` уже
   называла бенефициара в прозе. Саб-агент подтвердил дословно СРАЗУ тремя
   источниками: oborot.ru (16.06.2025) — «Владельцем и гендиректором фирмы
   является Владимир Захватошин»; sostav.ru (14.07.2025) — «Владелец и
   гендиректор компании — Владимир Захватошин»; realnoevremya.ru
   (11.06.2025) — «Бенефициаром ООО «Гермес» является предприниматель
   Владимир Захватошин».

2) `g2fbd1d7c` (Холдинг «Империя», покупатель отеля «Талион Империал» в
   Санкт-Петербурге через торги) — карточка `geb8edd5c» уже называла
   бенефициара в law.struct. Саб-агент подтвердил дословно по «Википедии»:
   «холдинг Андрея Фоменко «Империя»» — прямое указание, что холдинг
   принадлежит/основан Фоменко (не привязано к конкретной сделке). Нюанс,
   который саб-агент нашёл и который стоит помнить: ЮРИДИЧЕСКИМ
   покупателем на торгах выступила связанная с «Империей» компания «Лига»
   (Ведомости, Фонтанка), а не сам холдинг напрямую, — факт пишется на
   профиль ХОЛДИНГА (как и назван в карточке), а не на гипотетический
   профиль «Лиги», которого в базе нет.

3) `g21fac69d` (Инвестиционная группа «Инсайт», покупатель бизнес-центра
   «Легион II» у Siemens) — карточка `g8fb922a6» уже называла бенефициара
   в extra. Саб-агент подтвердил по versia.ru (06.09.2022, до сделки):
   «Генеральный директор и основатель инвестиционной группы «Инсайт» Авет
   Миракян» — и отдельно связку с SFI/Гуцериевым тем же источником. Дата
   факта — по versia.ru (сентябрь 2022, момент основания «Инсайта»), а не
   по дате самой сделки (апрель 2023): карточка сама говорит, что в июле
   2024 года Миракян продал свою долю — ownership здесь снимок на момент
   создания структуры и самой сделки, не текущее состояние (интерфейс это
   уже подписывает: «доли и состав показаны на дату источника»).

Запуск:
    python3 pipeline/fix_g8_ownership_germes_imperia_insight.py            # сухой прогон
    python3 pipeline/fix_g8_ownership_germes_imperia_insight.py --write    # запись
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__)).rsplit('/pipeline', 1)[0]
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

REALNOEVREMYA_GERMES = ['realnoevremya.ru', 'https://realnoevremya.ru/news/338081-fas-odobrila-prodazhu-seti-gipermarketov-obi-kompanii-germes']
WIKI_FOMENKO = ['Википедия', 'https://ru.wikipedia.org/wiki/Фоменко,_Андрей_Николаевич']
VERSIA_INSIGHT = ['Versia.ru', 'https://versia.ru/avet-mirakyan-vyshel-iz-sovetov-direktorov-gruppy-m-video-yeldorado-i-investicionnogo-xoldinga-sfi']

OWNERSHIP = {
    'g30bc92fd': [
        dict(name='Владимир Захватошин', id=None, share=None,
             as_of='2025-06', source=REALNOEVREMYA_GERMES),
    ],
    'g2fbd1d7c': [
        dict(name='Андрей Фоменко', id=None, share=None,
             as_of='2025-09', source=WIKI_FOMENKO),
    ],
    'g21fac69d': [
        dict(name='Авет Миракян', id=None, share=None,
             as_of='2022-09', source=VERSIA_INSIGHT),
    ],
}


def main(write=False):
    data = json.load(open(PATH, encoding='utf-8'))
    companies = data['companies']

    for cid, ownership in OWNERSHIP.items():
        assert cid in companies, f"нет профиля {cid}"
        assert not companies[cid].get('ownership'), f"{cid} уже несёт ownership: {companies[cid].get('ownership')!r}"
        print(f"{cid} ({companies[cid]['name']}): += ownership")
        for o in ownership:
            print(f"    {o['name']} — {o.get('share') or '(доля не названа)'} (на {o['as_of']})")
        companies[cid]['ownership'] = ownership

    if write:
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("ЗАПИСАНО")
    else:
        print("Сухой прогон. Запись — с --write.")


if __name__ == '__main__':
    import sys
    main(write='--write' in sys.argv)
