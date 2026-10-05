"""The public edition has no Discord bot at all. This stub only keeps the main window's calls working."""
from __future__ import annotations


class BotsTabMixin:
    def _init_bot(self):
        pass

    def _bot_autostart(self):
        pass

    def _bot_on_change(self):
        pass

    def _bot_theme_changed(self):
        pass

    def _bot_close(self):
        pass

    def handle_bot_event(self, ev: dict) -> bool:
        return str(ev.get("type", "")).startswith("bot_")
