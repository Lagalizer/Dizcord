"""Paths, profiles (save/load) and the API key store.

Profiles never contain API keys - keys live in data/keys.json (or environment
variables) so a profile can be shared/exported safely.
"""
import copy
import json
import os
import re
import sys
import threading
from pathlib import Path

from . import languages

if getattr(sys, "frozen", False):
    ROOT = Path(sys.executable).parent
else:
    ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
PROFILES_DIR = DATA_DIR / "profiles"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
LOGS_DIR = DATA_DIR / "logs"
MODELS_DIR = ROOT / "models"
KEYS_FILE = DATA_DIR / "keys.json"
APP_STATE_FILE = DATA_DIR / "app_state.json"

for _d in (DATA_DIR, PROFILES_DIR, TRANSCRIPTS_DIR, LOGS_DIR, MODELS_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def default_profile() -> dict:
    me = languages.system_language()
    them = "en" if languages.base(me) != "en" else "es"
    return {
        "name": "Default",
        "incoming": {                      # what other people say -> me
            "enabled": True,
            "source_lang": "auto",
            "target_lang": me,
            "speak": True,                 # read the translation out loud to me
            "show_subtitles": True,
            "skip_same_language": True,    # don't re-speak lines already in my language
            "output_device": "",           # where I hear translations ("" = system default)
            "volume": 1.0,
            "passthrough": False,          # forward the captured Discord audio to my output device
            "passthrough_volume": 1.0,
            "duck_passthrough": 0.25,      # passthrough volume multiplier while a translation is spoken
        },
        "outgoing": {                      # what I say -> other people
            "enabled": True,
            "source_lang": me,
            "target_lang": them,
            "follow_their_language": False,  # auto-switch target to the last language I heard
            "speak": True,
            "output_device": "CABLE Input",  # virtual cable that Discord uses as its microphone
            "volume": 1.0,
            "monitor_device": "",            # optionally hear your own translated voice
            "monitor_volume": 0.5,
            "monitor": False,
        },
        "input": {
            "listen_mode": "loopback",     # loopback = capture an output device, device = capture an input device
            "listen_device": "",           # loopback: output device name; device: input device name
            "mic_device": "",
            "mic_mode": "vad",             # vad | ptt | toggle
            "ptt_key": "f8",
            "listen_vad": {"auto": True, "threshold_db": -45.0, "silence_ms": 700, "min_speech_ms": 350,
                           "max_utterance_s": 12.0, "pre_roll_ms": 300},
            "mic_vad": {"auto": True, "threshold_db": -42.0, "silence_ms": 600, "min_speech_ms": 300,
                        "max_utterance_s": 15.0, "pre_roll_ms": 300},
            "pause_listen_while_speaking": True,   # avoid translating our own translations (echo)
            "ignore_mic_while_playing": True,      # don't send incoming translations back out through the mic
            "mic_gain_db": 0.0,
            "listen_gain_db": 0.0,
        },
        "stt": {"provider": "faster_whisper", "settings": {}},
        "translation": {
            "provider": "google_free",
            "settings": {},
            "style": "natural",            # natural | casual | formal | literal
            "context_lines": 4,            # recent lines given to AI models for better translations
            "glossary": "",                # one per line: term = translation   (or just term to keep as-is)
            "keep_profanity": True,
        },
        "ai": {"provider": "openai", "settings": {}, "custom_prompt": ""},
        "tts": {
            "provider": "edge",
            "settings": {},
            "voices": {},                  # provider_id -> {"incoming": voice, "outgoing": voice}
            "gender": "female",
        },
        "chat": {
            "auto_translate": False,       # read Discord messages from the window and translate them
            "target_lang": me,
            "skip_same_language": True,
            "include_embeds": True,
            "my_name": "",                 # your Discord display name - your own messages are skipped
            "history": 5,                  # translate the last N messages when you open a channel
            "poll_ms": 700,
            "overlay_attach": True,        # keep the chat overlay docked to the Discord window
            "overlay_lines": 6,
            "engine": "",                  # translation engine for text ("" = same as the Translation tab)
            "display": "inline",           # where translations show: inline (on the messages in Discord) | window | both
            "hotkey_inline": "ctrl+alt+i", # show the originals / the translations
            "speak": False,                # read translated chat messages out loud
            "speak_mode": "queue",         # queue = one after the other | interrupt = a new one cuts the old one
            "select_translate": True,      # translate text you highlight with the mouse
            "select_scope": "discord",     # discord | everywhere
            "popup_seconds": 10,
            "hotkey_selection": "ctrl+alt+t",
            "hotkey_draft": "ctrl+alt+y",  # translate what you typed in Discord's message box, in place
            "hotkey_ocr": "ctrl+alt+o",    # select a screen area and translate the text in it
            "compose_lang": "auto",        # auto = the language people use in the chat
            "draft_send": False,           # press Enter after translating the draft
            "ocr_lang": "auto",
            "clipboard_watch": False,      # translate everything you copy
        },
        "bot": {                           # Discord bot (Bots tab) - the token lives in data/keys.json
            "autostart": False,            # start the bot when Dizcord starts
            "context_menu": True,          # right-click a message -> Apps -> Translate
            "public_translate": False,     # also "Translate for everyone" (servers only)
            "slash_commands": True,        # /translate, /translate-settings, /languages
            "auto_translate": True,        # /autotranslate channels in servers you manage
            "flag_reactions": True,        # react with a flag -> translation in that language
            "webhook_mode": True,          # allow auto-translate "webhook" mode (posts as the author)
            "include_embeds": True,        # translate embeds and image alt text too
            "default_lang": "auto",        # auto = each user's Discord language
            "engine": "",                  # translation engine override ("" = same as the app)
            "rate_limit": 10,              # translations per user per minute (0 = no limit)
            "daily_char_limit": 0,         # characters per day (0 = no limit)
            "test_guild": "",              # server id for instant command sync while testing
            "cluster_channel": "",         # cloud copies: private channel id where they coordinate (fail-over)
            "cluster_name": "this-pc",     # this copy's name in that channel
            "cluster_priority": 9,         # 1 = main; the PC is normally the last backup
        },
        "ui": {
            "subtitle_font_size": 22,
            "subtitle_opacity": 0.85,
            "subtitle_show_original": True,
            "subtitle_lines": 3,
            "subtitle_show_mine": True,
            "autosave_transcript": True,
            "autosave_settings": True,       # save the profile by itself ~1 s after every change
        },
    }


def deep_merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict) and k not in ("settings", "voices"):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def _safe_filename(name: str) -> str:
    s = re.sub(r"[^\w\- ]+", "_", name, flags=re.UNICODE).strip()
    return s or "profile"


