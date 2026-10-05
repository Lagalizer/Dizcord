"""'Manual' tab: the user manual, chapter by chapter, read aloud by the voice built into Windows (no AI, offline).

Moving to another chapter - with Next / Previous or by clicking the list - cuts the voice that was reading the
old chapter, shows the new chapter and starts reading it. The narrator is silent whenever the tab is not visible."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QHBoxLayout, QLabel, QListWidget, QPushButton, QSlider, QTextBrowser,
                               QVBoxLayout, QWidget)

from .. import config
from ..manual import CHAPTERS, speakable
from ..sapi import Narrator
from .widgets import DataCombo


class ManualTabMixin:
    """Mixed into MainWindow. Needs: tabs, state, setStatus."""

    # ------------------------------------------------------------------ build
    def _build_manual_tab(self) -> QWidget:
        saved = self.state.get("manual") or {}
        self._narrator: Narrator | None = None            # created the first time it is needed (loads COM)
        self._manual_index = 0
        w = QWidget()
        root = QHBoxLayout(w)

        self.manual_list = QListWidget()
        self.manual_list.setFixedWidth(250)
        for ch in CHAPTERS:
            self.manual_list.addItem(ch.title)
        root.addWidget(self.manual_list)

        right = QVBoxLayout()
        self.manual_view = QTextBrowser()
        self.manual_view.setOpenExternalLinks(True)
        right.addWidget(self.manual_view, 1)

        nav = QHBoxLayout()
        self.manual_prev = QPushButton("◀ Previous")
        self.manual_prev.setToolTip("Previous chapter - the voice stops the current one and reads that one")
        self.manual_next = QPushButton("Next ▶")
        self.manual_next.setObjectName("primary")
        self.manual_next.setToolTip("Next chapter - the voice stops the current one and reads that one")
        self.manual_pos = QLabel()
        nav.addWidget(self.manual_prev)
        nav.addWidget(self.manual_next)
        nav.addWidget(self.manual_pos)
        nav.addStretch(1)
        right.addLayout(nav)

        voice = QHBoxLayout()
        self.manual_speak = QCheckBox("🔊 Read aloud")
        self.manual_speak.setChecked(bool(saved.get("speak", True)))
        again = QPushButton("🔁 Read again")
        stop = QPushButton("⏹ Stop")
        self.manual_voice = DataCombo([])
        self.manual_voice.setMinimumWidth(260)
        self.manual_speed = QSlider(Qt.Horizontal)
        self.manual_speed.setRange(-6, 6)
        self.manual_speed.setValue(int(saved.get("rate", 0)))
        self.manual_speed.setFixedWidth(110)
        self.manual_speed.setToolTip("Speed of the voice")
        voice.addWidget(self.manual_speak)
        voice.addWidget(again)
        voice.addWidget(stop)
        voice.addSpacing(12)
        voice.addWidget(QLabel("Voice"))
        voice.addWidget(self.manual_voice, 1)
        voice.addWidget(QLabel("Speed"))
        voice.addWidget(self.manual_speed)
        right.addLayout(voice)
        self.manual_note = QLabel("")
        self.manual_note.setWordWrap(True)
        self.manual_note.setObjectName("muted")
        right.addWidget(self.manual_note)
        root.addLayout(right, 1)

        self.manual_list.currentRowChanged.connect(lambda i: i >= 0 and self._manual_goto(i))
        self.manual_prev.clicked.connect(lambda: self._manual_goto(self._manual_index - 1))
        self.manual_next.clicked.connect(lambda: self._manual_goto(self._manual_index + 1))
        again.clicked.connect(lambda: self._manual_read())
        stop.clicked.connect(self._manual_stop)
        self.manual_speak.toggled.connect(self._manual_speak_toggled)
        self.manual_voice.changed.connect(self._manual_voice_changed)
        self.manual_speed.valueChanged.connect(self._manual_speed_changed)
        self._manual_saved_voice = saved.get("voice")
        self.manual_tab_widget = w
        self._manual_show(0)
        return w

    # ------------------------------------------------------------------ narrator
    def _manual_narrator(self) -> Narrator:
        if self._narrator is None:
            n = Narrator()
            if n.available:
                voices = n.voices()
                self.manual_voice.blockSignals(True)
                self.manual_voice.set_items([(name, name) for _i, name, _l in voices])
                names = [name for _i, name, _l in voices]
                pick = self._manual_saved_voice if self._manual_saved_voice in names else \
                    (names[n.default_voice()] if names else "")
                if pick:
                    self.manual_voice.setValue(pick)
                    n.set_voice(names.index(pick))
                self.manual_voice.blockSignals(False)
                n.set_rate(self.manual_speed.value())
                if not n.has_english_voice():
                    self.manual_note.setText("No English voice is installed - the manual is in English. Add one in "
                                             "Windows Settings → Time & language → Speech.")
            else:
                self.manual_note.setText("The Windows voice is not available on this PC - the manual is shown as "
                                         "text only.")
                self.manual_speak.setEnabled(False)
            self._narrator = n
        return self._narrator

    def _manual_read(self):
        """Read the chapter on screen from its beginning (the previous reading is cut first)."""
        n = self._manual_narrator()
        n.speak(speakable(CHAPTERS[self._manual_index].body))

    def _manual_stop(self):
        if self._narrator is not None:
            self._narrator.stop()

    # ------------------------------------------------------------------ navigation
    def _manual_show(self, i: int):
        self._manual_index = i
        self.manual_view.setMarkdown(CHAPTERS[i].body.strip())
        self.manual_view.verticalScrollBar().setValue(0)
        self.manual_pos.setText(f"   Chapter {i + 1} of {len(CHAPTERS)}")
        self.manual_prev.setEnabled(i > 0)
        self.manual_next.setEnabled(i < len(CHAPTERS) - 1)
        self.manual_list.blockSignals(True)
        self.manual_list.setCurrentRow(i)
        self.manual_list.blockSignals(False)

    def _manual_goto(self, i: int):
        i = max(0, min(len(CHAPTERS) - 1, i))
        changed = i != self._manual_index
        self._manual_stop()                      # the old chapter is cut at once
        self._manual_show(i)                     # the new chapter is shown...
        if changed and self.manual_speak.isChecked() and self._manual_tab_visible():
            self._manual_read()                  # ...and read

    def _manual_tab_visible(self) -> bool:
        return self.tabs.currentWidget() is getattr(self, "manual_tab_widget", None)

    # ------------------------------------------------------------------ settings, hooks
    def _manual_speak_toggled(self, on: bool):
        if on and self._manual_tab_visible():
            self._manual_read()
        elif not on:
            self._manual_stop()
        self._manual_save()

    def _manual_voice_changed(self):
        n = self._manual_narrator()
        names = [v[1] for v in n.voices()]
        name = self.manual_voice.value()
        if name in names:
            n.set_voice(names.index(name))
            if self.manual_speak.isChecked() and self._manual_tab_visible():
                self._manual_read()
        self._manual_save()

    def _manual_speed_changed(self, v: int):
        if self._narrator is not None:
            self._narrator.set_rate(v)
        self._manual_save()

    def _manual_save(self):
        self.state["manual"] = {"speak": self.manual_speak.isChecked(), "rate": self.manual_speed.value(),
                                "voice": self.manual_voice.value() or self._manual_saved_voice}
        try:
            config.save_app_state(self.state)
        except Exception:  # noqa: BLE001
            pass

    def _manual_tab_changed(self):
        """Called by MainWindow when the user changes tab: read when the Manual opens, be silent when it closes."""
        if getattr(self, "manual_tab_widget", None) is None:
            return
        if self._manual_tab_visible():
            if self.manual_speak.isChecked():
                self._manual_read()
        else:
            self._manual_stop()

    def _manual_close(self):
        self._manual_stop()
