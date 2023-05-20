# -*- encoding:utf-8 -*-
__author__ = 'receyuki'
__filename__ = 'button.py'
__copyright__ = 'Copyright 2023, '
__email__ = 'receyuki@gmail.com'

import tkinter
from enum import Enum
from typing import Union, Tuple, Callable, Optional

from customtkinter import CTkButton, CTkImage, CTkFont, CTkLabel

from sd_prompt_reader.constants import ACCESSIBLE_GRAY, INACCESSIBLE_GRAY, BUTTON_HOVER


class STkButton(CTkButton):
    def __init__(self,
                 master: any,
                 width: int = 140,
                 height: int = 28,
                 corner_radius: Optional[int] = None,
                 border_width: Optional[int] = None,
                 border_spacing: int = 2,

                 bg_color: Union[str, Tuple[str, str]] = "transparent",
                 fg_color: Optional[Union[str, Tuple[str, str]]] = None,
                 hover_color: Optional[Union[str, Tuple[str, str]]] = None,
                 border_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color: Optional[Union[str, Tuple[str, str]]] = None,
                 text_color_disabled: Optional[Union[str, Tuple[str, str]]] = None,

                 background_corner_colors: Union[Tuple[Union[str, Tuple[str, str]]], None] = None,
                 round_width_to_even_numbers: bool = True,
                 round_height_to_even_numbers: bool = True,

                 text: str = "CTkButton",
                 font: Optional[Union[tuple, CTkFont]] = None,
                 textvariable: Union[tkinter.Variable, None] = None,
                 image: Union[Tuple[CTkImage, CTkImage], None] = None,
                 state: str = "normal",
                 hover: bool = True,
                 command: Union[Callable[[], None], None] = None,
                 compound: str = "left",
                 anchor: str = "center",
                 label: CTkLabel = None,
                 arrow=None,
                 mode: Enum = None,
                 **kwargs):

        self.image = image
        self._label = label
        self._arrow = arrow
        self._mode = mode

        super().__init__(master=master,
                         width=width,
                         height=height,
                         corner_radius=corner_radius,
                         border_width=border_width,
                         border_spacing=border_spacing,

                         bg_color=bg_color,
                         fg_color=fg_color,
                         hover_color=hover_color,
                         border_color=border_color,
                         text_color=text_color,
                         text_color_disabled=text_color_disabled,

                         background_corner_colors=background_corner_colors,
                         round_width_to_even_numbers=round_width_to_even_numbers,
                         round_height_to_even_numbers=round_height_to_even_numbers,

                         text=text,
                         font=font,
                         textvariable=textvariable,
                         image=self.image[0],
                         state=state,
                         hover=hover,
                         command=command,
                         compound=compound,
                         anchor=anchor,
                         **kwargs)

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, label: CTkLabel = None):
        self._label = label

    @property
    def arrow(self):
        return self._arrow

    @arrow.setter
    def arrow(self, arrow):
        self._arrow = arrow

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, mode):
        self._mode = mode

    def disable(self):
        self.configure(state="disabled")
        self.configure(image=self.image[1])
        if self._label:
            self._label.configure(text_color=INACCESSIBLE_GRAY)
        if self._arrow:
            self._arrow.disable()

    def enable(self):
        self.configure(state="normal")
        self.configure(image=self.image[0])
        if self._label:
            self._label.configure(text_color=ACCESSIBLE_GRAY)
        if self._arrow:
            self._arrow.enable()

    def switch_on(self):
        self.configure(fg_color=BUTTON_HOVER)

    def switch_off(self):
        self.configure(fg_color="transparent")


class ViewMode(Enum):
    NORMAL = 0
    VERTICAL = 1


class SortMode(Enum):
    OFF = 0
    ASC = 1
    DES = 2
