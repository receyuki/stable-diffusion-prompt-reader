# -*- encoding:utf-8 -*-
__author__ = 'receyuki'
__filename__ = 'image_viewer.py'
__copyright__ = 'Copyright 2023'
__email__ = 'receyuki@gmail.com'

import re
from datetime import datetime

from customtkinter import CTkScrollableFrame, StringVar, CTkButton, CTk, CTkLabel, CTkImage, filedialog, ThemeManager, \
    CTkFrame
from PIL import Image
import sys

from sd_prompt_reader.image_data_reader import ImageDataReader
from tkinterdnd2.TkinterDnD import DnDEvent

from sd_prompt_reader.constants import *
from sd_prompt_reader.utility import get_images, select_image


class GalleryViewer(CTkScrollableFrame):
    def __init__(self, master, parent, images, display, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.command = command
        self.display = display
        self.radiobutton_variable = StringVar()
        self.frame_list = []
        self.label_list = []
        self.button_list = []
        self.item_list = []
        self.images = images
        self.index = 0
        self.parent = parent
        self.init = True
        self.label_names = ["format_label", "file_size_label", "size_label", "time_label", "name_label"]

        self.bind_all("<KeyPress-Shift_L>", lambda: self.test(), add="+")
        self.bind_all("<KeyPress-Left>", self.move, add="+")
        self.bind_all("<KeyPress-Right>", self.move, add="+")

    def test(self, event=None):
        print("test")

    def move(self, event):
        print(event)
        print(len(self.button_list))
        if event.keysym == "Right" and self.index < (len(self.button_list) - 1):
            # self.index += 1
            self._parent_canvas.xview("scroll", 30, "units")
            self.button_list[self.index + 1]._clicked()
        elif event.keysym == "Left" and self.index > 0:
            # self.index -= 1
            self._parent_canvas.xview("scroll", -30, "units")
            self.button_list[self.index - 1]._clicked()
        # self.parent.update_idletasks()
        print(self.index)

    def select(self, item, image):
        print(self.index)
        if self.index == item.index and not self.init:
            return
        self.button_list[item.index].configure(width=300, height=300)
        image.configure(size=item.size_l)
        print(item)
        self.display(item.path)
        self.update_idletasks()
        # print(item.name)
        # print(item.format)
        # print(item.size_str)
        # print(item.time)
        self.label_list[item.index]["format_label"].grid(row=0, column=0, padx=2, pady=(0, 10))
        self.label_list[item.index]["file_size_label"].grid(row=0, column=1, padx=2, pady=(0, 10))
        self.label_list[item.index]["size_label"].grid(row=0, column=2, padx=2, pady=(0, 10))
        self.label_list[item.index]["time_label"].grid(row=0, column=3, padx=2, pady=(0, 10))
        self.label_list[item.index]["name_label"].grid(row=3, column=0, columnspan=4, pady=(10, 0))
        # self.update_idletasks()
        # unselect
        if self.init:
            self.init = False
            return

        self.button_list[self.index].configure(width=100, height=100)
        self.button_list[self.index].cget("image").configure(size=self.item_list[self.index].size_s)
        for label in self.label_names:
            self.label_list[self.index][label].grid_forget()
        # self.update_idletasks()
        self.index = item.index

    def add_item(self, item, image=None):
        frame = CTkFrame(self, fg_color="transparent")
        format_label = CTkLabel(frame, text=item.format, compound="left", padx=5, anchor="w", fg_color=BUTTON_HOVER,
                                corner_radius=5)
        file_size_label = CTkLabel(frame, text=item.file_size, compound="left", padx=5, anchor="w",
                                   fg_color=BUTTON_HOVER,
                                   corner_radius=5)
        size_label = CTkLabel(frame, text=item.size_str, compound="left", padx=5, anchor="w", fg_color=BUTTON_HOVER,
                              corner_radius=5)
        time_label = CTkLabel(frame, text=item.time, compound="left", padx=5, anchor="w", fg_color=BUTTON_HOVER,
                              corner_radius=5)
        name_label = CTkLabel(frame, text=item.name, compound="left", padx=5, anchor="w", fg_color=BUTTON_HOVER,
                              corner_radius=5)
        button = CTkButton(frame, text="", image=image, width=100, height=100, fg_color="transparent")
        # if self.command is not None:
        #
        button.configure(command=lambda: self.select(item, image))

        frame.grid(row=0, column=len(self.button_list), pady=10, padx=5)
        button.grid(row=1, column=0, columnspan=4, pady=0, padx=0)

        labels = [format_label, file_size_label, size_label, time_label, name_label]
        label_dict = dict(zip(self.label_names, labels))

        self.label_list.append(label_dict)
        self.frame_list.append(frame)
        self.item_list.append(item)
        self.button_list.append(button)
        self.update_idletasks()

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
        # for label, button in list(zip(self.label_list, self.button_list)):
        for button, label, frame, item in list(zip(self.button_list, self.label_list, self.frame_list, self.item_list)):
            print(button)
            for label_name in self.label_names:
                label[label_name].destroy()
            button.destroy()
            frame.destroy()
            self.button_list.remove(button)
            self.label_list.remove(label)
            self.frame_list.remove(frame)
            self.item_list.remove(item)
        self.frame_list = []
        self.label_list = []
        self.item_list = []
        self.images = []
        self.button_list = []
        print(self.button_list)
        self.index = 0
        self.init = True

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

        #TODO 微调移动量


class ImageViewer:
    def __init__(self, parent, update_idletasks, display_info, status_bar):
        self.drop_image = CTkImage(Image.open(DROP_FILE), size=(48, 48))
        self.parent = parent
        self.display_info = display_info
        self.file_path = None
        self.images = []
        self.file_list = []
        self.update_idletasks = update_idletasks
        self.status_bar = status_bar

        self.parent.grid_rowconfigure(0, weight=1)
        self.parent.grid_rowconfigure(1, weight=1)
        self.parent.grid_rowconfigure(2, weight=1)
        self.parent.grid_columnconfigure(0, weight=1)
        self.parent.grid_columnconfigure(1, weight=1)
        self.parent.grid_columnconfigure(2, weight=1)

        # single image view
        self.image_label = CTkLabel(self.parent, width=560, text=MESSAGE["drop"][0],
                                    image=self.drop_image, compound="top", text_color=ACCESSIBLE_GRAY)

        self.image_label.bind("<Button-1>", lambda e: self.display_info(select_image(self.file_path),
                                                                        is_selected=True))
        self.image_label.grid(row=1, column=1)
        # self.image_label.pack(fill="both", expand=True)

        # gallery view

        # self.image_frame = customtkinter.CTkLabel(master=self, width=500, height=500,text="")
        # self.image_frame.grid(row=0,column=3)

        # create scrollable label and button frame
        # current_dir = os.path.dirname(os.path.abspath(__file__))
        self.gallery_viewer = GalleryViewer(master=self.parent, width=560, height=450,
                                            command=self.single_image,
                                            corner_radius=0,
                                            images=self.images,
                                            orientation="horizontal",
                                            parent=self.parent,
                                            display=self.display_info)

    def single_image(self, file):
        self.image_label.grid(row=1, column=1)
        self.gallery_viewer.grid_forget()
        # if isinstance(file, CTkImage) or file.suffix == ".txt":
        self.display_info(file)
        # else:
        #     self.images.append(CTkImage(Image.open(file), size=(100, 100)))

        self.parent.configure(fg_color=ThemeManager.theme["CTkFrame"]["fg_color"])

    def multi_image(self, image_list):
        # self.status_bar.warning("loading")
        # self.gallery_viewer.update_idletasks()
        for i in range(len(image_list)):  # add items with images
            with Image.open(image_list[i]) as f:
                image_info = self.ImageInfo(index=i, path=image_list[i], size=f.size, file_format=f.format)
                # if f.width >= f.height:
                #     size_s = (100, int(f.height / f.width * 100))
                # elif f.width < f.height:
                #     size_s = (int(f.width / f.height * 100), 100)
                # size_l = tuple(3 * n for n in size_s)
                if i == 0:
                    self.images.append(CTkImage(f, size=image_info.size_l))
                else:
                    self.images.append(CTkImage(f, size=image_info.size_s))
                self.gallery_viewer.add_item(image_info, image=self.images[i])
                self.gallery_viewer.update_idletasks()
        self.gallery_viewer.button_list[0]._clicked()
        self.gallery_viewer.grid(row=0, column=0, columnspan=3, padx=0, pady=0, sticky="nsew")
        self.image_label.grid_forget()
        self.parent.configure(fg_color="transparent")

    def clear_image(self):
        print(len(self.images))
        self.gallery_viewer.clear_item()
        self.images = []
        # self.image_label.grid(row=1, column=1)

    def read_dir(self, event, is_selected=False):
        path_list = []
        self.file_list = []
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

        for e in self.file_list:
            with open(e, "rb") as f:
                image_data = ImageDataReader(f)
                print(image_data.setting)
        self.clear_image()

        if len(path_list) == 1:
            self.single_image(path_list[0])
        else:
            # get all files in path list
            for p in path_list:
                if p.is_file() and p.suffix in SUPPORTED_FORMATS + [".txt"]:
                    self.file_list.append(p)
                elif p.is_dir():
                    self.file_list += get_images(p)
            print(len(self.file_list))
            self.multi_image(self.file_list)

    class ImageInfo:
        def __init__(self, index, path, size, file_format):
            self.index = index
            self.path = path
            self.size = size
            self.file_size = "{:.2f}".format(path.stat().st_size / 1000000) + " MB"
            self.format = file_format
            self.time = str(datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d %H:%M'))
            if size[0] >= size[1]:
                self.size_s = (100, int(size[1] / size[0] * 100))
            elif size[0] < size[1]:
                self.size_s = (int(size[0] / size[1] * 100), 100)
            self.size_l = (self.size_s[0] * 3, self.size_s[1] * 3)
            self.size_str = str(size[0]) + "×" + str(size[1])
            if len(path.name) > 30:
                self.name = path.name[:29]+"..."
            else:
                self.name = path.name
