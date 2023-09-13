__author__ = "receyuki"
__filename__ = "textbox.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

from typing import Union, Tuple, Optional

from customtkinter import CTkTextbox, CTkFont

from .constants import EDITABLE, ACCESSIBLE_GRAY


class STkTextbox(CTkTextbox):
    def __init__(
        self,
        master: any,
        width: int = 200,
        height: int = 200,
        corner_radius: Optional[int] = None,
        border_width: Optional[int] = None,
        border_spacing: int = 3,
        bg_color: Union[str, Tuple[str, str]] = "transparent",
        fg_color: Optional[Union[str, Tuple[str, str]]] = None,
        border_color: Optional[Union[str, Tuple[str, str]]] = None,
        text_color: Optional[Union[str, str]] = None,
        scrollbar_button_color: Optional[Union[str, Tuple[str, str]]] = None,
        scrollbar_button_hover_color: Optional[Union[str, Tuple[str, str]]] = None,
        font: Optional[Union[tuple, CTkFont]] = None,
        activate_scrollbars: bool = True,
        text: str = "",
        **kwargs
    ):
        self._text = text
        self.current_text = text

        super().__init__(
            master=master,
            width=width,
            height=height,
            corner_radius=corner_radius,
            border_width=border_width,
            border_spacing=border_spacing,
            bg_color=bg_color,
            fg_color=fg_color,
            border_color=border_color,
            text_color=text_color,
            scrollbar_button_color=scrollbar_button_color,
            scrollbar_button_hover_color=scrollbar_button_hover_color,
            font=font,
            activate_scrollbars=activate_scrollbars,
            **kwargs
        )

        if text:
            self.insert("end", text)
            self.configure(state="disabled")

    @property
    def ctext(self):
        return self.get("1.0", "end")

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text: str = ""):
        self._text = text
        self.current_text = text
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.insert("end", self._text)
        self.configure(state="disabled")

    def view_vertical(self):
        text = ",\n".join(
            list(
                filter(
                    None,
                    list(
                        map(
                            lambda x: x.lstrip(" "),
                            self._text.replace("\n", "").split(","),
                        )
                    ),
                )
            )
        )
        self.current_text = text
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.insert("end", text)
        self.configure(state="disabled")

    def view_normal(self):
        self.current_text = self._text
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.insert("end", self._text)
        self.configure(state="disabled")

    def sort_asc(self):
        text = "\n".join(list(filter(None, sorted(self.current_text.split("\n")))))
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.insert("end", text)
        self.configure(state="disabled")

    def sort_des(self):
        text = "\n".join(
            list(filter(None, sorted(self.current_text.split("\n"), reverse=True)))
        )
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.insert("end", text)
        self.configure(state="disabled")

    def sort_off(self):
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.insert("end", self.current_text)
        self.configure(state="disabled")

    def edit_on(self):
        self.configure(state="normal")
        self.configure(text_color=EDITABLE)

    def edit_off(self):
        self.configure(state="disabled")
        self.configure(text_color=ACCESSIBLE_GRAY)
