#!/usr/bin/env python3
"""ClassRoom Manager — Master tətbiqini başladır."""

import sys
import os

_this_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_this_dir)

sys.path.insert(0, _parent_dir)

_expected = os.path.join(_parent_dir, "classroom_manager")
if not os.path.exists(_expected) and os.path.basename(_this_dir) != "classroom_manager":
    try:
        os.symlink(_this_dir, _expected)
    except (OSError, FileExistsError):
        pass

from classroom_manager.master.main import main

if __name__ == "__main__":
    main()
