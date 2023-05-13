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
        self.clipboard_image = CTkImage(Image.open(COPY_FILE_L), size=(30, 30))
        self.remove_tag_image = CTkImage(Image.open(CLEAR_FILE), size=(24, 24))
        self.document_image = CTkImage(Image.open(DOCUMENT_FILE), size=(30, 30))
        self.expand_arrow_image = CTkImage(Image.open(EXPAND_FILE), size=(8, 8))
        self.icon_image = PhotoImage(file=ICON_FILE)
        self.iconphoto(False, self.icon_image)
        if platform.system() == "Windows":
            self.iconbitmap(ICO_FILE)

        # configure layout
        self.rowconfigure(tuple(range(4)), weight=1)
        self.columnconfigure(tuple(range(6)), weight=1)
        self.columnconfigure(0, weight=5)
        self.rowconfigure(0, weight=2)
        self.rowconfigure(1, weight=2)

        # image display
        self.image_frame = CTkFrame(self)
        self.image_frame.grid(row=0, column=0, rowspan=4, sticky="news", padx=20, pady=20)

        # text = "Drop image here or click to select"
        self.image_label = CTkLabel(self.image_frame, width=560, text="", image=self.drop_image, compound="top", text_color="gray")
        self.image_label.pack(fill="both", expand=True)
        self.image_label.bind("<Button-1>", lambda e: self.display_info(self.select_image(), is_selected=True))

        self.image = None
        self.image_tk = None
        self.image_data = None
        self.default_text_colour = ThemeManager.theme["CTkTextbox"]["text_color"]

        # status bar
        self.status_bar = StatusBar(self)
        self.status_bar.status_frame.grid(row=3, column=5, columnspan=2, sticky="ew", padx=20, pady=(0, 20), ipadx=5,
                                          ipady=5)

        # text box
        self.positive_box = CTkTextbox(self, wrap="word")
        self.positive_box.grid(row=0, column=1, columnspan=5, sticky="news", pady=(20, 20))
        self.positive_box.insert("end", "Prompt")
        self.positive_box.configure(state="disabled", text_color=ACCESSIBLE_GRAY, font=self.info_font)

        self.negative_box = CTkTextbox(self, wrap="word")
        self.negative_box.grid(row=1, column=1, columnspan=5, sticky="news", pady=(0, 20))
        self.negative_box.insert("end", "Negative Prompt")
        self.negative_box.configure(state="disabled", text_color=ACCESSIBLE_GRAY, font=self.info_font)

        self.setting_box = CTkTextbox(self, wrap="word", height=100)
        self.setting_box.grid(row=2, column=1, columnspan=5, sticky="news", pady=(0, 20))
        self.setting_box.insert("end", "Setting")
        self.setting_box.configure(state="disabled", text_color=ACCESSIBLE_GRAY, font=self.info_font)

        # copy buttons
        self.button_positive = CTkButton(self, width=50, height=50, image=self.clipboard_image, text="",
                                         command=lambda: self.copy_to_clipboard(self.image_data.positive))
        self.button_positive.grid(row=0, column=6, padx=20, pady=(20, 20))

        self.button_negative = CTkButton(self, width=50, height=50, image=self.clipboard_image, text="",
                                         command=lambda: self.copy_to_clipboard(self.image_data.negative))
        self.button_negative.grid(row=1, column=6, padx=20, pady=(0, 20))

        self.button_raw = CTkButton(self, width=120, height=50, image=self.clipboard_image, text="Raw Data",
                                    font=self.info_font, command=lambda: self.copy_to_clipboard(self.image_data.raw))
        self.button_raw.grid(row=3, column=4, pady=(0, 20))

        # setting switch
        # switch_setting_frame = CTkFrame(window, fg_color="transparent")
        # switch_setting_frame.grid(row=2, column=5, pady=(0, 20))
        # switch_setting = CTkSwitch(switch_setting_frame, switch_width=50, switch_height=25, width=50, text="",
        # font=info_font)
        # switch_setting.pack(side=TOP)
        # switch_setting_text = CTkLabel(switch_setting_frame, text="Display\nMode")
        # switch_setting_text.pack(side=TOP)

        # function buttons
        self.button_remove_option = CTkOptionMenu(self, width=50, height=50,
                                                  font=self.info_font, dynamic_resizing=False,
                                                  values=["select directory",
                                                          "overwrite the original image"],
                                                  command=self.remove_data)
        self.button_remove = CTkButton(self, width=108, height=50, image=self.remove_tag_image, text="Remove\n Data",
                                       font=self.info_font, command=lambda: self.remove_data())
        self.button_remove.grid(row=3, column=2, pady=(0, 20), padx=(0, 15), sticky="w")
        self.button_remove_option_arrow = CTkButton(self, width=10, height=50, text="", image=self.expand_arrow_image,
                                                    font=CTkFont(size=20, weight="bold"),
                                                    command=lambda: self.button_remove_option_open())
        self.button_remove_option_arrow.grid(row=3, column=2, pady=(0, 20), padx=(110, 15), sticky="w")

        self.button_export_option = CTkOptionMenu(self, width=50, height=50,
                                                  font=self.info_font, dynamic_resizing=False,
                                                  values=["select directory"],
                                                  command=self.export_txt)
        self.button_export = CTkButton(self, width=108, height=50, image=self.document_image, text="Export\nto txt",
                                       font=self.info_font, command=lambda: self.export_txt())
        self.button_export.grid(row=3, column=3, pady=(0, 20), padx=(0, 15), sticky="w")
        self.button_export_option_arrow = CTkButton(self, width=10, height=50, text="", image=self.expand_arrow_image,
                                                    font=CTkFont(size=20, weight="bold"),
                                                    command=lambda: self.button_export_option_open())
        self.button_export_option_arrow.grid(row=3, column=3, pady=(0, 20), padx=(110, 15), sticky="w")

        # text boxes and buttons
        self.boxes = [self.positive_box, self.negative_box, self.setting_box]
        self.buttons = [self.button_positive, self.button_negative, self.button_raw,
                        self.button_export, self.button_export_option_arrow,
                        self.button_remove, self.button_remove_option_arrow]

        for button in self.buttons:
            button.configure(state="disabled")

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
        # tmp
        self.button_tmp = CTkButton(self.positive_box, width=30, height=30, image=self.document_image, text="",
                                       bg_color="transparent")
        self.button_tmp.grid(row=0, column=1, pady=(0, 15), padx=(15, 15), sticky="se")

        tooltip_1 = CTkToolTip(self.button_remove, delay=TOOLTIP_DELAY, message="test test test")


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
                        box.configure(state="disabled", text_color=self.default_text_colour)
                    for button in self.buttons:
                        button.configure(state="normal")
                    self.status_bar.success(self.image_data.tool)
                self.image = Image.open(f)
                self.image_tk = CTkImage(self.image)
                self.resize_image()
        else:
            self.unsupported_format(MESSAGE["suffix_error"], True)

    def unsupported_format(self, message, reset_image=False):
        for box in self.boxes:
            box.insert("end", message[0])
            box.configure(state="disabled", text_color="gray")
        for button in self.buttons:
            button.configure(state="disabled")
        if reset_image:
            self.image_label.configure(image=self.drop_image)
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
            self.image_label.configure(image=self.image_tk)

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
    def select_image():
        return filedialog.askopenfilename(
            title='Select your image file',
            initialdir="/",
            filetypes=(("image files", "*.png *.jpg *jpeg *.webp"),)
        )


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
