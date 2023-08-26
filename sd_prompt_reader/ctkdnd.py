__author__ = "receyuki"
__filename__ = "ctkdnd.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

from customtkinter import *
from tkinterdnd2 import *


# Make dnd work with ctk
class Tk(CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)
