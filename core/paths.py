import sys
from pathlib import Path


def get_base_path() -> Path:
    """Returns the base path for bundled data files.
    When running inside a PyInstaller bundle, files are extracted to a
    temporary directory referenced by sys._MEIPASS.  Otherwise, uses the
    current working directory."""
    if getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS)
    return Path(".")
