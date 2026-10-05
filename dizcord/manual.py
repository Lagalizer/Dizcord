"""The user manual shown (and read aloud) in the Manual tab. Plain Markdown chapters - no tables, so the text
reads well when it is spoken - plus `speakable()`, which turns a chapter into text a voice can say."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Chapter:
    title: str
    body: str            # Markdown


CHAPTERS: list[Chapter] = [
    Chapter("1. Welcome", """
# Welcome to Dizcord

Dizcord is a real-time translator for Discord and any other voice chat. It runs entirely on your own PC.

- **You hear them in your language.** The app listens to what people say in Discord, writes it down,
  translates it, shows subtitles, and can read the translation to you with a natural voice.
- **They hear you in their language.** You speak into your microphone. The app translates what you said and
  speaks it into Discord through a virtual audio cable.
- **Text too.** It translates Discord messages in servers, direct messages and threads, any text you highlight
  with the mouse, and text on your screen using OCR. You can also write in their language.
- **Free to start.** The profile called Free, no keys needed, works without any account or payment.
  Paid cloud engines are optional.

This manual has twelve chapters. Use the Next and Previous buttons, or click a chapter in the list.
Every time you change chapter, the narrator stops the old one and reads the new one. The voice is the one built
into Windows. It uses no artificial intelligence, needs no internet and costs nothing.
"""),
    Chapter("2. First start", """
# First start

**Step 1. Open the app.** Double-click Dizcord.exe, or Dizcord.bat. The first time, the app builds its own private
copy of Python inside its folder. This downloads about 750 megabytes, takes a few minutes, and needs no
administrator rights. Nothing is installed in Windows itself.

**Step 2. Install a virtual audio cable.** Install VB-Audio Virtual Cable, which is free, and restart the PC. This
is the only thing outside the folder, because Windows needs a driver to create a virtual microphone.

**Step 3. Set up Discord.** Open Discord, then User Settings, then Voice and Video.

- Input Device: CABLE Output, from VB-Audio Virtual Cable.
- Output Device: your headphones.
- Turn off Noise Suppression, Echo Cancellation and Automatic Gain Control.

**Step 4. Set up the app.** Choose the profile Free, no keys needed. On the Output tab, send your translated
voice to CABLE Input. On the Input tab, choose the loopback of the headphones that Discord plays to, and your
real microphone. On the Live tab, choose the languages. Then press Start, or the F5 key.

The speech model, Whisper small, is about 460 megabytes and downloads the first time you use it.
"""),
    Chapter("3. The main window", """
# The main window

At the top you find the profile box. A profile stores all your settings for engines, languages and devices.
You can save, save as, delete, import and export profiles. Exported profiles never contain your API keys.

Your changes are saved automatically about one second after you make them. You can switch this off in the
Settings tab.

Next to the profile box are three buttons:

- **Subtitles** shows a floating subtitle window that you can drag, resize with the mouse wheel, and
  configure with a right-click.
- **Chat** turns on the translation of Discord text messages.
- **Start** begins the voice translator. The F5 key does the same.

The tabs are: Dashboard, Live, Text, Input, Output, Speech, Translation, AI Model, Voice, API Keys, Setup,
Settings, Manual and Log. The next chapters explain the ones you will use most.
"""),
    Chapter("4. Dashboard", """
# Dashboard

The Dashboard is your control panel. It is the first tab, and it shows everything at a glance.

- The **voice translator card** starts and stops live voice translation, and shows what it is doing:
  recognizing, translating or speaking.
- The **chat translation card** starts and stops the translation of Discord messages. It also has the option
  to read translated messages out loud, either one after the other, or letting a new message interrupt the
  one being read.
- The **You card** is where you set your Discord name and the language you write in.
- The **tools card** has shortcuts for highlight to translate, OCR and the subtitle window.
- The **hotkeys card** reminds you of your keyboard shortcuts.
- At the bottom, Latest translations shows the last lines that were translated.

Settings that appear in two places, for example in the Dashboard and in the Text tab, always stay in sync.
"""),
    Chapter("5. Live voice translation", """
# Live voice translation

This is the main feature. It works in two directions, and each one can be switched on separately.

**Incoming: they speak, you hear.** The app listens to the sound that Discord plays to your headphones. It
recognizes the speech, translates it, shows subtitles, and, if you want, speaks the translation. You choose
the language they speak, or Auto-detect.

**Outgoing: you speak, they hear.** The app listens to your microphone, translates what you say, and speaks it
into Discord through the virtual cable. Your own voice is not sent to Discord, only the translation.

