import tkinter as tk
from functools import partial
from tkinter import ttk, simpledialog
from tkinter.constants import W

import gettext

from vula.frontend import _WIDTH, _HEIGHT, DataProvider

_ = gettext.gettext


class Peers(tk.Frame):
    data = DataProvider()

    gui_components = []

    # need to save this numbers for updating the GUI,
    # as it takes quite long for dbus to make these changes
    num_peers = 0
    num_peers_after = 0
    num_peers_after_remove = 0

    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent, width=_WIDTH, height=_HEIGHT)

        self.app = parent

        # Make the frame resizeable
        self.pack_propagate(0)
        self.grid_propagate(0)

        # Display title of Peers view
        label = ttk.Label(self, text="Peers", font=("Arial", 20))
        label.grid(row=0, column=0, padx=1, pady=1, sticky=W)
        self.display_peers(False)

        self.update_loop()

    def show_messagebox(self, peer_id, peer_name):
        # show message to ask user if they really
        # want to remove a peer and refresh view
        box = tk.messagebox.askyesno(
            _("Remove"),
            _("Remove this peer: ") + peer_name + " ?",
        )

        if box:
            self.data.delete_peer(peer_id)
            self.num_peers_after_remove = self.num_peers - 1
            self.display_peers(True)
            self.display_peers(False)

    def pin_verify(self, peer_id, peer_name):
        # pin an refresh view
        self.data.pin_and_verify(peer_id, peer_name)
        self.display_peers(True)
        self.display_peers(False)

    def edit_peer(self, peer_id):
        dialog = simpledialog.askstring(
            _("Edit peer name"), _("Enter new peer name")
        )

        if dialog is not None:
            try:
                self.data.rename_peer(peer_id, dialog)
                self.display_peers(True)
                self.display_peers(False)
            except Exception as e:
                print(e)

    def add_peer(self):
        # show dialogs to add a new peer
        dialog = simpledialog.askstring(
            _("+ Add peer"),
            _(
                "Important: It may take a few minutes for new peers to be displayed!\n"  # noqa
                + "Enter a verification key:"
            ),
        )

        if dialog is not None:
            dialog_ip = simpledialog.askstring(
                _("+ Add peer"), _("Enter IP address")
            )
            if dialog_ip is not None:
                try:
                    self.data.add_peer(dialog, dialog_ip)
                    self.num_peers_after = self.num_peers + 1
                except Exception as e:
                    print(e)

    def update_loop(self):
        # function to update the GUI after adding
        # and removing peers (checks number of peers)
        peers = self.data.get_peers()
        if len(peers) > 0:
            if len(peers) == self.num_peers_after:
                try:
                    self.display_peers(True)
                    self.display_peers(False)
                    self.num_peers_after = 0
                except Exception as e:
                    print(e)

            if len(peers) == self.num_peers_after_remove:
                try:
                    self.display_peers(True)
                    self.display_peers(False)
                    self.num_peers_after_remove = 0
                except Exception as e:
                    print(e)

        # check every second if number of peers
        # has changed.
        self.after(1000, self.update_loop)

    def display_peers(self, clear_gui):
        if clear_gui:
            peers = []
            for c in self.gui_components:
                c.destroy()
            self.app.update()
            self.gui_components.clear()
        else:
            peers = self.data.get_peers()
            self.num_peers = len(peers)

        counter = 1

        if len(peers) == 0:
            no_peers_label = ttk.Label(
                self,
                text=_("No peers found"),
                font=("Arial", 12),
            )
            no_peers_label.grid(
                row=counter, column=0, padx=1, pady=1, sticky=W
            )
            self.gui_components.append(no_peers_label)
            counter += 1

        # Loop over all peers and display the content from dbus
        for peer in peers:
            # needed to call the button commands with arguments
            id = peer["id"]
            # if name of peer was changed, we need other_names for pin_verify
            if peer["other_names"]:
                name = peer["other_names"]
            else:
                name = peer["name"]
            remove_with_arg = partial(self.show_messagebox, id, name)
            pin_with_arg = partial(self.pin_verify, id, name)
            edit_name = partial(self.edit_peer, id)

            # buttons for editing/removing peers
            btn_remove_peer = ttk.Button(
                self, text=_("Remove"), command=remove_with_arg
            )
            btn_remove_peer.grid(
                row=counter, column=3, padx=1, pady=1, sticky=W
            )
            btn_edit = ttk.Button(self, text=_("Edit name"), command=edit_name)
            btn_edit.grid(row=counter, column=2, padx=1, pady=1, sticky=W)
            btn_pin = ttk.Button(
                self, text=_("Pin and verify"), command=pin_with_arg
            )
            btn_pin.grid(row=counter, column=4, padx=1, pady=1, sticky=W)
            self.gui_components.append(btn_remove_peer)
            self.gui_components.append(btn_edit)
            self.gui_components.append(btn_pin)

            # peer information
            for key, value in peer.items():
                key = ttk.Label(
                    self,
                    text=str(key) + ":",
                    font=("Arial", 12),
                )
                key.grid(row=counter, column=0, padx=1, pady=1, sticky=W)
                value = ttk.Label(self, text=str(value), font=("Arial", 12))
                value.grid(row=counter, column=1, padx=1, pady=1, sticky=W)
                counter += 1
                self.gui_components.append(value)
                self.gui_components.append(key)

            # Add a separator to split the peers
            sep = ttk.Separator(self, orient="horizontal")
            sep.grid(row=counter, column=0, padx=20, pady=20, sticky=W)
            counter += 1
            self.gui_components.append(sep)

        # button for adding new peers
        if not clear_gui:
            btn_add = ttk.Button(
                self, text=_("+ Add peer"), command=self.add_peer
            )
            btn_add.grid(row=counter, column=0, padx=1, pady=1, sticky=W)
            self.gui_components.append(btn_add)
