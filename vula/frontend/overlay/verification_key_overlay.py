import gettext
import json
import tkinter as tk

from vula.frontend import DataProvider
from vula.frontend.components import QRCodeLabel
from vula.frontend.constants import (
    BACKGROUND_COLOR,
    FONT,
    FONT_SIZE_HEADER,
    FONT_SIZE_TEXT_L,
    IMAGE_BASE_PATH,
    TEXT_COLOR_HEADER,
    TEXT_COLOR_WHITE,
)
from vula.peer import Descriptor

from .popupMessage import PopupMessage

_ = gettext.gettext


class VerificationKeyOverlay(tk.Toplevel):
    data = DataProvider()

    def __init__(self, parent: tk.Tk) -> None:
        tk.Toplevel.__init__(self, parent)
        self.root = parent

        self.wm_transient(self.root)

        # Root Window properties
        self.title("Vula | Verification Key")
        self.geometry("510x510")
        self.configure(bg=BACKGROUND_COLOR)

        # Create the Frames for diffrent sections
        title_frame = tk.Frame(
            self,
            bg=BACKGROUND_COLOR,
            width=510,
            height=70,
            pady=10,
            padx=10,
        )
        text_frame = tk.Frame(
            self, bg=BACKGROUND_COLOR, width=510, height=50, padx=20
        )
        qr_frame = tk.Frame(self, bg=BACKGROUND_COLOR, width=510, height=390)

        # Create the grid for the root TK
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Place the Frames on the grid
        title_frame.grid(row=0, sticky="nw")
        text_frame.grid(row=1, sticky="nw")
        qr_frame.grid(row=2, sticky="nsew")

        # Add a Title to the Window
        tk.Label(
            title_frame,
            text="Verification Key",
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR_HEADER,
            font=(FONT, FONT_SIZE_HEADER),
        ).pack()

        my_descriptors = {
            ip: Descriptor(d)
            for ip, d in json.loads(self.data.our_latest_descriptors()).items()
        }

        text_frame.grid_rowconfigure(1, weight=1)
        text_frame.grid_columnconfigure(2, weight=1)
        self.button_image = tk.PhotoImage(
            file=IMAGE_BASE_PATH + 'clipboard.png'
        )

        for d in my_descriptors.values():
            vk = "{}".format(d.vk)

            # Verification Key String Label
            tk.Label(
                text_frame,
                text=vk,
                bg=BACKGROUND_COLOR,
                fg=TEXT_COLOR_WHITE,
                font=(FONT, FONT_SIZE_TEXT_L),
            ).grid(row=0, column=0)

            copy_button = tk.Button(
                text_frame,
                text="Copy",
                image=self.button_image,
                borderwidth=0,
                highlightthickness=0,
                relief="sunken",
                background=BACKGROUND_COLOR,
                activebackground=BACKGROUND_COLOR,
                activeforeground=BACKGROUND_COLOR,
                command=lambda key=vk: self.add_to_clipbaord(key),
            )
            copy_button.grid(row=0, column=1)

            # Verification Key QR Code Image
            qr_data = "local.vula:vk:" + str(vk)
            qr_code = QRCodeLabel(parent=qr_frame, qr_data=qr_data, resize=1)
            qr_code.configure(background=BACKGROUND_COLOR)
            qr_code.pack()

    def add_to_clipbaord(self, text: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(text)
        PopupMessage.showPopupMessage(
            "Information", "Verification key copied to clipboard"
        )
