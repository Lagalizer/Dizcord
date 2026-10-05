"""Text-to-speech providers.

synthesize(text, lang, voice, gender) -> (mono float32 audio, sample_rate)
voice "auto" (or "") = pick a good default voice for the language.
list_voices(lang) -> [(voice_id, label)]
"""
from __future__ import annotations

import asyncio
import html
from pathlib import Path

import numpy as np

from .. import languages as L
from ..audio.utils import decode_audio, pcm16_to_float
from ..config import MODELS_DIR
from .base import Field, Provider, ProviderError, register


def _is_auto(voice) -> bool:
    return not voice or str(voice).lower() in ("auto", "default")


class TTSProvider(Provider):
    kind = "tts"

    def synthesize(self, text: str, lang: str, voice: str, gender: str = "female") -> tuple[np.ndarray, int]:
        raise NotImplementedError

    def list_voices(self, lang: str | None = None) -> list[tuple[str, str]]:
        return []


def _pct(v: float) -> str:
    v = int(round(v))
    return f"+{v}%" if v >= 0 else f"{v}%"


@register
class EdgeTTS(TTSProvider):
    id = "edge"
    name = "Microsoft Edge neural voices (free)"
    description = ("400+ very natural neural voices in 100+ languages, free, no key needed "
                   "(uses the Edge read-aloud service, so it needs internet).")
    requires = ["edge_tts"]
    pip_hint = "pip install edge-tts"
    fields = [
        Field("rate", "Speed %", "int", 8, min=-50, max=100, help="+10 = 10% faster"),
        Field("pitch", "Pitch (Hz)", "int", 0, min=-50, max=50),
        Field("volume", "Loudness %", "int", 0, min=-50, max=50),
    ]
    _voices_cache = None

    def synthesize(self, text, lang, voice, gender="female"):
        import edge_tts
        v = L.default_voice(lang, gender) if _is_auto(voice) else voice
        pitch = int(self.s("pitch", 0))

        async def run():
            com = edge_tts.Communicate(text, v, rate=_pct(self.s("rate", 0)),
                                       volume=_pct(self.s("volume", 0)),
                                       pitch=f"+{pitch}Hz" if pitch >= 0 else f"{pitch}Hz")
            buf = bytearray()
            async for chunk in com.stream():
                if chunk["type"] == "audio":
                    buf.extend(chunk["data"])
            return bytes(buf)

        try:
            data = asyncio.run(run())
        except Exception as e:
            raise ProviderError(f"Edge TTS ({v}): {e}") from e
        if not data:
            raise ProviderError(f"Edge TTS returned no audio for voice {v}.")
        return decode_audio(data)

    def list_voices(self, lang=None):
        import edge_tts
        if EdgeTTS._voices_cache is None:
            EdgeTTS._voices_cache = asyncio.run(edge_tts.list_voices())
        out = []
        loc = L.locale_tag(lang).lower() if lang and lang != L.AUTO else None
        b = L.base(lang) if lang and lang != L.AUTO else None
        for v in EdgeTTS._voices_cache:
            short = v["ShortName"]
            vloc = v.get("Locale", "").lower()
            if b and not vloc.startswith(b + "-") and "multilingual" not in short.lower():
                continue
            score = 0 if loc and vloc == loc else 1
            out.append((score, short, f"{short}  ({v.get('Gender', '')})"))
        out.sort()
        return [(s, lbl) for _, s, lbl in out]


