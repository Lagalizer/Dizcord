# 🎧 Dizcord Translator

**Real-time voice and chat translator for Discord** (and any voice chat). Hear everyone in your language,
speak in theirs. Runs on your own Windows PC - free engines included, no account needed.

## What it does

- **You hear them in your language.** Listens to what people say in Discord, transcribes it, translates it, shows
  subtitles and can read the translation to you.
- **They hear you in yours.** You talk into your mic; the translation is spoken into Discord through a virtual
  audio cable.
- **Text too.** Translates Discord messages inside Discord itself (servers, DMs, threads), anything you highlight
  with the mouse, and text on your screen with OCR. Write in their language with a hotkey.
- **Free or premium.** Every step (speech, translation, AI, voice) has a free engine and optional cloud
  engines (OpenAI, Groq, DeepL, ElevenLabs...) or fully offline ones (Whisper, Ollama, Piper).
- **Portable.** Everything lives in the app folder. Nothing is installed in Windows.
- **Built-in manual, read aloud.** The *Manual* tab explains every feature chapter by chapter and reads it to you
  with a natural neural voice (free, no key, needs internet) - or, with no internet, the voices built into Windows
  (offline, no AI). Next / Previous cut the old chapter and read the new one.
- **Updates in one click.** *Settings → Updates → Check for updates* downloads the newest release; your settings,
  keys and models are kept.

## Quick start

1. **Download** the latest release (or *Code → Download ZIP*) and unzip it anywhere.
2. Double-click **`Dizcord.exe`**. The first time it builds its own private Python inside the folder
   (about 750 MB, a few minutes, no admin rights).
3. Install the free [VB-Audio Virtual Cable](https://vb-audio.com/Cable/) once and restart Windows.
4. In Discord → *Voice & Video*: input device **CABLE Output**, turn off Noise Suppression, Echo Cancellation
   and Automatic Gain Control.
5. In Dizcord pick the profile **Free - no keys needed**, choose the languages on the *Live* tab and press
   **Start** (F5). Open the **Manual** tab for the full guide.

**Requirements:** Windows 10/11 (64-bit), about 1.5 GB of free disk space, a microphone and headphones.
The speech model (Whisper small, ~460 MB) downloads the first time you use it.

## Privacy

Your API keys stay in `data\keys.json` on your PC and are never put in profiles or exports. The *Free* profile
sends text to Google Translate and Microsoft Edge voices over the internet; the *Fully offline* profile keeps
everything on your PC.

## Folder

```
Dizcord.exe / Dizcord.bat    start the app        Dizcord-debug.bat   start with a console (bug reports)
setup.bat                    (re)build the runtime  install_extras.bat  optional offline engines / GPU
main.py, dizcord\            source code          tools\selftest.py   check the whole pipeline
```
