import gettext
import json
import tkinter as tk

from vula.frontend import DataProvider
from vula.frontend.components import QRCodeLabel
from vula.frontend.constants import (
    BACKGROUND_COLOR,
    FONT,
    FONT_SIZE_HEADER,
    FONT_SIZE_TEXT_XXL,
    TEXT_COLOR_HEADER,
    TEXT_COLOR_WHITE,
)
from vula.peer import Descriptor

_ = gettext.gettext


class DescriptorOverlay(tk.Toplevel):
    def __init__(self, parent: tk.Tk) -> None:
        self.root = parent

    def openNewWindow(self) -> None:
        data = DataProvider()
        newWindow = tk.Toplevel(self.root)
        newWindow.wm_transient(self.root)

        # Root Window properties
        newWindow.title("Vula | Descriptor")
        newWindow.geometry("510x530")
        newWindow.configure(bg=BACKGROUND_COLOR)

        # Create the Frames for diffrent sections
        title_frame = tk.Frame(
            newWindow,
            bg=BACKGROUND_COLOR,
            width=510,
            height=70,
            pady=10,
            padx=10,
        )
        text_frame = tk.Frame(
            newWindow, bg=BACKGROUND_COLOR, width=510, height=50, padx=20
        )
        qr_frame = tk.Frame(
            newWindow, bg=BACKGROUND_COLOR, width=510, height=410
        )

        # Create the grid for the root TK
        newWindow.grid_rowconfigure(2, weight=1)
        newWindow.grid_columnconfigure(0, weight=1)

        # Place the Frames on the grid
        title_frame.grid(row=0, sticky="nw")
        text_frame.grid(row=1, sticky="nw")
        qr_frame.grid(row=2, sticky="nsew")

        # Add a Title to the Window
        tk.Label(
            title_frame,
            text="Descriptor",
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR_HEADER,
            font=(FONT, FONT_SIZE_HEADER),
        ).pack()

        my_descriptors = {
            ip: Descriptor(d)
            for ip, d in json.loads(data.our_latest_descriptors()).items()
        }

        for ip, desc in my_descriptors.items():
            # IP Label
            label_ip = tk.Label(
                text_frame,
                text=ip,
                bg=BACKGROUND_COLOR,
                fg=TEXT_COLOR_WHITE,
                font=(FONT, FONT_SIZE_TEXT_XXL),
            )
            label_ip.pack()

            # Descriptor QR Code Image
            qr_data = "local.vula:desc:" + str(desc)
            qr_code = QRCodeLabel(parent=qr_frame, qr_data=qr_data, resize=2)
            qr_code.configure(background=BACKGROUND_COLOR)
            qr_code.pack()