class OpenAICompatTTS(TTSProvider):
    base_url = ""
    key_ref = "custom_tts"
    default_model = ""
    model_options: list[str] = []
    voice_options: list[str] = []
    default_voice_name = "alloy"
    key_optional = False

    @classmethod
    def build_fields(cls):
        return [
            Field("base_url", "Base URL", "str", cls.base_url),
            Field("api_key", "API key", "secret", "", key_ref=cls.key_ref),
            Field("model", "Model", "combo", cls.default_model, options=cls.model_options),
            Field("default_voice", "Voice when 'auto'", "combo", cls.default_voice_name, options=cls.voice_options),
            Field("speed", "Speed", "float", 1.05, min=0.25, max=4, step=0.05),
            Field("instructions", "Voice instructions", "str", "Speak naturally, like a friendly person in a voice chat.",
                  help="Tone/accent instructions (gpt-4o-mini-tts only)"),
            Field("timeout", "Timeout (s)", "float", 30, min=3, max=120),
        ]

    def synthesize(self, text, lang, voice, gender="female"):
        url = self.s("base_url").rstrip("/") + "/audio/speech"
        key = self.key() if self.key_optional else self.need_key()
        body = {"model": self.s("model"), "input": text, "response_format": "wav",
                "voice": self.s("default_voice") if _is_auto(voice) else voice,
                "speed": float(self.s("speed", 1.0))}
        if "gpt-4o" in self.s("model") and self.s("instructions"):
            body["instructions"] = self.s("instructions")
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        r = self.http("POST", url, json=body, headers=headers, timeout=float(self.s("timeout", 30)))
        return decode_audio(r.content)

    def list_voices(self, lang=None):
        return [(v, v) for v in self.voice_options]