def list_profiles() -> list[str]:
    names = []
    for p in sorted(PROFILES_DIR.glob("*.json")):
        try:
            names.append(json.loads(p.read_text(encoding="utf-8")).get("name") or p.stem)
        except Exception:
            names.append(p.stem)
    return names


def profile_path(name: str) -> Path:
    return PROFILES_DIR / f"{_safe_filename(name)}.json"


def load_profile(name: str) -> dict:
    p = profile_path(name)
    data = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    prof = deep_merge(default_profile(), data)
    prof["name"] = name
    return prof


def save_profile(profile: dict, name: str | None = None) -> Path:
    if name:
        profile["name"] = name
    p = profile_path(profile["name"])
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, p)
    return p


def delete_profile(name: str) -> None:
    p = profile_path(name)
    if p.exists():
        p.unlink()


def import_profile(path: str) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    prof = deep_merge(default_profile(), data)
    prof["name"] = data.get("name") or Path(path).stem
    return prof


def export_profile(profile: dict, path: str) -> None:
    Path(path).write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")


# Starter profiles written on first run: (name, overrides)
TEMPLATES = [
    ("Free - no keys needed", {}),
    ("OpenAI - best all-round", {
        "stt": {"provider": "openai_stt", "settings": {}},
        "translation": {"provider": "llm", "settings": {}},
        "ai": {"provider": "openai", "settings": {}},
        "tts": {"provider": "openai_tts", "settings": {}},
    }),
    ("Groq + Edge - fast and cheap", {
        "stt": {"provider": "groq_stt", "settings": {}},
        "translation": {"provider": "llm", "settings": {}},
        "ai": {"provider": "groq", "settings": {}},
        "tts": {"provider": "edge", "settings": {}},
    }),
    ("Claude + ElevenLabs - premium", {
        "stt": {"provider": "openai_stt", "settings": {}},
        "translation": {"provider": "llm", "settings": {}},
        "ai": {"provider": "anthropic", "settings": {}},
        "tts": {"provider": "elevenlabs", "settings": {}},
    }),
    ("Fully offline (Whisper + Ollama + Piper)", {
        "stt": {"provider": "faster_whisper", "settings": {}},
        "translation": {"provider": "llm", "settings": {}},
        "ai": {"provider": "ollama", "settings": {}},
        "tts": {"provider": "piper", "settings": {}},
    }),
]


