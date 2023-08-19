# -*- encoding:utf-8 -*-
__author__ = 'receyuki'
__filename__ = 'prompt_viewer.py'
__copyright__ = 'Copyright 2023'
__email__ = 'receyuki@gmail.com'

from sd_prompt_reader.button import STkButton, SortMode, ViewMode
from sd_prompt_reader.constants import *
from sd_prompt_reader.ctk_tooltip import CTkToolTip
from sd_prompt_reader.textbox import STkTextbox
from sd_prompt_reader.utility import load_icon, copy_to_clipboard

from customtkinter import CTkFrame


class PromptViewer:
    def __init__(self, parent, status_bar, default_text):
        self.clipboard_image = load_icon(COPY_FILE_L, (24, 24))
        self.clipboard_image_s = load_icon(COPY_FILE_S, (20, 20))
        self.sort_image = load_icon(SORT_FILE, (20, 20))
        self.view_image = load_icon(LIGHTBULB_FILE, (20, 20))

        self.status_bar = status_bar

        self.prompt_box = STkTextbox(parent, wrap="word", height=120)
        # self.prompt_box.grid(row=0, column=1, columnspan=6, sticky="news", padx=(0, 20), pady=(20, 20))
        self.prompt_box.text = default_text

        self.button_frame = CTkFrame(self.prompt_box, fg_color="transparent")
        self.button_frame.grid(row=0, column=1, padx=(20, 10), pady=(5, 0))
        self.button_copy = STkButton(self.button_frame, width=BUTTON_WIDTH_S, height=BUTTON_HEIGHT_S,
                                     image=self.clipboard_image_s, text="",
                                     command=lambda: copy_to_clipboard(self.status_bar, self.prompt_box.text))
        self.button_copy.pack(side="top")
        self.button_copy_tooltip = CTkToolTip(self.button_copy, delay=TOOLTIP_DELAY,
                                              message=TOOLTIP["copy_prompt"])
        self.button_sort = STkButton(self.button_frame, width=BUTTON_WIDTH_S, height=BUTTON_HEIGHT_S,
                                     image=self.sort_image, text="",
                                     command=lambda: self.mode_switch(self.button_sort,
                                                                      self.prompt_box),
                                     mode=SortMode.OFF)
        self.button_sort.pack(side="top", pady=10)
        self.button_sort_tooltip = CTkToolTip(self.button_sort, delay=TOOLTIP_DELAY,
                                              message=TOOLTIP["sort"])
        self.button_view = STkButton(self.button_frame, width=BUTTON_WIDTH_S, height=BUTTON_HEIGHT_S,
                                     image=self.view_image, text="",
                                     command=lambda: self.mode_switch(self.button_view,
                                                                      self.prompt_box,
                                                                      sort_button=self.button_sort),
                                     mode=ViewMode.NORMAL)
        self.button_view.pack(side="top")
        self.button_view_tooltip = CTkToolTip(self.button_view, delay=TOOLTIP_DELAY,
                                              message=TOOLTIP["view_prompt"])

        # sdxl
        self.prompt_box = STkTextbox(parent, wrap="word", height=120)
        # self.prompt_box.grid(row=0, column=1, columnspan=6, sticky="news", padx=(0, 20), pady=(20, 20))
        self.prompt_box.text = default_text

        self.button_frame = CTkFrame(self.prompt_box, fg_color="transparent")
        self.button_frame.grid(row=0, column=1, padx=(20, 10), pady=(5, 0))
        self.button_copy = STkButton(self.button_frame, width=BUTTON_WIDTH_S, height=BUTTON_HEIGHT_S,
                                     image=self.clipboard_image_s, text="",
                                     command=lambda: copy_to_clipboard(self.status_bar, self.prompt_box.text))
        self.button_copy.pack(side="top")
        self.button_copy_tooltip = CTkToolTip(self.button_copy, delay=TOOLTIP_DELAY,
                                              message=TOOLTIP["copy_prompt"])
        self.button_sort = STkButton(self.button_frame, width=BUTTON_WIDTH_S, height=BUTTON_HEIGHT_S,
                                     image=self.sort_image, text="",
                                     command=lambda: self.mode_switch(self.button_sort,
                                                                      self.prompt_box),
                                     mode=SortMode.OFF)
        self.button_sort.pack(side="top", pady=10)
        self.button_sort_tooltip = CTkToolTip(self.button_sort, delay=TOOLTIP_DELAY,
                                              message=TOOLTIP["sort"])
        self.button_view = STkButton(self.button_frame, width=BUTTON_WIDTH_S, height=BUTTON_HEIGHT_S,
                                     image=self.view_image, text="",
                                     command=lambda: self.mode_switch(self.button_view,
                                                                      self.prompt_box,
                                                                      sort_button=self.button_sort),
                                     mode=ViewMode.NORMAL)
        self.button_view.pack(side="top")
        self.button_view_tooltip = CTkToolTip(self.button_view, delay=TOOLTIP_DELAY,
                                              message=TOOLTIP["view_prompt"])


    def edit_on(self):
        self.prompt_box.edit_on()

    def edit_off(self):
        self.prompt_box.edit_off()

    def text(self, text=None):
        if text:
            self.prompt_box.text = text
        else:
            return self.prompt_box.ctext

    def mode_switch(self, button: STkButton, textbox: STkTextbox, sort_button: STkButton = None):
        if isinstance(button.mode, ViewMode):
            match button.mode:
                case ViewMode.NORMAL:
                    button.switch_on()
                    button.mode = ViewMode.VERTICAL
                    textbox.view_vertical()
                    if sort_button:
                        match sort_button.mode:
                            case SortMode.ASC:
                                textbox.sort_asc()
                            case SortMode.DES:
                                textbox.sort_des()
                    self.status_bar.info(MESSAGE["view_prompt"][0])
                case ViewMode.VERTICAL:
                    button.switch_off()
                    button.mode = ViewMode.NORMAL
                    textbox.view_normal()
                    if sort_button:
                        match sort_button.mode:
                            case SortMode.ASC:
                                textbox.sort_asc()
                            case SortMode.DES:
                                textbox.sort_des()
                    self.status_bar.info(MESSAGE["view_prompt"][-1])
        elif isinstance(button.mode, SortMode):
            match button.mode:
                case SortMode.OFF:
                    button.switch_on()
                    button.mode = SortMode.ASC
                    textbox.sort_asc()
                    self.status_bar.info(MESSAGE["sort"][0])
                case SortMode.ASC:
                    button.switch_on()
                    button.mode = SortMode.DES
                    textbox.sort_des()
                    self.status_bar.info(MESSAGE["sort"][1])
                case SortMode.DES:
                    button.switch_off()
                    button.mode = SortMode.OFF
                    textbox.sort_off()
                    self.status_bar.info(MESSAGE["sort"][-1])