_OPENAI_VOICES = ["alloy", "ash", "ballad", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer", "verse"]

for _pid, _name, _url, _ref, _model, _models, _voices, _dv in [
    ("openai_tts", "OpenAI", "https://api.openai.com/v1", "openai", "gpt-4o-mini-tts",
     ["gpt-4o-mini-tts", "tts-1", "tts-1-hd"], _OPENAI_VOICES, "coral"),
    ("custom_tts", "Custom OpenAI-compatible", "http://localhost:8880/v1", "custom_tts", "kokoro",
     ["kokoro", "tts-1"], ["af_heart", "af_bella", "am_michael", "bf_emma", "pf_dora", "pm_alex"], "af_heart"),
]:
    _cls = type(f"TTS_{_pid}", (OpenAICompatTTS,), {
        "id": _pid, "name": _name, "base_url": _url, "key_ref": _ref, "default_model": _model,
        "model_options": _models, "voice_options": _voices, "default_voice_name": _dv,
        "key_optional": _pid == "custom_tts",
        "description": f"{_name} text-to-speech (/audio/speech). "
                       + ("Works with Kokoro-FastAPI, speaches, LocalAI, AllTalk..." if _pid == "custom_tts" else
                          "Voices are multilingual."),
    })
    _cls.fields = _cls.build_fields()
    register(_cls)


@register
class ElevenLabsTTS(TTSProvider):
    id = "elevenlabs"
    name = "ElevenLabs"
    description = "The most natural/expressive voices. Multilingual models speak 29-70+ languages with any voice."
    fields = [
        Field("api_key", "API key", "secret", "", key_ref="elevenlabs"),
        Field("model", "Model", "combo", "eleven_flash_v2_5",
              options=["eleven_flash_v2_5", "eleven_turbo_v2_5", "eleven_multilingual_v2", "eleven_v3"],
              help="flash = lowest latency, multilingual_v2 = highest quality"),
        Field("default_voice", "Voice ID when 'auto'", "combo", "JBFqnCBsd6RMkjVDRZzb",
              options=["JBFqnCBsd6RMkjVDRZzb", "21m00Tcm4TlvDq8ikWAM", "EXAVITQu4vr4xnSDxMaL"]),
        Field("stability", "Stability", "float", 0.5, min=0, max=1, step=0.05),
        Field("similarity", "Similarity boost", "float", 0.75, min=0, max=1, step=0.05),
        Field("speed", "Speed", "float", 1.0, min=0.7, max=1.2, step=0.05),
        Field("timeout", "Timeout (s)", "float", 30, min=3, max=120),
    ]

    def synthesize(self, text, lang, voice, gender="female"):
        vid = self.s("default_voice") if _is_auto(voice) else voice
        body = {"text": text, "model_id": self.s("model"),
                "voice_settings": {"stability": float(self.s("stability")),
                                   "similarity_boost": float(self.s("similarity")),
                                   "speed": float(self.s("speed", 1.0))}}
        if lang and self.s("model") in ("eleven_flash_v2_5", "eleven_turbo_v2_5"):
            body["language_code"] = L.base(lang)
        r = self.http("POST", f"https://api.elevenlabs.io/v1/text-to-speech/{vid}",
                      params={"output_format": "pcm_24000"},
                      headers={"xi-api-key": self.need_key(), "Content-Type": "application/json"},
                      json=body, timeout=float(self.s("timeout", 30)))
        return pcm16_to_float(r.content), 24000

    def list_voices(self, lang=None):
        r = self.http("GET", "https://api.elevenlabs.io/v1/voices", headers={"xi-api-key": self.need_key()})
        return [(v["voice_id"], f"{v['name']}  ({v.get('category', '')})") for v in r.json().get("voices", [])]


@register
class AzureTTS(TTSProvider):
    id = "azure_tts"
    name = "Azure Speech"
    description = "Microsoft Azure neural voices (same voices as Edge, with an SLA and more styles)."
    fields = [
        Field("api_key", "API key", "secret", "", key_ref="azure_speech"),
        Field("region", "Region", "str", "eastus"),
        Field("rate", "Speed %", "int", 5, min=-50, max=100),
        Field("timeout", "Timeout (s)", "float", 20, min=3, max=120),
    ]

    def synthesize(self, text, lang, voice, gender="female"):
        v = L.default_voice(lang, gender) if _is_auto(voice) else voice
        loc = "-".join(v.split("-")[:2])
        ssml = (f"<speak version='1.0' xml:lang='{loc}'><voice name='{v}'>"
                f"<prosody rate='{_pct(self.s('rate', 0))}'>{html.escape(text)}</prosody></voice></speak>")
        r = self.http("POST", f"https://{self.s('region')}.tts.speech.microsoft.com/cognitiveservices/v1",
                      headers={"Ocp-Apim-Subscription-Key": self.need_key(),
                               "Content-Type": "application/ssml+xml",
                               "X-Microsoft-OutputFormat": "riff-24khz-16bit-mono-pcm",
                               "User-Agent": "Dizcord"},
                      data=ssml.encode("utf-8"), timeout=float(self.s("timeout", 20)))
        return decode_audio(r.content)

    def list_voices(self, lang=None):
        r = self.http("GET", f"https://{self.s('region')}.tts.speech.microsoft.com/cognitiveservices/voices/list",
                      headers={"Ocp-Apim-Subscription-Key": self.need_key()})
        b = L.base(lang) if lang and lang != L.AUTO else None
        return [(v["ShortName"], f"{v['ShortName']}  ({v.get('Gender', '')})") for v in r.json()
                if not b or v.get("Locale", "").lower().startswith(b + "-")]


@register
class GoogleTTS(TTSProvider):
    id = "google_tts"
    name = "Google Cloud Text-to-Speech"
    description = "Google Cloud TTS (Neural2 / WaveNet / Chirp voices) with an API key."
    fields = [
        Field("api_key", "API key", "secret", "", key_ref="google_cloud"),
        Field("speaking_rate", "Speed", "float", 1.05, min=0.25, max=4, step=0.05),
        Field("timeout", "Timeout (s)", "float", 20, min=3, max=120),
    ]

    def synthesize(self, text, lang, voice, gender="female"):
        import base64
        vsel = {"languageCode": L.locale_tag(lang)}
        if _is_auto(voice):
            vsel["ssmlGender"] = "MALE" if gender == "male" else "FEMALE"
        else:
            vsel["name"] = voice
            vsel["languageCode"] = "-".join(voice.split("-")[:2])
        body = {"input": {"text": text}, "voice": vsel,
                "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 24000,
                                "speakingRate": float(self.s("speaking_rate", 1.0))}}
        r = self.http("POST", "https://texttospeech.googleapis.com/v1/text:synthesize",
                      params={"key": self.need_key()}, json=body, timeout=float(self.s("timeout", 20)))
        return decode_audio(base64.b64decode(r.json()["audioContent"]))

    def list_voices(self, lang=None):
        params = {"key": self.need_key()}
        if lang and lang != L.AUTO:
            params["languageCode"] = L.locale_tag(lang)
        r = self.http("GET", "https://texttospeech.googleapis.com/v1/voices", params=params)
        return [(v["name"], f"{v['name']}  ({v.get('ssmlGender', '')})") for v in r.json().get("voices", [])]