def ensure_starter_profiles() -> None:
    if any(PROFILES_DIR.glob("*.json")):
        return
    for name, overrides in TEMPLATES:
        prof = deep_merge(default_profile(), overrides)
        prof["name"] = name
        save_profile(prof)


def load_app_state() -> dict:
    try:
        return json.loads(APP_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_app_state(state: dict) -> None:
    APP_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- keys

# key id -> (label, environment variable)
KNOWN_KEYS = {
    "openai":        ("OpenAI", "OPENAI_API_KEY"),
    "anthropic":     ("Anthropic (Claude)", "ANTHROPIC_API_KEY"),
    "gemini":        ("Google Gemini", "GEMINI_API_KEY"),
    "groq":          ("Groq", "GROQ_API_KEY"),
    "openrouter":    ("OpenRouter", "OPENROUTER_API_KEY"),
    "together":      ("Together AI", "TOGETHER_API_KEY"),
    "mistral":       ("Mistral", "MISTRAL_API_KEY"),
    "deepseek":      ("DeepSeek", "DEEPSEEK_API_KEY"),
    "xai":           ("xAI (Grok)", "XAI_API_KEY"),
    "fireworks":     ("Fireworks AI", "FIREWORKS_API_KEY"),
    "cerebras":      ("Cerebras", "CEREBRAS_API_KEY"),
    "custom_llm":    ("Custom OpenAI-compatible LLM", "CUSTOM_LLM_API_KEY"),
    "custom_stt":    ("Custom OpenAI-compatible STT", "CUSTOM_STT_API_KEY"),
    "custom_tts":    ("Custom OpenAI-compatible TTS", "CUSTOM_TTS_API_KEY"),
    "deepl":         ("DeepL", "DEEPL_API_KEY"),
    "google_cloud":  ("Google Cloud (Translate / Speech / TTS)", "GOOGLE_API_KEY"),
    "azure_speech":  ("Azure Speech", "AZURE_SPEECH_KEY"),
    "azure_translator": ("Azure Translator", "AZURE_TRANSLATOR_KEY"),
    "elevenlabs":    ("ElevenLabs", "ELEVENLABS_API_KEY"),
    "deepgram":      ("Deepgram", "DEEPGRAM_API_KEY"),
    "libretranslate": ("LibreTranslate", "LIBRETRANSLATE_API_KEY"),
    "discord_bot":   ("Discord bot token (Bots tab)", "DISCORD_BOT_TOKEN"),
}


class KeyStore:
    """API keys from data/keys.json, falling back to environment variables."""

    def __init__(self, path: Path = KEYS_FILE):
        self.path = path
        self._lock = threading.Lock()
        try:
            self._keys = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            self._keys = {}

    def get(self, key_id: str) -> str:
        v = (self._keys.get(key_id) or "").strip()
        if v:
            return v
        env = KNOWN_KEYS.get(key_id, (None, key_id.upper() + "_API_KEY"))[1]
        return os.environ.get(env, "").strip()

    def stored(self, key_id: str) -> str:
        return self._keys.get(key_id, "")

    def set(self, key_id: str, value: str) -> None:
        with self._lock:
            if value:
                self._keys[key_id] = value.strip()
            else:
                self._keys.pop(key_id, None)

    def save(self) -> None:
        with self._lock:
            self.path.write_text(json.dumps(self._keys, indent=2), encoding="utf-8")
