__author__ = "receyuki"
__filename__ = "constants.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

from importlib import resources
from pathlib import Path
from . import resources as res

RELEASE_URL = "https://api.github.com/repos/receyuki/stable-diffusion-prompt-reader/releases/latest"
RESOURCE_DIR = str(resources.files(res))
SUPPORTED_FORMATS = [".png", ".jpg", ".jpeg", ".webp"]
COLOR_THEME = Path(RESOURCE_DIR, "gray.json")
INFO_FILE = Path(RESOURCE_DIR, "info_24.png")
ERROR_FILE = Path(RESOURCE_DIR, "error_24.png")
WARNING_FILE = Path(RESOURCE_DIR, "warning_24.png")
OK_FILE = Path(RESOURCE_DIR, "check_circle_24.png")
UPDATE_FILE = Path(RESOURCE_DIR, "update_24.png")
DROP_FILE = Path(RESOURCE_DIR, "place_item_48.png")
COPY_FILE_L = (
    Path(RESOURCE_DIR, "content_copy_24.png"),
    Path(RESOURCE_DIR, "content_copy_24_alpha.png"),
)
COPY_FILE_S = (
    Path(RESOURCE_DIR, "content_copy_20.png"),
    Path(RESOURCE_DIR, "content_copy_20_alpha.png"),
)
CLEAR_FILE = (Path(RESOURCE_DIR, "mop_24.png"), Path(RESOURCE_DIR, "mop_24_alpha.png"))
DOCUMENT_FILE = (
    Path(RESOURCE_DIR, "description_24.png"),
    Path(RESOURCE_DIR, "description_24_alpha.png"),
)
EXPAND_FILE = (
    Path(RESOURCE_DIR, "expand_more_24.png"),
    Path(RESOURCE_DIR, "expand_more_24_alpha.png"),
)
EDIT_FILE = (Path(RESOURCE_DIR, "edit_24.png"), Path(RESOURCE_DIR, "edit_24_alpha.png"))
EDIT_OFF_FILE = (
    Path(RESOURCE_DIR, "edit_off_24.png"),
    Path(RESOURCE_DIR, "edit_off_24_alpha.png"),
)
LIGHTBULB_FILE = (
    Path(RESOURCE_DIR, "lightbulb_20.png"),
    Path(RESOURCE_DIR, "lightbulb_20_alpha.png"),
)
SAVE_FILE = (Path(RESOURCE_DIR, "save_24.png"), Path(RESOURCE_DIR, "save_24_alpha.png"))
SORT_FILE = (
    Path(RESOURCE_DIR, "sort_by_alpha_20.png"),
    Path(RESOURCE_DIR, "sort_by_alpha_20_alpha.png"),
)
VIEW_SEPARATE_FILE = (
    Path(RESOURCE_DIR, "view_week_20.png"),
    Path(RESOURCE_DIR, "view_week_20_alpha.png"),
)
VIEW_TAB_FILE = (
    Path(RESOURCE_DIR, "view_sidebar_20.png"),
    Path(RESOURCE_DIR, "view_sidebar_20_alpha.png"),
)
ICON_FILE = Path(RESOURCE_DIR, "icon.png")
ICO_FILE = Path(RESOURCE_DIR, "icon.ico")
MESSAGE = {
    "drop": ["Drop image here or click to select"],
    "default": ["Drag and drop your image file into the window"],
    "success": ["Voilà!"],
    "format_error": ["", "No data detected or unsupported format"],
    "suffix_error": ["Unsupported format"],
    "clipboard": ["Copied to the clipboard"],
    "update": ["A new version is available, click here to download"],
    "export": ["The TXT file has been generated"],
    "alongside": ["The TXT file has been generated alongside the image"],
    "txt_select": ["The TXT file has been generated in the selected directory"],
    "remove": ["A new image file has been generated"],
    "suffix": ["A new image file with suffix has been generated"],
    "overwrite": ["A new image file has overwritten the original image"],
    "remove_select": ["A new image file has been generated in the selected directory"],
    "txt_error": [
        "Importing TXT file is only allowed in edit mode",
        "unsupported TXT format",
    ],
    "txt_imported": ["The TXT file has been successfully imported"],
    "edit": ["Edit mode", "View mode"],
    "sort": ["Ascending order", "Descending order", "Original order"],
    "view_prompt": ["Vertical orientation", "Horizontal orientation"],
    "view_setting": ["Simple mode", "Normal mode"],
}
TOOLTIP = {
    "edit": "Edit image metadata",
    "save": "Save edited image",
    "clear": "Remove metadata from the image",
    "export": "Export metadata to a TXT file",
    "copy_raw": "Copy raw metadata to the clipboard",
    "copy_prompt": "Copy prompt to the clipboard",
    "copy_setting": "Copy setting to the clipboard",
    "sort": "Sort prompt lines in ascending or descending order",
    "view_prompt": "View prompt in vertical orientation",
    "view_setting": "View setting in simple mode",
    "view_separate": "View Clip G, Clip L and Refiner prompt in separate textbox",
    "view_tab": "View Clip G, Clip L and Refiner prompt in one textbox",
}
DEFAULT_GRAY = "#8E8E93"
ACCESSIBLE_GRAY = ("#6C6C70", "#AEAEB2")
INACCESSIBLE_GRAY = ("gray60", "gray45")
EDITABLE = ("gray10", "#DCE4EE")
BUTTON_HOVER = ("gray86", "gray17")
TOOLTIP_DELAY = 1.5
BUTTON_WIDTH_L = 40
BUTTON_HEIGHT_L = 40
BUTTON_WIDTH_S = 36
BUTTON_HEIGHT_S = 36
LABEL_HEIGHT = 20
ARROW_WIDTH_L = 28
STATUS_BAR_IPAD = 5
PARAMETER_WIDTH = 280
STATUS_BAR_HEIGHT = BUTTON_HEIGHT_L + LABEL_HEIGHT - STATUS_BAR_IPAD * 2
PARAMETER_PLACEHOLDER = "                    "