@register
class DeepgramTTS(TTSProvider):
    id = "deepgram_tts"
    name = "Deepgram Aura"
    description = "Deepgram Aura-2: very low latency natural voices (English and Spanish)."
    fields = [
        Field("api_key", "API key", "secret", "", key_ref="deepgram"),
        Field("default_voice", "Voice when 'auto'", "combo", "aura-2-thalia-en",
              options=["aura-2-thalia-en", "aura-2-andromeda-en", "aura-2-apollo-en", "aura-2-arcas-en",
                       "aura-2-celeste-es", "aura-2-nestor-es"]),
        Field("timeout", "Timeout (s)", "float", 20, min=3, max=120),
    ]

    def synthesize(self, text, lang, voice, gender="female"):
        model = self.s("default_voice") if _is_auto(voice) else voice
        r = self.http("POST", "https://api.deepgram.com/v1/speak",
                      params={"model": model, "encoding": "linear16", "sample_rate": 24000, "container": "none"},
                      headers={"Authorization": f"Token {self.need_key()}", "Content-Type": "application/json"},
                      json={"text": text}, timeout=float(self.s("timeout", 20)))
        return pcm16_to_float(r.content), 24000

    def list_voices(self, lang=None):
        return [(v, v) for v in self.fields[1].options]


@register
class PiperTTS(TTSProvider):
    id = "piper"
    name = "Piper"
    local = True
    description = ("Fast offline voices. Download voices (.onnx + .onnx.json) from "
                   "huggingface.co/rhasspy/piper-voices into models/piper/. 'auto' picks a voice "
                   "whose file name starts with the language code (e.g. pt_BR-faber-medium.onnx).")
    requires = ["piper"]
    pip_hint = "pip install piper-tts"
    fields = [
        Field("folder", "Voices folder", "path", str(MODELS_DIR / "piper")),
        Field("length_scale", "Slowness (1 = normal)", "float", 0.95, min=0.5, max=2, step=0.05),
    ]
    _loaded: dict = {}

    def _voice_files(self):
        folder = Path(self.s("folder"))
        folder.mkdir(parents=True, exist_ok=True)
        return sorted(folder.glob("*.onnx"))

    def _pick(self, lang, voice):
        files = self._voice_files()
        if not files:
            raise ProviderError(f"Piper: no voices in {self.s('folder')}. Download some .onnx voices first.")
        if not _is_auto(voice):
            for f in files:
                if f.stem == voice or str(f) == voice:
                    return f
        loc = L.locale_tag(lang).replace("-", "_").lower()
        b = L.base(lang)
        for f in files:
            if f.stem.lower().startswith(loc):
                return f
        for f in files:
            if f.stem.lower().startswith(b + "_"):
                return f
        raise ProviderError(f"Piper: no voice for language '{lang}' in {self.s('folder')}.")

    def synthesize(self, text, lang, voice, gender="female"):
        from piper import PiperVoice
        path = self._pick(lang, voice)
        with self.lock:
            pv = PiperTTS._loaded.get(str(path))
            if pv is None:
                pv = PiperTTS._loaded[str(path)] = PiperVoice.load(str(path))
            ls = float(self.s("length_scale", 1.0))
            try:  # piper-tts >= 1.3
                from piper import SynthesisConfig
                chunks = list(pv.synthesize(text, syn_config=SynthesisConfig(length_scale=ls)))
                audio = np.concatenate([c.audio_float_array for c in chunks]) if chunks else np.zeros(0)
                return audio.astype(np.float32), chunks[0].sample_rate if chunks else pv.config.sample_rate
            except ImportError:  # piper-tts 1.2
                raw = b"".join(pv.synthesize_stream_raw(text, length_scale=ls))
                return pcm16_to_float(raw), pv.config.sample_rate

    def list_voices(self, lang=None):
        return [(f.stem, f.stem) for f in self._voice_files()]


