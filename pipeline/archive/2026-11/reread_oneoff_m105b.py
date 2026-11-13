# -*- coding: utf-8 -*-
"""Вычитка 13 ноября 2026, партия m105, вторая часть: бизнес-центр Comcity (g560a4b70).

Доказательства и тексты — в докстроке и таблицах `reread_oneoff_m105.py` (первая часть: стороны по реестру,
профили и записи реестра ФНС). Здесь применяется только Comcity: mass_edit_guard пускает не больше десяти
опубликованных карточек за один скрипт. Ведомости, 16.12.2022: «в середине октября новым владельцем фирмы Comcity
Office B.V. … стала инвесткомпания Inventa» — дата годом; 25–27 млрд ₽ — оценка Николая Горюнова (IBC Real Estate),
не цена; РИА Недвижимость (аренда Совкомбанка, 2025) — не о сделке.

    python3 pipeline/archive/2026-11/reread_oneoff_m105b.py [--write]
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('reread_oneoff_m105', os.path.join(HERE, 'reread_oneoff_m105.py'))
part = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(part)
part.PART.update(first=False, cards={part.COMCITY})
part.BY = 'reread_oneoff_m105b'

def main(write):
    code = part.main(write)
    if write and not code:
        # Comcity: исправлено старое нарушение правил текста (издание в скобках) — список известных только
        # сокращается (text_rules.py --rebaseline нового не добавляет).
        import subprocess
        root = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
        subprocess.run([sys.executable, os.path.join(root, 'pipeline', 'text_rules.py'), '--rebaseline'],
                       cwd=root, check=True)
    return code


if __name__ == '__main__':
    sys.exit(main('--write' in sys.argv))
