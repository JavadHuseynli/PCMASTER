#!/usr/bin/env python3
"""ClassRoom Manager — Master tətbiqini başladır."""

import sys
import os

# Layihə kök qovluğunu path-ə əlavə et
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classroom_manager.master.main import main

if __name__ == "__main__":
    main()
