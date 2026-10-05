"""The translation engine: two pipelines (incoming + outgoing) sharing providers and outputs.

incoming: Discord audio (loopback/input) -> VAD -> STT -> translate -> subtitles + TTS to my headphones
outgoing: my mic -> VAD/PTT -> STT -> translate -> TTS to the virtual cable (Discord's microphone)

Events are delivered to the GUI through emit(dict).
"""
from __future__ import annotations

import collections
import itertools
import logging
import queue
import re
import threading
import time

import numpy as np

from . import languages as L
from .audio import devices
from .audio.capture import InputDeviceSource, LoopbackSource
from .audio.player import OutputManager
from .audio.vad import Segmenter
from .providers import REGISTRY, ProviderError
from .providers.translate import TranslateContext
from .textengine import TextEngine, detect_text_language  # noqa: F401  (re-exported)

log = logging.getLogger("dizcord.engine")

# Things Whisper likes to "hear" in silence/noise.
_HALLUCINATIONS = {
    "thank you", "thanks for watching", "thank you for watching", "thanks for watching and see you next time",
    "please subscribe", "subscribe", "you", "bye", "obrigado", "obrigada", "tchau", "gracias", "merci",
    "ご視聴ありがとうございました", "продолжение следует", "субтитры сделал dimatorzok", "amen",
    "legendas pela comunidade amara.org", "sous-titres réalisés par la communauté d'amara.org",
    "untertitel der amara.org-community", "subtítulos realizados por la comunidad de amara.org",
}


def _norm(text: str) -> str:
    return re.sub(r"[^\w\s']", "", text.lower(), flags=re.UNICODE).strip()


def is_garbage(text: str) -> bool:
    t = _norm(text)
    if not t or not re.search(r"\w", t):
        return True
    if t in _HALLUCINATIONS or "amara.org" in text.lower():
        return True
    return False


