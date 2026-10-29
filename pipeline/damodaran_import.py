# -*- coding: utf-8 -*-
"""Мировой ориентир Дамодарана (NYU Stern, развивающиеся рынки) — из его xls в
`static/data/sector_multiples_external.json`: EV/EBIT, EV/EBITDA, EV/Sales, P/B.

    python3 pipeline/damodaran_import.py <папка с vebitdaemerg.xls pbvemerg.xls psemerg.xls> [--write]

Зачем (владелец, 29 октября 2026): «у нас практически ни у одного таргета нет
EBITDA… умножать мультипликаторы из Дамодарана на операционную прибыль — не
так корректно». У Дамодарана есть EV/EBIT — он прикладывается к операционной
прибыли без натяжки; P/B — к капиталу, EV/Sales — к выручке. Берутся столбцы
«Only positive EBITDA firms». Соответствие наших отраслей его секторам — то,
что уже стоит в файле у строк `damodaran_*` (docs/price_estimate_sources.md).
Файлы: https://pages.stern.nyu.edu/~adamodar/pc/datasets/{vebitdaemerg,pbvemerg,psemerg}.xls
"""
import io, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, 'static', 'data', 'sector_multiples_external.json')


def sheet_rows(path):
    import xlrd
    sh = xlrd.open_workbook(path).sheet_by_name('Industry Averages')
    head = next(r for r in range(sh.nrows) if str(sh.cell_value(r, 0)).strip() == 'Industry Name')
    cols = [str(c).strip() for c in sh.row_values(head)]
    out = {}
    for r in range(head + 1, sh.nrows):
        name = str(sh.cell_value(r, 0)).strip()
        if name:
            out[name] = dict(zip(cols, sh.row_values(r)))
    return out, head


def main(folder, write):
    data = json.load(io.open(PATH, encoding='utf-8'))
    source = next(k for k, v in data['sources'].items() if k.startswith('damodaran'))
    year = data['sources'][source].get('year') or 2026
    ev, _ = sheet_rows(os.path.join(folder, 'vebitdaemerg.xls'))
    pb, _ = sheet_rows(os.path.join(folder, 'pbvemerg.xls'))
    ps, _ = sheet_rows(os.path.join(folder, 'psemerg.xls'))
    # у vebitda два блока столбцов с одинаковыми именами; zip оставляет ПОСЛЕДНИЙ
    # («All firms») — берем первый блок явно по позициям
    import xlrd
    sh = xlrd.open_workbook(os.path.join(folder, 'vebitdaemerg.xls')).sheet_by_name('Industry Averages')
    head = next(r for r in range(sh.nrows) if str(sh.cell_value(r, 0)).strip() == 'Industry Name')
    ev = {str(sh.cell_value(r, 0)).strip(): {'EV/EBITDA': sh.cell_value(r, 3), 'EV/EBIT': sh.cell_value(r, 4)}
          for r in range(head + 1, sh.nrows) if str(sh.cell_value(r, 0)).strip()}
    changed = 0
    for ind, rows in data['industries'].items():
        labels = {r['label'] for r in rows if r['source'] == source}
        if not labels:
            continue
        label = sorted(labels)[0]
        want = {}
        if label in ev:
            want['ev_ebitda'] = ev[label]['EV/EBITDA']; want['ev_ebit'] = ev[label]['EV/EBIT']
        if label in pb:
            want['pb'] = pb[label]['PBV']
        if label in ps:
            want['ev_sales'] = ps[label]['EV/Sales']
        for metric, val in want.items():
            try:
                val = round(float(val), 1)
            except (TypeError, ValueError):
                continue
            if val <= 0:
                continue
            row = next((r for r in rows if r['source'] == source and r['metric'] == metric), None)
            if row is None:
                rows.append({'metric': metric, 'value': val, 'year': year, 'source': source, 'label': label}); changed += 1
            elif row['value'] != val:
                row['value'] = val; row['year'] = year; changed += 1
        missing = [l for l in labels if l not in ev]
        if missing:
            print('нет в xls:', ind, missing)
    print('строк добавлено или обновлено:', changed)
    if write:
        json.dump(data, io.open(PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('записано')


if __name__ == '__main__':
    main(sys.argv[1], '--write' in sys.argv)