On the **Live** tab you set the languages for both directions, watch the level meters and read the transcript.
You can use a push to talk button, and the Type to speak box, where you type a line, it is translated and spoken
into Discord. The option Reply in the language they speak makes your output language follow the last language
detected from the other person.

On the **Input** tab you choose what to listen to and how your microphone starts: voice activity, push to talk,
or toggle. There is also a sensitivity control and echo protection, which ignores the captured audio while your
own translations are playing.

On the **Output** tab you choose where translations play, the virtual cable for your voice, and pass through
with ducking. Ducking lowers the original voices while a translation is spoken, so you can still hear them.
"""),
    Chapter("6. Engines: speech, translation, AI and voice", """
# Engines

Every step of the translation can use a different engine, and you can switch them at any time. They are saved
in your profile.

- **Speech tab.** Turns speech into text. The free choice is Whisper, which runs on your PC. Cloud choices need a
  key: OpenAI, Groq, Deepgram, ElevenLabs, Azure and Google. There is a microphone test on this tab.
- **Translation tab.** The free choice is Google Translate, which needs no key. Others are DeepL, Azure,
  LibreTranslate, MyMemory, and the offline engine Argos. You can set the tone: natural, casual, formal or
  literal. A glossary lets you fix how certain words, such as names and game terms, are translated.
- **AI Model tab.** Used when the translation engine is the AI model. It can be a cloud model or one running on
  your PC, for example with Ollama or LM Studio. You can add extra instructions for slang or names.
- **Voice tab.** The engine that speaks the translations. The free choice is Microsoft Edge neural voices.
  Piper and Kokoro work offline. ElevenLabs, OpenAI, Azure and Google are paid options. Pick a voice for each
  direction, or let the app choose a natural voice for each language.

Every tab has a Test button, so you can check an engine before using it.

The starter profiles are: Free, no keys needed. OpenAI. Groq with Edge. Claude with ElevenLabs. And Fully
offline, with Whisper, Ollama and Piper.
"""),
    Chapter("7. API keys", """
# API keys

Free engines need no keys. If you want a paid or cloud engine, you need an API key from that company.

Open the **API Keys** tab and paste each key in its box. All keys are kept in one place, in the file
data, keys dot json, inside the app folder. Keys are never stored inside profiles, and never included when you
export a profile, so you can share profiles safely.

Keep that file private. If you copy the whole folder to another PC, your keys go with it.

Optional local engines, such as Piper, Kokoro, Argos and the NVIDIA graphics card libraries, are installed
with install extras dot bat, or with the Install now button next to the engine in the app.
"""),
    Chapter("8. Translating Discord text", """
# Translating Discord text

Press the **Chat** button, or use the chat card in the Dashboard. The app then reads the messages you see in the
Discord app, using the Windows accessibility features, like a screen reader. It needs no token, no bot, and
sends nothing to Discord.

New messages are translated and drawn on top of the original text, right inside Discord, or in a small window
next to it. You choose which in the Text tab, under Show translations. It works in servers, direct messages,
group chats, threads and forum posts, even with Discord in the background. Messages already in your language,
and your own messages, are skipped. The translations only show while Discord is the active window, so they never
cover your game.

The Text tab has more tools:

- **Highlight to translate.** Select text, or double-click a word, and a popup with the translation appears
  next to the mouse.
- **Control Alt T** translates the current selection in any app.
- **Control Alt Y** replaces what you typed in Discord's message box with its translation into the language used
  in that chat.
- **Write in their language.** Type in the Text tab, then copy, paste into Discord, or send.
- **Control Alt O** lets you drag a box over any part of the screen. The app reads the text with OCR and shows
  the translation on top of it. It can repeat every few seconds.
- **Copied text.** Optionally translate everything you copy.

You can change every hotkey in the Text tab. For OCR in other alphabets, such as Russian or Japanese, add that
language in Windows Settings.
"""),
    Chapter("9. Subtitles and transcripts", """
# Subtitles and transcripts

The **subtitle window** floats above your game or Discord. Drag it to move it. Use the mouse wheel to resize it.
Right-click for options, such as how many lines to show, whether to show the original text, and the background.
In Settings you can change its text size and font.

Every conversation can be saved as a **transcript**. This is on by default, and you switch it off on the Output
tab. Transcripts are saved in the data folder, under transcripts, and you can open that folder from the Log tab
or from Settings.

