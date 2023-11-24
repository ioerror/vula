import gettext
import math
from tkinter import Button, Canvas, Frame, Label, PhotoImage
from typing import List

from vula.frontend import DataProvider, PeerType
from vula.frontend.constants import (
    BACKGROUND_COLOR,
    BACKGROUND_COLOR_CARD,
    FONT,
    FONT_SIZE_HEADER_2,
    FONT_SIZE_TEXT_L,
    FONT_SIZE_TEXT_M,
    FONT_SIZE_TEXT_S,
    FONT_SIZE_TEXT_XS,
    IMAGE_BASE_PATH,
    TEXT_COLOR_GREEN,
    TEXT_COLOR_GREY,
    TEXT_COLOR_HEADER_2,
    TEXT_COLOR_PURPLE,
    TEXT_COLOR_WHITE,
    TEXT_COLOR_YELLOW,
)
from vula.frontend.overlay import PeerDetailsOverlay, PopupMessage

_ = gettext.gettext


class Peers(Frame):
    data = DataProvider()

    peer_frames: List[Frame] = []

    # need to save this numbers for updating the GUI,
    # as it takes quite long for dbus to make these changes
    num_peers = 0
    num_peers_after_remove = 0

    # navigation to show more pages with peers if needed
    peer_page = 1
    peers_per_page = 5

    def __init__(self, parent: Frame) -> None:
        Frame.__init__(self, parent)
        self.app = parent

        self.display_header()
        self.display_peers()
        self.display_buttons()
        self.update_loop()

    def display_header(self) -> None:
        self.title_frame = Frame(
            self.app, bg=BACKGROUND_COLOR, width=400, height=40
        )
        title = Canvas(
            self.title_frame,
            bg=BACKGROUND_COLOR,
            height=40,
            width=400,
            bd=0,
            highlightthickness=0,
            relief="ridge",
        )
        title.place(x=0, y=0)
        title.create_text(
            0,
            0,
            anchor="nw",
            text="Peers",
            fill=TEXT_COLOR_HEADER_2,
            font=(FONT, FONT_SIZE_HEADER_2),
        )
        self.title_frame.grid(row=0, column=0, pady=(10, 0), sticky="w")

    def display_buttons(self) -> None:
        self.buttons_frame = Frame(
            self.app, bg=BACKGROUND_COLOR, width=400, height=80
        )
        self.buttons_frame.grid(row=99, column=0, sticky="w", pady=10)

        input_canvas = Canvas(
            self.buttons_frame,
            bg=BACKGROUND_COLOR,
            height=80,
            width=400,
            bd=0,
            highlightthickness=0,
            relief="ridge",
        )
        input_canvas.place(x=0, y=0)

        self.button_image_previous_page = PhotoImage(
            file=IMAGE_BASE_PATH + 'previous.png'
        )
        self.button_previous_page = Button(
            master=self.buttons_frame,
            image=self.button_image_previous_page,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.previous_page(),
            relief="flat",
        )

        self.button_image_next_page = PhotoImage(
            file=IMAGE_BASE_PATH + 'next.png'
        )
        self.button_next_page = Button(
            master=self.buttons_frame,
            image=self.button_image_next_page,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.next_page(),
            relief="flat",
        )

        if math.ceil(self.num_peers / self.peers_per_page) > 1:
            self.button_next_page.place(
                x=321.0, y=0.0, width=79.0, height=23.0
            )

    def next_page(self) -> None:
        self.peer_page += 1

        self.button_previous_page.place(
            x=232.0, y=0.0, width=79.0, height=23.0
        )
        if self.peer_page == math.ceil(self.num_peers / self.peers_per_page):
            self.button_next_page.place_forget()

        self.clear_peers()
        self.display_peers()

    def previous_page(self) -> None:
        self.peer_page -= 1

        self.button_next_page.place(x=321.0, y=0.0, width=79.0, height=23.0)
        if self.peer_page == 1:
            self.button_previous_page.place_forget()

        self.clear_peers()
        self.display_peers()

    def display_peers(self) -> None:
        peers = self.data.get_peers()
        self.num_peers = len(peers)
        counter = 1

        if self.num_peers == 0:
            no_peers_label = Label(
                self.app,
                text="No Peers to display",
                bg=BACKGROUND_COLOR,
                fg=TEXT_COLOR_WHITE,
                font=(FONT, FONT_SIZE_TEXT_L),
            )
            no_peers_label.grid(row=counter, column=0, sticky="w", pady=10)

        # Get slice of array for current page
        # [0:5], [5, 10] etc.
        peers_for_page = peers[
            (self.peer_page - 1)
            * self.peers_per_page : (self.peer_page - 1)
            * self.peers_per_page
            + self.peers_per_page
        ]

        for peer in peers_for_page:
            peer_frame = Frame(
                self.app, bg=BACKGROUND_COLOR, width=400, height=70
            )
            peer_frame.grid(row=counter, column=0, sticky="w", pady=10)

            canvas = Canvas(
                peer_frame,
                bg=BACKGROUND_COLOR,
                height=70,
                width=400,
                bd=0,
                highlightthickness=0,
                relief="ridge",
            )

            canvas.place(x=0, y=0)

            self.round_rectangle(
                canvas, 0, 0, 400, 70, r=30, fill=BACKGROUND_COLOR_CARD
            )

            if peer["name"]:
                name = peer["name"]
            else:
                name = peer["other_names"]

            # Peer name
            canvas.create_text(
                20.0,
                10.0,
                anchor="nw",
                text=name,
                fill=TEXT_COLOR_GREEN,
                font=(FONT, FONT_SIZE_TEXT_S),
            )

            # Endpoint IP
            canvas.create_text(
                20.0,
                40.0,
                anchor="nw",
                text=peer["endpoint"],
                fill=TEXT_COLOR_GREY,
                font=(FONT, FONT_SIZE_TEXT_XS),
            )

            # Status labels
            if "enabled" in peer["status"]:
                canvas.create_text(
                    205.0,
                    40.0,
                    anchor="nw",
                    text="enabled",
                    fill=TEXT_COLOR_YELLOW,
                    font=(FONT, FONT_SIZE_TEXT_M),
                )
            if "unpinned" not in peer["status"]:
                canvas.create_text(
                    270.0,
                    40.0,
                    anchor="nw",
                    text="pinned",
                    fill=TEXT_COLOR_PURPLE,
                    font=(FONT, FONT_SIZE_TEXT_M),
                )
            if "unverified" not in peer["status"]:
                canvas.create_text(
                    325.0,
                    40.0,
                    anchor="nw",
                    text="verified",
                    fill=TEXT_COLOR_GREEN,
                    font=(FONT, FONT_SIZE_TEXT_M),
                )

            canvas.bind("<Button-1>", lambda e=_, p=peer: self.open_details(p))

            self.peer_frames.append(peer_frame)
            counter += 1

    def open_details(self, peer: PeerType) -> None:
        popup = PeerDetailsOverlay(self.app, peer)
        result = popup.show()
        if result == "delete":
            self.num_peers_after_remove = self.num_peers - 1
            self.peer_page = 1
            self.clear_peers()
            self.display_peers()
        if (
            result == "pin_and_verify"
            or result == "rename"
            or result == "additional_ip"
        ):
            self.clear_peers()
            self.display_peers()

    def update_loop(self) -> None:
        # function to update the GUI after
        # removing peers (checks number of peers)
        peers = self.data.get_peers()
        if len(peers) > 0:
            if (
                len(peers) == self.num_peers_after_remove
                or len(peers) != self.num_peers
            ):
                try:
                    self.clear_peers()
                    self.display_peers()
                    self.num_peers_after_remove = 0
                except Exception:
                    PopupMessage.showPopupMessage(
                        "Error", "Could not update peers"
                    )

        # check every 5 seconds if number of peers
        # has changed.
        self.after(5000, self.update_loop)

    def clear_peers(self) -> None:
        for frame in self.peer_frames:
            frame.destroy()
        self.app.update()
        self.peer_frames.clear()

    def round_rectangle(
        self,
        canvas: Canvas,
        x: int,
        y: int,
        w: int,
        h: int,
        r=25,
        **kwargs,
    ) -> None:
        xr = x + r
        yr = y + r
        wr = w - r
        hr = h - r
        points = [
            xr,
            y,
            xr,
            y,
            wr,
            y,
            wr,
            y,
            w,
            y,
            w,
            yr,
            w,
            yr,
            w,
            hr,
            w,
            hr,
            w,
            h,
            wr,
            h,
            wr,
            h,
            xr,
            h,
            xr,
            h,
            x,
            h,
            x,
            hr,
            x,
            hr,
            x,
            yr,
            x,
            yr,
            x,
            y,
        ]
        canvas.create_polygon(points, **kwargs, smooth=True)
