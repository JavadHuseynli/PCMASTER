#!/usr/bin/env python3
"""ClassRoom Manager — Master tətbiqini başladır."""

import sys
import os
import types

_this_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_this_dir)

sys.path.insert(0, _parent_dir)

# Qovluq adı "classroom_manager" deyilsə (məs. "PCMASTER"),
# virtual paket yaradıb sys.modules-a əlavə et — symlink lazım deyil
if os.path.basename(_this_dir) != "classroom_manager":
    _expected = os.path.join(_parent_dir, "classroom_manager")
    if not os.path.exists(_expected):
        pkg = types.ModuleType("classroom_manager")
        pkg.__path__ = [_this_dir]
        pkg.__package__ = "classroom_manager"
        sys.modules["classroom_manager"] = pkg

from classroom_manager.master.main import main

if __name__ == "__main__":
    main()
