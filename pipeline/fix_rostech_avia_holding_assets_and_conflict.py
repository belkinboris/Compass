# -*- coding: utf-8 -*-
"""Месячная очередь (REVISION_BRIEF, третий уровень), карточка
`gmru-rostech-avia-holding` («Ростех» консолидирует авиатранспортные
активы в новом холдинге, Обсуждается, 20 июля 2026) — не был назван сам
состав объединяемых активов, и не была раскрыта вторая причина
консолидации (внутренний конфликт менеджмента, а не только финансы).

Проверено ЛИЧНО прямым WebFetch:
- kommersant.ru/doc/8830172 (уже в `src`, повторно прочитан целиком): в
  холдинг войдут «Red Wings (пассажирская авиакомпания)», «SkyGates
  (грузовая авиакомпания)», «Национальная служба санитарной авиации»,
  ««Авиакапитал-Сервис» (лизинговая компания)»; управляющая компания —
  ИФК («Ильюшин Финанс Ко») — это уже отражено в `law.struct`, состав
  активов — нет.
- rb.ru/news/aviakompanii-red-wings-i-skygates-obedinyat-v-edinyj-
  holding-rosteh-nachal-uporyadochivat-svoi-aktivy/: источники называют
  «ухудшение финансовых результатов Red Wings в I половине 2026 года и
  внутренние конфликты в менеджменте»; «из-за разногласий между
  топ-менеджерами совет директоров до сих пор не утвердил заместителей
  гендиректора»; «чистая прибыль Red Wings за 2025 год снизилась на 9%
  — до 2,3 млрд рублей» (по данным Rusprofile).

НЕ ВНЕСЕНО: деталь «из трёх Boeing только один летает регулярно»
(finance.mail.ru) — при повторной проверке цитата отдавалась
пересказом, а не гарантированно дословным текстом; вносить без точной
цитаты нельзя.

Прогресса к закрытию/оформлению холдинга к сентябрю 2026 года не
найдено ни в одном источнике — `status`/`buyer`/`seller`/`target`
карточки НЕ тронуты: состав сторон у консолидации внутри госкорпорации
неоднозначен (нет классических продавца/покупателя), решение об этом —
за человеком/притоком.

Запуск: python3 pipeline/fix_rostech_avia_holding_assets_and_conflict.py
        python3 pipeline/fix_rostech_avia_holding_assets_and_conflict.py --write
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'deals_promoted.json')

DEAL_ID = 'gmru-rostech-avia-holding'

OLD_ECO_SHARE = '—'
NEW_ECO_SHARE = (
    'В холдинг войдут пассажирская авиакомпания Red Wings, грузовая '
    'авиакомпания SkyGates, Национальная служба санитарной авиации и '
    'лизинговая компания «Авиакапитал-Сервис».'
)

OLD_ECO_CONTEXT = (
    'Главная претензия «Ростеха» к перевозчику, по неофициальным '
    'данным, — существенное ухудшение финансового результата в первой '
    'половине 2026 года; конкретные показатели не раскрывались. В Red '
    'Wings снижение показателей подтвердили, но объяснили его '
    'пересмотром чартерной программы на самолётах Boeing 777: '
    'эксплуатацию этих машин хотят продлить до поступления новых '
    'лайнеров и расширения парка.'
)
NEW_ECO_CONTEXT = (
    OLD_ECO_CONTEXT + ' Источники называют и вторую причину —'
    ' внутренние конфликты в менеджменте: из-за разногласий между '
    'топ-менеджерами совет директоров до сих пор не утвердил '
    'заместителей гендиректора. По данным Rusprofile, чистая прибыль '
    'Red Wings за весь 2025 год снизилась на 9%, до 2,3 млрд ₽.'
)


def main(write=False):
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    deal = next(d for d in data['deals'] if d['id'] == DEAL_ID)

    assert deal['eco']['share'] == OLD_ECO_SHARE
    assert deal['eco']['context'] == OLD_ECO_CONTEXT

    print('=== eco.share: станет ===')
    print(NEW_ECO_SHARE)
    print('\n=== eco.context: станет ===')
    print(NEW_ECO_CONTEXT)

    if write:
        deal['eco']['share'] = NEW_ECO_SHARE
        deal['eco']['context'] = NEW_ECO_CONTEXT
        with open(PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print('\nЗаписано.')
    else:
        print('\nСухой прогон — ничего не записано. Запустите с --write.')


if __name__ == '__main__':
    main(write='--write' in sys.argv)