class Pipeline:
    def __init__(self, engine: "Engine", direction: str):
        self.engine = engine
        self.dir = direction                  # "incoming" | "outgoing"
        self.source = None
        self.segmenter = None
        self.stt_q: queue.Queue = queue.Queue()
        self.tts_q: queue.Queue = queue.Queue()
        self.running = False
        self.threads: list[threading.Thread] = []
        self._passthrough_ok = False

    # ------------------------------------------------------------ config
    @property
    def p(self) -> dict:
        return self.engine.profile

    @property
    def cfg(self) -> dict:
        return self.p[self.dir]

    def _listen_device_name(self) -> str:
        return self.p["input"]["listen_device"] or devices.default_name("output")

    # ------------------------------------------------------------ lifecycle
    def start(self):
        inp = self.p["input"]
        if self.dir == "incoming":
            mode = "vad"
            vad_cfg = inp["listen_vad"]
            gain = inp.get("listen_gain_db", 0.0)
            cable_out = self._cable_recording_side(inp["listen_device"]) if inp["listen_mode"] == "loopback" else None
            if cable_out:
                # WASAPI loopback of a VB-Audio cable endpoint is silent - record its other side instead.
                self.engine.emit_status(f"Listening to '{cable_out}' (recording side of the virtual cable)")
                self.source = InputDeviceSource(cable_out, self._on_audio)
            elif inp["listen_mode"] == "loopback":
                self.source = LoopbackSource(inp["listen_device"], self._on_audio)
            else:
                self.source = InputDeviceSource(inp["listen_device"], self._on_audio)
        else:
            mode = inp["mic_mode"]
            vad_cfg = inp["mic_vad"]
            gain = inp.get("mic_gain_db", 0.0)
            self.source = InputDeviceSource(inp["mic_device"], self._on_audio)

        self.running = True
        self.source.start()
        self.segmenter = Segmenter(self.source.samplerate, self._on_utterance, self._on_level, mode, vad_cfg, gain)
        self._passthrough_ok = self._check_passthrough()
        for fn in (self._stt_worker, self._tts_worker):
            t = threading.Thread(target=fn, name=f"{self.dir}-{fn.__name__}", daemon=True)
            t.start()
            self.threads.append(t)

    def stop(self):
        self.running = False
        if self.source:
            self.source.stop()
            self.source = None
        self.stt_q.put(None)
        self.tts_q.put(None)

    @staticmethod
    def _cable_recording_side(output_name: str) -> str | None:
        """'CABLE-A Input (VB-Audio Cable A)' -> matching 'CABLE-A Output …' input device, if any."""
        m = re.match(r"^(CABLE(?:-\w+)?) Input\b", output_name or "", re.I)
        if not m:
            return None
        want = f"{m.group(1)} Output".lower()
        for name in devices.input_devices():
            if name.lower().startswith(want):
                return name
        return None

    def _check_passthrough(self) -> bool:
        if self.dir != "incoming" or not self.cfg.get("passthrough"):
            return False
        inp = self.p["input"]
        res = self.engine.outputs.resolve
        if inp["listen_mode"] == "loopback" and res(self.cfg["output_device"]) == res(inp["listen_device"]):
            self.engine.emit_error("Pass-through disabled: you can't play the captured device back into "
                                   "itself (feedback loop). Capture a separate device (e.g. CABLE-B / Voicemeeter).")
            return False
        return True

    # ------------------------------------------------------------ audio thread
    def _on_audio(self, chunk: np.ndarray):
        if not self.running or self.segmenter is None:
            return
        if self._passthrough_ok:
            try:
                self.engine.outputs.get(self.cfg["output_device"]).push_live(
                    chunk, self.source.samplerate, float(self.cfg.get("passthrough_volume", 1.0)))
            except Exception as e:
                self._passthrough_ok = False
                self.engine.emit_error(f"Pass-through failed: {e}")
        self.segmenter.muted = self._should_mute()
        self.segmenter.feed(chunk)

    def _should_mute(self) -> bool:
        inp = self.p["input"]
        if not self.cfg.get("enabled", True):
            return True
        if self.dir == "incoming":
            if self.engine.paused_incoming:
                return True
            if inp.get("pause_listen_while_speaking") and inp["listen_mode"] == "loopback":
                dev = self.engine.outputs.existing(inp["listen_device"])
                return bool(dev and dev.is_playing())
            return False
        # outgoing: don't pick up translations coming out of the speakers
        if self.engine.muted_outgoing:
            return True
        if inp.get("ignore_mic_while_playing"):
            return self.engine.outputs.any_playing("incoming") or self.engine.outputs.any_playing("monitor")
        return False

    def _on_level(self, db, speech):
        self.engine.emit({"type": "level", "dir": self.dir, "db": db, "speech": speech,
                          "threshold": self.segmenter.effective_threshold if self.segmenter else -45})

    def _on_utterance(self, audio16, duration):
        if self.stt_q.qsize() >= 4:  # falling behind: drop the oldest so we stay live
            try:
                self.stt_q.get_nowait()
                self.engine.emit_status(f"{self.dir}: running behind, skipped a sentence")
            except queue.Empty:
                pass
        self.stt_q.put((time.monotonic(), audio16, duration))

    # ------------------------------------------------------------ workers
    def _stt_worker(self):
        while True:
            item = self.stt_q.get()
            if item is None or not self.running:
                return
            t_captured, audio, duration = item
            try:
                self.process_audio(audio, t_captured)
            except ProviderError as e:
                self.engine.emit_error(str(e))
            except Exception as e:
                log.exception("pipeline error")
                self.engine.emit_error(f"{self.dir}: {e}")
            finally:
                self.engine.emit({"type": "busy", "dir": self.dir, "stage": None})

    def process_audio(self, audio, t0=None):
        eng = self.engine
        t0 = t0 or time.monotonic()
        src_cfg = self.cfg["source_lang"]
        src = None if src_cfg == L.AUTO else src_cfg
        eng.emit({"type": "busy", "dir": self.dir, "stage": "stt"})
        stt = eng.provider("stt")
        if src is None and not getattr(stt, "supports_auto", True):
            src = eng.profile["outgoing"]["source_lang"] if self.dir == "outgoing" else None
        t = time.monotonic()
        text, detected = stt.transcribe(audio, src)
        t_stt = time.monotonic() - t
        if is_garbage(text):
            return
        detected = detected or src or detect_text_language(text)
        self.process_text(text, detected, t0=t0, timings={"stt": t_stt})

    def process_text(self, text, detected=None, t0=None, timings=None, typed=False):
        eng = self.engine
        t0 = t0 or time.monotonic()
        timings = dict(timings or {})
        target = self.target_language()
        if detected is None:
            src_cfg = self.cfg["source_lang"]
            detected = None if src_cfg == L.AUTO else src_cfg
            detected = detected or detect_text_language(text)

        if self.dir == "incoming" and detected and not L.same_language(detected, eng.profile["incoming"]["target_lang"]):
            eng.set_their_language(detected)

        # regional variants (pt-PT vs pt-BR...) still go through translation
        skipped = L.same_language(detected, target) and target not in ("pt-PT", "en-GB", "zh-TW", "es-MX")
        translated = text
        if not skipped:
            eng.emit({"type": "busy", "dir": self.dir, "stage": "translate"})
            t = time.monotonic()
            tr = eng.provider("translate")
            ctx = eng.translate_context(self.dir)
            src_for_mt = detected
            if tr.needs_source and not src_for_mt:
                raise ProviderError(f"{tr.name}: couldn't detect the spoken language for: “{text[:60]}”")
            translated, det2 = tr.translate(text, src_for_mt, target, ctx)
            detected = detected or det2
            timings["mt"] = time.monotonic() - t
            if not translated.strip():
                return

        eng.add_history("Them" if self.dir == "incoming" else "Me", text, translated)
        speak = bool(self.cfg.get("speak", True)) and not (skipped and self.dir == "incoming"
                                                           and self.cfg.get("skip_same_language", True))
        line_id = eng.next_line_id()
        eng.emit({"type": "line", "dir": self.dir, "id": line_id, "original": text, "translated": translated,
                  "src": detected, "tgt": target, "timings": timings, "skipped": skipped, "typed": typed,
                  "latency": time.monotonic() - t0})
        if speak:
            self.tts_q.put((line_id, translated, target, t0, timings))

    def target_language(self) -> str:
        if self.dir == "outgoing" and self.cfg.get("follow_their_language") and self.engine.their_language:
            return self.engine.their_language
        return self.cfg["target_lang"]

    def _tts_worker(self):
        while True:
            item = self.tts_q.get()
            if item is None:
                return
            line_id, text, lang, t0, timings = item
            try:
                self.engine.emit({"type": "busy", "dir": self.dir, "stage": "tts"})
                t = time.monotonic()
                audio, sr = self.engine.synthesize(text, lang, self.dir)
                timings["tts"] = time.monotonic() - t
                self.engine.play(self.dir, audio, sr)
                self.engine.emit({"type": "spoken", "dir": self.dir, "id": line_id, "timings": timings,
                                  "latency": time.monotonic() - t0})
            except ProviderError as e:
                self.engine.emit_error(str(e))
            except Exception as e:
                log.exception("tts error")
                self.engine.emit_error(f"Voice: {e}")
            finally:
                self.engine.emit({"type": "busy", "dir": self.dir, "stage": None})


