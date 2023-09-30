__author__ = "receyuki"
__filename__ = "image_viewer.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import re
import threading
from datetime import datetime

from customtkinter import (
    CTkScrollableFrame,
    StringVar,
    CTkButton,
    CTk,
    CTkLabel,
    CTkImage,
    filedialog,
    ThemeManager,
    CTkFrame,
    CTkOptionMenu,
)
from PIL import Image
import sys

from .image_data_reader import ImageDataReader
from tkinterdnd2.TkinterDnD import DnDEvent

from .constants import *
from .button import STkButton
from .utility import (
    load_icon,
    get_images,
    select_image,
    get_canvas_total_size,
    ease_out,
    ease_in,
    ease_in_out,
)


class GalleryViewer:
    def __init__(
        self, master, parent, images, display, width, height, command=None, **kwargs
    ):
        self.viewer_frame = CTkFrame(master, width, height, fg_color=BUTTON_HOVER)
        self.lightbox = self.Lightbox(self.viewer_frame, self)
        self.button_bar = self.ButtonBar(master, self, fg_color="transparent")

        self.thumbnail_carousel = self.ThumbnailCarousel(
            self.viewer_frame,
            parent,
            images,
            display,
            self.lightbox,
            width=width,
            height=70,
            command=command,
            **kwargs
        )
        # self.lightbox.image_frame.grid(row=0, column=0, pady=5)
        # self.thumbnail_carousel.grid(row=1, column=0)
        self.lightbox.image_frame.pack(side="top", fill="both", pady=5)
        self.thumbnail_carousel.pack(side="top", fill="x")
        self.button_bar.pack(side="bottom", fill="x", pady=5)

        self.fullscreen_image = None

    class Lightbox:
        def __init__(self, master, parent):
            self.left_image = load_icon(LEFT_FILE_L, (48, 48))
            self.right_image = load_icon(RIGHT_FILE_L, (48, 48))
            self.image = None
            self.image_frame = CTkFrame(master)

            self.image_frame.rowconfigure(tuple(range(3)), weight=1)
            self.image_frame.columnconfigure(tuple(range(5)), weight=1)
            self.image_frame.columnconfigure(0, weight=3)
            self.image_frame.columnconfigure(5, weight=3)
            self.image_frame.rowconfigure(1, weight=6)

            self.left_button = STkButton(
                self.image_frame,
                width=48,
                height=48,
                image=self.left_image,
                text="",
                hover_color=BUTTON_HOVER_TOP,
            )
            self.right_button = STkButton(
                self.image_frame,
                width=48,
                height=48,
                image=self.right_image,
                text="",
                hover_color=BUTTON_HOVER_TOP,
            )
            self.image_label = CTkLabel(
                self.image_frame,
                width=330,
                height=330,
                text="",
                # image=self.icon_image,
                compound="top",
                text_color=INACCESSIBLE_GRAY,
            )

            self.label_names = [
                "format_label",
                "file_size_label",
                "size_label",
                "time_label",
                "name_label",
            ]

            self.format_label = CTkLabel(
                self.image_frame,
                text="",
                compound="left",
                padx=5,
                anchor="w",
                fg_color=BUTTON_HOVER_TOP,
                corner_radius=5,
            )
            self.file_size_label = CTkLabel(
                self.image_frame,
                text="",
                compound="left",
                padx=5,
                anchor="w",
                fg_color=BUTTON_HOVER_TOP,
                corner_radius=5,
            )
            self.size_label = CTkLabel(
                self.image_frame,
                text="",
                compound="left",
                padx=5,
                anchor="w",
                fg_color=BUTTON_HOVER_TOP,
                corner_radius=5,
            )
            self.time_label = CTkLabel(
                self.image_frame,
                text="",
                compound="left",
                padx=5,
                anchor="w",
                fg_color=BUTTON_HOVER_TOP,
                corner_radius=5,
            )
            self.name_label = CTkLabel(
                self.image_frame,
                text="",
                compound="left",
                padx=5,
                anchor="w",
                fg_color=BUTTON_HOVER_TOP,
                corner_radius=5,
            )

            self.file_size_label.grid(row=0, column=1, padx=2, pady=5)
            self.size_label.grid(row=0, column=2, padx=2, pady=5)
            self.time_label.grid(row=0, column=3, padx=2, pady=5)
            self.name_label.grid(row=2, column=1, columnspan=3, pady=5)

            self.image_label.grid(row=1, column=1, columnspan=3)
            self.left_button.grid(row=0, column=0, rowspan=3, sticky="sn")
            self.right_button.grid(row=0, column=5, rowspan=3, sticky="sn")

        def select(self, item, image):
            self.image = CTkImage(image, size=item.size_l)
            self.image_label.configure(image=self.image)
            self.file_size_label.configure(text=item.size_str)
            self.size_label.configure(text=item.file_size)
            self.time_label.configure(text=item.time)
            self.name_label.configure(text=item.name)

    class ThumbnailCarousel(CTkScrollableFrame):
        def __init__(
            self, master, parent, images, display, lightbox, command=None, **kwargs
        ):
            super().__init__(master, **kwargs)
            self.lightbox = lightbox
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

            self.bind_all("<KeyPress-Shift_L>", lambda: self.test(), add="+")
            self.bind_all("<KeyPress-Left>", self.move, add="+")
            self.bind_all("<KeyPress-Right>", self.move, add="+")

            self.total_width = 0
            self.display_thread = None

        def test(self, event=None):
            print("test")

        def move(self, event):
            print(event)
            print(len(self.button_list))
            current_x = self._parent_canvas.xview()
            last_x = current_x[0]
            if event.keysym == "Right" and self.index < (len(self.button_list) - 1):
                # self.index += 1
                # self._parent_canvas.xview("scroll", 30, "units")
                # while moved_step < ((self.index * 130 + 15) / self.total_width):
                #     moved_step += 0.005
                #     self._parent_canvas.xview_moveto(moved_step)
                #     self.after(1)
                #     self.update_idletasks()
                self.button_list[self.index + 1]._clicked()
                # self._parent_canvas.xview_moveto(((self.index-1) * 130 + 15) / self.total_width)
                # self.after(1)
                # self.update_idletasks()
                x_change = (((self.index - 1) * 130 + 15) / self.total_width) - last_x
                steps = int(abs(x_change) / 0.01)
                print(steps)
                for t in range(steps):
                    current_x = ease_in_out(t, last_x, x_change, steps)
                    self._parent_canvas.xview_moveto(current_x)
                    self.update_idletasks()
                    self.after(1)

            elif event.keysym == "Left" and self.index > 0:
                x_change = (((self.index - 2) * 130 + 15) / self.total_width) - last_x
                steps = int(abs(x_change) / 0.01)
                print(last_x, x_change)
                for t in range(steps):
                    current_x = ease_in_out(t, last_x, x_change, steps)
                    self._parent_canvas.xview_moveto(current_x)
                    self.update_idletasks()
                    self.after(1)
                self.button_list[self.index - 1]._clicked()
                # self.index -= 1
                # self._parent_canvas.xview_moveto(((self.index - 2) * 130 + 15) / self.total_width)
                # self._parent_canvas.xview("scroll", -30, "units")
                # self.after(1)
                # self.update_idletasks()

            # self.parent.update_idletasks()
            print(self.index)

        def select(self, item, image):
            # self.display(None)
            print(self.index)
            if self.index == item.index and not self.init:
                return

            for button in self.button_list:
                button.configure(fg_color="transparent")

            self.button_list[item.index].configure(fg_color=BUTTON_HOVER_TOP)

            self.lightbox.select(item, image)
            # self.label_list[item.index]["file_size_label"].grid(row=0, column=1, padx=2, pady=(0, 10))
            #
            # self.label_list[item.index]["name_label"].grid(row=3, column=0, columnspan=4, pady=(10, 0))
            #
            # self.label_list[item.index]["size_label"].grid(row=0, column=2, padx=2, pady=(0, 10))
            #
            # self.label_list[item.index]["time_label"].grid(row=0, column=3, padx=2, pady=(0, 10))
            # self.update_idletasks()
            # self.after(1)

            # label_conf = [
            #     lambda: self.label_list[item.index]["file_size_label"].configure(
            #         text=item.file_size, fg_color=BUTTON_HOVER
            #     ),
            #     lambda: self.label_list[item.index]["size_label"].configure(
            #         text=item.size_str, fg_color=BUTTON_HOVER
            #     ),
            #     lambda: self.label_list[item.index]["time_label"].configure(
            #         text=item.time, fg_color=BUTTON_HOVER
            #     ),
            #     lambda: self.label_list[item.index]["name_label"].configure(
            #         text=item.name, fg_color=BUTTON_HOVER
            #     ),
            # ]
            #
            # label_grid = [
            #     lambda: self.label_list[item.index]["file_size_label"].grid(
            #         row=0, column=1, padx=2, pady=(0, 10)
            #     ),
            #     lambda: self.label_list[item.index]["size_label"].grid(
            #         row=0, column=2, padx=2, pady=(0, 10)
            #     ),
            #     lambda: self.label_list[item.index]["time_label"].grid(
            #         row=0, column=3, padx=2, pady=(0, 10)
            #     ),
            #     lambda: self.label_list[item.index]["name_label"].grid(
            #         row=3, column=0, columnspan=4, pady=(10, 0)
            #     ),
            # ]
            #
            # if not self.init:
            #     for label in self.label_names:
            #         self.label_list[self.index][label].configure(
            #             text="", fg_color="transparent"
            #         )

            ease_step = 6
            # for t in range(ease_step):
            #     # if not self.init and t > 2:
            #     #     self.label_list[self.index][self.label_names[t-3]].configure(text="", fg_color="transparent")
            #     # if t > 2:
            #     #     label_conf[t-3]()
            #     #     self.update_idletasks()
            #     #     self.after(1)
            #     # label_grid[t-3]()
            #     # self.update_idletasks()
            #     # self.after(1)
            #
            #     current_size = (
            #         int(
            #             ease_out(
            #                 t,
            #                 item.size_s[0],
            #                 item.size_l[0] - item.size_s[0],
            #                 ease_step,
            #             )
            #         ),
            #         int(
            #             ease_out(
            #                 t,
            #                 item.size_s[1],
            #                 item.size_l[1] - item.size_s[1],
            #                 ease_step,
            #             )
            #         ),
            #     )
            #     image.configure(size=current_size)
            #
            #     frame_width = int(ease_out(t, 120, 320 - 120, ease_step))
            #     #
            #     # self.button_list[item.index].configure(width=frame_width)
            #     self.frame_list[item.index].configure(width=frame_width)
            #
            #     if not self.init:
            #         last_item = self.item_list[self.index]
            #         last_item_current_size = (
            #             int(
            #                 ease_out(
            #                     t,
            #                     last_item.size_l[0],
            #                     last_item.size_s[0] - last_item.size_l[0],
            #                     ease_step,
            #                 )
            #             ),
            #             int(
            #                 ease_out(
            #                     t,
            #                     last_item.size_l[1],
            #                     last_item.size_s[1] - last_item.size_l[1],
            #                     ease_step,
            #                 )
            #             ),
            #         )
            #         self.button_list[self.index].cget("image").configure(
            #             size=last_item_current_size
            #         )
            #
            #         last_frame_width = int(ease_out(t, 320, 120 - 320, ease_step))
            #
            #         self.button_list[self.index].configure(width=last_frame_width)
            #         self.frame_list[self.index].configure(width=last_frame_width)
            #
            #     self.update_idletasks()
            #     self.after(1)

            # while current_size[0] < item.size_l[0]:
            #     current_size = (int(current_size[0]), int(current_size[1] * 1.3))
            #     image.configure(size=current_size)
            #     self.update_idletasks()
            #     self.after(1)
            # image.configure(size=item.size_l)
            # self.button_list[item.index].configure(width=320, height=320)
            # self.frame_list[item.index].configure(width=320, height=400)
            # self.update_idletasks()
            # self.after(1)
            # print(item.name)
            # print(item.format)
            # print(item.size_str)
            # print(item.time)
            # self.label_list[item.index]["format_label"].grid(row=0, column=0, padx=2, pady=(0, 10))
            # self.label_list[item.index]["file_size_label"].grid(row=0, column=1, padx=2, pady=(0, 10))
            #
            # self.label_list[item.index]["name_label"].grid(row=3, column=0, columnspan=4, pady=(10, 0))
            # self.update_idletasks()
            # self.after(1)
            # self.label_list[item.index]["size_label"].grid(row=0, column=2, padx=2, pady=(0, 10))
            # self.update_idletasks()
            # self.after(1)
            # self.label_list[item.index]["time_label"].grid(row=0, column=3, padx=2, pady=(0, 10))
            # self.update_idletasks()
            # self.after(1)

            # for e in label_conf:
            #     e()
            self.update_idletasks()
            self.after(1)

            # if not self.init:
            #     for label in self.label_names:
            #         self.label_list[self.index][label].grid_forget()

            # unselect
            if self.init:
                self.init = False
                return

            # self.button_list[self.index].configure(width=120, height=120)
            # self.frame_list[self.index].configure(width=120, height=400)

            # self.update_idletasks()
            # self.after(1)
            # current_size_old = self.button_list[self.index].cget("image").cget("size")
            # old_item = self.item_list[self.index]

            # for t in range(6):
            #     # current_size_old = (int(ease_out(t, old_item.size_l[0], old_item.size_s[0] - old_item.size_l[0], 6)),
            #     #                     int(ease_out(t, old_item.size_l[1], old_item.size_s[1] - old_item.size_l[1], 6)))
            #     # current_size_old = (int(current_size_old[0] * 0.8), int(current_size_old[1] * 0.8))
            #     # self.button_list[self.index].cget("image").configure(size=current_size_old)
            #     self.update_idletasks()
            #     self.after(1)

            # while current_size_old[0] > self.item_list[self.index].size_s[0]:
            #
            #     current_size_old = (int(current_size_old[0] * 0.8), int(current_size_old[1] * 0.8))
            #     self.button_list[self.index].cget("image").configure(size=current_size_old)
            #     self.update_idletasks()
            #     self.after(1)
            # self.button_list[self.index].cget("image").configure(
            #     size=self.item_list[self.index].size_s
            # )

            self.index = item.index
            self.after(1)
            self.update_idletasks()
            if self.display_thread:
                self.display_thread.join()
            self.display_thread = threading.Thread(target=self.display(item.path))
            self.display_thread.start()

        def add_item(self, item, image=None):
            frame = CTkFrame(self, fg_color="transparent", width=70, height=70)

            frame.grid_rowconfigure(0, weight=1)
            # frame.grid_rowconfigure(1, weight=1)
            frame.grid_rowconfigure(2, weight=1)

            # format_label = CTkLabel(frame, text=item.format, compound="left", padx=5, anchor="w", fg_color=BUTTON_HOVER,
            #                         corner_radius=5)
            # file_size_label = CTkLabel(frame, text=item.file_size, compound="left", padx=5, anchor="w",
            #                            fg_color=BUTTON_HOVER,
            #                            corner_radius=5)
            # size_label = CTkLabel(frame, text=item.size_str, compound="left", padx=5, anchor="w", fg_color=BUTTON_HOVER,
            #                       corner_radius=5)
            # time_label = CTkLabel(frame, text=item.time, compound="left", padx=5, anchor="w", fg_color=BUTTON_HOVER,
            #                       corner_radius=5)
            # name_label = CTkLabel(frame, text=item.name, compound="left", padx=5, anchor="w", fg_color=BUTTON_HOVER,
            #                       corner_radius=5)
            # format_label = CTkLabel(
            #     frame,
            #     text="",
            #     compound="left",
            #     padx=5,
            #     anchor="w",
            #     fg_color="transparent",
            #     corner_radius=5,
            # )
            # file_size_label = CTkLabel(
            #     frame,
            #     text="",
            #     compound="left",
            #     padx=5,
            #     anchor="w",
            #     fg_color="transparent",
            #     corner_radius=5,
            # )
            # size_label = CTkLabel(
            #     frame,
            #     text="",
            #     compound="left",
            #     padx=5,
            #     anchor="w",
            #     fg_color="transparent",
            #     corner_radius=5,
            # )
            # time_label = CTkLabel(
            #     frame,
            #     text="",
            #     compound="left",
            #     padx=5,
            #     anchor="w",
            #     fg_color="transparent",
            #     corner_radius=5,
            # )
            # name_label = CTkLabel(
            #     frame,
            #     text="",
            #     compound="left",
            #     padx=5,
            #     anchor="w",
            #     fg_color="transparent",
            #     corner_radius=5,
            # )
            #
            # file_size_label.grid(row=0, column=1, padx=2, pady=(0, 10)),
            # size_label.grid(row=0, column=2, padx=2, pady=(0, 10)),
            # time_label.grid(row=0, column=3, padx=2, pady=(0, 10)),
            # name_label.grid(row=3, column=0, columnspan=4, pady=(10, 0))
            ctk_image = CTkImage(image, size=item.size_s)
            button = CTkButton(
                frame,
                text="",
                image=ctk_image,
                width=70,
                height=70,
                border_spacing=0,
                fg_color="transparent",
            )
            # if self.command is not None:
            #
            button.configure(command=lambda: self.select(item, image))

            frame.grid(row=0, column=len(self.button_list), pady=5, padx=0, sticky="ew")
            button.grid(row=1, column=0, columnspan=4, pady=0, padx=0, sticky="ns")

            # if len(self.item_list) == 1:
            #     self.total_width = 320
            # else:
            #     self.total_width += 120

            # labels = [format_label, file_size_label, size_label, time_label, name_label]
            # label_dict = dict(zip(self.label_names, labels))
            #
            # self.label_list.append(label_dict)
            self.frame_list.append(frame)
            self.item_list.append(item)
            self.button_list.append(button)
            self.after(1)
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
            for button, label, frame, item in list(
                zip(self.button_list, self.label_list, self.frame_list, self.item_list)
            ):
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
            self.total_width = 0

        def _mouse_wheel_all(self, event):
            if self.check_if_master_is_canvas(event.widget):
                if sys.platform.startswith("win"):
                    if self._parent_canvas.xview() != (0.0, 1.0):
                        self._parent_canvas.xview(
                            "scroll", -int(event.delta / 6), "units"
                        )

                elif sys.platform == "darwin":
                    if self._parent_canvas.xview() != (0.0, 1.0):
                        self._parent_canvas.xview("scroll", -event.delta, "units")

                else:
                    if self._parent_canvas.xview() != (0.0, 1.0):
                        self._parent_canvas.xview("scroll", -event.delta, "units")

    class ButtonBar(CTkFrame):
        def __init__(self, master, parent, **kwargs):
            super().__init__(master, **kwargs)
            self.batch_image = load_icon(BATCH_FILE, (24, 24))
            self.filter_image = load_icon(FILTER_FILE, (24, 24))
            self.sort_image = load_icon(SORT_LIST_FILE, (24, 24))
            self.clear_image = load_icon(CLEAR_LIST_FILE, (24, 24))
            self.fullscreen_image = load_icon(FULLSCREEN_FILE, (24, 24))
            self.left_image = load_icon(LEFT_FILE_S, (24, 24))
            self.right_image = load_icon(RIGHT_FILE_S, (24, 24))
            self.fullscreen_image = load_icon(FULLSCREEN_FILE, (24, 24))

            self.parent = parent

            self.batch_button = STkButton(
                self,
                width=BUTTON_WIDTH_L,
                height=BUTTON_HEIGHT_L,
                image=self.batch_image,
                text="",
            )
            self.filter_button = STkButton(
                self,
                width=BUTTON_WIDTH_L,
                height=BUTTON_HEIGHT_L,
                image=self.filter_image,
                text="",
            )
            self.sort_button = STkButton(
                self,
                width=BUTTON_WIDTH_L,
                height=BUTTON_HEIGHT_L,
                image=self.sort_image,
                text="",
            )
            self.clear_button = STkButton(
                self,
                width=BUTTON_WIDTH_L,
                height=BUTTON_HEIGHT_L,
                image=self.clear_image,
                text="",
            )
            self.fullscreen_image = STkButton(
                self,
                width=BUTTON_WIDTH_L,
                height=BUTTON_HEIGHT_L,
                image=self.fullscreen_image,
                text="",
                command=lambda: self.fullscreen(),
            )
            self.left_button = STkButton(
                self,
                width=BUTTON_WIDTH_L,
                height=BUTTON_HEIGHT_L,
                image=self.left_image,
                text="",
            )
            self.right_image = STkButton(
                self,
                width=BUTTON_WIDTH_L,
                height=BUTTON_HEIGHT_L,
                image=self.right_image,
                text="",
            )
            self.page_select = STkButton(
                self,
                width=BUTTON_WIDTH_L,
                height=BUTTON_HEIGHT_L,
                text="1",
                fg_color=BUTTON_HOVER,
                command=lambda: self.select_page(),
            )
            self.page_dropdown = CTkOptionMenu(
                self,
                width=BUTTON_WIDTH_L,
                height=BUTTON_HEIGHT_L,
                values=["1", "2", "3"],
                command=self.page_dropdown_callback,
            )
            self.load_counter_label = CTkLabel(
                self,
                text="1 - 10 of 100",
                padx=10,
                anchor="center",
            )

            self.columnconfigure(tuple(range(9)), weight=1)
            self.columnconfigure(8, weight=3)

            self.batch_button.grid(row=0, column=0, sticky="w")
            self.filter_button.grid(row=0, column=1, sticky="w")
            self.sort_button.grid(row=0, column=2, sticky="w")
            self.clear_button.grid(row=0, column=3, sticky="w")

            self.left_button.grid(row=0, column=4)
            self.page_select.grid(row=0, column=5)
            self.right_image.grid(row=0, column=6)

            self.fullscreen_image.grid(row=0, column=7, sticky="e")
            self.load_counter_label.grid(row=0, column=8, sticky="e")

        def select_page(self):
            self.page_dropdown._dropdown_menu.open(
                self.page_select.winfo_rootx(),
                self.page_select.winfo_rooty()
                + self.page_select._apply_widget_scaling(
                    self.page_select._current_height + 0
                ),
            )

        def page_dropdown_callback(self, choice):
            self.page_select.configure(text=choice)

        def fullscreen(self):
            print(
                self.parent.thumbnail_carousel.item_list[
                    self.parent.thumbnail_carousel.index
                ].path
            )
            self.parent.fullscreen_display(
                self.parent.thumbnail_carousel.item_list[
                    self.parent.thumbnail_carousel.index
                ].path
            )

    def fullscreen_display(self, file_path):
        image_window = CTk()
        image_window.title("Image Viewer")
        screen_width = image_window.winfo_screenwidth()
        screen_height = image_window.winfo_screenheight()

        f = Image.open(file_path)
        self.fullscreen_image = CTkImage(f, size=(screen_height, screen_height))

        panel = CTkLabel(image_window, text="aaaaa", image=self.fullscreen_image)
        panel.image = self.fullscreen_image
        panel.pack()


