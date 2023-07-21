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

from sd_prompt_reader.image_data_reader import ImageDataReader
from tkinterdnd2.TkinterDnD import DnDEvent

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

        self.bind_all("<KeyPress-Shift_L>", lambda: self.test(), add="+")
        self.bind_all("<KeyPress-Left>", self.move, add="+")
        self.bind_all("<KeyPress-Right>", self.move, add="+")

    def test(self, event=None):
        print("test")

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
        label = CTkLabel(self, text="", image=image, compound="left", padx=5, anchor="w")
        button = CTkButton(self, text="", image=image, width=100, height=100, fg_color="transparent")
        if self.command is not None:
            button.configure(command=lambda: self.display(image))
        label.grid(row=len(self.label_list), column=0, pady=(0, 10), sticky="w")
        button.grid(row=0, column=len(self.button_list), pady=(0, 10), padx=5)
        self.label_list.append(label)
        self.button_list.append(button)

    def remove_item(self, item):
        for label, button in list(zip(self.label_list, self.button_list)):
            if item == label.cget("text"):
                label.destroy()
                button.destroy()
                self.label_list.remove(label)
                self.button_list.remove(button)
                return

    def clear_item(self):
        print(self.button_list)
        for label, button in list(zip(self.label_list, self.button_list)):
            print(button)
            label.destroy()
            button.destroy()
            self.label_list.remove(label)
            self.button_list.remove(button)


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

        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_rowconfigure(2, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_columnconfigure(2, weight=1)

        # single image view
        self.image_label = CTkLabel(self.parent, width=560, text=MESSAGE["drop"][0],
                                    image=self.drop_image, compound="top", text_color=ACCESSIBLE_GRAY)

        self.image_label.bind("<Button-1>", lambda e: self.display_info(select_image(self.file_path),
                                                                        is_selected=True))
        self.image_label.grid(row=1, column=1)

        # gallery view
        self.images = []

        # self.image_frame = customtkinter.CTkLabel(master=self, width=500, height=500,text="")
        # self.image_frame.grid(row=0,column=3)

        # create scrollable label and button frame
        # current_dir = os.path.dirname(os.path.abspath(__file__))
        self.gallery_viewer = GalleryViewer(master=self.parent, width=560, height=300,
                                            # command=self.label_button_frame_event,
                                            corner_radius=0,
                                            images=self.images,
                                            orientation="horizontal")

    def add_image(self, image_list):
        print(len(self.images))
        for i in image_list:
            self.images.append(CTkImage(Image.open(i), size=(100, 100)))
        self.images[0].configure(size=(300, 300))
        for i in range(len(image_list)):  # add items with images
            self.gallery_viewer.add_item(f"image and item {i}", image=self.images[i % len(self.images)])
            if i == 1:
                self.gallery_viewer.button_list[0]._clicked()
            self.parent.update_idletasks()
        self.gallery_viewer.grid(row=1, column=0, padx=0, pady=0, sticky="nsew")
        self.image_label.grid_forget()

    def clear_image(self):
        print(len(self.images))
        self.gallery_viewer.clear_item()
        self.images = []
        # self.image_label.grid(row=1, column=1)

    def read_dir(self, event, is_selected=False):
        path_list = []
        file_list = []
        # selected by filedialog or open with
        if is_selected:
            if event == "":
                return
            path_list = Path(event)
        # dnd
        elif isinstance(event, DnDEvent):
            # preprocessing for extracting bracketed paths
            path_raw = " " + event.data + " "

            # dir with curly brackets
            bracket_pattern = r"\s\{(.*?)\}\s"
            path_list = re.findall(bracket_pattern, path_raw)
            if path_list:
                for p in path_list:
                    path_raw = path_raw.replace("{" + p + "}", "")

            # dir separated by space
            space_pattern = r"(?<!\\)\s"
            path_list += map(lambda x: x.replace("\\", ""), re.split(space_pattern, path_raw))
            path_list = list(map(lambda x: Path(x), filter(None, path_list)))

        # get all files in path list
        for p in path_list:
            if p.is_file():
                file_list.append(p)
            elif p.is_dir():
                file_list += get_images(p)

        print(len(file_list))
        for e in file_list:
            with open(e, "rb") as f:
                image_data = ImageDataReader(f)
                print(image_data.setting)
        self.clear_image()
        self.add_image(file_list)
