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
COLOR_THEME = Path(RESOURCE_DIR, "gray.json")
INFO_FILE = Path(RESOURCE_DIR, "info.png")
ERROR_FILE = Path(RESOURCE_DIR, "error.png")
BOX_IMPORTANT_FILE = Path(RESOURCE_DIR, "box-important.png")
OK_FILE = Path(RESOURCE_DIR, "ok.png")
AVAILABLE_UPDATES_FILE = Path(RESOURCE_DIR, "available-updates.png")
DROP_FILE = Path(RESOURCE_DIR, "drag-and-drop.png")
CLIPBOARD_FILE = Path(RESOURCE_DIR, "copy-to-clipboard.png")
REMOVE_TAG_FILE = Path(RESOURCE_DIR, "remove-tag.png")
DOCUMENT_FILE = Path(RESOURCE_DIR, "document.png")
EXPAND_ARROW_FILE = Path(RESOURCE_DIR, "expand-arrow.png")
ICON_FILE = Path(RESOURCE_DIR, "icon.png")
ICO_FILE = Path(RESOURCE_DIR, "icon.ico")
MESSAGE = {
    "default":          ["Drag and drop your image file into the window"],
    "success":          ["Voilà!"],
    "format_error":     ["No data", "No data detected or unsupported format"],
    "suffix_error":     ["Unsupported format"],
    "clipboard":        ["Copied to clipboard"],
    "update":           ["A new version is available, click here to download"],
    "export":           ["The TXT file has been generated"],
    "alongside":        ["The TXT file has been generated alongside the image"],
    "txt_select":       ["The TXT file has been generated in the selected directory"],
    "remove":           ["A new image file has been generated"],
    "suffix":           ["A new image file with suffix has been generated"],
    "overwrite":        ["A new image file has overwritten the original image"],
    "remove_select":    ["A new image file has been generated in the selected directory"],
}
DEFAULT_GRAY = "#8E8E93"
ACCESSIBLE_GRAY = ("#6C6C70", "#AEAEB2")
TOOLTIP_DELAY = 1.5
