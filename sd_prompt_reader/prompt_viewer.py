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

from customtkinter import CTkFrame, CTkLabel


class PromptViewer:
    def __init__(self, parent, status_bar, default_text):
        self.status_bar = status_bar
        self.default_text = default_text
        self.is_sdxl = False

        self.viewer_frame = CTkFrame(parent, fg_color="transparent")

        self.prompt_frame = CTkFrame(self.viewer_frame, fg_color="transparent")
        self.prompt_frame.pack(fill="both", expand=True)
        self.prompt_box = self.PromptBox(self, self.prompt_frame)
        self.prompt_box.textbox.pack(fill="both", expand=True)

        self.prompt_frame_sdxl = CTkFrame(self.viewer_frame, fg_color="transparent")
        self.prompt_box_g = self.PromptBox(self, self.prompt_frame_sdxl, "Clip G")
        self.prompt_box_l = self.PromptBox(self, self.prompt_frame_sdxl, "Clip L")
        self.prompt_box_refiner = self.PromptBox(self, self.prompt_frame_sdxl, "Refiner")
        self.prompt_box_g.textbox.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.prompt_box_l.textbox.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.prompt_box_refiner.textbox.pack(side="left", fill="both", expand=True)

    def edit_on(self):
        if not self.is_sdxl:
            self.prompt_box.textbox.edit_on()
            self.prompt_box.button_view.disable()
            self.prompt_box.button_sort.disable()
        else:
            self.prompt_box_g.textbox.edit_on()
            self.prompt_box_l.textbox.edit_on()
            self.prompt_box_refiner.textbox.edit_on()

            self.prompt_box_g.button_view.disable()
            self.prompt_box_g.button_sort.disable()
            self.prompt_box_l.button_view.disable()
            self.prompt_box_l.button_sort.disable()
            self.prompt_box_refiner.button_view.disable()
            self.prompt_box_refiner.button_sort.disable()

    def edit_off(self):
        if not self.is_sdxl:
            self.prompt_box.textbox.edit_off()
            self.prompt_box.button_view.enable()
            self.prompt_box.button_sort.enable()
        else:
            self.prompt_box_g.textbox.edit_off()
            self.prompt_box_l.textbox.edit_off()
            self.prompt_box_refiner.textbox.edit_off()

            self.prompt_box_g.button_view.enable()
            self.prompt_box_g.button_sort.enable()
            self.prompt_box_l.button_view.enable()
            self.prompt_box_l.button_sort.enable()
            self.prompt_box_refiner.button_view.enable()
            self.prompt_box_refiner.button_sort.enable()

    def copy_on(self):
        if not self.is_sdxl:
            self.prompt_box.button_copy.enable()
        else:
            self.prompt_box_g.button_copy.enable()
            self.prompt_box_l.button_copy.enable()
            self.prompt_box_refiner.button_copy.enable()

    def copy_off(self):
        if not self.is_sdxl:
            self.prompt_box.button_copy.disable()
        else:
            self.prompt_box_g.button_copy.disable()
            self.prompt_box_l.button_copy.disable()
            self.prompt_box_refiner.button_copy.disable()

    def all_off(self):
        if not self.is_sdxl:
            self.prompt_box.button_copy.disable()
            self.prompt_box.button_view.disable()
            self.prompt_box.button_sort.disable()
        else:
            self.prompt_box_g.button_copy.disable()
            self.prompt_box_g.button_view.disable()
            self.prompt_box_g.button_sort.disable()
            self.prompt_box_g.button_copy.disable()
            self.prompt_box_l.button_view.disable()
            self.prompt_box_l.button_sort.disable()
            self.prompt_box_refiner.button_copy.disable()
            self.prompt_box_refiner.button_view.disable()
            self.prompt_box_refiner.button_sort.disable()

    def all_on(self):
        if not self.is_sdxl:
            self.prompt_box.button_copy.enable()
            self.prompt_box.button_view.enable()
            self.prompt_box.button_sort.enable()
        else:
            self.prompt_box_g.button_copy.enable()
            self.prompt_box_g.button_view.enable()
            self.prompt_box_g.button_sort.enable()
            self.prompt_box_g.button_copy.enable()
            self.prompt_box_l.button_view.enable()
            self.prompt_box_l.button_sort.enable()
            self.prompt_box_refiner.button_copy.enable()
            self.prompt_box_refiner.button_view.enable()
            self.prompt_box_refiner.button_sort.enable()

    def text(self, text=None):
        if not self.is_sdxl:
            if text:
                self.prompt_box.textbox.text = text
            else:
                return self.prompt_box.textbox.ctext
        else:
            # TODO
            if text:
                self.prompt_box.textbox.text = text
            else:
                return self.prompt_box.textbox.ctext

    def mode_update(self):
        if not self.is_sdxl:
            self.prompt_box.mode_update()
        else:
            self.prompt_box_g.mode_update()
            self.prompt_box_l.mode_update()
            self.prompt_box_refiner.mode_update()

    def display(self, prompt):
        if isinstance(prompt, str):
            self.prompt_frame_sdxl.pack_forget()

            self.prompt_frame.pack(fill="both", expand=True)
            self.text(prompt)
        elif isinstance(prompt, dict):
            self.prompt_frame.pack_forget()

            self.prompt_frame_sdxl.pack(fill="both", expand=True)
            self.prompt_box_g.textbox.text = prompt.get("Clip G")
            self.prompt_box_l.textbox.text = prompt.get("Clip L")
            if prompt.get("Refiner"):
                self.prompt_box_refiner.textbox.pack(side="left", fill="both", expand=True)
                self.prompt_box_refiner.textbox.text = prompt.get("Refiner")
            else:
                self.prompt_box_refiner.textbox.pack_forget()
        #TODO edit&text

    class PromptBox:
        def __init__(self, prompt_viewer, frame, prompt_type=None):
            self.clipboard_image = load_icon(COPY_FILE_L, (24, 24))
            self.clipboard_image_s = load_icon(COPY_FILE_S, (20, 20))
            self.sort_image = load_icon(SORT_FILE, (20, 20))
            self.view_image = load_icon(LIGHTBULB_FILE, (20, 20))

            self.default_text = prompt_viewer.default_text
            self.status_bar = prompt_viewer.status_bar
            self.textbox = STkTextbox(frame, wrap="word", height=120)
            # self.prompt_box.grid(row=0, column=1, columnspan=6, sticky="news", padx=(0, 20), pady=(20, 20))
            self.textbox.text = self.default_text

            if prompt_type:
                self.button_frame = CTkFrame(self.textbox, fg_color="transparent")
                self.button_frame.grid(row=1, column=0, rowspan=2, padx=(10, 0), pady=5, sticky="news")

                self.prompt_label = CTkLabel(self.button_frame, height=BUTTON_HEIGHT_S, text=prompt_type)
                self.prompt_label.pack(side="left", padx=(5, 0))
                self.button_copy = STkButton(self.button_frame, width=BUTTON_WIDTH_S, height=BUTTON_HEIGHT_S,
                                             image=self.clipboard_image_s, text="",
                                             command=lambda: copy_to_clipboard(self.status_bar, self.textbox.text))
                self.button_copy.pack(side="left", padx=(5, 0))
                self.button_copy_tooltip = CTkToolTip(self.button_copy, delay=TOOLTIP_DELAY,
                                                      message=TOOLTIP["copy_prompt"])

                self.button_sort = STkButton(self.button_frame, width=BUTTON_WIDTH_S, height=BUTTON_HEIGHT_S,
                                             image=self.sort_image, text="",
                                             command=lambda: self.mode_switch(self.button_sort),
                                             mode=SortMode.OFF)
                self.button_sort.pack(side="left", padx=(5, 0))
                self.button_sort_tooltip = CTkToolTip(self.button_sort, delay=TOOLTIP_DELAY,
                                                      message=TOOLTIP["sort"])
                self.button_view = STkButton(self.button_frame, width=BUTTON_WIDTH_S, height=BUTTON_HEIGHT_S,
                                             image=self.view_image, text="",
                                             command=lambda: self.mode_switch(self.button_view,
                                                                              sort_button=self.button_sort),
                                             mode=ViewMode.NORMAL)
                self.button_view.pack(side="left", padx=(5, 0))
                self.button_view_tooltip = CTkToolTip(self.button_view, delay=TOOLTIP_DELAY,
                                                      message=TOOLTIP["view_prompt"])

            else:
                self.button_frame = CTkFrame(self.textbox, fg_color="transparent")
                self.button_frame.grid(row=0, column=1, padx=(20, 10), pady=(5, 0))
                self.button_copy = STkButton(self.button_frame, width=BUTTON_WIDTH_S, height=BUTTON_HEIGHT_S,
                                             image=self.clipboard_image_s, text="",
                                             command=lambda: copy_to_clipboard(self.status_bar, self.textbox.text))
                self.button_copy.pack(side="top")
                self.button_copy_tooltip = CTkToolTip(self.button_copy, delay=TOOLTIP_DELAY,
                                                      message=TOOLTIP["copy_prompt"])
                self.button_sort = STkButton(self.button_frame, width=BUTTON_WIDTH_S, height=BUTTON_HEIGHT_S,
                                             image=self.sort_image, text="",
                                             command=lambda: self.mode_switch(self.button_sort),
                                             mode=SortMode.OFF)
                self.button_sort.pack(side="top", pady=10)
                self.button_sort_tooltip = CTkToolTip(self.button_sort, delay=TOOLTIP_DELAY,
                                                      message=TOOLTIP["sort"])
                self.button_view = STkButton(self.button_frame, width=BUTTON_WIDTH_S, height=BUTTON_HEIGHT_S,
                                             image=self.view_image, text="",
                                             command=lambda: self.mode_switch(self.button_view,
                                                                              sort_button=self.button_sort),
                                             mode=ViewMode.NORMAL)
                self.button_view.pack(side="top")
                self.button_view_tooltip = CTkToolTip(self.button_view, delay=TOOLTIP_DELAY,
                                                      message=TOOLTIP["view_prompt"])

        def mode_switch(self, button: STkButton, sort_button: STkButton = None):
            if isinstance(button.mode, ViewMode):
                match button.mode:
                    case ViewMode.NORMAL:
                        button.switch_on()
                        button.mode = ViewMode.VERTICAL
                        self.textbox.view_vertical()
                        if sort_button:
                            match sort_button.mode:
                                case SortMode.ASC:
                                    self.textbox.sort_asc()
                                case SortMode.DES:
                                    self.textbox.sort_des()
                        self.status_bar.info(MESSAGE["view_prompt"][0])
                    case ViewMode.VERTICAL:
                        button.switch_off()
                        button.mode = ViewMode.NORMAL
                        self.textbox.view_normal()
                        if sort_button:
                            match sort_button.mode:
                                case SortMode.ASC:
                                    self.textbox.sort_asc()
                                case SortMode.DES:
                                    self.textbox.sort_des()
                        self.status_bar.info(MESSAGE["view_prompt"][-1])
            elif isinstance(button.mode, SortMode):
                match button.mode:
                    case SortMode.OFF:
                        button.switch_on()
                        button.mode = SortMode.ASC
                        self.textbox.sort_asc()
                        self.status_bar.info(MESSAGE["sort"][0])
                    case SortMode.ASC:
                        button.switch_on()
                        button.mode = SortMode.DES
                        self.textbox.sort_des()
                        self.status_bar.info(MESSAGE["sort"][1])
                    case SortMode.DES:
                        button.switch_off()
                        button.mode = SortMode.OFF
                        self.textbox.sort_off()
                        self.status_bar.info(MESSAGE["sort"][-1])

        def mode_update(self):
            match self.button_view.mode:
                case ViewMode.NORMAL:
                    match self.button_sort.mode:
                        case SortMode.ASC:
                            self.textbox.sort_asc()
                        case SortMode.DES:
                            self.textbox.sort_des()
                case ViewMode.VERTICAL:
                    self.textbox.view_vertical()
                    match self.button_sort.mode:
                        case SortMode.ASC:
                            self.textbox.sort_asc()
                        case SortMode.DES:
                            self.textbox.sort_des()
