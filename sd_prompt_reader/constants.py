# -*- encoding:utf-8 -*-
__author__ = 'receyuki'
__filename__ = 'constants.py'
__copyright__ = 'Copyright 2023, '
__email__ = 'receyuki@gmail.com'

from importlib import resources
from pathlib import Path

RELEASE_URL = "https://api.github.com/repos/receyuki/stable-diffusion-prompt-reader/releases/latest"
RESOURCE_DIR = str(resources.files("resources"))
SUPPORTED_FORMATS = [".png", ".jpg", ".jpeg", ".webp"]
INFO_FILE = Path(RESOURCE_DIR, "info.png")
ERROR_FILE = Path(RESOURCE_DIR, "error.png")
BOX_IMPORTANT_FILE = Path(RESOURCE_DIR, "box-important.png")
OK_FILE = Path(RESOURCE_DIR, "ok.png")
AVAILABLE_UPDATES_FILE = Path(RESOURCE_DIR, "available-updates.png")
DROP_FILE = Path(RESOURCE_DIR, "drag-and-drop.png")
CLIPBOARD_FILE = Path(RESOURCE_DIR, "copy-to-clipboard.png")
REMOVE_TAG_FILE = Path(RESOURCE_DIR, "remove-tag.png")
ICON_FILE = Path(RESOURCE_DIR, "icon.png")
ICO_FILE = Path(RESOURCE_DIR, "icon.ico")
MESSAGE = {
    "success": ["Voilà!"],
    "format_error": ["No data", "No data detected or unsupported format"],
    "suffix_error": ["Unsupported format"]
}