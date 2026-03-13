"""
ClassRoom Manager Master - Monitorinq handler.
Screenshot qəbulu və agentlərə yönləndirmə.
"""

import logging

logger = logging.getLogger(__name__)


class MonitorHandler:
    """Screenshot qəbulu və idarəetmə."""

    def __init__(self):
        self._screenshot_callback = None

    def set_callback(self, callback):
        """Screenshot alındıqda çağırılacaq funksiyanı təyin edir."""
        self._screenshot_callback = callback

    def on_screenshot(self, agent_id: str, base64_data: str):
        """Agent-dən screenshot alındıqda."""
        if self._screenshot_callback:
            self._screenshot_callback(agent_id, base64_data)
