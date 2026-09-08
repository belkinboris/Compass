# -*- coding: utf-8 -*-
"""Месячная очередь, 8 сентября 2026 — продолжение системного замера «75
карточек без `status`» (найден в предыдущие часы при дочитывании
Нижфарма/ФЕСКО). Первая же страница очереди в этот час дала СЕМЬ
кандидатов подряд из этого класса; шесть решены здесь, седьмая
(`cfdc0e962`) оставлена без изменений — источник (Vedomosti) закрыт
подпиской, вывода о статусе честно сделать не из чего.

1) `c0b43766f» (продажа «Витязь Авто» на Камчатке) — личный WebFetch
   (kamchatkamedia.ru): «Новым собственником камчатского ООО «Витязь
   Авто»... стала Наталья Барабанова, следует из данных ЕГРЮЛ» — сделка
   зарегистрирована, статус «Закрыта».

2) `caac79625» (Росэлектроника продала «Спецмагнит» Артёму Ченцову) —
   НАЙДЕНА ОШИБКА ВЕЛИЧИНЫ: поле `sum` несло «960,2 млн ₽» — это
   СТАРТОВАЯ цена торгов, а не цена продажи. Личный WebFetch
   (dvizhenie.ru): «Сумма сделки составила 576,1 млн рублей» при
   «стартовой в 960,2 млн рублей» и «минимально допустимой цене в 480,1
   млн рублей». Сумма исправлена на реальную цену продажи, старт и
   минимум сохранены в `eco.val` как контекст. Статус — «Закрыта».

3) `c3bdd7fd4» (Wildberries-Russ получил в залог «Рив Гош») — сам текст
   карточки уже описывает состоявшийся факт («Договоры залога действуют
   с 23 сентября согласно ЕГРЮЛ», партнёрство объявлено 26 сентября) —
   новых источников не потребовалось, статус «Закрыта».

4) `c31a23b22» (SRV Group продала долю в «Жемчужная плаза» Central
   Properties) — собственный текст карточки уже цитирует SRV: «сделка
   заключена 20 декабря 2024 года: 50-процентная доля... перешла
   компании CP Invest Limited» — статус «Закрыта».

5) `c197ac551» (ВЭБ.РФ выделяет ₽25 млрд через «Вертикаль Инвестиции») —
   собственный текст карточки уже подтверждает исполнение: «Первые две
   сделки на 10 миллиардов рублей уже закрыты: инвестиции в Softline и
   холдинг кибербезопасности «Сайберус»» — холдинг создан и начал
   инвестировать, статус «Закрыта».

6) `c25d07929» (Банк «Точка»/ФРИИ создают инвестиционный конвейер) — в
   отличие от предыдущей карточки, здесь НЕТ подтверждения исполнения:
   заголовок источника (Vedomosti) сам звучит как план — «planiruyut-
   investirovat» — статус «Обсуждается».

Поля `status` не проходят вычитку (не прозаические). У `caac79625`
`eco.val` уже нёс дублирующее старое значение суммы («960,2 млн ₽.») —
не в `proofread_absorbed` и не в таблице FIXES (проверено grep'ом),
поэтому заменяется прямой правкой, а не слиянием.

Запуск:
    python3 pipeline/fix_missing_status_batch_sept8_h10.py            # сухой прогон
    python3 pipeline/fix_missing_status_batch_sept8_h10.py --write    # запись
"""
import json
import sys

DATA = 'static/data/deals_promoted.json'

OLD_SUM_SPETSMAGNIT = '960,2 млн ₽'
NEW_SUM_SPETSMAGNIT = '576,1 млн ₽'
OLD_VAL_SPETSMAGNIT = '960,2 млн ₽.'
NEW_VAL_SPETSMAGNIT = (
    'Стартовая цена торгов — 960,2 млн ₽, минимально допустимая — 480,1 '
    'млн ₽; итоговая цена продажи (576,1 млн ₽) сложилась между ними.'
)

STATUS_FIXES = {
    'c0b43766f': 'Закрыта',
    'c3bdd7fd4': 'Закрыта',
    'c31a23b22': 'Закрыта',
    'c197ac551': 'Закрыта',
    'c25d07929': 'Обсуждается',
    'caac79625': 'Закрыта',
}


def main(write=False):
    with open(DATA, encoding='utf-8') as f:
        data = json.load(f)
    by_id = {d['id']: d for d in data['deals']}

    for cid, new_status in STATUS_FIXES.items():
        card = by_id[cid]
        assert card.get('status') is None, \
            '%s: status уже занят: %r' % (cid, card.get('status'))
        print('%s: status None -> %r' % (cid, new_status))

    spec = by_id['caac79625']
    assert spec['sum'] == OLD_SUM_SPETSMAGNIT, \
        'caac79625: sum уже другой: %r' % (spec['sum'],)
    assert spec['eco']['sum'] == OLD_SUM_SPETSMAGNIT, \
        'caac79625: eco.sum уже другой: %r' % (spec['eco']['sum'],)
    assert spec['eco'].get('val') == OLD_VAL_SPETSMAGNIT, \
        'caac79625: eco.val уже другой: %r' % (spec['eco'].get('val'),)
    print('caac79625: sum/eco.sum %r -> %r (была стартовая цена торгов, '
          'не цена продажи)' % (OLD_SUM_SPETSMAGNIT, NEW_SUM_SPETSMAGNIT))
    print('caac79625: eco.val %r -> %r' % (OLD_VAL_SPETSMAGNIT, NEW_VAL_SPETSMAGNIT))

    if not write:
        print('Сухой прогон. Запись — с ключом --write.')
        return

    for cid, new_status in STATUS_FIXES.items():
        by_id[cid]['status'] = new_status

    spec['sum'] = NEW_SUM_SPETSMAGNIT
    spec['eco']['sum'] = NEW_SUM_SPETSMAGNIT
    spec['eco']['val'] = NEW_VAL_SPETSMAGNIT

    with open(DATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print('Записано.')


if __name__ == '__main__':
    main('--write' in sys.argv)
