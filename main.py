# import asyncio
import threading
# import piexif
# from piexif import helper
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

bundle_dir = path.abspath(path.dirname(__file__))
current_version = "1.1.0"


# Make dnd work with ctk
class Tk(CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


# Modified from:
# https://github.com/AUTOMATIC1111/stable-diffusion-webui/blob/22bcc7be428c94e9408f589966c2040187245d81/modules/images.py#L614
def read_info_from_image(image):
    items = image.info or {}

    geninfo = items.pop('parameters', None)

    # if "exif" in items:
    #     exif = piexif.load(items["exif"])
    #     exif_comment = (exif or {}).get("Exif", {}).get(piexif.ExifIFD.UserComment, b'')
    #     try:
    #         exif_comment = piexif.helper.UserComment.load(exif_comment)
    #     except ValueError:
    #         exif_comment = exif_comment.decode('utf8', errors="ignore")
    #
    #     if exif_comment:
    #         items['exif comment'] = exif_comment
    #         geninfo = exif_comment
    #
    #     for field in ['jfif', 'jfif_version', 'jfif_unit', 'jfif_density', 'dpi', 'exif',
    #                   'loop', 'background', 'timestamp', 'duration']:
    #         items.pop(field, None)

    #     if items.get("Software", None) == "NovelAI":
    #         try:
    #             json_info = json.loads(items["Comment"])
    #             sampler = sd_samplers.samplers_map.get(json_info["sampler"], "Euler a")
    #
    #             geninfo = f"""{items["Description"]}
    # Negative prompt: {json_info["uc"]}
    # Steps: {json_info["steps"]}, Sampler: {sampler}, CFG scale: {json_info["scale"]}, Seed: {json_info["seed"]}, Size: {image.width}x{image.height}, Clip skip: 2, ENSD: 31337"""
    #         except Exception:
    #             print("Error parsing NovelAI image generation parameters:", file=sys.stderr)
    #             print(traceback.format_exc(), file=sys.stderr)

    return geninfo, items


# Modified from:
# https://github.com/AUTOMATIC1111/stable-diffusion-webui/blob/22bcc7be428c94e9408f589966c2040187245d81/modules/images.py#L650
def image_data(file):
    try:
        image = Image.open(file)
        textinfo, _ = read_info_from_image(image)
        return textinfo, None
    except Exception:
        pass

    # try:
    #     text = data.decode('utf8')
    #     assert len(text) < 10000
    #     return text, None
    #
    # except Exception:
    #     pass

    return '', None


def image_info_format(text):
    if text:
        prompt_index = [text.index("\nNegative prompt:"),
                        text.index("\nSteps:")]
        positive = text[:prompt_index[0]]
        negative = text[prompt_index[0] + 1 + len("Negative prompt: "):prompt_index[1]]
        setting = text[prompt_index[1] + 1:]
        return positive, negative, setting, text
    else:
        return None


def display_info(event, is_selected=False):
    global image, image_tk, image_label, info, scaling
    # stop update thread when reading first image
    if update_check:
        close_update_thread()
    # select or drag and drop
    if is_selected:
        if event == "":
            return
        file_path = event
    else:
        file_path = event.data.replace("}", "").replace("{", "")
    # clear text
    for box in boxes:
        box.configure(state=NORMAL)
        box.delete("1.0", END)
    if file_path.lower().endswith(".png"):
        with open(file_path, "rb") as f:
            text_line, _ = image_data(f)
            info = image_info_format(text_line)
            if not info:
                for box in boxes:
                    box.insert(END, "No data")
                    box.configure(state=DISABLED, text_color="gray")
                status_label.configure(image=box_important_image, text="No data detected or unsupported format")
                for button in buttons:
                    button.configure(state=DISABLED)
            else:
                # insert prompt
                positive_box.insert(END, info[0])
                negative_box.insert(END, info[1])
                setting_box.insert(END, info[2])
                for box in boxes:
                    box.configure(state=DISABLED, text_color=default_text_colour)
                status_label.configure(image=ok_image, text="Voilà!")
                for button in buttons:
                    button.configure(state=NORMAL)
            image = Image.open(f)
            image_tk = CTkImage(image)
            resize_image()
            # aspect_ratio = image.size[0] / image.size[1]
            # scaling = ScalingTracker.get_window_dpi_scaling(window)
            # # resize image to window size
            # if image.size[0] > image.size[1]:
            #     image_tk.configure(size=tuple(num / scaling for num in
            #                                   (image_frame.winfo_height(), image_frame.winfo_height() / aspect_ratio)))
            # else:
            #     image_tk.configure(size=tuple(num / scaling for num in
            #                                   (image_label.winfo_height() * aspect_ratio, image_label.winfo_height())))
            # # display image
            # image_label.configure(image=image_tk)
    else:
        for box in boxes:
            box.insert(END, "Unsupported format")
            box.configure(state=DISABLED, text_color="gray")
            image_label.configure(image=drop_image)
            image = None
            status_label.configure(image=box_important_image, text="Unsupported format")
        for button in buttons:
            button.configure(state=DISABLED)


def resize_image(event=None):
    # resize image to window size
    global image, image_label, image_tk, scaling
    if image:
        aspect_ratio = image.size[0] / image.size[1]
        scaling = ScalingTracker.get_window_dpi_scaling(window)
        # resize image to window size
        if image.size[0] > image.size[1]:
            image_tk.configure(size=tuple(num / scaling for num in
                                          (image_frame.winfo_height(), image_frame.winfo_height() / aspect_ratio)))
        else:
            image_tk.configure(size=tuple(num / scaling for num in
                                          (image_label.winfo_height() * aspect_ratio, image_label.winfo_height())))
        # display image
        image_label.configure(image=image_tk)


def copy_to_clipboard(content):
    try:
        pyperclip.copy(content)
    except:
        print("Copy error")
    else:
        status_label.configure(image=ok_image, text="Copied to clipboard")


def add_margin(img, top, bottom, left, right):
    width, height = img.size
    new_width = width + right + left
    new_height = height + top + bottom
    result = Image.new(img.mode, (new_width, new_height))
    result.paste(img, (left, top))
    return result


def select_image():
    return filedialog.askopenfilename(
        title='Select your image file',
        initialdir="/",
        filetypes=(("png files", "*.png"),)
    )


# async def check_update():
def check_update():
    url = "https://api.github.com/repos/receyuki/stable-diffusion-prompt-reader/releases/latest"
    # async with aiohttp.request("GET", url, timeout=aiohttp.ClientTimeout(total=1)) as resp:
    #     assert resp.status == 200
    #     data = await resp.json()
    #     print(data["name"])
    #     latest = data["name"]
    # async_loop.call_soon_threadsafe(async_loop.stop)
    try:
        response = requests.get(url, timeout=3).json()
    except Exception:
        print("Github api connection error")
    else:
        latest = response["name"]
        if version.parse(latest) > version.parse(current_version):
            download_url = response["html_url"]
            status_label.configure(image=available_updates_image,
                                   text="A new version is available, click here to download")
            status_label.bind("<Button-1>", lambda e: webbrowser.open_new(download_url))


# clean up threads that are no longer in use
def close_update_thread():
    global update_check
    update_check = False
    status_label.unbind("<Button-1>")
    # async_loop.call_soon_threadsafe(async_loop.stop)
    # async_loop.close()
    update_thread.join()


def get_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


# window = TkinterDnD.Tk()
window = Tk()
window.title("SD Prompt Reader")
window.geometry("1200x650")

# set_appearance_mode("Light")
# deactivate_automatic_dpi_awareness()
# set_widget_scaling(1)
# set_window_scaling(0.8)
# info_font = CTkFont(size=20)
info_font = CTkFont()
scaling = ScalingTracker.get_window_dpi_scaling(window)

add_file = path.join(bundle_dir, "resources/add.png")
add_image = CTkImage(add_margin(Image.open(add_file), 0, 0, 0, 33), size=(40, 30))
error_file = path.join(bundle_dir, "resources/error.png")
error_image = CTkImage(add_margin(Image.open(error_file), 0, 0, 0, 33), size=(40, 30))
box_important_file = path.join(bundle_dir, "resources/box-important.png")
box_important_image = CTkImage(add_margin(Image.open(box_important_file), 0, 0, 0, 33), size=(40, 30))
ok_file = path.join(bundle_dir, "resources/ok.png")
ok_image = CTkImage(add_margin(Image.open(ok_file), 0, 0, 0, 33), size=(40, 30))
available_updates_file = path.join(bundle_dir, "resources/available-updates.png")
available_updates_image = CTkImage(add_margin(Image.open(available_updates_file), 0, 0, 0, 33), size=(40, 30))
drop_file = path.join(bundle_dir, "resources/drag-and-drop.png")
drop_image = CTkImage(light_image=Image.open(drop_file), dark_image=Image.open(drop_file), size=(100, 100))
clipboard_file = path.join(bundle_dir, "resources/copy-to-clipboard.png")
clipboard_image = CTkImage(light_image=Image.open(clipboard_file), dark_image=Image.open(clipboard_file), size=(50, 50))

icon_file = path.join(bundle_dir, "resources/icon.png")
ico_file = path.join(bundle_dir, "resources/icon.ico")
icon_image = PhotoImage(file=icon_file)
window.iconphoto(False, icon_image)
if name == "nt":
    window.iconbitmap(ico_file)

window.rowconfigure(tuple(range(4)), weight=1)
window.columnconfigure(tuple(range(5)), weight=1)
window.columnconfigure(0, weight=5)
window.rowconfigure(0, weight=2)
window.rowconfigure(1, weight=2)

image_frame = CTkFrame(window)
image_frame.grid(row=0, column=0, rowspan=4, sticky="news", padx=20, pady=20)

image_label = CTkLabel(image_frame, text="", image=drop_image)
image_label.pack(fill=BOTH, expand=True)
image_label.bind("<Button-1>", lambda e: display_info(select_image(), True))

image = None
image_tk = None
info = [""] * 4

positive_box = CTkTextbox(window, wrap=WORD)
positive_box.grid(row=0, column=1, columnspan=4, sticky="news", pady=(20, 20))
default_text_colour = positive_box._text_color
positive_box.insert(END, "Prompt")
positive_box.configure(state=DISABLED, text_color="gray", font=info_font)

negative_box = CTkTextbox(window, wrap=WORD)
negative_box.grid(row=1, column=1, columnspan=4, sticky="news", pady=(0, 20))
negative_box.insert(END, "Negative Prompt")
negative_box.configure(state=DISABLED, text_color="gray", font=info_font)

setting_box = CTkTextbox(window, wrap=WORD, height=100)
setting_box.grid(row=2, column=1, columnspan=4, sticky="news", pady=(0, 20))
setting_box.insert(END, "Setting")
setting_box.configure(state=DISABLED, text_color="gray", font=info_font)

button_positive = CTkButton(window, width=50, height=50, image=clipboard_image, text="",
                            command=lambda: copy_to_clipboard(info[0]))
button_positive.grid(row=0, column=5, padx=20, pady=(20, 20))

button_negative = CTkButton(window, width=50, height=50, image=clipboard_image, text="",
                            command=lambda: copy_to_clipboard(info[1]))
button_negative.grid(row=1, column=5, padx=20, pady=(0, 20))

button_raw = CTkButton(window, width=50, height=50, image=clipboard_image, text="Raw Data", font=info_font,
                       command=lambda: copy_to_clipboard(info[3]))
button_raw.grid(row=3, column=3, pady=(0, 20))


status = "Drag and drop your file into the window"
status_frame = CTkFrame(window, height=50)
status_frame.grid(row=3, column=4, columnspan=2, sticky="ew", padx=20, pady=(0, 20), ipadx=5, ipady=5)
status_label = CTkLabel(status_frame, height=50, text=status, text_color="gray", wraplength=130,
                        image=add_image, compound="left")
status_label.pack(side=LEFT, expand=True)

boxes = [positive_box, negative_box, setting_box]
buttons = [button_positive, button_negative, button_raw]

for button in buttons:
    button.configure(state=DISABLED)

window.drop_target_register(DND_FILES)
window.dnd_bind("<<Drop>>", display_info)
window.bind("<Configure>", resize_image)

update_check = True
# start a new thread for checking update
# async_loop = asyncio.get_event_loop()
# update_thread = threading.Thread(target=get_loop, args=(async_loop,))
update_thread = threading.Thread(target=check_update)
update_thread.start()
# asyncio.run_coroutine_threadsafe(check_update(), async_loop)
window.mainloop()
