"""Downloads the offline natural voice (Piper) of the app language into models/piper - once, about 60 MB.

After that the tour and the Manual are read aloud without internet."""
from __future__ import annotations

from .config import MODELS_DIR
from .i18n import Language

TIMEOUT = 30


def download(lang: Language, progress=None, cancelled=lambda: False) -> None:
    """Fetch both files of `lang`'s voice. progress(done_bytes, total_bytes) is called while downloading.
    Raises on failure; a half-downloaded file never replaces a good one."""
    import requests
    folder = MODELS_DIR / "piper"
    folder.mkdir(parents=True, exist_ok=True)
    todo = [(url, folder / name) for url, name in lang.piper_urls if not (folder / name).is_file()]
    sizes = []
    for url, _dst in todo:
        try:
            r = requests.head(url, allow_redirects=True, timeout=TIMEOUT)
            sizes.append(int(r.headers.get("content-length") or 0))
        except requests.RequestException:
            sizes.append(0)
    total, done = sum(sizes), 0
    for url, dst in todo:
        part = dst.with_name(dst.name + ".part")
        with requests.get(url, stream=True, timeout=TIMEOUT) as r:
            r.raise_for_status()
            with open(part, "wb") as f:
                for block in r.iter_content(1 << 16):
                    if cancelled():
                        raise RuntimeError("cancelled")
                    f.write(block)
                    done += len(block)
                    if progress:
                        progress(done, total)
        part.replace(dst)