The Log tab shows what the app is doing in real time. It also has buttons to open the logs, the transcripts and
the app folder. If something goes wrong, the log is the first place to look.

The status bar at the bottom shows the delay of each stage: speech recognition, translation and voice, so you
can see which engine is slow.
"""),
    Chapter("10. Settings and updates", """
# Settings and updates

The **Settings** tab controls how the app looks: the theme, dark or light, the font, and the text size of the app
and of the translations shown inside Discord, in the small chat window and in the popups. It also has all the
hotkeys in one place, a switch to keep the window above other windows, and buttons to reset the window positions
and open the app, data and log folders.

The switch Save changes automatically keeps your profile saved about one second after every change. It is on by
default.

**Updates.** Press Check for updates. If a newer version exists on GitHub, the button Update now appears. It
downloads the new version and replaces the program files. Your settings, profiles, API keys and downloaded models
are never touched. If the list of required packages changed, they are updated too. When it finishes, the app
offers to restart. The app also checks quietly a few seconds after it starts.
"""),
    Chapter("11. Troubleshooting", """
# Troubleshooting

**Run the self test.** Open a console in the app folder and run `runtime\\python.exe tools\\selftest.py`. It plays
a test sentence into the virtual cable and runs both directions. If it ends with the word PASS, recognition,
translation and voice all work.

**Nobody hears my translation.** In Discord, the input device must be CABLE Output. In the app, the Output tab
must send to CABLE Input. Check that Noise Suppression is off in Discord.

**The app hears nothing.** On the Input tab, check that the loopback device is the one Discord plays to. Look at
the level meters on the Live tab. If they do not move, the device is wrong.

**My own translation is heard twice, or the app translates itself.** Turn on echo protection on the Input tab and
use headphones.

**An engine fails.** Open the Log tab. A message that says forbidden, or blocked, usually means the key or the
model is not allowed for your account. Try another engine, then test again.

**Chat translation shows nothing.** Make sure Discord is the active window and that the Chat button is on. The
feature is made for the Discord desktop app.

**Still stuck.** Start the app with Dizcord debug dot bat. It opens a console that shows errors, which helps when
you report a problem.
"""),
    Chapter("12. About this manual", """
# About this manual

You are reading the manual built into Dizcord. The narrator is the voice that comes with Windows. It works
offline, uses no artificial intelligence, and does not send anything anywhere.

- **Next and Previous** move between chapters. The narrator stops reading the old chapter and starts the new
  one, and the new text is shown at the same time.
- **Read aloud** turns the narrator on or off. When it is off, the manual is just text.
- **Read again** starts the current chapter from the beginning.
- **Stop** silences the narrator.
- **Voice** and **Speed** let you change how it sounds. The manual is written in English, so choose an English
  voice. Windows includes some by default. If you want more voices, add them in Windows Settings, under Time and
  language, then Speech.

The narrator is silent when you leave this tab, and it never starts by itself while you are using the
translator.

That is the end of the manual. Enjoy Dizcord!
"""),
]


# --------------------------------------------------------------------------- text for the voice
_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_MARKS = re.compile(r"[*_`#>]+")
_COMBO = re.compile(r"(?<=\w)\+(?=\w)")


def speakable(md: str) -> str:
    """Markdown -> plain sentences for a speech engine: no symbols, 'Ctrl+Alt+T' -> 'Control Alt T'.
    Lines that are only wrapped for the editor are joined, so the voice does not pause in the middle of a sentence."""
    items: list[str] = []            # one entry per heading / bullet / paragraph
    cur = ""
    for raw in md.strip().splitlines():
        line = raw.strip()
        starts_new = line.startswith("#") or bool(re.match(r"^[-*]\s", line))
        if not line or starts_new:
            if cur:
                items.append(cur)
            cur = ""
        if not line:
            continue
        line = _LINK.sub(r"\1", line)
        line = re.sub(r"^[-*]\s+", "", line)
        cur = f"{cur} {line}".strip() if cur and not starts_new else line
    if cur:
        items.append(cur)
    out = []
    for it in items:
        it = _MARKS.sub("", it).strip()
        if it:
            out.append(it if it[-1] in ".!?:;" else it + ".")
    text = " ".join(out)
    text = text.replace("Ctrl", "Control").replace("\\", " ")
    text = _COMBO.sub(" ", text)
    text = re.sub(r"[^\x20-\x7EÀ-ɏ]", " ", text)      # drop emojis and arrows
    return re.sub(r"\s+", " ", text).strip()
