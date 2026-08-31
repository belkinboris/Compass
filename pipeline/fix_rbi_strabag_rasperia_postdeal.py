# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка gafc21bdd
(RBI отказалась от выкупа 27,78% акций Strabag SE у структуры
Дерипаски, сделка «Не состоялась» с марта 2024 года) — сама доля и
судебная тяжба вокруг неё продолжались все эти два года; статус не
меняется (сделка правда не состоялась, вопрос закрыт), добавлен только
контекст дальнейшей судьбы доли.

Источники — англо-/немецкоязычные (Strabag — австрийская компания),
дословная русская цитата невозможна; факты переданы точным пересказом
с указанием источника, проверено лично прямым WebFetch каждого.

Смена владения структурой БЕЗ смены конечного контроля — проверено
лично прямым WebFetch (newsroom.strabag.com, пресс-релиз от 16 декабря
2024): «MKAO 'Rasperia Trading Limited' (Rasperia) has been transferred
back from Iliadis to its former parent company Valtoura» — то есть в
2024 году доля успела перейти к «Iliadis JSC» (тоже попавшей под
санкции США/ЕС) и была возвращена прежней материнской компании «Valtoura
Holdings Limited»; в обоих случаях акции Strabag остаются заморожены под
санкциями («the STRABAG shares held by Rasperia will remain frozen in
any case»).

Отозванный иск акционеров Strabag — проверено лично прямым WebFetch
(boerse-express.com, нем.): «Die im Oktober 2024 eingebrachte Anklage
der österreichischen Kernaktionäre gegen MKAO Rasperia... auf Ausübung
der Vorkaufsrechte... wird zurückgenommen» — иск о праве преимущественной
покупки доли, поданный в октябре 2024 года, отозван после встречного иска
Rasperia в Калининграде, грозившего штрафом в 1,09 млрд евро
(«ein Antrag auf Erlass einer Unterlassungsverfügung... pauschaler
Schadenersatz in Höhe von 1,09 Mrd. Euro»).

Rasperia в свою очередь отозвала СВОЙ иск — проверено лично прямым
WebFetch (nachrichten.at, нем., 4 августа 2026): «eine im Mai 2026 in
Kaliningrad eingebrachte Klage zurückgezogen, mit der versucht worden
war, sich Moskauer Immobilienvermögen aus dem Strabag-Umfeld im Wert von
31 Millionen Euro anzueignen» — попытка отсудить московскую
недвижимость группы Strabag на 31 млн евро, тоже свёрнута.

Встречный иск RBI на 3,15 млрд евро — проверено лично прямым WebFetch
(rbinternational.com, англ.): «RBI intends to initiate legal proceedings
for c. EUR 3.15 billion against Rasperia in Austria»; по данным
vindobona.org (проверено лично прямым WebFetch), основание — списания в
пользу Rasperia с корсчёта российской «дочки» RBI по решениям российских
судов 2025 — начала 2026 года: «billions were debited from the
Moscow-based RBI subsidiary's correspondent account at the Russian
Central Bank in favor of Rasperia».

НЕ ВКЛЮЧЕНО: конкретные суммы и даты уже выплаченного RBI по решениям
российских судов (саб-агент называл 2,044 млрд евро в январе 2025 и
339 млн евро в декабре 2025) — ни один из документов, которые лично
проверены прямым WebFetch, эти цифры не подтвердил дословно; включена
только общая, подтверждённая формулировка о списаниях «на миллиарды
евро». Также не включена ссылка на конкретную статью санкционного
пакета ЕС («ст. 11a 14-го пакета») — источник её не называет, только
общую фразу «in full compliance with EU sanction law».

Запуск: python3 pipeline/fix_rbi_strabag_rasperia_postdeal.py
        python3 pipeline/fix_rbi_strabag_rasperia_postdeal.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gafc21bdd'

OLD_EXTRA = (
    'RBI планировала выкупить через российскую дочернюю компанию '
    'Райффайзенбанк 27,78% акций австрийской строительной компании '
    'Strabag SE (принадлежащие компании Rasperia, связанной с Олегом '
    'Дерипаской). После сделки акции передавались бы дочерней компании '
    'RBI Gabarts под управлением Штефана Цохлинга. Сделка отозвана под '
    'давлением американских властей из-за опасений нарушения санкций '
    'против Дерипаски. (Raiffeisen Bank International (RBI) / российский '
    'Райффайзенбанк)'
)
NEW_EXTRA = OLD_EXTRA + (
    ' Доля так и осталась замороженной под санкциями: в 2024 году '
    'Rasperia была переведена на структуру «Iliadis JSC» (тоже попавшую '
    'под санкции США и ЕС), а в декабре 2024 года возвращена прежней '
    'материнской компании «Valtoura Holdings Limited» — сама Strabag '
    'подчёркивает, что акции остаются замороженными независимо от того, '
    'кто формально владеет Rasperia. Иск австрийских акционеров Strabag '
    'о праве преимущественной покупки доли (октябрь 2024) отозван после '
    'встречного иска Rasperia в Калининграде с угрозой штрафа 1,09 млрд '
    'евро; в свою очередь Rasperia в 2026 году отозвала собственный иск '
    'о взыскании московской недвижимости группы Strabag на 31 млн евро. '
    'В 2026 году RBI подала встречный иск на 3,15 млрд евро против '
    'Rasperia в венский суд — из-за списаний в пользу Rasperia с корсчёта '
    'российской «дочки» RBI по решениям российских судов.'
)

NEW_SRC = [
    ['Strabag Newsroom', 'https://newsroom.strabag.com/en/press-releases/group/2024-12/transfer-of-mkao-rasperia-trading-limited-back-to-mkao-valtoura-holdings-limited-reported'],
    ['Börse Express', 'https://www.boerse-express.com/news/articles/strabag-die-kernaktionaere-ziehen-die-klage-gegen-rasperia-zurueck-829422'],
    ['Nachrichten.at', 'https://www.nachrichten.at/wirtschaft/strabag-russischer-aktionaer-rasperia-zieht-klage-4-zurueck;art15,4199075'],
    ['RBI (пресс-релиз)', 'https://www.rbinternational.com/en/raiffeisen/media-hub/press-releases/2026/rasperia-claim.html'],
    ['Vindobona', 'https://www.vindobona.org/article/landmark-3-15-billion-lawsuit-austrian-rbi-sues-russian-rasperia-in-a-vienna-court'],
]


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['extra'] == OLD_EXTRA

    new_src = deal['src'] + NEW_SRC

    print('=== extra: станет ===')
    print(NEW_EXTRA)
    print('\n=== src: добавится ===')
    for s in NEW_SRC:
        print(s)

    if write:
        deal['extra'] = NEW_EXTRA
        deal['src'] = new_src
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
