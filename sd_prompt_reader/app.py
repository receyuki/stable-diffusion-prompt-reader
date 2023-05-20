# -*- encoding:utf-8 -*-
__author__ = 'receyuki'
__filename__ = 'app.py'
__copyright__ = 'Copyright 2023'
__email__ = 'receyuki@gmail.com'

import platform
import sys
from tkinter import PhotoImage, Menu

import pyperclip as pyperclip
from PIL import Image
from customtkinter import CTkFont, ScalingTracker, CTkImage, CTkFrame, CTkLabel, CTkTextbox, ThemeManager, CTkButton, \
    filedialog, CTkOptionMenu, set_default_color_theme
from tkinterdnd2 import DND_FILES

from sd_prompt_reader.constants import *
from sd_prompt_reader.ctkdnd import Tk
from sd_prompt_reader.image_data_reader import ImageDataReader
from sd_prompt_reader.status_bar import StatusBar
from sd_prompt_reader.update_checker import UpdateChecker
from sd_prompt_reader.ctk_tooltip import CTkToolTip
from sd_prompt_reader.button import STkButton, ViewMode, SortMode


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
        self.save_image = self.load_icon(SAVE_FILE, (24, 24))
        self.expand_image = self.load_icon(EXPAND_FILE, (12, 24))
        self.sort_image = self.load_icon(SORT_FILE, (20, 20))
        self.view_image = self.load_icon(LIGHTBULB_FILE, (20, 20))

        self.icon_image = PhotoImage(file=ICON_FILE)
        self.iconphoto(False, self.icon_image)
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
        self.image_frame.grid(row=0, column=0, rowspan=4, sticky="news", padx=20, pady=20)

        self.image_label = CTkLabel(self.image_frame, width=560, text="Drop image here or click to select",
                                    image=self.drop_image, compound="top", text_color=ACCESSIBLE_GRAY)
        self.image_label.pack(fill="both", expand=True)
        self.image_label.bind("<Button-1>", lambda e: self.display_info(self.select_image(), is_selected=True))

        self.image = None
        self.image_tk = None
        self.image_data = None
        self.default_text_colour = ThemeManager.theme["CTkTextbox"]["text_color"]

        # status bar
        self.status_bar = StatusBar(self)
        self.status_bar.status_frame.grid(row=3, column=6, sticky="ew", padx=20, pady=(0, 20), ipadx=STATUS_BAR_IPAD,
                                          ipady=STATUS_BAR_IPAD)

        # text box
        self.positive_box = CTkTextbox(self, wrap="word", height=120)
        self.positive_box.grid(row=0, column=1, columnspan=6, sticky="news", padx=(0, 20), pady=(20, 20))
        self.positive_box.insert("end", "Prompt")
        self.positive_box.configure(state="disabled", text_color=ACCESSIBLE_GRAY, font=self.info_font)

        self.negative_box = CTkTextbox(self, wrap="word", height=120)
        self.negative_box.grid(row=1, column=1, columnspan=6, sticky="news", padx=(0, 20), pady=(0, 20))
        self.negative_box.insert("end", "Negative Prompt")
        self.negative_box.configure(state="disabled", text_color=ACCESSIBLE_GRAY, font=self.info_font)

        self.setting_box = CTkTextbox(self, wrap="word", height=80)
        self.setting_box.grid(row=2, column=1, columnspan=6, sticky="news", padx=(0, 20), pady=(0, 20))
        self.setting_box.insert("end", "Setting")
        self.setting_box.configure(state="disabled", text_color=ACCESSIBLE_GRAY, font=self.info_font)

        # textbox buttons
        self.button_positive_frame = CTkFrame(self.positive_box, fg_color="transparent")
        self.button_positive_frame.grid(row=0, column=1, padx=(20, 10), pady=(5, 0))
        self.button_copy_positive = STkButton(self.button_positive_frame, width=BUTTON_WIDTH_S, height=BUTTON_HEIGHT_S,
                                              image=self.clipboard_image_s, text="",
                                              command=lambda: self.copy_to_clipboard(self.image_data.positive))
        self.button_copy_positive.pack(side="top")
        self.button_sort_positive = STkButton(self.button_positive_frame, width=BUTTON_WIDTH_S, height=BUTTON_HEIGHT_S,
                                              image=self.sort_image, text="",
                                              command=lambda: self.mode_switch(self.button_sort_positive,
                                                                               self.positive_box),
                                              mode=SortMode.OFF)
        self.button_sort_positive.pack(side="top", pady=10)
        self.button_view_positive = STkButton(self.button_positive_frame, width=BUTTON_WIDTH_S, height=BUTTON_HEIGHT_S,
                                              image=self.view_image, text="",
                                              command=lambda: self.mode_switch(self.button_view_positive,
                                                                               self.positive_box),
                                              mode=ViewMode.NORMAL)
        self.button_view_positive.pack(side="top")

        self.button_negative_frame = CTkFrame(self.negative_box, fg_color="transparent")
        self.button_negative_frame.grid(row=0, column=1, padx=(20, 10), pady=(5, 0))
        self.button_copy_negative = STkButton(self.button_negative_frame, width=BUTTON_WIDTH_S, height=BUTTON_HEIGHT_S,
                                              image=self.clipboard_image_s, text="",
                                              command=lambda: self.copy_to_clipboard(self.image_data.negative))
        self.button_copy_negative.pack(side="top")
        self.button_sort_negative = STkButton(self.button_negative_frame, width=BUTTON_WIDTH_S, height=BUTTON_HEIGHT_S,
                                              image=self.sort_image, text="",
                                              command=lambda: self.mode_switch(self.button_sort_negative,
                                                                               self.negative_box),
                                              mode=SortMode.OFF)
        self.button_sort_negative.pack(side="top", pady=10)
        self.button_view_negative = STkButton(self.button_negative_frame, width=BUTTON_WIDTH_S, height=BUTTON_HEIGHT_S,
                                              image=self.view_image, text="",
                                              command=lambda: self.mode_switch(self.button_view_negative,
                                                                               self.negative_box),
                                              mode=ViewMode.NORMAL)
        self.button_view_negative.pack(side="top")

        self.button_setting_frame = CTkFrame(self.setting_box, fg_color="transparent")
        self.button_setting_frame.grid(row=0, column=1, padx=(20, 10), pady=(5, 0))
        self.button_copy_setting = STkButton(self.button_setting_frame, width=BUTTON_WIDTH_S, height=BUTTON_HEIGHT_S,
                                             image=self.clipboard_image_s, text="",
                                             command=lambda: self.copy_to_clipboard(self.image_data.setting))
        self.button_copy_setting.pack(side="top", pady=(0, 10))
        self.button_view_setting = STkButton(self.button_setting_frame, width=BUTTON_WIDTH_S, height=BUTTON_HEIGHT_S,
                                             image=self.view_image, text="",
                                             command=lambda: self.mode_switch(self.button_view_setting,
                                                                              self.setting_box),
                                             mode=ViewMode.NORMAL)
        self.button_view_setting.pack(side="top")

        # function buttons
        self.button_edit_frame = CTkFrame(self, fg_color="transparent")
        self.button_edit_frame.grid(row=3, column=1, pady=(0, 20), padx=(0, 20), sticky="w")
        self.button_edit = STkButton(self.button_edit_frame, width=BUTTON_WIDTH_L, height=BUTTON_HEIGHT_L,
                                     image=self.edit_image, text="", font=self.info_font)
        self.button_edit.pack(side="top")
        self.button_edit_label = CTkLabel(self.button_edit_frame, width=BUTTON_WIDTH_L, height=LABEL_HEIGHT,
                                          text="Edit", font=self.info_font)
        self.button_edit_label.pack(side="bottom")
        self.button_edit_tooltip = CTkToolTip(self.button_edit, delay=TOOLTIP_DELAY, message="test")
        self.button_edit.label = self.button_edit_label

        self.button_save_frame = CTkFrame(self, fg_color="transparent")
        self.button_save_frame.grid(row=3, column=2, pady=(0, 20), padx=(0, 20), sticky="w")
        self.button_save_option_frame = CTkFrame(self.button_save_frame, fg_color="transparent")
        self.button_save_option_frame.pack(side="top")
        self.button_save = STkButton(self.button_save_option_frame, width=BUTTON_WIDTH_L, height=BUTTON_HEIGHT_L,
                                     image=self.save_image, text="",
                                     font=self.info_font)
        self.button_save.pack(side="left")
        self.button_save_option_arrow = STkButton(self.button_save_option_frame, width=ARROW_WIDTH_L,
                                                  height=BUTTON_HEIGHT_L, text="", image=self.expand_image, )
        self.button_save_option_arrow.pack(side="right")
        self.button_save_label = CTkLabel(self.button_save_frame, width=BUTTON_WIDTH_L, height=LABEL_HEIGHT,
                                          text="Save", font=self.info_font)
        self.button_save_label.pack(side="left")
        self.button_save.label = self.button_save_label
        self.button_save.arrow = self.button_save_option_arrow

        self.button_remove_frame = CTkFrame(self, fg_color="transparent")
        self.button_remove_frame.grid(row=3, column=3, pady=(0, 20), padx=(0, 20), sticky="w")
        self.button_remove_option_frame = CTkFrame(self.button_remove_frame, fg_color="transparent")
        self.button_remove_option_frame.pack(side="top")
        self.button_remove = STkButton(self.button_remove_option_frame, width=BUTTON_WIDTH_L, height=BUTTON_HEIGHT_L,
                                       image=self.clear_image, text="",
                                       font=self.info_font, command=lambda: self.remove_data())
        self.button_remove.pack(side="left")
        self.button_remove_option = CTkOptionMenu(self.button_remove_frame,
                                                  font=self.info_font, dynamic_resizing=False,
                                                  values=["select directory",
                                                          "overwrite the original image"],
                                                  command=self.remove_data)
        self.button_remove_option_arrow = STkButton(self.button_remove_option_frame, width=ARROW_WIDTH_L,
                                                    height=BUTTON_HEIGHT_L, text="",
                                                    image=self.expand_image,
                                                    command=lambda: self.button_remove_option_open())
        self.button_remove_option_arrow.pack(side="right")
        self.button_remove_label = CTkLabel(self.button_remove_frame, width=BUTTON_WIDTH_L, height=LABEL_HEIGHT,
                                            text="Clear", font=self.info_font)
        self.button_remove_label.pack(side="left")
        self.button_remove.label = self.button_remove_label
        self.button_remove.arrow = self.button_remove_option_arrow

        self.button_export_frame = CTkFrame(self, fg_color="transparent")
        self.button_export_frame.grid(row=3, column=4, pady=(0, 20), padx=(0, 20), sticky="w")
        self.button_remove_option_frame = CTkFrame(self.button_export_frame, fg_color="transparent")
        self.button_remove_option_frame.pack(side="top")
        self.button_export = STkButton(self.button_remove_option_frame, width=BUTTON_WIDTH_L, height=BUTTON_HEIGHT_L,
                                       image=self.document_image, text="",
                                       font=self.info_font, command=lambda: self.export_txt())
        self.button_export.pack(side="left")
        self.button_export_option = CTkOptionMenu(self,
                                                  font=self.info_font, dynamic_resizing=False,
                                                  values=["select directory"],
                                                  command=self.export_txt)
        self.button_export_option_arrow = STkButton(self.button_remove_option_frame, width=ARROW_WIDTH_L,
                                                    height=BUTTON_HEIGHT_L, text="",
                                                    image=self.expand_image,
                                                    command=lambda: self.button_export_option_open())
        self.button_export_option_arrow.pack(side="right")
        self.button_export_label = CTkLabel(self.button_export_frame, width=BUTTON_WIDTH_L, height=LABEL_HEIGHT,
                                            text="Export", font=self.info_font)
        self.button_export_label.pack(side="left")
        self.button_export.label = self.button_export_label
        self.button_export.arrow = self.button_export_option_arrow

        self.button_copy_raw_frame = CTkFrame(self, fg_color="transparent")
        self.button_copy_raw_frame.grid(row=3, column=5, pady=(0, 20), sticky="w")
        self.button_raw = STkButton(self.button_copy_raw_frame, width=BUTTON_WIDTH_L, height=BUTTON_HEIGHT_L,
                                    image=self.clipboard_image, text="",
                                    font=self.info_font, command=lambda: self.copy_to_clipboard(self.image_data.raw))
        self.button_raw.pack(side="top")
        self.button_raw_label = CTkLabel(self.button_copy_raw_frame, width=BUTTON_WIDTH_L, height=LABEL_HEIGHT,
                                         text="Copy", font=self.info_font)
        self.button_raw_label.pack(side="bottom")
        self.button_raw.label = self.button_raw_label

        # text boxes and buttons
        self.boxes = [self.positive_box, self.negative_box, self.setting_box]

        self.function_buttons = [self.button_copy_positive, self.button_sort_positive, self.button_view_positive,
                                 self.button_copy_negative, self.button_sort_negative, self.button_view_negative,
                                 self.button_copy_setting, self.button_view_setting,
                                 self.button_raw, self.button_edit, self.button_save,
                                 self.button_remove, self.button_export, self.button_remove]

        for button in self.function_buttons:
            button.disable()

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
            self.file_path = Path(event)
        else:
            self.file_path = Path(event.data.replace("}", "").replace("{", ""))

        # clear text
        for box in self.boxes:
            box.configure(state="normal")
            box.delete("1.0", "end")

        # detect suffix and read
        if self.file_path.suffix in SUPPORTED_FORMATS:
            with open(self.file_path, "rb") as f:
                self.image_data = ImageDataReader(f)
                if not self.image_data.raw:
                    self.unsupported_format(MESSAGE["format_error"])
                else:
                    # insert prompt
                    self.positive_box.insert("end", self.image_data.positive)
                    self.negative_box.insert("end", self.image_data.negative)
                    self.setting_box.insert("end", self.image_data.setting)
                    for box in self.boxes:
                        # box.configure(state="disabled", text_color=self.default_text_colour)
                        box.configure(state="disabled")
                    # for button in self.function_buttons:
                    #     button.configure(state="normal")
                    for button in self.function_buttons:
                        button.enable()
                    self.status_bar.success(self.image_data.tool)
                self.image = Image.open(f)
                self.image_tk = CTkImage(self.image)
                self.resize_image()
        else:
            self.unsupported_format(MESSAGE["suffix_error"], True)

    def unsupported_format(self, message, reset_image=False):
        for box in self.boxes:
            box.insert("end", message[0])
            # box.configure(state="disabled", text_color="gray")
            box.configure(state="disabled")
        # for button in self.function_buttons:
        #     button.configure(state="disabled")
        for button in self.function_buttons:
            button.disable()
        if reset_image:
            self.image_label.configure(image=self.drop_image, text="Drop image here or click to select")
            self.image = None
        self.status_bar.warning(message[-1])

    def resize_image(self, event=None):
        # resize image to window size
        if self.image:
            aspect_ratio = self.image.size[0] / self.image.size[1]
            # fix windows huge image problem under hidpi
            self.scaling = ScalingTracker.get_window_dpi_scaling(self)
            # resize image to window size
            if self.image.size[0] > self.image.size[1]:
                self.image_tk.configure(size=tuple(num / self.scaling for num in
                                                   (self.image_frame.winfo_height(),
                                                    self.image_frame.winfo_height() / aspect_ratio)))
            else:
                self.image_tk.configure(size=tuple(num / self.scaling for num in
                                                   (self.image_label.winfo_height() * aspect_ratio,
                                                    self.image_label.winfo_height())))
            # display image
            self.image_label.configure(image=self.image_tk, text="")

    def copy_to_clipboard(self, content):
        try:
            pyperclip.copy(content)
        except:
            print("Copy error")
        else:
            self.status_bar.clipboard()

    def button_export_option_open(self):
        self.button_export_option._dropdown_menu.open(
            self.button_export.winfo_rootx(),
            self.button_export.winfo_rooty() +
            self.button_export._apply_widget_scaling(self.button_export._current_height + 0))

    def button_remove_option_open(self):
        self.button_remove_option._dropdown_menu.open(
            self.button_remove.winfo_rootx(),
            self.button_remove.winfo_rooty() +
            self.button_remove._apply_widget_scaling(self.button_remove._current_height + 0))

    def export_txt(self, export_mode: str = None):
        if not export_mode:
            with open(self.file_path.with_suffix(".txt"), "w", encoding="utf-8") as f:
                f.write(self.image_data.raw)
                self.status_bar.success(MESSAGE["alongside"][0])
        else:
            match export_mode:
                # case "alongside the image file":
                #
                case "select directory":
                    path = filedialog.asksaveasfilename(
                        title='Select directory',
                        initialdir=self.file_path.parent,
                        initialfile=self.file_path.stem,
                        filetypes=(("text file", "*.txt"),))
                    if path:
                        with open(Path(path).with_suffix(".txt"), "w", encoding="utf-8") as f:
                            f.write(self.image_data.raw)
                            self.status_bar.success(MESSAGE["txt_select"][0])

    def remove_data(self, remove_mode: str = None):
        image_without_exif = self.image_data.remove_data(self.file_path)
        new_stem = self.file_path.stem + "_data_removed"
        new_path = self.file_path.with_stem(new_stem)
        if not remove_mode:
            try:
                image_without_exif.save(new_path)
                self.status_bar.success(MESSAGE["suffix"][0])
            except:
                print("Remove error")
        else:
            match remove_mode:
                # case "add suffix":
                #
                case "overwrite the original image":
                    try:
                        image_without_exif.save(self.file_path)
                        self.status_bar.success(MESSAGE["overwrite"][0])
                    except:
                        print("Remove error")
                case "select directory":
                    path = filedialog.asksaveasfilename(
                        title='Select directory',
                        initialdir=self.file_path.parent,
                        initialfile=new_path.name, )
                    if path:
                        image_without_exif.save(path)
                        self.status_bar.success(MESSAGE["remove_select"][0])

    @staticmethod
    def mode_switch(button: STkButton, textbox: CTkTextbox):
        if isinstance(button.mode, ViewMode):
            match button.mode:
                case ViewMode.NORMAL:
                    button.switch_on()
                    button.mode = ViewMode.VERTICAL
                case ViewMode.VERTICAL:
                    button.switch_off()
                    button.mode = ViewMode.NORMAL
        elif isinstance(button.mode, SortMode):
            match button.mode:
                case SortMode.OFF:
                    button.switch_on()
                    button.mode = SortMode.ASC
                case SortMode.ASC:
                    button.switch_on()
                    button.mode = SortMode.DES
                case SortMode.DES:
                    button.switch_off()
                    button.mode = SortMode.OFF

    @staticmethod
    def select_image():
        return filedialog.askopenfilename(
            title='Select your image file',
            initialdir="/",
            filetypes=(("image files", "*.png *.jpg *jpeg *.webp"),)
        )

    @staticmethod
    def load_icon(icon_file, size):
        return (CTkImage(Image.open(icon_file[0]), size=size),
                CTkImage(Image.open(icon_file[1]), size=size))


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
