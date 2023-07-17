# -*- encoding:utf-8 -*-
__author__ = 'receyuki'
__filename__ = 'image_viewer.py'
__copyright__ = 'Copyright 2023'
__email__ = 'receyuki@gmail.com'

import os
import re

from customtkinter import CTkScrollableFrame, StringVar, CTkButton, CTk, CTkLabel, CTkImage, filedialog
from PIL import Image
import sys

from sd_prompt_reader.constants import *
from sd_prompt_reader.utility import get_images, select_image


class GalleryViewer(CTkScrollableFrame):
    def __init__(self, master, images, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.command = command
        self.radiobutton_variable = StringVar()
        self.label_list = []
        self.button_list = []
        self.images = images
        self.index = 0

        self.bind_all("<KeyPress-Shift_L>", lambda: self.aaaa(), add="+")
        self.bind_all("<KeyPress-Left>", self.move, add="+")
        self.bind_all("<KeyPress-Right>", self.move, add="+")

    def aaaa(self, event=None):
        print("aaaa")

    def move(self, event):
        print(event)
        if event.keysym == "Right":
            self.index = self.index + 1
            self._parent_canvas.xview("scroll", 30, "units")
        else:
            self.index = self.index - 1
            self._parent_canvas.xview("scroll", -30, "units")
        if len(self.button_list) > 0:
            self.button_list[self.index]._clicked()

    def display(self, image):
        for i in self.images:
            if i.cget("size") != (100, 100):
                i.configure(size=(100, 100))
        image.configure(size=(300, 300))

    def add_item(self, item, image=None):
        # label = customtkinter.CTkLabel(self, text=item, image=image, compound="left", padx=5, anchor="w")
        button = CTkButton(self, text="", image=image, width=100, height=100, fg_color="transparent")
        if self.command is not None:
            button.configure(command=lambda: self.display(image))
        # label.grid(row=len(self.label_list), column=0, pady=(0, 10), sticky="w")
        button.grid(row=0, column=len(self.button_list), pady=(0, 10), padx=5)
        # self.label_list.append(label)
        self.button_list.append(button)

    def remove_item(self, item):
        for label, button in zip(self.label_list, self.button_list):
            if item == label.cget("text"):
                label.destroy()
                button.destroy()
                self.label_list.remove(label)
                self.button_list.remove(button)
                return

    def _mouse_wheel_all(self, event):
        if self.check_if_master_is_canvas(event.widget):
            if sys.platform.startswith("win"):
                if self._parent_canvas.xview() != (0.0, 1.0):
                    self._parent_canvas.xview("scroll", -int(event.delta / 6), "units")

            elif sys.platform == "darwin":
                if self._parent_canvas.xview() != (0.0, 1.0):
                    self._parent_canvas.xview("scroll", -event.delta, "units")

            else:
                if self._parent_canvas.xview() != (0.0, 1.0):
                    self._parent_canvas.xview("scroll", -event.delta, "units")


class ImageViewer:
    def __init__(self, parent, display_info, status_bar):
        self.drop_image = CTkImage(Image.open(DROP_FILE), size=(48, 48))
        self.parent = parent
        self.display_info = display_info
        self.file_path = None

        self.image_label = CTkLabel(self.parent, width=560, text=MESSAGE["drop"][0],
                                    image=self.drop_image, compound="top", text_color=ACCESSIBLE_GRAY)

        self.image_label.bind("<Button-1>", lambda e: self.display_info(select_image(self.file_path),
                                                                        is_selected=True))
        self.image_label.pack(fill="both", expand=True)

        # # gallery view
        # images = []
        # for i in get_images("./tests/performance_test_select/"):
        #     images.append(CTkImage(Image.open(i), size=(100, 100)))
        # print(len(images))
        # # self.image_frame = customtkinter.CTkLabel(master=self, width=500, height=500,text="")
        # # self.image_frame.grid(row=0,column=3)
        #
        # # create scrollable label and button frame
        # current_dir = os.path.dirname(os.path.abspath(__file__))
        # self.gallery_viewer = GalleryViewer(master=parent, width=560, height=300,
        #                                     command=self.label_button_frame_event,
        #                                     corner_radius=0,
        #                                     images=images,
        #                                     orientation="horizontal")
        #
        # self.gallery_viewer.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
        # images[0].configure(size=(300, 300))
        # for i in range(10):  # add items with images
        #     self.gallery_viewer.add_item(f"image and item {i}", image=images[i % len(images)])
        #     if i == 1:
        #         self.gallery_viewer.button_list[0]._clicked()
        #     parent.update_idletasks()