_KOKORO_LANG = {"en": "en-us", "en-GB": "en-gb", "es": "es", "es-MX": "es", "fr": "fr-fr", "it": "it",
                "pt": "pt-br", "pt-PT": "pt-br", "hi": "hi", "ja": "ja", "zh": "cmn"}
_KOKORO_VOICE = {"en": ("af_heart", "am_michael"), "en-GB": ("bf_emma", "bm_george"), "es": ("ef_dora", "em_alex"),
                 "fr": ("ff_siwis", "ff_siwis"), "it": ("if_sara", "im_nicola"), "pt": ("pf_dora", "pm_alex"),
                 "hi": ("hf_alpha", "hm_omega"), "ja": ("jf_alpha", "jm_kumo"), "zh": ("zf_xiaobei", "zm_yunxi")}


@register
class KokoroTTS(TTSProvider):
    id = "kokoro"
    name = "Kokoro"
    local = True
    description = ("High quality offline voices (82M model). Languages: English, Spanish, French, Italian, "
                   "Portuguese (BR), Hindi, Japanese, Chinese. Put kokoro-v1.0.onnx and voices-v1.0.bin "
                   "in models/kokoro/ (github.com/thewh1teagle/kokoro-onnx releases).")
    requires = ["kokoro_onnx"]
    pip_hint = "pip install kokoro-onnx"
    fields = [
        Field("model_path", "Model file", "path", str(MODELS_DIR / "kokoro" / "kokoro-v1.0.onnx")),
        Field("voices_path", "Voices file", "path", str(MODELS_DIR / "kokoro" / "voices-v1.0.bin")),
        Field("speed", "Speed", "float", 1.05, min=0.5, max=2, step=0.05),
    ]
    _engine = None

    def _load(self):
        from kokoro_onnx import Kokoro
        if KokoroTTS._engine is None:
            mp, vp = Path(self.s("model_path")), Path(self.s("voices_path"))
            if not mp.exists() or not vp.exists():
                raise ProviderError(f"Kokoro: model files not found ({mp.name}, {vp.name}).")
            KokoroTTS._engine = Kokoro(str(mp), str(vp))
        return KokoroTTS._engine

    def synthesize(self, text, lang, voice, gender="female"):
        key = lang if lang in _KOKORO_LANG else L.base(lang)
        if key not in _KOKORO_LANG:
            raise ProviderError(f"Kokoro doesn't support '{L.name(lang)}'. Pick another voice engine.")
        if _is_auto(voice):
            pair = _KOKORO_VOICE.get(key) or _KOKORO_VOICE[L.base(key)]
            voice = pair[1] if gender == "male" else pair[0]
        with self.lock:
            samples, sr = self._load().create(text, voice=voice, speed=float(self.s("speed", 1.0)),
                                              lang=_KOKORO_LANG[key])
        return np.asarray(samples, dtype=np.float32), int(sr)

    def list_voices(self, lang=None):
        try:
            return [(v, v) for v in sorted(self._load().get_voices())]
        except Exception:
            return [(v, v) for pair in _KOKORO_VOICE.values() for v in pair]
