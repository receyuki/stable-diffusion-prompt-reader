__author__ = "receyuki"
__filename__ = "app.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import platform
import sys
from tkinter import PhotoImage, Menu

import pyperclip as pyperclip
from CTkToolTip import *
from PIL import Image
from customtkinter import (
    ScalingTracker,
    CTkFrame,
    ThemeManager,
    filedialog,
    CTkOptionMenu,
    set_default_color_theme,
)
from tkinterdnd2 import DND_FILES

from .button import *
from .constants import *
from .ctkdnd import Tk
from .image_data_reader import ImageDataReader
from .parameter_viewer import ParameterViewer
from .prompt_viewer import PromptViewer
from .status_bar import StatusBar
from .textbox import STkTextbox
from .update_checker import UpdateChecker
from .__version__ import VERSION


class App(Tk):
    def __init__(self):
        super().__init__()

        # window = TkinterDnD.Tk()
        # window = Tk()
        self.title("SD Prompt Reader")
        self.geometry("1280x600")
        # set_appearance_mode("Light")
        # deactivate_automatic_dpi_awareness()
        # set_widget_scaling(1)
        # set_window_scaling(0.8)
        # info_font = CTkFont(size=20)
        self.info_font = CTkFont()
        self.scaling = ScalingTracker.get_window_dpi_scaling(self)
        set_default_color_theme(COLOR_THEME)

        # remove menubar on macos
        empty_menubar = Menu(self)
        self.config(menu=empty_menubar)

        # load icon images
        self.drop_image = CTkImage(Image.open(DROP_FILE), size=(48, 48))
        self.clipboard_image = self.load_icon(COPY_FILE_L, (24, 24))
        self.clipboard_image_s = self.load_icon(COPY_FILE_S, (20, 20))
        self.clear_image = self.load_icon(CLEAR_FILE, (24, 24))
        self.document_image = self.load_icon(DOCUMENT_FILE, (24, 24))
        self.edit_image = self.load_icon(EDIT_FILE, (24, 24))
        self.edit_off_image = self.load_icon(EDIT_OFF_FILE, (24, 24))
        self.save_image = self.load_icon(SAVE_FILE, (24, 24))
        self.expand_image = self.load_icon(EXPAND_FILE, (12, 24))
        self.sort_image = self.load_icon(SORT_FILE, (20, 20))
        self.view_image = self.load_icon(LIGHTBULB_FILE, (20, 20))
        self.icon_image = CTkImage(Image.open(ICON_FILE), size=(100, 100))

        self.icon_image_pi = PhotoImage(file=ICON_FILE)
        self.iconphoto(False, self.icon_image_pi)
        if platform.system() == "Windows":
            self.iconbitmap(ICO_FILE)

        # configure layout
        self.rowconfigure(tuple(range(4)), weight=1)
        self.columnconfigure(tuple(range(7)), weight=1)
        self.columnconfigure(0, weight=6)
        # self.rowconfigure(0, weight=2)
        # self.rowconfigure(1, weight=2)
        # self.rowconfigure(2, weight=1)
        # self.rowconfigure(3, weight=1)

        # image display
        self.image_frame = CTkFrame(self)
        self.image_frame.grid(
            row=0, column=0, rowspan=4, sticky="news", padx=20, pady=20
        )

        self.image_label = CTkLabel(
            self.image_frame,
            width=560,
            text=VERSION + "\n\n" + MESSAGE["drop"][0],
            image=self.icon_image,
            compound="top",
            text_color=ACCESSIBLE_GRAY,
        )
        self.image_label.pack(fill="both", expand=True)
        self.image_label.bind(
            "<Button-1>",
            lambda e: self.display_info(self.select_image(), is_selected=True),
        )

        self.image = None
        self.image_tk = None
        self.image_data = None
        self.textbox_fg_color = ThemeManager.theme["CTkTextbox"]["fg_color"]
        self.readable = False

        # status bar
        self.status_bar = StatusBar(self)
        self.status_bar.status_frame.grid(
            row=3,
            column=6,
            sticky="ew",
            padx=20,
            pady=(0, 20),
            ipadx=STATUS_BAR_IPAD,
            ipady=STATUS_BAR_IPAD,
        )

        # textbox
        self.positive_box = PromptViewer(self, self.status_bar, "Prompt")
        self.positive_box.viewer_frame.grid(
            row=0, column=1, columnspan=6, sticky="news", padx=(0, 20), pady=(20, 20)
        )

        self.negative_box = PromptViewer(self, self.status_bar, "Negative Prompt")
        self.negative_box.viewer_frame.grid(
            row=1, column=1, columnspan=6, sticky="news", padx=(0, 20), pady=(0, 20)
        )

        self.setting_box = STkTextbox(self, wrap="word", height=80)
        self.setting_box.grid(
            row=2, column=1, columnspan=6, sticky="news", padx=(0, 20), pady=(0, 20)
        )
        self.setting_box.text = "Setting"

        # textbox simple mode
        self.setting_box_simple = CTkFrame(
            self, height=80, fg_color=self.textbox_fg_color
        )
        self.setting_box_parameter = CTkFrame(
            self.setting_box_simple, fg_color="transparent"
        )
        self.setting_box_parameter = ParameterViewer(
            self.setting_box_simple, self.status_bar
        )
        self.setting_box_parameter.setting_box_parameter.pack(side="left", padx=5)

        # setting box
        self.button_setting_frame = CTkFrame(self.setting_box, fg_color="transparent")
        self.button_setting_frame.grid(row=0, column=1, padx=(20, 10), pady=(5, 0))
        self.button_copy_setting = STkButton(
            self.button_setting_frame,
            width=BUTTON_WIDTH_S,
            height=BUTTON_HEIGHT_S,
            image=self.clipboard_image_s,
            text="",
            command=lambda: self.copy_to_clipboard(self.setting_box.ctext),
        )
        self.button_copy_setting.pack(side="top", pady=(0, 10))
        self.button_copy_setting_tooltip = CTkToolTip(
            self.button_copy_setting,
            delay=TOOLTIP_DELAY,
            message=TOOLTIP["copy_setting"],
        )
        self.button_view_setting = STkButton(
            self.button_setting_frame,
            width=BUTTON_WIDTH_S,
            height=BUTTON_HEIGHT_S,
            image=self.view_image,
            text="",
            command=lambda: self.setting_mode_switch(),
            mode=SettingMode.NORMAL,
        )
        self.button_view_setting.pack(side="top")
        self.button_view_setting_tooltip = CTkToolTip(
            self.button_view_setting,
            delay=TOOLTIP_DELAY,
            message=TOOLTIP["view_setting"],
        )

        # setting box simple mode
        self.button_setting_frame_simple = CTkFrame(
            self.setting_box_simple, fg_color="transparent"
        )
        self.button_setting_frame_simple.pack(side="right", padx=(20, 10), pady=5)
        self.button_copy_setting_simple = STkButton(
            self.button_setting_frame_simple,
            width=BUTTON_WIDTH_S,
            height=BUTTON_HEIGHT_S,
            image=self.clipboard_image_s,
            text="",
            command=lambda: self.copy_to_clipboard(self.image_data.setting),
        )
        self.button_copy_setting_simple.pack(side="top", pady=(0, 10))
        self.button_copy_setting_simple_tooltip = CTkToolTip(
            self.button_copy_setting_simple,
            delay=TOOLTIP_DELAY,
            message=TOOLTIP["copy_setting"],
        )
        self.button_view_setting_simple = STkButton(
            self.button_setting_frame_simple,
            width=BUTTON_WIDTH_S,
            height=BUTTON_HEIGHT_S,
            image=self.view_image,
            text="",
            command=lambda: self.setting_mode_switch(),
        )
        self.button_view_setting_simple.switch_on()
        self.button_view_setting_simple.pack(side="top")
        self.button_view_setting_simple_tooltip = CTkToolTip(
            self.button_view_setting_simple,
            delay=TOOLTIP_DELAY,
            message=TOOLTIP["view_setting"],
        )

        # function buttons
        # edit
        self.button_edit_frame = CTkFrame(self, fg_color="transparent")
        self.button_edit_frame.grid(
            row=3, column=1, pady=(0, 20), padx=(0, 20), sticky="w"
        )
        self.button_edit = STkButton(
            self.button_edit_frame,
            width=BUTTON_WIDTH_L,
            height=BUTTON_HEIGHT_L,
            image=self.edit_image,
            text="",
            font=self.info_font,
            command=lambda: self.edit_mode_switch(),
            mode=EditMode.OFF,
        )
        self.button_edit.pack(side="top")
        self.button_edit_label = CTkLabel(
            self.button_edit_frame,
            width=BUTTON_WIDTH_L,
            height=LABEL_HEIGHT,
            text="Edit",
            font=self.info_font,
        )
        self.button_edit_label.pack(side="bottom")
        self.button_edit.label = self.button_edit_label
        self.button_edit_tooltip = CTkToolTip(
            self.button_edit, delay=TOOLTIP_DELAY, message=TOOLTIP["edit"]
        )

        # save
        self.button_save_frame = CTkFrame(self, fg_color="transparent")
        self.button_save_frame.grid(
            row=3, column=2, pady=(0, 20), padx=(0, 20), sticky="w"
        )
        self.button_save = STkButton(
            self.button_save_frame,
            width=BUTTON_WIDTH_L,
            height=BUTTON_HEIGHT_L,
            image=self.save_image,
            text="",
            font=self.info_font,
            command=lambda: self.save_data(),
        )
        self.button_save.grid(row=0, column=0)
        self.button_save_option = CTkOptionMenu(
            self.button_save_frame,
            font=self.info_font,
            dynamic_resizing=False,
            values=["select directory", "overwrite the original image"],
            command=self.save_data,
        )
        self.button_save_option_arrow = STkButton(
            self.button_save_frame,
            width=ARROW_WIDTH_L,
            height=BUTTON_HEIGHT_L,
            text="",
            image=self.expand_image,
            command=lambda: self.option_open(self.button_save, self.button_save_option),
        )
        self.button_save_option_arrow.grid(row=0, column=1)
        self.button_save_label = CTkLabel(
            self.button_save_frame,
            width=BUTTON_WIDTH_L,
            height=LABEL_HEIGHT,
            text="Save",
            font=self.info_font,
        )
        self.button_save_label.grid(row=1, column=0, rowspan=2)
        self.button_save.label = self.button_save_label
        self.button_save.arrow = self.button_save_option_arrow
        self.button_save_tooltip = CTkToolTip(
            self.button_save, delay=TOOLTIP_DELAY, message=TOOLTIP["save"]
        )

        # remove
        self.button_remove_frame = CTkFrame(self, fg_color="transparent")
        self.button_remove_frame.grid(
            row=3, column=3, pady=(0, 20), padx=(0, 20), sticky="w"
        )
        self.button_remove = STkButton(
            self.button_remove_frame,
            width=BUTTON_WIDTH_L,
            height=BUTTON_HEIGHT_L,
            image=self.clear_image,
            text="",
            font=self.info_font,
            command=lambda: self.remove_data(),
        )
        self.button_remove.grid(row=0, column=0)
        self.button_remove_option = CTkOptionMenu(
            self.button_remove_frame,
            font=self.info_font,
            dynamic_resizing=False,
            values=["select directory", "overwrite the original image"],
            command=self.remove_data,
        )
        self.button_remove_option_arrow = STkButton(
            self.button_remove_frame,
            width=ARROW_WIDTH_L,
            height=BUTTON_HEIGHT_L,
            text="",
            image=self.expand_image,
            command=lambda: self.option_open(
                self.button_remove, self.button_remove_option
            ),
        )
        self.button_remove_option_arrow.grid(row=0, column=1)
        self.button_remove_label = CTkLabel(
            self.button_remove_frame,
            width=BUTTON_WIDTH_L,
            height=LABEL_HEIGHT,
            text="Clear",
            font=self.info_font,
        )
        self.button_remove_label.grid(row=1, column=0, rowspan=2)
        self.button_remove.label = self.button_remove_label
        self.button_remove.arrow = self.button_remove_option_arrow
        self.button_remove_tooltip = CTkToolTip(
            self.button_remove, delay=TOOLTIP_DELAY, message=TOOLTIP["clear"]
        )

        # export
        self.button_export_frame = CTkFrame(self, fg_color="transparent")
        self.button_export_frame.grid(
            row=3, column=4, pady=(0, 20), padx=(0, 20), sticky="w"
        )
        self.button_export = STkButton(
            self.button_export_frame,
            width=BUTTON_WIDTH_L,
            height=BUTTON_HEIGHT_L,
            image=self.document_image,
            text="",
            font=self.info_font,
            command=lambda: self.export_txt(),
        )
        self.button_export.grid(row=0, column=0)
        self.button_export_option = CTkOptionMenu(
            self,
            font=self.info_font,
            dynamic_resizing=False,
            values=["select directory"],
            command=self.export_txt,
        )
        self.button_export_option_arrow = STkButton(
            self.button_export_frame,
            width=ARROW_WIDTH_L,
            height=BUTTON_HEIGHT_L,
            text="",
            image=self.expand_image,
            command=lambda: self.option_open(
                self.button_export, self.button_export_option
            ),
        )
        self.button_export_option_arrow.grid(row=0, column=1)
        self.button_export_label = CTkLabel(
            self.button_export_frame,
            width=BUTTON_WIDTH_L,
            height=LABEL_HEIGHT,
            text="Export",
            font=self.info_font,
        )
        self.button_export_label.grid(row=1, column=0, rowspan=2)
        self.button_export.label = self.button_export_label
        self.button_export.arrow = self.button_export_option_arrow
        self.button_export_tooltip = CTkToolTip(
            self.button_export, delay=TOOLTIP_DELAY, message=TOOLTIP["export"]
        )

        # copy
        self.button_copy_raw_frame = CTkFrame(self, fg_color="transparent")
        self.button_copy_raw_frame.grid(row=3, column=5, pady=(0, 20), sticky="w")
        self.button_raw = STkButton(
            self.button_copy_raw_frame,
            width=BUTTON_WIDTH_L,
            height=BUTTON_HEIGHT_L,
            image=self.clipboard_image,
            text="",
            font=self.info_font,
            command=lambda: self.copy_to_clipboard(self.image_data.raw),
        )
        self.button_raw.grid(row=0, column=0)
        self.button_raw_option = CTkOptionMenu(
            self,
            font=self.info_font,
            dynamic_resizing=False,
            values=["single line prompt"],
            command=self.copy_raw,
        )
        self.button_raw_option_arrow = STkButton(
            self.button_copy_raw_frame,
            width=ARROW_WIDTH_L,
            height=BUTTON_HEIGHT_L,
            text="",
            image=self.expand_image,
            command=lambda: self.option_open(self.button_raw, self.button_raw_option),
        )
        self.button_raw_option_arrow.grid(row=0, column=1)
        self.button_raw_label = CTkLabel(
            self.button_copy_raw_frame,
            width=BUTTON_WIDTH_L,
            height=LABEL_HEIGHT,
            text="Copy",
            font=self.info_font,
        )
        self.button_raw_label.grid(row=1, column=0, rowspan=2)
        self.button_raw.label = self.button_raw_label
        self.button_raw.arrow = self.button_raw_option_arrow
        self.button_raw_tooltip = CTkToolTip(
            self.button_raw, delay=TOOLTIP_DELAY, message=TOOLTIP["copy_raw"]
        )

        # text boxes and buttons
        self.boxes = [self.positive_box, self.negative_box, self.setting_box]

        # general button list
        self.function_buttons = [
            self.button_copy_setting,
            self.button_view_setting,
            self.button_copy_setting_simple,
            self.button_raw,
            self.button_remove,
            self.button_export,
            self.button_remove,
        ]

        # button list for edit mode
        self.non_edit_buttons = [
            self.button_view_setting,
            self.button_export,
            self.button_raw,
        ]

        self.edit_buttons = [
            self.button_copy_setting,
            self.button_remove,
            self.button_edit,
        ]

        for button in self.function_buttons:
            button.disable()
        self.positive_box.all_off()
        self.negative_box.all_off()
        self.button_save.disable()
        self.button_edit.disable()
        self.file_path = None

        # bind dnd and resize
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self.display_info)
        self.bind("<Configure>", self.resize_image)

        # update checker
        self.update_checker = UpdateChecker(self.status_bar)

        # open with in windows
        if len(sys.argv) > 1:
            self.display_info(sys.argv[1], is_selected=True)
        # open with in macOS
        self.createcommand("::tk::mac::OpenDocument", self.open_document_handler)

    def open_document_handler(self, *args):
        self.display_info(args[0], is_selected=True)

    def display_info(self, event, is_selected=False):
        # stop update thread when reading first image
        self.update_checker.close_thread()
        # selected or drag and drop
        if is_selected:
            if event == "":
                return
            new_path = Path(event)
        else:
            new_path = Path(event.data.replace("}", "").replace("{", ""))

        # detect suffix and read
        if new_path.suffix in SUPPORTED_FORMATS:
            self.file_path = new_path
            with open(self.file_path, "rb") as f:
                self.image_data = ImageDataReader(f)
                if not self.image_data.tool:
                    self.unsupported_format(MESSAGE["format_error"])
                else:
                    self.readable = True
                    # insert prompt
                    if not self.image_data.is_sdxl:
                        self.positive_box.display(self.image_data.positive)
                        self.negative_box.display(self.image_data.negative)
                    else:
                        self.positive_box.display(self.image_data.positive_sdxl)
                        self.negative_box.display(self.image_data.negative_sdxl)
                    self.setting_box.text = self.image_data.setting
                    self.setting_box_parameter.update_text(self.image_data.parameter)
                    self.positive_box.mode_update()
                    self.negative_box.mode_update()
                    if self.button_edit.mode == EditMode.OFF:
                        for button in self.function_buttons:
                            button.enable()
                        self.positive_box.all_on()
                        self.negative_box.all_on()
                    for button in self.edit_buttons:
                        button.enable()
                    self.positive_box.copy_on()
                    self.negative_box.copy_on()
                    if self.image_data.tool != "A1111 webUI":
                        self.button_raw_option_arrow.disable()
                    if self.image_data.is_sdxl:
                        self.button_edit.disable()
                    self.status_bar.success(self.image_data.tool)
                self.image = Image.open(f)
                self.image_tk = CTkImage(self.image)
                self.resize_image()
            if self.button_edit.mode == EditMode.ON:
                self.edit_mode_update()

        # txt importing
        elif new_path.suffix == ".txt":
            if self.button_edit.mode == EditMode.ON:
                with open(new_path, "r") as f:
                    txt_data = ImageDataReader(f, is_txt=True)
                    if txt_data.raw:
                        self.positive_box.text = txt_data.positive
                        self.negative_box.text = txt_data.negative
                        self.setting_box.text = txt_data.setting
                        self.edit_mode_update()
                        self.status_bar.warning(MESSAGE["txt_imported"][0])
                    else:
                        self.status_bar.warning(MESSAGE["txt_error"][-1])
            else:
                self.status_bar.warning(MESSAGE["txt_error"][0])

        else:
            self.unsupported_format(MESSAGE["suffix_error"], True)
            if self.button_edit.mode == EditMode.ON:
                for box in self.boxes:
                    box.edit_off()
            self.button_edit.disable()

    def unsupported_format(self, message, reset_image=False):
        self.readable = False
        self.setting_box.text = message[0]
        self.positive_box.display(message[0])
        self.negative_box.display(message[0])
        self.setting_box_parameter.reset_text()
        for button in self.function_buttons:
            button.disable()
        self.positive_box.all_off()
        self.negative_box.all_off()
        if reset_image:
            self.image_label.configure(image=self.drop_image, text=MESSAGE["drop"][0])
            self.image = None
        else:
            self.button_edit.enable()
        self.status_bar.warning(message[-1])

    def resize_image(self, event=None):
        # resize image to window size
        if self.image:
            aspect_ratio = self.image.size[0] / self.image.size[1]
            # fix windows huge image problem under hidpi
            self.scaling = ScalingTracker.get_window_dpi_scaling(self)
            # resize image to window size
            image_frame_height = (
                self.image_frame.winfo_height()
                if self.image_frame.winfo_height() > 2
                else 560
            )
            image_frame_width = (
                self.image_frame.winfo_width() - 5
                if self.image_frame.winfo_width() > 2
                else 560
            )
            if self.image.size[0] > self.image.size[1]:
                self.image_tk.configure(
                    size=tuple(
                        int(num / self.scaling)
                        for num in (image_frame_width, image_frame_width / aspect_ratio)
                    )
                )
            else:
                self.image_tk.configure(
                    size=tuple(
                        int(num / self.scaling)
                        for num in (
                            image_frame_height * aspect_ratio,
                            image_frame_height,
                        )
                    )
                )
            # display image
            self.image_label.configure(image=self.image_tk, text="")

    def copy_to_clipboard(self, content):
        try:
            pyperclip.copy(content)
        except:
            print("Copy error")
        else:
            self.status_bar.clipboard()

    # alt option menu button trigger for CTkOptionMenu
    @staticmethod
    def option_open(button: CTkButton, option_menu: CTkOptionMenu):
        option_menu._dropdown_menu.open(
            button.winfo_rootx(),
            button.winfo_rooty()
            + button._apply_widget_scaling(button._current_height + 0),
        )

    def export_txt(self, export_mode: str = None):
        if not export_mode:
            with open(self.file_path.with_suffix(".txt"), "w", encoding="utf-8") as f:
                f.write(self.image_data.raw)
                self.status_bar.success(MESSAGE["alongside"][0])
        else:
            match export_mode:
                case "select directory":
                    path = filedialog.asksaveasfilename(
                        title="Select directory",
                        initialdir=self.file_path.parent,
                        initialfile=self.file_path.stem,
                        filetypes=(("text file", "*.txt"),),
                    )
                    if path:
                        with open(
                            Path(path).with_suffix(".txt"), "w", encoding="utf-8"
                        ) as f:
                            f.write(self.image_data.raw)
                            self.status_bar.success(MESSAGE["txt_select"][0])

    def remove_data(self, remove_mode: str = None):
        image_without_exif = self.image_data.remove_data(self.file_path)
        new_stem = self.file_path.stem + "_data_removed"
        new_path = self.file_path.with_stem(new_stem)
        if not remove_mode:
            try:
                self.image_data.save_image(
                    self.file_path, new_path, self.image_data.format
                )
            except:
                print("Remove error")
            else:
                self.status_bar.success(MESSAGE["suffix"][0])
        else:
            match remove_mode:
                # case "add suffix":
                #
                case "overwrite the original image":
                    try:
                        self.image_data.save_image(
                            self.file_path, self.file_path, self.image_data.format
                        )
                    except:
                        print("Remove error")
                    else:
                        self.status_bar.success(MESSAGE["overwrite"][0])
                case "select directory":
                    path = filedialog.asksaveasfilename(
                        title="Select directory",
                        initialdir=self.file_path.parent,
                        initialfile=new_path.name,
                    )
                    if path:
                        try:
                            self.image_data.save_image(
                                self.file_path, path, self.image_data.format
                            )
                        except:
                            print("Remove error")
                        else:
                            self.status_bar.success(MESSAGE["remove_select"][0])

    def save_data(self, save_mode: str = None):
        with Image.open(self.file_path) as image:
            new_stem = self.file_path.stem + "_edited"
            new_path = self.file_path.with_stem(new_stem)
            data = (
                self.positive_box.text
                + "Negative prompt: "
                + self.negative_box.text
                + self.setting_box.ctext
            )
            if not save_mode:
                try:
                    self.image_data.save_image(
                        self.file_path, new_path, self.image_data.format, data
                    )
                except:
                    print("Save error")
                else:
                    self.status_bar.success(MESSAGE["suffix"][0])
            else:
                match save_mode:
                    case "overwrite the original image":
                        try:
                            self.image_data.save_image(
                                self.file_path,
                                self.file_path,
                                self.image_data.format,
                                data,
                            )
                        except:
                            print("Save error")
                        else:
                            self.status_bar.success(MESSAGE["overwrite"][0])
                    case "select directory":
                        path = filedialog.asksaveasfilename(
                            title="Select directory",
                            initialdir=self.file_path.parent,
                            initialfile=new_path.name,
                        )
                        if path:
                            try:
                                self.image_data.save_image(
                                    self.file_path, path, self.image_data.format, data
                                )
                            except:
                                print("Save error")
                            else:
                                self.status_bar.success(MESSAGE["remove_select"][0])

    def copy_raw(self, copy_mode: str = None):
        match copy_mode:
            case "single line prompt":
                self.copy_to_clipboard(self.image_data.prompt_to_line())

    def edit_mode_switch(self):
        match self.button_edit.mode:
            case EditMode.OFF:
                self.button_edit.mode = EditMode.ON
                self.button_edit.image = self.edit_off_image
                self.button_edit.switch_on()
                self.positive_box.edit_on()
                self.negative_box.edit_on()
                self.setting_box.edit_on()
                if self.button_view_setting.mode == SettingMode.SIMPLE:
                    self.setting_mode_switch()
                for button in self.non_edit_buttons:
                    button.disable()
                self.button_save.enable()
                self.status_bar.info(MESSAGE["edit"][0])
            case EditMode.ON:
                self.button_edit.mode = EditMode.OFF
                self.button_edit.image = self.edit_image
                self.button_edit.switch_off()
                self.positive_box.edit_off()
                self.negative_box.edit_off()
                self.setting_box.edit_off()
                if self.readable:
                    for button in self.non_edit_buttons:
                        button.enable()
                self.button_save.disable()
                self.status_bar.info(MESSAGE["edit"][-1])

    def edit_mode_update(self):
        match self.button_edit.mode:
            case EditMode.OFF:
                self.positive_box.edit_off()
                self.negative_box.edit_off()
                self.setting_box.edit_off()
                if self.readable:
                    for button in self.non_edit_buttons:
                        button.enable()
                self.button_save.disable()
            case EditMode.ON:
                self.positive_box.edit_on()
                self.negative_box.edit_on()
                self.setting_box.edit_on()
                for button in self.non_edit_buttons:
                    button.disable()
                self.button_save.enable()

    def setting_mode_switch(self):
        match self.button_view_setting.mode:
            case SettingMode.NORMAL:
                self.button_view_setting.mode = SettingMode.SIMPLE
                self.setting_box_simple.grid(
                    row=2,
                    column=1,
                    columnspan=6,
                    sticky="news",
                    padx=(0, 20),
                    pady=(0, 20),
                )
                self.setting_box.grid_forget()
                self.status_bar.info(MESSAGE["view_setting"][0])
            case SettingMode.SIMPLE:
                self.button_view_setting.mode = SettingMode.NORMAL
                self.setting_box.grid(
                    row=2,
                    column=1,
                    columnspan=6,
                    sticky="news",
                    padx=(0, 20),
                    pady=(0, 20),
                )
                self.setting_box_simple.grid_forget()
                self.status_bar.info(MESSAGE["view_setting"][-1])

    @staticmethod
    def mode_update(button: STkButton, textbox: STkTextbox, sort_button: STkButton):
        match button.mode:
            case ViewMode.NORMAL:
                match sort_button.mode:
                    case SortMode.ASC:
                        textbox.sort_asc()
                    case SortMode.DES:
                        textbox.sort_des()
            case ViewMode.VERTICAL:
                textbox.view_vertical()
                match sort_button.mode:
                    case SortMode.ASC:
                        textbox.sort_asc()
                    case SortMode.DES:
                        textbox.sort_des()

    def select_image(self):
        initialdir = self.file_path.parent if self.file_path else "/"
        return filedialog.askopenfilename(
            title="Select your image file",
            initialdir=initialdir,
            filetypes=(("image files", "*.png *.jpg *jpeg *.webp"),),
        )

    @staticmethod
    def load_icon(icon_file, size):
        return (
            CTkImage(Image.open(icon_file[0]), size=size),
            CTkImage(Image.open(icon_file[1]), size=size),
        )


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
