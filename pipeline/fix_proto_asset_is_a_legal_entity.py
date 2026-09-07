# -*- coding: utf-8 -*-
"""Предмет сделки «Базис»/Proto назван брендом, а юрлицо стоит в других полях.

Что чинит. У карточки `g95370469` («Базис» купил 70% компании Proto,
очередь предпросмотра) `asset` = «Proto» — бренд. При этом сама карточка
дважды называет реальное юрлицо: в «Финансах предмета» («доходы ООО
«ПротоСервисез» по итогам 2025 г. ...») и в «Структуре сделки» («ООО
«ПротоСервисез» войдет в группу «Базис» как дочерняя»). Это ровно правило
«имя профиля — это компания, а не предмет сделки»: читатель видит бренд
там, где мы уже знаем юрлицо.

Откуда взялось. Замечание партнёра в консоли 7 сентября 2026: «в карточке
в показателях актива есть информация, что это ООО «Протосервисез» —
почему этого нет в предмете? Так как это ООО, можно в выписке увидеть
собственника и сказать, кто продавец».

Вторая половина замечания — про продавца — снята чтением источника, а не
выпиской. CNews (уже стоит в `src` карточки) пишет прямо: «Сделка
реализована путем внесения в капитал Proto денежных средств». Это вклад в
капитал (cash-in): деньги идут самой компании, доля возникает из
допэмиссии, продающего участника в такой сделке нет вовсе — и «Продавец не
раскрыт» здесь было бы не честной пустотой, а несуществующей ролью
(см. CLAUDE.md, урок про ПСБ/«Атом»). Поэтому `type` остаётся
«Инвестиция», а не M&A, и `seller` не заполняется. Прежние участники
названы в источнике и добавлены в «Структуру сделки» — они размылись,
а не продали.

Отдельно про «Структуру сделки»: это поле ставила таблица `FIXES`
(дочитывание притока тем же утром), и переписанное руками оно перестаёт
совпадать с записью таблицы посимвольно — `test_review_table_is_applied_
and_not_pending` из-за этого краснеет. По правилу репозитория такая правка
обязана дописать в карточку ОТПЕЧАТОК прежнего значения
(`review.fix_fingerprint` → `proofread_absorbed`): запись таблицы остаётся
применённой, а поле живёт дальше своей жизнью. Тот же приём, что у вычитки.

Запуск: python3 pipeline/fix_proto_asset_is_a_legal_entity.py [--write]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'ingest'))
import review  # noqa: E402  (pipeline/ingest в sys.path)

PENDING = Path(__file__).resolve().parent.parent / 'static' / 'data' / 'pending.json'
DEAL_ID = 'g95370469'
OLD_ASSET = 'Proto'
NEW_ASSET = 'ООО «ПротоСервисез» (бренд Proto)'
OLD_STRUCT = ('ООО «ПротоСервисез» войдет в группу «Базис» как дочерняя, а ее '
              'финансовые результаты будут учитываться в отчетности группы.')
NEW_STRUCT = (
    'Доля получена вкладом в капитал: сделка реализована путём внесения в капитал '
    'Proto денежных средств, то есть 70% возникли у «Базиса» из допэмиссии, а не '
    'выкуплены у прежних участников — продающей стороны в такой сделке нет. '
    'На момент сообщения о сделке уставный капитал ООО «ПротоСервисез» (25 тыс. ₽) '
    'был поровну разделён между Надеждой Фердман и Денисом Безкоровайным. '
    + OLD_STRUCT)


def main(write: bool) -> None:
    data = json.loads(PENDING.read_text(encoding='utf-8'))
    cards = {c['id']: c for c in data['cards']}
    card = cards[DEAL_ID]
    if card.get('asset') not in (OLD_ASSET, NEW_ASSET):
        raise AssertionError(f"предмет уже другой: {card.get('asset')!r}")
    if (card.get('law') or {}).get('struct') == NEW_STRUCT:
        print('уже применено — скрипт идемпотентен')
        # отпечаток мог не лечь при прошлом прогоне; дописываем и выходим
        absorbed = card.setdefault('proofread_absorbed', {}).setdefault('law.struct', [])
        stamp = review.fix_fingerprint(OLD_STRUCT)
        if stamp in absorbed:
            return
        if write:
            absorbed.append(stamp)
            PENDING.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
            print('Отпечаток прежнего значения дописан.')
        else:
            print('Не хватает отпечатка прежнего значения. Запись — с ключом --write.')
        return
    assert (card.get('law') or {}).get('struct') == OLD_STRUCT, 'структура сделки уже другая'
    assert not card.get('seller') and not card.get('seller_id'), 'продавец уже записан — разберитесь руками'
    assert card.get('type') == 'Инвестиция', 'тип сделки изменился — вклад в капитал больше не подтверждается'
    # Юрлицо не выдумано: оно дословно стоит в двух полях самой карточки.
    for field in ((card.get('eco') or {}).get('target_fin'), OLD_STRUCT):
        assert 'ПротоСервисез' in (field or ''), 'юрлица нет в тексте карточки — основание правки пропало'
    print(f"{DEAL_ID}")
    print(f"  asset       {OLD_ASSET!r} → {NEW_ASSET!r}")
    print(f"  law.struct  +вклад в капитал и прежние участники (было {len(OLD_STRUCT)} знаков, стало {len(NEW_STRUCT)})")
    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return
    card['asset'] = NEW_ASSET
    card['law']['struct'] = NEW_STRUCT
    absorbed = card.setdefault('proofread_absorbed', {}).setdefault('law.struct', [])
    stamp = review.fix_fingerprint(OLD_STRUCT)
    if stamp not in absorbed:
        absorbed.append(stamp)
    PENDING.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
