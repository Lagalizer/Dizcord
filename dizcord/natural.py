"""Natural voices for the Manual tab: Microsoft Edge neural voices (free, no key, needs internet).

Same small interface as sapi.Narrator (speak / stop), but the text is turned into speech sentence by sentence in a
background thread, so the first words start quickly and a new call cuts the previous reading at once.
If the service cannot be reached, `on_error(message)` is called (from the worker thread) and nothing is played.
"""
from __future__ import annotations

import asyncio
import logging
import queue
import re
import threading

import numpy as np

from .audio.utils import decode_audio

log = logging.getLogger("dizcord.natural")

# (voice id, label) - a short, curated list of English neural voices
VOICES = [
    ("en-US-AriaNeural", "Aria - US, female"),
    ("en-US-JennyNeural", "Jenny - US, female"),
    ("en-US-AvaNeural", "Ava - US, female"),
    ("en-US-GuyNeural", "Guy - US, male"),
    ("en-US-AndrewNeural", "Andrew - US, male"),
    ("en-GB-SoniaNeural", "Sonia - UK, female"),
    ("en-GB-RyanNeural", "Ryan - UK, male"),
    ("en-AU-NatashaNeural", "Natasha - Australia, female"),
]
_CHUNK = 280                       # characters per request: short enough to start fast, long enough to sound natural


def _chunks(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?:])\s+", text.strip())
    out, cur = [], ""
    for s in sentences:
        if cur and len(cur) + len(s) + 1 > _CHUNK:
            out.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        out.append(cur)
    return out


class NaturalNarrator:
    def __init__(self, on_error=None):
        self.available = False
        self.on_error = on_error
        self._gen = 0
        self._lock = threading.Lock()
        try:
            import edge_tts  # noqa: F401
            import sounddevice  # noqa: F401
            self.available = True
        except Exception as e:  # noqa: BLE001
            log.info("natural voices not available: %s", e)

    def voices(self) -> list[tuple[str, str]]:
        return list(VOICES)

    # ------------------------------------------------------------------ speaking
    def speak(self, text: str, voice: str, rate: int = 0) -> None:
        """Say `text` now with `voice` (a short name); `rate` is a percentage (-50 .. +100). Returns at once."""
        self.stop()
        if not self.available or not text.strip():
            return
        with self._lock:
            gen = self._gen
        q: queue.Queue = queue.Queue(maxsize=2)       # synthesised audio waiting to be played
        threading.Thread(target=self._produce, args=(gen, _chunks(text), voice, rate, q), daemon=True).start()
        threading.Thread(target=self._play, args=(gen, q), daemon=True).start()

    def stop(self) -> None:
        with self._lock:
            self._gen += 1
        if self.available:
            try:
                import sounddevice as sd
                sd.stop()
            except Exception:  # noqa: BLE001
                pass

    def _alive(self, gen: int) -> bool:
        return gen == self._gen

    def _produce(self, gen, chunks, voice, rate, q):
        import edge_tts
        pct = f"+{int(rate)}%" if rate >= 0 else f"{int(rate)}%"

        async def one(t):
            buf = bytearray()
            async for c in edge_tts.Communicate(t, voice, rate=pct).stream():
                if c["type"] == "audio":
                    buf.extend(c["data"])
            return bytes(buf)

        try:
            for t in chunks:
                if not self._alive(gen):
                    return
                data = asyncio.run(one(t))
                if not data:
                    raise RuntimeError("no audio returned")
                audio, sr = decode_audio(data)
                while self._alive(gen):
                    try:
                        q.put((audio, sr), timeout=0.2)
                        break
                    except queue.Full:
                        pass
        except Exception as e:  # noqa: BLE001
            log.warning("natural voice failed: %s", e)
            if self._alive(gen) and self.on_error:
                self.on_error(str(e))
        finally:
            while self._alive(gen):                       # tell the player there is nothing more
                try:
                    q.put(None, timeout=0.2)
                    break
                except queue.Full:
                    pass

    def _play(self, gen, q):
        import sounddevice as sd
        while self._alive(gen):
            try:
                item = q.get(timeout=0.2)
            except queue.Empty:
                continue
            if item is None:
                return
            audio, sr = item
            try:
                sd.play(np.asarray(audio, dtype=np.float32), sr)
                n = len(audio) / float(sr)
                waited = 0.0
                while waited < n + 0.3 and self._alive(gen):
                    threading.Event().wait(0.05)
                    waited += 0.05
            except Exception as e:  # noqa: BLE001
                log.warning("could not play: %s", e)
                return
