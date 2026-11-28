"""Снять правки карточки g121443b6 из общих партий FIXES (карточка снята, `test_ingest` требует, чтобы
правок снятой карточки не оставалось). Вырезаются только словари с 'id': 'g121443b6' из списка FIXES;
остальные записи и комментарии партии не трогаются."""
import ast, sys, os
ID = 'g121443b6'
FILES = ['written_2026_11_27_vm.py', 'accept_g46_2026_11_27.py', 'g46new_2026_11_27_vsk.py']
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'ingest', 'fixes')
for name in FILES:
    path = os.path.join(D, name)
    src = open(path, encoding='utf-8').read()
    lines = src.split('\n')
    tree = ast.parse(src)
    spans, total = [], 0
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', '') == 'FIXES' and isinstance(node.value, ast.List):
            for el in node.value.elts:
                total += 1
                if isinstance(el, ast.Dict):
                    for k, v in zip(el.keys, el.values):
                        if isinstance(k, ast.Constant) and k.value == 'id' and isinstance(v, ast.Constant) and v.value == ID:
                            spans.append((el.lineno, el.end_lineno, el.col_offset, el.end_col_offset))
    print(name, 'записей', total, 'вырезать', len(spans))
    if '--write' not in sys.argv or not spans:
        continue
    if len(spans) == total:
        os.remove(path); print('  файл удален'); continue
    for (a, b, c0, c1) in sorted(spans, reverse=True):
        before = lines[a - 1][:c0]
        after = lines[b - 1][c1:]
        rest = (before + after).strip().lstrip(',').strip() if False else None
        lines[a - 1:b] = [before + after.lstrip(', ').rstrip() if (before.strip() or after.strip(' ,')) else '__DEL__']
    out = '\n'.join(l for l in lines if l != '__DEL__')
    ast.parse(out)
    open(path, 'w', encoding='utf-8').write(out)
    print('  записано')
