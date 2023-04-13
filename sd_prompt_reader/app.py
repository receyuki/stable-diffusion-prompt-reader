# -*- encoding:utf-8 -*-
__author__ = 'receyuki'
__filename__ = 'main.py'
__copyright__ = 'Copyright 2023'
__email__ = 'receyuki@gmail.com'

import platform
from importlib import resources
from pathlib import Path
from tkinter import PhotoImage

import pyperclip as pyperclip
from PIL import Image
from customtkinter import *
from tkinterdnd2 import DND_FILES

from sd_prompt_reader.ctkdnd import Tk
from sd_prompt_reader.image_data_reader import ImageDataReader
from sd_prompt_reader.update_checker import UpdateChecker

RESOURCE_DIR = str(resources.files("resources"))
SUPPORTED_FORMATS = [".png", ".jpg", ".jpeg", ".webp"]
INFO_FILE = Path(RESOURCE_DIR, "info.png")
ERROR_FILE = Path(RESOURCE_DIR, "error.png")
BOX_IMPORTANT_FILE = Path(RESOURCE_DIR, "box-important.png")
OK_FILE = Path(RESOURCE_DIR, "ok.png")
AVAILABLE_UPDATES_FILE = Path(RESOURCE_DIR, "available-updates.png")
DROP_FILE = Path(RESOURCE_DIR, "drag-and-drop.png")
CLIPBOARD_FILE = Path(RESOURCE_DIR, "copy-to-clipboard.png")
REMOVE_TAG_FILE = Path(RESOURCE_DIR, "remove-tag.png")
ICON_FILE = Path(RESOURCE_DIR, "icon.png")
ICO_FILE = Path(RESOURCE_DIR, "icon.ico")
MESSAGE = {
    "success": ["Voilà!"],
    "format_error": ["No data", "No data detected or unsupported format"],
    "suffix_error": ["Unsupported format"]
}