class Engine(TextEngine):
    def __init__(self, profile: dict, keys, emit):
        super().__init__(profile, keys)
        self._emit = emit
        self.outputs = OutputManager()
        self.pipelines: dict[str, Pipeline] = {}
        self.their_language: str | None = None
        self.running = False
        self.paused_incoming = False
        self.muted_outgoing = False
        self._ids = itertools.count(1)
        self._hotkey_hooks = []
        self._ptt_down = False

    # --------------------------------------------------------------- events
    def emit(self, ev: dict):
        try:
            self._emit(ev)
        except Exception:
            pass

    def emit_status(self, text):
        log.info(text)
        self.emit({"type": "status", "text": text})

    def emit_error(self, text):
        log.error(text)
        self.emit({"type": "error", "text": text})

    def next_line_id(self) -> int:
        return next(self._ids)

    def set_their_language(self, lang):
        if lang and lang != self.their_language:
            self.their_language = lang
            self.emit({"type": "their_lang", "lang": lang})

    def voice_for(self, direction: str) -> str:
        tts = self.profile["tts"]
        return (tts.get("voices", {}).get(tts["provider"], {}) or {}).get(direction, "auto") or "auto"

    def synthesize(self, text, lang, direction):
        tts = self.provider("tts")
        audio, sr = tts.synthesize(text, lang, self.voice_for(direction), self.profile["tts"].get("gender", "female"))
        if audio is None or len(audio) == 0:
            raise ProviderError(f"{tts.name}: no audio returned")
        from .audio.utils import trim_silence
        return trim_silence(np.asarray(audio, dtype=np.float32), sr), sr

    def play(self, direction, audio, sr, wait=True):
        cfg = self.profile[direction]
        clips = []
        if direction == "incoming":
            clips.append(self.outputs.get(cfg["output_device"]).play(audio, sr, float(cfg.get("volume", 1.0)),
                                                                     "incoming"))
            self.outputs.get(cfg["output_device"]).duck = float(cfg.get("duck_passthrough", 0.25))
        else:
            clips.append(self.outputs.get(cfg["output_device"]).play(audio, sr, float(cfg.get("volume", 1.0)),
                                                                     "outgoing"))
            if cfg.get("monitor"):
                try:
                    clips.append(self.outputs.get(cfg.get("monitor_device", "")).play(
                        audio, sr, float(cfg.get("monitor_volume", 0.5)), "monitor"))
                except Exception as e:
                    self.emit_error(f"Monitor output: {e}")
        if wait:  # keep sentences in order and let the echo guard see playback
            for c in clips:
                c.done.wait(timeout=len(audio) / sr + 5)

    # --------------------------------------------------------------- control
    def start(self):
        if self.running:
            return
        self.running = True
        self.emit({"type": "state", "running": True})
        threading.Thread(target=self._start_bg, daemon=True).start()

    def _start_bg(self):
        try:
            self.emit_status("Loading engines…")
            for kind in ("stt", "translate", "tts"):
                self.provider(kind)
            if self.profile["translation"]["provider"] == "llm":
                self.provider("llm")
            stt = self.provider("stt")
            if stt.local:
                self.emit_status(f"Loading {stt.name} model… (the first time it is downloaded - this can take "
                                 "a few minutes)")
            stt.warmup()
            started = []
            for d in ("incoming", "outgoing"):
                if not self.profile[d].get("enabled", True):
                    continue
                pl = Pipeline(self, d)
                try:
                    pl.start()
                    self.pipelines[d] = pl
                    started.append(d)
                except Exception as e:
                    pl.stop()
                    self.emit_error(f"Could not start {d} audio: {e}")
            # open outputs now so the first sentence isn't delayed
            for name in {self.profile["incoming"]["output_device"], self.profile["outgoing"]["output_device"]}:
                try:
                    self.outputs.get(name)
                except Exception as e:
                    self.emit_error(str(e))
            self._install_hotkeys()
            if not self.running:   # stopped while we were loading
                self._teardown()
                return
            if started:
                self.emit_status("Running: " + " + ".join(started))
            else:
                self.emit_error("Nothing started - check the Input tab.")
                self.stop()
        except ProviderError as e:
            self.emit_error(str(e))
            self.stop()
        except Exception as e:
            log.exception("start failed")
            self.emit_error(f"Start failed: {e}")
            self.stop()

    def stop(self):
        self.running = False
        self._teardown()
        self.emit({"type": "state", "running": False})
        self.emit_status("Stopped")

    def _teardown(self):
        self._remove_hotkeys()
        for pl in list(self.pipelines.values()):
            try:
                pl.stop()
            except Exception:
                pass
        self.pipelines.clear()
        self.outputs.close_all()

    def shutdown(self):
        self.stop()
        for p in self._providers.values():
            try:
                p.close()
            except Exception:
                pass

    def apply_profile(self, profile: dict):
        """Live-update settings that don't need a restart (languages, voices, volumes, VAD...)."""
        self.profile = profile
        for d, pl in self.pipelines.items():
            if pl.segmenter:
                inp = profile["input"]
                pl.segmenter.update_config(inp["listen_vad"] if d == "incoming" else inp["mic_vad"])
                if d == "outgoing":
                    pl.segmenter.mode = inp["mic_mode"]

    # --------------------------------------------------------------- manual input
    def say(self, text: str):
        """Typed message -> translate -> speak into Discord."""
        def run():
            pl = self.pipelines.get("outgoing") or Pipeline(self, "outgoing")
            try:
                pl.process_text(text, typed=True)
                if pl not in self.pipelines.values():  # not running: speak synchronously
                    while not pl.tts_q.empty():
                        line_id, tr, lang, t0, timings = pl.tts_q.get()
                        audio, sr = self.synthesize(tr, lang, "outgoing")
                        self.play("outgoing", audio, sr)
                        self.emit({"type": "spoken", "dir": "outgoing", "id": line_id, "timings": timings,
                                   "latency": time.monotonic() - t0})
            except ProviderError as e:
                self.emit_error(str(e))
            except Exception as e:
                log.exception("say failed")
                self.emit_error(f"Say: {e}")
        threading.Thread(target=run, daemon=True).start()

    def set_ptt(self, down: bool):
        pl = self.pipelines.get("outgoing")
        if pl and pl.segmenter:
            pl.segmenter.set_ptt(down)
            self.emit({"type": "ptt", "down": pl.segmenter.ptt_down})

    def stop_speaking(self):
        for d in self.outputs.all():
            d.stop_clips()

    # --------------------------------------------------------------- hotkeys
    def _install_hotkeys(self):
        key = (self.profile["input"].get("ptt_key") or "").strip()
        if self.profile["input"]["mic_mode"] not in ("ptt", "toggle") or not key:
            return
        try:
            import keyboard
        except ImportError:
            self.emit_status("Global hotkeys unavailable (pip install keyboard) - use the on-screen button.")
            return
        try:
            def on_down(_e):
                if not self._ptt_down:
                    self._ptt_down = True
                    self.set_ptt(True)

            def on_up(_e):
                if self._ptt_down:
                    self._ptt_down = False
                    if self.profile["input"]["mic_mode"] == "ptt":
                        self.set_ptt(False)
            self._hotkey_hooks = [keyboard.on_press_key(key, on_down), keyboard.on_release_key(key, on_up)]
        except Exception as e:
            self.emit_error(f"Could not register hotkey '{key}': {e}")

    def _remove_hotkeys(self):
        if not self._hotkey_hooks:
            return
        try:
            import keyboard
            for h in self._hotkey_hooks:
                keyboard.unhook(h)
        except Exception:
            pass
        self._hotkey_hooks = []
