# -*- encoding:utf-8 -*-
__author__ = 'receyuki'
__filename__ = 'status_bar.py'
__copyright__ = 'Copyright 2023, '
__email__ = 'receyuki@gmail.com'

from PIL import Image
from customtkinter import CTkImage, CTkFrame, CTkLabel, LEFT

from sd_prompt_reader.constants import *


class StatusBar:
    def __init__(self, ):
        self.info_image = self.load_status_icon(INFO_FILE)
        self.error_image = self.load_status_icon(ERROR_FILE)
        self.box_important_image = self.load_status_icon(BOX_IMPORTANT_FILE)
        self.ok_image = self.load_status_icon(OK_FILE)
        self.available_updates_image = self.load_status_icon(AVAILABLE_UPDATES_FILE)

        self.status = "Drag and drop your file into the window"
        self.status_frame = CTkFrame(self, height=50)
        self.status_frame.grid(row=3, column=4, columnspan=2, sticky="ew", padx=20, pady=(0, 20), ipadx=5, ipady=5)
        self.status_label = CTkLabel(self.status_frame, height=50, text=self.status, text_color="gray", wraplength=130,
                                     image=self.info_image, compound="left")
        self.status_label.pack(side=LEFT, expand=True)

    def load_status_icon(self, file):
        return CTkImage(self.add_margin(Image.open(file), 0, 0, 0, 33), size=(40, 30))


    def warning(self, message):
        self.status_label.configure(image=self.box_important_image,
                                    text=message[-1])

    def ok(self):
        self.status_label.configure(image=self.ok_image,
                                    text=MESSAGE["success"])

    def clipboard(self):
        self.status_label.configure(image=self.ok_image, text="Copied to clipboard")

    def update(self):
        self.status_label.configure(image=self.update_image,
                                    text="A new version is available, click here to download")

    @staticmethod
    def add_margin(img, top, bottom, left, right):
        width, height = img.size
        new_width = width + right + left
        new_height = height + top + bottom
        result = Image.new(img.mode, (new_width, new_height))
        result.paste(img, (left, top))
        return result
