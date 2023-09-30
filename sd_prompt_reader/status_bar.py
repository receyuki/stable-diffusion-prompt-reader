__author__ = "receyuki"
__filename__ = "status_bar.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import webbrowser

from PIL import Image
from customtkinter import CTkImage, CTkFrame, CTkLabel, LEFT

from .constants import *


class StatusBar:
    def __init__(self, parent):
        self.info_image = self.load_status_icon(INFO_FILE)
        self.error_image = self.load_status_icon(ERROR_FILE)
        self.warning_image = self.load_status_icon(WARNING_FILE)
        self.ok_image = self.load_status_icon(OK_FILE)
        self.available_updates_image = self.load_status_icon(UPDATE_FILE)

        self.status_frame = CTkFrame(parent)
        self.status_label = CTkLabel(
            self.status_frame,
            width=230,
            height=STATUS_BAR_HEIGHT,
            text=MESSAGE["default"][0],
            text_color=ACCESSIBLE_GRAY,
            wraplength=190,
            image=self.info_image,
            compound="left",
        )
        self.status_label.pack(side=LEFT, expand=True)

    # append space to the right of status icon
    def load_status_icon(self, file):
        # margin right 35/24*96-96=30
        return CTkImage(self.add_margin(Image.open(file), 0, 0, 0, 44), size=(35, 24))

    def warning(self, message):
        self.status_label.configure(image=self.error_image, text=message)

    def success(self, message):
        self.status_label.configure(image=self.ok_image, text=message)

    def info(self, message):
        self.status_label.configure(image=self.info_image, text=message)

    def clipboard(self):
        self.status_label.configure(image=self.ok_image, text=MESSAGE["clipboard"][0])

    def export(self, export_mode: str):
        match export_mode:
            case "alongside the image file":
                self.info(MESSAGE["alongside"][0])
            case "select directory":
                self.info(MESSAGE["txt_select"][0])

    def remove(self, remove_mode: str):
        match remove_mode:
            case "add suffix":
                self.info(MESSAGE["suffix"][0])
            case "overwrite the original image":
                self.info(MESSAGE["overwrite"][0])
            case "select directory":
                self.info(MESSAGE["remove_select"][0])

    def update(self, download_url):
        self.status_label.configure(
            image=self.available_updates_image, text=MESSAGE["update"][0]
        )
        self.status_label.bind(
            "<Button-1>", lambda e: webbrowser.open_new(download_url)
        )

    def stop_update(self):
        self.status_label.unbind("<Button-1>")

    @staticmethod
    def add_margin(img, top, bottom, left, right):
        width, height = img.size
        new_width = width + right + left
        new_height = height + top + bottom
        result = Image.new(img.mode, (new_width, new_height))
        result.paste(img, (left, top))
        return result