class App(Tk):
    def __init__(self):
        super().__init__()

        # window = TkinterDnD.Tk()
        # window = Tk()
        self.title("SD Prompt Reader")
        self.geometry("1200x650")
        # set_appearance_mode("Light")
        # deactivate_automatic_dpi_awareness()
        # set_widget_scaling(1)
        # set_window_scaling(0.8)
        # info_font = CTkFont(size=20)
        self.info_font = CTkFont()
        self.scaling = ScalingTracker.get_window_dpi_scaling(self)

        self.info_image = self.load_status_icon(INFO_FILE)
        self.error_image = self.load_status_icon(ERROR_FILE)
        self.box_important_image = self.load_status_icon(BOX_IMPORTANT_FILE)
        self.ok_image = self.load_status_icon(OK_FILE)
        self.available_updates_image = self.load_status_icon(AVAILABLE_UPDATES_FILE)
        self.drop_image = CTkImage(Image.open(DROP_FILE), size=(100, 100))
        self.clipboard_image = CTkImage(Image.open(CLIPBOARD_FILE), size=(50, 50))
        self.remove_tag_image = CTkImage(Image.open(REMOVE_TAG_FILE), size=(50, 50))
        self.icon_image = PhotoImage(file=ICON_FILE)
        self.iconphoto(False, self.icon_image)
        if platform.system() == "Windows":
            self.iconbitmap(ICO_FILE)

        self.rowconfigure(tuple(range(4)), weight=1)
        self.columnconfigure(tuple(range(5)), weight=1)
        self.columnconfigure(0, weight=5)
        self.rowconfigure(0, weight=2)
        self.rowconfigure(1, weight=2)

        self.image_frame = CTkFrame(self)
        self.image_frame.grid(row=0, column=0, rowspan=4, sticky="news", padx=20, pady=20)

        self.image_label = CTkLabel(self.image_frame, text="", image=self.drop_image)
        self.image_label.pack(fill=BOTH, expand=True)
        self.image_label.bind("<Button-1>", lambda e: self.display_info(self.select_image(), True))

        self.image = None
        self.image_tk = None
        self.image_data = None
        self.default_text_colour = ThemeManager.theme["CTkTextbox"]["text_color"]

        self.positive_box = CTkTextbox(self, wrap=WORD)
        self.positive_box.grid(row=0, column=1, columnspan=4, sticky="news", pady=(20, 20))
        self.positive_box.insert(END, "Prompt")
        self.positive_box.configure(state=DISABLED, text_color="gray", font=self.info_font)

        self.negative_box = CTkTextbox(self, wrap=WORD)
        self.negative_box.grid(row=1, column=1, columnspan=4, sticky="news", pady=(0, 20))
        self.negative_box.insert(END, "Negative Prompt")
        self.negative_box.configure(state=DISABLED, text_color="gray", font=self.info_font)

        self.setting_box = CTkTextbox(self, wrap=WORD, height=100)
        self.setting_box.grid(row=2, column=1, columnspan=4, sticky="news", pady=(0, 20))
        self.setting_box.insert(END, "Setting")
        self.setting_box.configure(state=DISABLED, text_color="gray", font=self.info_font)

        self.button_positive = CTkButton(self, width=50, height=50, image=self.clipboard_image, text="",
                                         command=lambda: self.copy_to_clipboard(self.image_data.positive))
        self.button_positive.grid(row=0, column=5, padx=20, pady=(20, 20))

        self.button_negative = CTkButton(self, width=50, height=50, image=self.clipboard_image, text="",
                                         command=lambda: self.copy_to_clipboard(self.image_data.negative))
        self.button_negative.grid(row=1, column=5, padx=20, pady=(0, 20))

        self.button_raw = CTkButton(self, width=50, height=50, image=self.clipboard_image, text="Raw Data",
                                    font=self.info_font, command=lambda: self.copy_to_clipboard(self.image_data.raw))
        self.button_raw.grid(row=3, column=3, pady=(0, 20))

        # switch_setting_frame = CTkFrame(window, fg_color="transparent")
        # switch_setting_frame.grid(row=2, column=5, pady=(0, 20))
        # switch_setting = CTkSwitch(switch_setting_frame, switch_width=50, switch_height=25, width=50, text="", font=info_font)
        # switch_setting.pack(side=TOP)
        # switch_setting_text = CTkLabel(switch_setting_frame, text="Display\nMode")
        # switch_setting_text.pack(side=TOP)

        # button_remove = CTkButton(window, width=50, height=50, image=remove_tag_image, text="Remove\n Metadata",
        #                           font=info_font, command=lambda: copy_to_clipboard(info[3]))
        # button_remove.grid(row=3, column=2, pady=(0, 20))

        self.status = "Drag and drop your file into the window"
        self.status_frame = CTkFrame(self, height=50)
        self.status_frame.grid(row=3, column=4, columnspan=2, sticky="ew", padx=20, pady=(0, 20), ipadx=5, ipady=5)
        self.status_label = CTkLabel(self.status_frame, height=50, text=self.status, text_color="gray", wraplength=130,
                                     image=self.info_image, compound="left")
        self.status_label.pack(side=LEFT, expand=True)

        self.boxes = [self.positive_box, self.negative_box, self.setting_box]
        self.buttons = [self.button_positive, self.button_negative, self.button_raw]

        for button in self.buttons:
            button.configure(state=DISABLED)

        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self.display_info)
        self.bind("<Configure>", self.resize_image)

        self.update_checker = UpdateChecker(self.status_label, self.available_updates_image)

    def display_info(self, event, is_selected=False):
        # stop update thread when reading first image
        self.update_checker.close_thread()
        # select or drag and drop
        if is_selected:
            if event == "":
                return
            file_path = Path(event)
        else:
            file_path = Path(event.data.replace("}", "").replace("{", ""))

        # clear text
        for box in self.boxes:
            box.configure(state=NORMAL)
            box.delete("1.0", END)

        if file_path.suffix in SUPPORTED_FORMATS:
            with open(file_path, "rb") as f:
                self.image_data = ImageDataReader(f)
                if not self.image_data.raw:
                    self.unsupported_format(MESSAGE["format_error"])
                else:
                    # insert prompt
                    self.positive_box.insert(END, self.image_data.positive)
                    self.negative_box.insert(END, self.image_data.negative)
                    self.setting_box.insert(END, self.image_data.setting)
                    for box in self.boxes:
                        box.configure(state=DISABLED, text_color=self.default_text_colour)
                    for button in self.buttons:
                        button.configure(state=NORMAL)
                    self.status_label.configure(image=self.ok_image, text="Voilà!")
                self.image = Image.open(f)
                self.image_tk = CTkImage(self.image)
                self.resize_image()
        else:
            self.unsupported_format(MESSAGE["suffix_error"], True)

    def unsupported_format(self, message, reset_image=False):
        for box in self.boxes:
            box.insert(END, message[0])
            box.configure(state=DISABLED, text_color="gray")
        for button in self.buttons:
            button.configure(state=DISABLED)
        if reset_image:
            self.image_label.configure(image=self.drop_image)
            self.image = None
        self.status_label.configure(image=self.box_important_image,
                                    text=message[-1])

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
            self.status_label.configure(image=self.ok_image, text="Copied to clipboard")

    def load_status_icon(self, file):
        return CTkImage(self.add_margin(Image.open(file), 0, 0, 0, 33), size=(40, 30))

    @staticmethod
    def add_margin(img, top, bottom, left, right):
        width, height = img.size
        new_width = width + right + left
        new_height = height + top + bottom
        result = Image.new(img.mode, (new_width, new_height))
        result.paste(img, (left, top))
        return result

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