class ImageViewer:
    def __init__(self, parent, update_idletasks, display_info, status_bar):
        self.drop_image = CTkImage(Image.open(DROP_FILE), size=(48, 48))
        self.icon_image = CTkImage(Image.open(ICON_FILE), size=(128, 128))
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
        self.image_label = CTkLabel(
            self.parent,
            width=560,
            text="\n" + MESSAGE["drop"][0],
            image=self.icon_image,
            compound="top",
            text_color=ACCESSIBLE_GRAY,
        )

        self.image_label.bind(
            "<Button-1>",
            lambda e: self.display_info(select_image(self.file_path)),
        )
        # self.image_label.grid(row=1, column=1)

        # gallery view

        # self.image_frame = customtkinter.CTkLabel(master=self, width=500, height=500,text="")
        # self.image_frame.grid(row=0,column=3)

        # create scrollable label and button frame
        # current_dir = os.path.dirname(os.path.abspath(__file__))
        self.gallery_viewer = GalleryViewer(
            master=self.parent,
            width=560,
            height=450,
            command=self.single_image,
            corner_radius=0,
            images=self.images,
            orientation="horizontal",
            parent=self.parent,
            display=self.display_info,
        )
        self.gallery_viewer.lightbox.image_label.bind(
            "<Button-1>",
            lambda e: self.display_info(select_image(self.file_path)),
        )
        self.gallery_viewer.viewer_frame.pack(fill="both", expand=True)

    def single_image(self, file):
        self.image_label.grid(row=1, column=1)
        self.gallery_viewer.viewer_frame.grid_forget()
        # if isinstance(file, CTkImage) or file.suffix == ".txt":
        self.display_info(file)
        # else:
        #     self.images.append(CTkImage(Image.open(file), size=(100, 100)))

        self.parent.configure(fg_color=ThemeManager.theme["CTkFrame"]["fg_color"])

    def multi_image(self, image_list):
        self.status_bar.info("Loading images")
        # self.gallery_viewer.update_idletasks()
        self.gallery_viewer.viewer_frame.pack(fill="both", expand=True)
        self.image_label.grid_forget()
        self.parent.configure(fg_color="transparent")
        self.gallery_viewer.thumbnail_carousel.update_idletasks()
        self.gallery_viewer.thumbnail_carousel.after(1)

        for i in range(len(image_list)):  # add items with images
            with Image.open(image_list[i]) as f:
                image_info = self.ImageInfo(
                    index=i, path=image_list[i], size=f.size, file_format=f.format
                )
                f.thumbnail(image_info.size_l)
                # if f.width >= f.height:
                #     size_s = (100, int(f.height / f.width * 100))
                # elif f.width < f.height:
                #     size_s = (int(f.width / f.height * 100), 100)
                # size_l = tuple(3 * n for n in size_s)

                self.images.append(f)
                self.gallery_viewer.thumbnail_carousel.add_item(
                    image_info, image=self.images[i]
                )
                if i == 0:
                    self.gallery_viewer.thumbnail_carousel.button_list[0]._clicked()
                self.gallery_viewer.thumbnail_carousel.update_idletasks()
                self.gallery_viewer.thumbnail_carousel.after(1)

        self.gallery_viewer.thumbnail_carousel._parent_canvas.xview_moveto(0)
        self.status_bar.success(str(len(image_list)) + " images loaded")

        self.gallery_viewer.total_width = get_canvas_total_size(
            self.gallery_viewer.thumbnail_carousel._parent_canvas
        )[0]
        print(self.gallery_viewer.thumbnail_carousel.frame_list[0])

    def clear_image(self):
        print(len(self.images))
        self.gallery_viewer.thumbnail_carousel.clear_item()
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
            path_list += map(
                lambda x: x.replace("\\", ""), re.split(space_pattern, path_raw)
            )
            path_list = list(map(lambda x: Path(x), filter(None, path_list)))

        # for e in self.file_list:
        #     with open(e, "rb") as f:
        #         image_data = ImageDataReader(f)
        #         print(image_data.setting)
        self.clear_image()

        if len(path_list) == 1 and path_list[0].is_file():
            self.single_image(path_list[0])
        else:
            # get all files in path list
            for p in path_list:
                print(p)
                if p.is_file() and p.suffix in SUPPORTED_FORMATS + [".txt"]:
                    self.file_list.append(p)
                elif p.is_dir():
                    self.file_list += get_images(p)
            print(self.file_list)
            self.multi_image(self.file_list)

    class ImageInfo:
        def __init__(self, index, path, size, file_format):
            self.index = index
            self.path = path
            self.size = size
            self.file_size = (
                "{:.2f}".format(
                    max(round(path.stat().st_size / (KILO * KILO), 2), 0.01)
                )
                + " MB"
            )
            self.format = file_format
            self.time = str(
                datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            )
            if size[0] >= size[1]:
                self.size_s = (THUMBNAIL_SIZE, int(size[1] / size[0] * THUMBNAIL_SIZE))
            elif size[0] < size[1]:
                self.size_s = (int(size[0] / size[1] * THUMBNAIL_SIZE), THUMBNAIL_SIZE)
            self.size_l = (self.size_s[0] * 5, self.size_s[1] * 5)
            self.size_str = str(size[0]) + "×" + str(size[1])
            if len(path.name) > 30:
                self.name = path.name[:29] + "..."
            else:
                self.name = path.name
