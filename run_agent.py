#!/usr/bin/env python3
"""ClassRoom Manager — Agent tətbiqini başladır."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classroom_manager.agent.main import main

if __name__ == "__main__":
    main()
