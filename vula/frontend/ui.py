import locale
import os
import tkinter as tk
from sys import platform
from tkinter import ttk

import i18n

from vula import common
from vula.frontend import DataProvider
from vula.frontend.view import (
    Peers,
    Prefs,
    Information,
)

try:
    import qrcode
except ImportError:
    qrcode = None

loc = locale.getlocale()  # get current locale
locals_path = os.path.dirname(__file__) + "/locals"
i18n.load_path.append(locals_path)

if loc[0].__contains__("en"):
    i18n.set('locale', 'en')
elif loc[0].__contains__("de"):
    i18n.set('locale', 'de')
else:
    i18n.set('fallback', 'en')


class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        # Create instance of dataprovider
        data = DataProvider()

        tk.Tk.__init__(self, *args, **kwargs)

        # Create parent container
        container = ttk.Frame(self)
        container.pack(side="top", fill="both", expand=True)

        if not platform == 'linux':
            error_label = ttk.Label(self, text="Your OS is not supported")
            error_label.pack(
                side="top", fill="both", expand=True, ipadx=30, ipady=30
            )
        else:
            status_values = data.get_status()
            if status_values is None:
                error_label = ttk.Label(self, text="Vula is not running")
                error_label.pack(
                    side="top", fill="both", expand=True, ipadx=30, ipady=30
                )
            else:
                # Create Menu
                menu = tk.Menu(self)
                self.config(menu=menu)

                # Add several menu points
                menu.add_command(
                    label=i18n.t("vula.preferences"),
                    command=lambda: self.show_frame(Prefs),
                )

                menu.add_command(
                    label=i18n.t("vula.peers"),
                    command=lambda: self.show_frame(Peers),
                )

                menu.add_command(
                    label=i18n.t("vula.information"),
                    command=lambda: self.show_frame(Information),
                )

                # Add submenu with different command
                commands = tk.Menu(menu)
                commands.add_command(
                    label=i18n.t("vula.rediscover"),
                    command=lambda: self.rediscover(),
                )
                commands.add_command(
                    label=i18n.t("vula.repair"), command=lambda: self.repair()
                )
                commands.add_command(
                    label=i18n.t("vula.release_gateway"),
                    command=lambda: self.release_gateway(),
                )
                menu.add_cascade(label=i18n.t("vula.actions"), menu=commands)

                # Get the status of the different vula processes
                state = data.get_status()

                # Display the status at the bottom
                status_label = ttk.Label(
                    self,
                    text=f'Publish: {i18n.t("vula." + state["publish"])} '
                    f'\t Discover: {i18n.t("vula." + state["discover"])} '
                    f'\t Organize: {i18n.t("vula." + state["organize"])}',
                    font=("Arial", 15),  # noqa: E501
                )
                status_label.pack(side="top", fill="both", expand=True)
                self.frames = {}

                # Loop over all frames and set padding on every side
                for F in (
                    Prefs,
                    Peers,
                    Information,
                ):
                    frame = F(container, self)
                    self.frames[F] = frame
                    frame.grid(row=0, column=0, padx=20, pady=20, sticky="we")

                # Show Peers as default view
                self.show_frame(Prefs)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

    def rediscover(self):
        common.organize_dbus_if_active().rediscover()

    def release_gateway(self):
        common.organize_dbus_if_active().release_gateway()

    def repair(self):
        res = common.organize_dbus_if_active().sync(True)
        if res:
            print(res)


def main():
    try:
        app = App()
        app.title("Vula")
        app.mainloop()
    except RuntimeError:
        return
