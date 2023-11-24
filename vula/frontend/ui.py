import gettext
import tkinter as tk
from tkinter import Button, Canvas, Frame, PhotoImage

from vula import common
from vula.frontend import DataProvider
from vula.frontend.constants import (
    BACKGROUND_COLOR,
    FONT,
    FONT_SIZE_HEADER,
    FONT_SIZE_TEXT_L,
    FONT_SIZE_TEXT_XL,
    HEIGHT,
    IMAGE_BASE_PATH,
    TEXT_COLOR_HEADER,
    TEXT_COLOR_WHITE,
    WIDTH,
)
from vula.frontend.overlay import (
    DescriptorOverlay,
    HelpOverlay,
    VerificationKeyOverlay,
)
from vula.frontend.view import Peers, Prefs

_ = gettext.gettext


class App(tk.Tk):
    def __init__(self, *args, **kwargs) -> None:
        data = DataProvider()
        tk.Tk.__init__(self, *args, **kwargs)

        self.geometry("{}x{}".format(WIDTH, HEIGHT))
        self.config(bg=BACKGROUND_COLOR)

        # create all of the main containers
        header_frame = Frame(
            self, bg=BACKGROUND_COLOR, width=1200, height=50, pady=3
        )
        content_frame = Frame(
            self, bg=BACKGROUND_COLOR, width=1200, height=600, padx=3, pady=3
        )
        footer_frame = Frame(
            self, bg=BACKGROUND_COLOR, width=1200, height=150, pady=30, padx=30
        )
        bottom_frame = Frame(
            self, bg=BACKGROUND_COLOR, width=600, height=50, pady=3
        )

        # layout all of the main containers
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header_frame.grid(row=0, sticky="ew")
        content_frame.grid(row=1, sticky="nsew")
        footer_frame.grid(row=2, sticky="e")
        bottom_frame.grid(row=3, sticky="s")

        # create the center widgets
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)

        pref_frame = Frame(
            content_frame,
            bg=BACKGROUND_COLOR,
            width=600,
            height=600,
            padx=3,
            pady=3,
        )
        pref_frame.grid(row=0, column=0, sticky="ns")
        pref_frame.grid_propagate(0)
        self.prefs = Prefs(pref_frame)

        peers_frame = Frame(
            content_frame,
            bg=BACKGROUND_COLOR,
            width=600,
            height=600,
            padx=3,
            pady=3,
        )
        peers_frame.grid(row=0, column=1, sticky="nsew")
        peers_frame.grid_propagate(0)
        self.peers_new = Peers(peers_frame)

        peers_frame.grid_columnconfigure(0, weight=1)

        header = Canvas(
            header_frame,
            bg=BACKGROUND_COLOR,
            height=50,
            width=1200,
            bd=0,
            highlightthickness=0,
            relief="ridge",
        )

        header.place(x=0, y=0)
        header.create_text(
            30.0,
            10.0,
            anchor="nw",
            text="Dashboard",
            fill=TEXT_COLOR_HEADER,
            font=(FONT, FONT_SIZE_HEADER),
        )

        footer_frame.grid_rowconfigure(1, weight=1)
        footer_frame.grid_columnconfigure(1, weight=1)

        vk_label = tk.Label(
            footer_frame,
            text="Verification Key:",
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR_WHITE,
            font=(FONT, FONT_SIZE_TEXT_L),
        )
        vk_label.grid(row=0, column=0, sticky="w")

        self.button_image = PhotoImage(file=IMAGE_BASE_PATH + 'show_qr.png')
        vk_button = tk.Button(
            footer_frame,
            text="Show QR",
            image=self.button_image,
            borderwidth=0,
            highlightthickness=0,
            relief="sunken",
            background=BACKGROUND_COLOR,
            activebackground=BACKGROUND_COLOR,
            activeforeground=BACKGROUND_COLOR,
            command=lambda: self.open_vk_qr_code(),
        )
        vk_button.grid(row=0, column=1)

        desc_label = tk.Label(
            footer_frame,
            text="Descriptor:",
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR_WHITE,
            font=(FONT, FONT_SIZE_TEXT_L),
        )
        desc_label.grid(row=1, column=0, sticky="w")

        desc = DescriptorOverlay(self)

        desc_button = tk.Button(
            footer_frame,
            text="Show QR",
            image=self.button_image,
            borderwidth=0,
            highlightthickness=0,
            relief="sunken",
            background=BACKGROUND_COLOR,
            activebackground=BACKGROUND_COLOR,
            activeforeground=BACKGROUND_COLOR,
            command=lambda: desc.openNewWindow(),
        )
        desc_button.grid(row=1, column=1)

        # Get the status of the different vula processes
        state = data.get_status()

        # Display the status at the bottom
        status_label = tk.Label(
            bottom_frame,
            text=f'Publish: {_(state["publish"])} '
            f'\t Discover: {_(state["discover"])} '
            f'\t Organize: {_(state["organize"])}',
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR_WHITE,
            font=(FONT, FONT_SIZE_TEXT_XL),
        )
        status_label.grid(row=0, column=0)

        # Add different command
        self.button_image_rediscover = PhotoImage(
            file=IMAGE_BASE_PATH + 'rediscover.png'
        )
        btn_Rediscover = Button(
            bottom_frame,
            text="Rediscover",
            image=self.button_image_rediscover,
            borderwidth=0,
            highlightthickness=0,
            relief="sunken",
            background=BACKGROUND_COLOR,
            activebackground=BACKGROUND_COLOR,
            activeforeground=BACKGROUND_COLOR,
            command=lambda: self.rediscover(),
        )
        self.button_image_repair = PhotoImage(
            file=IMAGE_BASE_PATH + 'repair.png'
        )
        btn_Repair = Button(
            bottom_frame,
            text="Repair",
            image=self.button_image_repair,
            command=lambda: self.repair(),
            borderwidth=0,
            highlightthickness=0,
            relief="sunken",
            background=BACKGROUND_COLOR,
            activebackground=BACKGROUND_COLOR,
            activeforeground=BACKGROUND_COLOR,
        )
        self.button_image_gate = PhotoImage(
            file=IMAGE_BASE_PATH + 'release_gateway.png'
        )
        btn_Release_Gateway = Button(
            bottom_frame,
            text="Release Gateway",
            image=self.button_image_gate,
            command=lambda: self.release_gateway(),
            borderwidth=0,
            highlightthickness=0,
            relief="sunken",
            background=BACKGROUND_COLOR,
            activebackground=BACKGROUND_COLOR,
            activeforeground=BACKGROUND_COLOR,
        )

        info_Help = HelpOverlay(self)

        self.button_image_help = PhotoImage(file=IMAGE_BASE_PATH + 'help.png')
        btn_Help = Button(
            bottom_frame,
            text="Help",
            image=self.button_image_help,
            command=lambda: info_Help.openNewWindow(),
            borderwidth=0,
            highlightthickness=0,
            relief="sunken",
            background=BACKGROUND_COLOR,
            activebackground=BACKGROUND_COLOR,
            activeforeground=BACKGROUND_COLOR,
        )
        btn_Rediscover.grid(row=0, column=1, pady=(20, 20), padx=(40, 20))
        btn_Repair.grid(row=0, column=2, pady=(20, 20), padx=(20, 20))
        btn_Release_Gateway.grid(row=0, column=3, pady=(20, 20), padx=(20, 20))
        btn_Help.grid(row=0, column=4, pady=(20, 20), padx=(20, 20))

    def rediscover(self) -> None:
        common.organize_dbus_if_active().rediscover()

    def release_gateway(self) -> None:
        common.organize_dbus_if_active().release_gateway()

    def repair(self) -> None:
        common.organize_dbus_if_active().sync(True)

    def open_vk_qr_code(self) -> None:
        VerificationKeyOverlay(self)


def main() -> None:
    try:
        app = App()
        app.title("Vula")
        app.mainloop()
    except RuntimeError as e:
        print(e)
