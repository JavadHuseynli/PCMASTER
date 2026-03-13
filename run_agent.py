#!/usr/bin/env python3
"""ClassRoom Manager — Agent tətbiqini başladır."""

import sys
import os

# Bu skriptin olduğu qovluğu "classroom_manager" paketi kimi tanıt
_this_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_this_dir)

# Üst qovluqda "classroom_manager" qovluğu varsa — normal struktur
# Yoxdursa — repo birbaşa klonlanıb, qovluq adını simvolik əlaqə ilə həll et
sys.path.insert(0, _parent_dir)

# Əgər üst qovluqda classroom_manager yoxdursa, yaradaq
_expected = os.path.join(_parent_dir, "classroom_manager")
if not os.path.exists(_expected) and os.path.basename(_this_dir) != "classroom_manager":
    # Symlink yarat: parent/classroom_manager -> bu qovluq
    try:
        os.symlink(_this_dir, _expected)
    except (OSError, FileExistsError):
        pass

from classroom_manager.agent.main import main

if __name__ == "__main__":
    main()
