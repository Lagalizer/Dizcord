"""Dizcord Translator - entry point.  Run:  Dizcord.bat  (or python main.py)"""
import logging
import logging.handlers
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Keep every download (Whisper models, HF cache...) inside the app folder -> portable.
os.environ.setdefault("HF_HOME", str(ROOT / "models" / "huggingface"))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("ARGOS_PACKAGES_DIR", str(ROOT / "models" / "argos"))
os.environ.setdefault("XDG_DATA_HOME", str(ROOT / "models"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / "models" / "cache"))


def _add_cuda_dlls():
    """Make pip-installed NVIDIA libraries (GPU extras) visible to CTranslate2 on Windows."""
    if os.name != "nt":
        return
    for sp in sys.path:
        nv = Path(sp) / "nvidia"
        if nv.is_dir():
            for bin_dir in nv.glob("*/bin"):
                try:
                    os.add_dll_directory(str(bin_dir))
                except OSError:
                    pass
                os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")


def _setup_logging():
    from dizcord.config import LOGS_DIR
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    fh = logging.handlers.RotatingFileHandler(LOGS_DIR / "dizcord.log", maxBytes=2_000_000, backupCount=3,
                                              encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root.addHandler(fh)
    if sys.stderr:
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        root.addHandler(sh)
    for noisy in ("httpx", "httpcore", "urllib3", "faster_whisper", "huggingface_hub"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def main():
    sys.path.insert(0, str(ROOT))
    _add_cuda_dlls()
    _setup_logging()
    log = logging.getLogger("dizcord")

    def excepthook(et, ev, tb):
        log.error("Unhandled error", exc_info=(et, ev, tb))
    sys.excepthook = excepthook

    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from dizcord import APP_NAME, __version__
    from dizcord.gui.main_window import MainWindow

    if os.name == "nt":  # own taskbar icon/group instead of python's
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Dizcord.Translator")
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    icon = ROOT / "assets" / "icon.ico"
    if icon.exists():
        app.setWindowIcon(QIcon(str(icon)))
    log.info("%s %s starting (Python %s)", APP_NAME, __version__, sys.version.split()[0])
    win = MainWindow(app)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
