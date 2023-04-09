# -*- encoding:utf-8 -*-
__author__ = 'receyuki'
__filename__ = 'main.py'
__copyright__ = 'Copyright 2023'
__email__ = 'receyuki@gmail.com'

import threading
import requests
import pyperclip as pyperclip
from PIL import Image, ImageTk
from tkinter import TOP, END, Frame, Text, LEFT, Scrollbar, VERTICAL, RIGHT, Y, BOTH, X, Canvas, DISABLED, NORMAL, \
    WORD, BOTTOM, CENTER, Label, ttk, PhotoImage, filedialog
from tkinter.ttk import *
from tkinterdnd2 import *
from os import path, name
from customtkinter import *
from packaging import version
import webbrowser

from sd_prompt_reader.image_data_reader import ImageDataReader

bundle_dir = path.abspath(path.dirname(__file__))
current_version = "1.1.0"
release_url = "https://api.github.com/repos/receyuki/stable-diffusion-prompt-reader/releases/latest"
info_file = path.join(bundle_dir, "../resources/info.png")
error_file = path.join(bundle_dir, "../resources/error.png")
box_important_file = path.join(bundle_dir, "../resources/box-important.png")
ok_file = path.join(bundle_dir, "../resources/ok.png")
available_updates_file = path.join(bundle_dir, "../resources/available-updates.png")
drop_file = path.join(bundle_dir, "../resources/drag-and-drop.png")
clipboard_file = path.join(bundle_dir, "../resources/copy-to-clipboard.png")
remove_tag_file = path.join(bundle_dir, "../resources/remove-tag.png")
icon_file = path.join(bundle_dir, "../resources/icon.png")
ico_file = path.join(bundle_dir, "../resources/icon.ico")


# Make dnd work with ctk
class Tk(CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


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

        self.info_image = CTkImage(self.add_margin(Image.open(info_file), 0, 0, 0, 33), size=(40, 30))
        self.error_image = CTkImage(self.add_margin(Image.open(error_file), 0, 0, 0, 33), size=(40, 30))
        self.box_important_image = CTkImage(self.add_margin(Image.open(box_important_file), 0, 0, 0, 33), size=(40, 30))
        self.ok_image = CTkImage(self.add_margin(Image.open(ok_file), 0, 0, 0, 33), size=(40, 30))
        self.available_updates_image = CTkImage(self.add_margin(Image.open(available_updates_file), 0, 0, 0, 33),
                                                size=(40, 30))
        self.drop_image = CTkImage(Image.open(drop_file), size=(100, 100))
        self.clipboard_image = CTkImage(Image.open(clipboard_file), size=(50, 50))
        self.remove_tag_image = CTkImage(Image.open(remove_tag_file), size=(50, 50))
        self.icon_image = PhotoImage(file=icon_file)
        self.iconphoto(False, self.icon_image)
        if name == "nt":
            self.iconbitmap(ico_file)

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
        self.info = {}
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
                                         command=lambda: self.copy_to_clipboard(self.info.get("positive")))
        self.button_positive.grid(row=0, column=5, padx=20, pady=(20, 20))

        self.button_negative = CTkButton(self, width=50, height=50, image=self.clipboard_image, text="",
                                         command=lambda: self.copy_to_clipboard(self.info.get("negative")))
        self.button_negative.grid(row=1, column=5, padx=20, pady=(0, 20))

        self.button_raw = CTkButton(self, width=50, height=50, image=self.clipboard_image, text="Raw Data",
                                    font=self.info_font, command=lambda: self.copy_to_clipboard(self.info.get("raw")))
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

        self.update_check = True

        self.update_thread = threading.Thread(target=self.check_update)
        self.update_thread.start()

    def display_info(self, event, is_selected=False):
        # stop update thread when reading first image
        if self.update_check:
            self.close_update_thread()
        # select or drag and drop
        if is_selected:
            if event == "":
                return
            file_path = event
        else:
            file_path = event.data.replace("}", "").replace("{", "")
        # clear text
        for box in self.boxes:
            box.configure(state=NORMAL)
            box.delete("1.0", END)
        if file_path.lower().endswith(".png") or \
                file_path.lower().endswith(".jpg") or \
                file_path.lower().endswith(".jpeg") or \
                file_path.lower().endswith(".webp"):
            with open(file_path, "rb") as f:
                # text_line, _ = image_data(f)
                # info = image_info_format(text_line)
                image_data = ImageDataReader(f)
                self.info = {"positive": image_data.positive,
                             "negative": image_data.negative,
                             "setting": image_data.setting,
                             "raw": image_data.raw}
                if not image_data.raw:
                    for box in self.boxes:
                        box.insert(END, "No data")
                        box.configure(state=DISABLED, text_color="gray")
                    self.status_label.configure(image=self.box_important_image,
                                                text="No data detected or unsupported format")
                    for button in self.buttons:
                        button.configure(state=DISABLED)
                else:
                    # insert prompt
                    self.positive_box.insert(END, image_data.positive)
                    self.negative_box.insert(END, image_data.negative)
                    self.setting_box.insert(END, image_data.setting)
                    for box in self.boxes:
                        box.configure(state=DISABLED, text_color=self.default_text_colour)
                    self.status_label.configure(image=self.ok_image, text="Voilà!")
                    for button in self.buttons:
                        button.configure(state=NORMAL)
                self.image = Image.open(f)
                self.image_tk = CTkImage(self.image)
                self.resize_image()
        else:
            for box in self.boxes:
                box.insert(END, "Unsupported format")
                box.configure(state=DISABLED, text_color="gray")
                self.image_label.configure(image=self.drop_image)
                self.image = None
                self.status_label.configure(image=self.box_important_image, text="Unsupported format")
            for button in self.buttons:
                button.configure(state=DISABLED)

    def resize_image(self, event=None):
        # resize image to window size
        if self.image:
            aspect_ratio = self.image.size[0] / self.image.size[1]
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

    # async def check_update():
    def check_update(self):
        try:
            response = requests.get(release_url, timeout=3).json()
        except Exception:
            print("Github api connection error")
        else:
            latest = response["name"]
            if version.parse(latest) > version.parse(current_version):
                download_url = response["html_url"]
                self.status_label.configure(image=self.available_updates_image,
                                            text="A new version is available, click here to download")
                self.status_label.bind("<Button-1>", lambda e: webbrowser.open_new(download_url))

    # clean up threads that are no longer in use
    def close_update_thread(self):
        self.update_check = False
        self.status_label.unbind("<Button-1>")
        self.update_thread.join()

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
            filetypes=(("PNG files", "*.png"), ("JPEG files", "*.jpg *jpeg"), ("WEBP files", "*.webp"))
        )


if __name__ == "__main__":
    app = App()
    app.mainloop()
