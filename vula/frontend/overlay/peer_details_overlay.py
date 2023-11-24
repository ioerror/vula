import gettext
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Literal

from vula.frontend import DataProvider, PeerType
from vula.frontend.constants import (
    BACKGROUND_COLOR,
    BACKGROUND_COLOR_ENTRY,
    FONT,
    FONT_SIZE_HEADER,
    FONT_SIZE_TEXT_M,
    IMAGE_BASE_PATH,
    TEXT_COLOR_BLACK,
    TEXT_COLOR_HEADER,
    TEXT_COLOR_ORANGE,
    TEXT_COLOR_WHITE,
)

from .popupMessage import PopupMessage

_ = gettext.gettext


class PeerDetailsOverlay(tk.Toplevel):
    data = DataProvider()

    def __init__(self, parent: tk.Frame, peer: PeerType) -> None:
        tk.Toplevel.__init__(self, parent)
        self.app = parent
        self.peer = peer

        self.id = peer["id"]
        if peer["name"]:
            self.name = peer["name"]
        else:
            self.name = peer["other_names"]

        self.title("Vula | Peer Details: " + self.name)
        self.geometry("520x500")
        self.config(bg=BACKGROUND_COLOR)
        self.resizable(True, True)
        self.return_value: Literal[
            'delete', 'pin_and_verify', 'rename', 'additional_ip', None
        ] = None
        self.display_peer_details()

    def display_peer_details(self) -> None:

        self.top_frame = tk.Frame(
            self,
            bg=BACKGROUND_COLOR,
            highlightthickness=0,
            width=500,
            padx=2,
            pady=2,
        )

        self.top_canvas = tk.Canvas(
            self.top_frame,
            bg=BACKGROUND_COLOR,
            width=500,
            bd=0,
            highlightthickness=0,
            relief="ridge",
        )

        self.yscrollbar = ttk.Scrollbar(
            self.top_frame,
            orient="vertical",
            command=self.top_canvas.yview,
        )

        frame = tk.Frame(
            self.top_canvas,
            bg=BACKGROUND_COLOR,
            width=600,
            height=870,
            highlightthickness=0,
        )
        frame.grid(row=0, sticky="ew")
        self.canvas = tk.Canvas(
            frame,
            bg=BACKGROUND_COLOR,
            height=870,
            width=600,
            bd=0,
            highlightthickness=0,
            relief="ridge",
        )
        self.canvas.place(x=0, y=0)

        # Packing and configuring
        self.top_canvas.pack(side="left", fill="y", expand="yes", anchor="nw")

        self.yscrollbar.pack(side="right", fill="y")

        self.top_canvas.configure(yscrollcommand=self.yscrollbar.set)
        self.top_canvas.bind(
            '<Configure>',
            lambda e: self.top_canvas.configure(
                scrollregion=self.top_canvas.bbox('all')
            ),
        )

        self.top_canvas.create_window((0, 0), window=frame, anchor="nw")

        self.top_frame.pack(
            fill="both", expand="yes", padx=(0, 0), pady=(0, 0), side="left"
        )

        self.top_frame.columnconfigure(0, weight=1)

        self.label = tk.Label(frame, text="test")

        # Title
        self.canvas.create_text(
            33.0,
            26.0,
            anchor="nw",
            text="Peer",
            fill=TEXT_COLOR_HEADER,
            font=(FONT, FONT_SIZE_HEADER),
        )

        # Delete
        self.button_delete_image = tk.PhotoImage(
            file=IMAGE_BASE_PATH + 'delete.png'
        )
        button_delete = tk.Button(
            frame,
            image=self.button_delete_image,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.delete_peer(self.peer["id"], self.name),
            relief="sunken",
            background=BACKGROUND_COLOR,
            activebackground=BACKGROUND_COLOR,
            activeforeground=BACKGROUND_COLOR,
        )
        button_delete.place(x=450.0, y=34.0, width=39.0, height=31.0)

        # Name entry
        self.canvas.create_text(
            33.0,
            93.0,
            anchor="nw",
            text="name:",
            fill=TEXT_COLOR_WHITE,
            font=(FONT, FONT_SIZE_TEXT_M),
        )

        self.entry_image_name = tk.PhotoImage(
            file=IMAGE_BASE_PATH + 'edit_name_entry.png'
        )
        self.entry_image_name_bg = self.canvas.create_image(
            110.0, 126.5, image=self.entry_image_name
        )
        self.entry_name = tk.Entry(
            frame,
            bd=0,
            bg=BACKGROUND_COLOR_ENTRY,
            fg=TEXT_COLOR_BLACK,
            highlightthickness=0,
        )
        self.entry_name.insert(0, self.peer["name"])
        self.entry_name.place(x=45.5, y=114.0, width=129.0, height=23.0)

        # name save
        self.button_image_name = tk.PhotoImage(
            file=IMAGE_BASE_PATH + 'save.png'
        )
        button_name = tk.Button(
            frame,
            image=self.button_image_name,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.edit_peer(),
            relief="sunken",
            background=BACKGROUND_COLOR,
            activebackground=BACKGROUND_COLOR,
            activeforeground=BACKGROUND_COLOR,
        )
        button_name.place(x=190.0, y=115.0, width=34.0, height=23.0)

        # Id
        self.canvas.create_text(
            33.0,
            168.0,
            anchor="nw",
            text="id:",
            fill=TEXT_COLOR_WHITE,
            font=(FONT, FONT_SIZE_TEXT_M),
        )

        self.canvas.create_text(
            33.0,
            194.0,
            anchor="nw",
            text=self.peer["id"],
            fill=TEXT_COLOR_ORANGE,
            font=(FONT, FONT_SIZE_TEXT_M),
        )

        self.button_image_copy_id = tk.PhotoImage(
            file=IMAGE_BASE_PATH + 'clipboard.png'
        )
        button_copy_id = tk.Button(
            frame,
            image=self.button_image_copy_id,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.add_to_clipbaord(self.peer["id"]),
            relief="sunken",
            background=BACKGROUND_COLOR,
            activebackground=BACKGROUND_COLOR,
            activeforeground=BACKGROUND_COLOR,
        )
        button_copy_id.place(x=53.0, y=163.0, width=34.0, height=23.0)

        # Other names
        self.canvas.create_text(
            33.0,
            236.0,
            anchor="nw",
            text="other_names:",
            fill=TEXT_COLOR_WHITE,
            font=(FONT, FONT_SIZE_TEXT_M),
        )

        self.canvas.create_text(
            33.0,
            262.0,
            anchor="nw",
            text=self.peer["other_names"],
            fill=TEXT_COLOR_ORANGE,
            font=(FONT, FONT_SIZE_TEXT_M),
        )

        # Status
        self.canvas.create_text(
            33.0,
            304.0,
            anchor="nw",
            text="status:",
            fill=TEXT_COLOR_WHITE,
            font=(FONT, FONT_SIZE_TEXT_M),
        )

        self.canvas.create_text(
            33.0,
            330.0,
            anchor="nw",
            text=self.peer["status"],
            fill=TEXT_COLOR_ORANGE,
            font=(FONT, FONT_SIZE_TEXT_M),
        )

        self.button_image_pin_verify = tk.PhotoImage(
            file=IMAGE_BASE_PATH + 'pin_and_verify.png'
        )
        button_pin_verify = tk.Button(
            frame,
            image=self.button_image_pin_verify,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.pin_verify(),
            relief="sunken",
            background=BACKGROUND_COLOR,
            activebackground=BACKGROUND_COLOR,
            activeforeground=BACKGROUND_COLOR,
        )
        button_pin_verify.place(x=78.0, y=299.0, width=92.0, height=23.0)

        # Endpoint
        self.canvas.create_text(
            33.0,
            372.0,
            anchor="nw",
            text="endpoint:",
            fill=TEXT_COLOR_WHITE,
            font=(FONT, FONT_SIZE_TEXT_M),
        )

        self.canvas.create_text(
            33.0,
            398.0,
            anchor="nw",
            text=self.peer["endpoint"],
            fill=TEXT_COLOR_ORANGE,
            font=(FONT, FONT_SIZE_TEXT_M),
        )

        # Allowed IP
        self.canvas.create_text(
            33.0,
            440.0,
            anchor="nw",
            text="allowed_ip:",
            fill=TEXT_COLOR_WHITE,
            font=(FONT, FONT_SIZE_TEXT_M),
        )

        self.canvas.create_text(
            33.0,
            466.0,
            anchor="nw",
            text=str(self.peer["allowed_ip"]),
            fill=TEXT_COLOR_ORANGE,
            font=(FONT, FONT_SIZE_TEXT_M),
        )

        # Latest signature
        self.canvas.create_text(
            33.0,
            508.0,
            anchor="nw",
            text="latest_signature:",
            fill=TEXT_COLOR_WHITE,
            font=(FONT, FONT_SIZE_TEXT_M),
        )

        self.canvas.create_text(
            33.0,
            534.0,
            anchor="nw",
            text=self.peer["latest_signature"],
            fill=TEXT_COLOR_ORANGE,
            font=(FONT, FONT_SIZE_TEXT_M),
        )

        # Latest handshake
        self.canvas.create_text(
            33.0,
            576.0,
            anchor="nw",
            text="latest_handshake:",
            fill=TEXT_COLOR_WHITE,
            font=(FONT, FONT_SIZE_TEXT_M),
        )

        self.canvas.create_text(
            33.0,
            602.0,
            anchor="nw",
            text=self.peer["latest_handshake"],
            fill=TEXT_COLOR_ORANGE,
            font=(FONT, FONT_SIZE_TEXT_M),
        )

        # Wg pubkey
        self.canvas.create_text(
            33.0,
            644.0,
            anchor="nw",
            text="wg_pubkey:",
            fill=TEXT_COLOR_WHITE,
            font=(FONT, FONT_SIZE_TEXT_M),
        )

        self.canvas.create_text(
            33.0,
            670.0,
            anchor="nw",
            text=self.peer["wg_pubkey"],
            fill=TEXT_COLOR_ORANGE,
            font=(FONT, FONT_SIZE_TEXT_M),
        )

        self.button_image_copy_wg_pubkey = tk.PhotoImage(
            file=IMAGE_BASE_PATH + 'clipboard.png'
        )
        button_copy_wg_pubkey = tk.Button(
            frame,
            image=self.button_image_copy_wg_pubkey,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.add_to_clipbaord(self.peer["wg_pubkey"]),
            relief="sunken",
            background=BACKGROUND_COLOR,
            activebackground=BACKGROUND_COLOR,
            activeforeground=BACKGROUND_COLOR,
        )
        button_copy_wg_pubkey.place(x=108.0, y=639.0, width=34.0, height=23.0)

        # Allowed IPs
        self.canvas.create_text(
            33.0,
            712.0,
            anchor="nw",
            text="allowed_ips:",
            fill=TEXT_COLOR_WHITE,
            font=(FONT, FONT_SIZE_TEXT_M),
        )

        self.canvas.create_text(
            33.0,
            738.0,
            anchor="nw",
            text=self.peer["allowed_ips"],
            fill=TEXT_COLOR_ORANGE,
            font=(FONT, FONT_SIZE_TEXT_M),
        )

        # Name entry
        self.canvas.create_text(
            33.0,
            775.0,
            anchor="nw",
            text="Add additional IP to Peer:",
            fill=TEXT_COLOR_WHITE,
            font=(FONT, FONT_SIZE_TEXT_M),
        )

        self.entry_image_additional_ip = tk.PhotoImage(
            file=IMAGE_BASE_PATH + 'add_ip_to_peer_entry.png'
        )
        self.entry_image_additional_ip_bg = self.canvas.create_image(
            144.0, 808.5, image=self.entry_image_additional_ip
        )
        self.entry_additional_ip = tk.Entry(
            frame,
            bd=0,
            bg=BACKGROUND_COLOR_ENTRY,
            fg=TEXT_COLOR_BLACK,
            highlightthickness=0,
        )
        self.entry_additional_ip.place(
            x=45.5, y=796.0, width=197.0, height=23.0
        )

        # name save
        self.button_image_additional_ip = tk.PhotoImage(
            file=IMAGE_BASE_PATH + 'save.png'
        )
        button_additional_ip = tk.Button(
            frame,
            image=self.button_image_additional_ip,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.add_additional_ip(),
            relief="sunken",
            background=BACKGROUND_COLOR,
            activebackground=BACKGROUND_COLOR,
            activeforeground=BACKGROUND_COLOR,
        )
        button_additional_ip.place(x=260.0, y=797.0, width=34.0, height=23.0)

    def delete_peer(self, peer_id: str, peer_name: str) -> None:
        # show message to ask user if they really
        # want to remove a peer

        box = messagebox.askyesno(
            _("Remove"),
            _("Remove this peer: ") + peer_name + " ?",
            parent=self,
        )

        if box:
            self.data.delete_peer(peer_id)
            self.return_value = "delete"
            self.destroy()

    def edit_peer(self) -> None:
        try:
            self.data.rename_peer(self.peer["id"], self.entry_name.get())
            self.return_value = "rename"
            self.destroy()
        except Exception:
            PopupMessage.showPopupMessage("Error", "Failed to edit peer")

    def pin_verify(self) -> None:
        # if name of peer was changed, we need other_names for pin_verify
        if self.peer["other_names"]:
            name = self.peer["other_names"]
        else:
            name = self.peer["name"]
        self.data.pin_and_verify(self.peer["id"], name)
        self.return_value = "pin_and_verify"
        self.destroy()

    def add_additional_ip(self) -> None:
        if len(self.entry_additional_ip.get()) == 0:
            return

        try:
            self.data.add_peer(self.peer["id"], self.entry_additional_ip.get())
            self.entry_additional_ip.delete(0, "end")
            self.return_value = "additional_ip"
            self.destroy()
        except Exception:
            PopupMessage.showPopupMessage(
                "Error", "Failed to add an additional ip address"
            )

    def add_to_clipbaord(self, text: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(text)
        PopupMessage.showPopupMessage("Information", "Copied to clipboard")

    def show(
        self,
    ) -> Literal['delete', 'pin_and_verify', 'rename', 'additional_ip', None]:
        self.deiconify()
        self.wm_transient(self.app)
        self.wm_protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_window(self)
        return self.return_value
