__author__ = "receyuki"
__filename__ = "prompt_viewer.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"


from CTkToolTip import *
from customtkinter import CTkFrame, CTkLabel, ThemeManager

from .button import STkButton, SortMode, ViewMode, PromptMode, EditMode
from .constants import *
from .textbox import STkTextbox
from .utility import load_icon, copy_to_clipboard


class PromptViewer:
    def __init__(self, parent, status_bar, default_text):
        self.clipboard_image = load_icon(COPY_FILE_L, (24, 24))
        self.clipboard_image_s = load_icon(COPY_FILE_S, (20, 20))
        self.sort_image = load_icon(SORT_FILE, (20, 20))
        self.view_image = load_icon(LIGHTBULB_FILE, (20, 20))
        self.separate_image = load_icon(VIEW_SEPARATE_FILE, (20, 20))
        self.tab_image = load_icon(VIEW_TAB_FILE, (20, 20))

        self.status_bar = status_bar
        self.default_text = default_text
        self.is_sdxl = False
        self.parent = parent

        self.viewer_frame = CTkFrame(self.parent, fg_color="transparent")

        self.prompt_frame = CTkFrame(self.viewer_frame, fg_color="transparent")
        self.prompt_frame.pack(fill="both", expand=True)
        self.prompt_box = self.PromptBox(self, self.prompt_frame)
        self.prompt_box.textbox.pack(fill="both", expand=True)

        # SDXL
        self.prompt_box_mode = PromptMode.TAB

        self.prompt_frame_sdxl = CTkFrame(self.viewer_frame, fg_color="transparent")
        self.prompt_box_sdxl = self.PromptBox(self, self.prompt_frame_sdxl, True)
        self.prompt_box_sdxl.textbox.pack(fill="both", expand=True)

        self.prompt_frame_sdxl_separate = CTkFrame(
            self.viewer_frame, fg_color="transparent"
        )
        self.prompt_box_g = self.PromptBox(
            self, self.prompt_frame_sdxl_separate, "Clip G"
        )
        self.prompt_box_l = self.PromptBox(
            self, self.prompt_frame_sdxl_separate, "Clip L"
        )
        self.prompt_box_r = self.PromptBox(
            self, self.prompt_frame_sdxl_separate, "Refiner"
        )
        self.prompt_box_g.textbox.pack(
            side="left", fill="both", expand=True, padx=(0, 10)
        )
        self.prompt_box_l.textbox.pack(
            side="left", fill="both", expand=True, padx=(0, 10)
        )
        self.prompt_box_r.textbox.pack(
            side="left", fill="both", expand=True, padx=(0, 10)
        )

        self.sdxl_button_frame_outer = CTkFrame(
            self.prompt_frame_sdxl_separate,
            fg_color=ThemeManager.theme["CTkTextbox"]["fg_color"],
        )
        self.sdxl_button_frame_outer.pack(side="right", fill="y")
        self.sdxl_button_frame = CTkFrame(
            self.sdxl_button_frame_outer, fg_color="transparent"
        )
        self.sdxl_button_frame.pack(expand=True, padx=10, pady=3)
        self.button_sort = STkButton(
            self.sdxl_button_frame,
            width=BUTTON_WIDTH_S,
            height=BUTTON_HEIGHT_S,
            image=self.sort_image,
            text="",
            command=lambda: self.mode_switch(self.button_sort),
            mode=SortMode.OFF,
        )
        self.button_sort.pack(side="top")
        self.button_sort_tooltip = CTkToolTip(
            self.button_sort, delay=TOOLTIP_DELAY, message=TOOLTIP["sort"]
        )
        self.button_view = STkButton(
            self.sdxl_button_frame,
            width=BUTTON_WIDTH_S,
            height=BUTTON_HEIGHT_S,
            image=self.view_image,
            text="",
            command=lambda: self.mode_switch(
                self.button_view, sort_button=self.button_sort
            ),
            mode=ViewMode.NORMAL,
        )
        self.button_view.pack(side="top", pady=10)
        self.button_view_tooltip = CTkToolTip(
            self.button_view, delay=TOOLTIP_DELAY, message=TOOLTIP["view_prompt"]
        )
        self.prompt_tab_mode = STkButton(
            self.sdxl_button_frame,
            height=BUTTON_HEIGHT_S,
            width=BUTTON_WIDTH_S,
            text="",
            image=self.tab_image,
            command=lambda: self.switch_view(PromptMode.TAB),
        )
        self.prompt_tab_mode.pack(side="top")
        self.prompt_tab_mode_tooltip = CTkToolTip(
            self.prompt_tab_mode, delay=TOOLTIP_DELAY, message=TOOLTIP["view_tab"]
        )

        self.prompt_box_list_sdxl = [
            self.prompt_box_sdxl,
            self.prompt_box_g,
            self.prompt_box_l,
            self.prompt_box_r,
        ]
        self.edit_button_list_sdxl = []
        self.copy_button_list_sdxl = [
            self.prompt_box_sdxl.button_copy,
            self.prompt_box_g.button_copy,
            self.prompt_box_l.button_copy,
            self.prompt_box_r.button_copy,
        ]
        self.all_button_list_non_sdxl = [
            self.prompt_box.button_copy,
            self.prompt_box.button_view,
            self.prompt_box.button_sort,
        ]
        self.all_button_list_sdxl = [
            self.prompt_box_sdxl.button_copy,
            self.prompt_box_sdxl.button_view,
            self.prompt_box_sdxl.button_sort,
            self.prompt_box_g.button_copy,
            self.prompt_box_l.button_copy,
            self.prompt_box_r.button_copy,
            self.button_view,
            self.button_sort,
        ]

    def edit_on(self):
        self.prompt_box.textbox.edit_on()
        self.prompt_box.button_view.disable()
        self.prompt_box.button_sort.disable()

    def edit_off(self):
        self.prompt_box.textbox.edit_off()
        self.prompt_box.button_view.enable()
        self.prompt_box.button_sort.enable()

    def copy_on(self):
        if not self.is_sdxl:
            self.prompt_box.button_copy.enable()
        else:
            for button in self.copy_button_list_sdxl:
                button.enable()

    def copy_off(self):
        if not self.is_sdxl:
            self.prompt_box.button_copy.disable()
        else:
            for button in self.copy_button_list_sdxl:
                button.disable()

    def all_off(self):
        if not self.is_sdxl:
            for button in self.all_button_list_non_sdxl:
                button.disable()
        else:
            for button in self.all_button_list_sdxl:
                button.disable()

    def all_on(self):
        if not self.is_sdxl:
            for button in self.all_button_list_non_sdxl:
                button.enable()
        else:
            for button in self.all_button_list_sdxl:
                button.enable()

    def mode_update(self):
        if not self.is_sdxl:
            self.prompt_box.mode_update()
        else:
            self.prompt_box_sdxl.mode_update()
            self.prompt_box_g.mode_update(self.button_view, self.button_sort)
            self.prompt_box_l.mode_update(self.button_view, self.button_sort)
            self.prompt_box_r.mode_update(self.button_view, self.button_sort)

    def display(self, prompt):
        if isinstance(prompt, str):
            if self.is_sdxl:
                match self.prompt_box_mode:
                    case PromptMode.TAB:
                        self.prompt_frame_sdxl.pack_forget()
                    case PromptMode.SEPARATE:
                        self.prompt_frame_sdxl_separate.pack_forget()
                self.prompt_frame.pack(fill="both", expand=True)
            self.text = prompt or ""
            self.is_sdxl = False
        elif isinstance(prompt, dict):
            if self.parent.button_edit.mode == EditMode.ON:
                self.parent.button_edit.switch_off()
                self.parent.edit_mode_switch()
            # TAB
            self.prompt_box_sdxl.prompt = prompt
            # SEPARATE
            self.prompt_box_g.textbox.text = prompt.get("Clip G") or ""
            self.prompt_box_l.textbox.text = prompt.get("Clip L") or ""
            self.prompt_box_r.textbox.text = prompt.get("Refiner") or ""

            self.prompt_frame.pack_forget()
            match self.prompt_box_mode:
                case PromptMode.TAB:
                    self.prompt_frame_sdxl.pack(fill="both", expand=True)
                case PromptMode.SEPARATE:
                    self.prompt_frame_sdxl_separate.pack(fill="both", expand=True)

            self.is_sdxl = True

    def switch_view(self, mode):
        match mode:
            case PromptMode.SEPARATE:
                self.prompt_frame_sdxl.pack_forget()
                self.prompt_frame_sdxl_separate.pack(fill="both", expand=True)
                self.prompt_box_mode = PromptMode.SEPARATE
            case PromptMode.TAB:
                self.prompt_frame_sdxl_separate.pack_forget()
                self.prompt_frame_sdxl.pack(fill="both", expand=True)
                self.prompt_box_mode = PromptMode.TAB

    def mode_switch(self, button: STkButton, sort_button: STkButton = None):
        self.prompt_box_g.mode_switch(button, sort_button, False)
        self.prompt_box_l.mode_switch(button, sort_button, False)
        self.prompt_box_r.mode_switch(button, sort_button)

    @property
    def text(self):
        return self.prompt_box.textbox.ctext

    @text.setter
    def text(self, text):
        self.prompt_box.textbox.text = text

    class PromptBox:
        def __init__(self, prompt_viewer, frame, sdxl=None):
            self.default_text = prompt_viewer.default_text
            self.status_bar = prompt_viewer.status_bar
            self.textbox = STkTextbox(frame, wrap="word", height=120, width=100)
            self.textbox.text = self.default_text
            self._prompt = None

            if isinstance(sdxl, str):
                self.button_frame = CTkFrame(self.textbox, fg_color="transparent")
                self.button_frame.grid(
                    row=1, column=0, columnspan=2, padx=10, pady=(5, 10), sticky="news"
                )
                self.prompt_label = CTkLabel(
                    self.button_frame, height=BUTTON_HEIGHT_S, text=sdxl
                )
                self.prompt_label.pack(side="left", padx=10)
                self.button_copy = STkButton(
                    self.button_frame,
                    width=BUTTON_WIDTH_S,
                    height=BUTTON_HEIGHT_S,
                    image=prompt_viewer.clipboard_image_s,
                    text="",
                    command=lambda: copy_to_clipboard(
                        self.status_bar, self.textbox.text
                    ),
                )
                self.button_copy.pack(side="right", padx=5)
                self.button_copy_tooltip = CTkToolTip(
                    self.button_copy,
                    delay=TOOLTIP_DELAY,
                    message=TOOLTIP["copy_prompt"],
                )
            else:
                self.button_frame = CTkFrame(self.textbox, fg_color="transparent")
                self.button_frame.grid(
                    row=0, column=1, rowspan=2, padx=(20, 10), pady=(5, 0)
                )
                self.button_copy = STkButton(
                    self.button_frame,
                    width=BUTTON_WIDTH_S,
                    height=BUTTON_HEIGHT_S,
                    image=prompt_viewer.clipboard_image_s,
                    text="",
                    command=lambda: copy_to_clipboard(
                        self.status_bar, self.textbox.text
                    ),
                )
                self.button_copy.pack(side="top")
                self.button_copy_tooltip = CTkToolTip(
                    self.button_copy,
                    delay=TOOLTIP_DELAY,
                    message=TOOLTIP["copy_prompt"],
                )
                self.button_sort = STkButton(
                    self.button_frame,
                    width=BUTTON_WIDTH_S,
                    height=BUTTON_HEIGHT_S,
                    image=prompt_viewer.sort_image,
                    text="",
                    command=lambda: self.mode_switch(self.button_sort),
                    mode=SortMode.OFF,
                )
                self.button_sort.pack(side="top", pady=10)
                self.button_sort_tooltip = CTkToolTip(
                    self.button_sort, delay=TOOLTIP_DELAY, message=TOOLTIP["sort"]
                )
                self.button_view = STkButton(
                    self.button_frame,
                    width=BUTTON_WIDTH_S,
                    height=BUTTON_HEIGHT_S,
                    image=prompt_viewer.view_image,
                    text="",
                    command=lambda: self.mode_switch(
                        self.button_view, sort_button=self.button_sort
                    ),
                    mode=ViewMode.NORMAL,
                )
                self.button_view.pack(side="top")
                self.button_view_tooltip = CTkToolTip(
                    self.button_view,
                    delay=TOOLTIP_DELAY,
                    message=TOOLTIP["view_prompt"],
                )

                if sdxl:
                    self.tab_frame = CTkFrame(self.textbox, fg_color="transparent")
                    self.tab_frame.grid(
                        row=1, column=0, padx=5, pady=(0, 10), sticky="news"
                    )

                    self.prompt_tab_g = STkButton(
                        self.tab_frame,
                        height=BUTTON_HEIGHT_S,
                        text="Clip G",
                        command=lambda: self.prompt_switch(PromptMode.CLIP_G),
                    )
                    self.prompt_tab_g.pack(side="left", padx=5, expand=True, fill="x")
                    self.prompt_tab_g.switch_on()
                    self.prompt_tab_l = STkButton(
                        self.tab_frame,
                        height=BUTTON_HEIGHT_S,
                        text="Clip L",
                        command=lambda: self.prompt_switch(PromptMode.CLIP_L),
                    )
                    self.prompt_tab_l.pack(side="left", padx=5, expand=True, fill="x")
                    self.prompt_tab_r = STkButton(
                        self.tab_frame,
                        height=BUTTON_HEIGHT_S,
                        text="Refiner",
                        command=lambda: self.prompt_switch(PromptMode.REFINER),
                    )
                    self.prompt_tab_r.pack(side="left", padx=5, expand=True, fill="x")
                    self.prompt_tab_mode = STkButton(
                        self.tab_frame,
                        height=BUTTON_HEIGHT_S,
                        width=BUTTON_WIDTH_S,
                        text="",
                        image=prompt_viewer.separate_image,
                        command=lambda: prompt_viewer.switch_view(PromptMode.SEPARATE),
                    )
                    self.prompt_tab_mode.pack(side="right", padx=5)
                    self.prompt_tab_mode_tooltip = CTkToolTip(
                        self.prompt_tab_mode,
                        delay=TOOLTIP_DELAY,
                        message=TOOLTIP["view_separate"],
                    )

        def mode_switch(
            self, button: STkButton, sort_button: STkButton = None, update_status=True
        ):
            if isinstance(button.mode, ViewMode):
                match button.mode:
                    case ViewMode.NORMAL:
                        button.switch_on()
                        button.mode = (
                            ViewMode.VERTICAL if update_status else ViewMode.NORMAL
                        )
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
                        button.mode = (
                            ViewMode.NORMAL if update_status else ViewMode.VERTICAL
                        )
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
                        button.mode = SortMode.ASC if update_status else SortMode.OFF
                        self.textbox.sort_asc()
                        self.status_bar.info(MESSAGE["sort"][0])
                    case SortMode.ASC:
                        button.switch_on()
                        button.mode = SortMode.DES if update_status else SortMode.ASC
                        self.textbox.sort_des()
                        self.status_bar.info(MESSAGE["sort"][1])
                    case SortMode.DES:
                        button.switch_off()
                        button.mode = SortMode.OFF if update_status else SortMode.DES
                        self.textbox.sort_off()
                        self.status_bar.info(MESSAGE["sort"][-1])

        def mode_update(self, button_view=None, button_sort=None):
            button_view = button_view if button_view else self.button_view
            button_sort = button_sort if button_sort else self.button_sort
            match button_view.mode:
                case ViewMode.NORMAL:
                    match button_sort.mode:
                        case SortMode.ASC:
                            self.textbox.sort_asc()
                        case SortMode.DES:
                            self.textbox.sort_des()
                case ViewMode.VERTICAL:
                    self.textbox.view_vertical()
                    match button_sort.mode:
                        case SortMode.ASC:
                            self.textbox.sort_asc()
                        case SortMode.DES:
                            self.textbox.sort_des()

        def prompt_switch(self, mode):
            match mode:
                case PromptMode.CLIP_G:
                    self.prompt_tab_g.switch_on()
                    self.prompt_tab_l.switch_off()
                    self.prompt_tab_r.switch_off()
                    self.textbox.text = self._prompt.get("Clip G") or ""
                    self.mode_update()
                case PromptMode.CLIP_L:
                    self.prompt_tab_g.switch_off()
                    self.prompt_tab_l.switch_on()
                    self.prompt_tab_r.switch_off()
                    self.textbox.text = self._prompt.get("Clip L") or ""
                    self.mode_update()
                case PromptMode.REFINER:
                    self.prompt_tab_g.switch_off()
                    self.prompt_tab_l.switch_off()
                    self.prompt_tab_r.switch_on()
                    self.textbox.text = self._prompt.get("Refiner") or ""
                    self.mode_update()

        @property
        def prompt(self):
            return self._prompt

        @prompt.setter
        def prompt(self, prompt):
            self._prompt = prompt
            self.prompt_switch(PromptMode.CLIP_G)
