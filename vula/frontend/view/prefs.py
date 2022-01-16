import tkinter as tk
from tkinter import ttk
from tkinter.constants import W

import i18n

from vula.frontend import _WIDTH, _HEIGHT, dataprovider


class Prefs(tk.Frame):
    data = dataprovider.DataProvider()

    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent, width=_WIDTH, height=_HEIGHT)
        # Make the frame resizeable
        self.pack_propagate(0)
        self.grid_propagate(0)

        self.grid(row=0, column=0, sticky="ew")

        # Display title of Preference view
        label = ttk.Label(
            self, text=i18n.t("vula.preferences"), font=("Arial", 20)
        )
        label.grid(row=0, column=0, padx=1, pady=1, sticky=W)
        self.display_prefs()

    def display_prefs(self):
        # Get preferences from dataprovider
        prefs = self.data.get_prefs()

        counter = 1
        # Loop over all preferences and display them
        for key, value in prefs.items():
            key_label = ttk.Label(
                self, text=i18n.t("vula." + str(key)) + ":", font=("Arial", 12)
            )
            key_label.grid(row=counter, column=0, padx=1, pady=1, sticky=W)

            if (
                str(key) == "subnets_allowed"
                or str(key) == "local_domains"
                or str(key) == "subnets_forbidden"
                or str(key) == "iface_prefix_allowed"
            ):
                if len(value) == 0:
                    value_label = ttk.Label(
                        self, text="None", font=("Arial", 12)
                    )
                    value_label.grid(
                        row=counter, column=1, padx=1, pady=1, sticky=W
                    )
                    counter += 1
                for i in range(len(value)):
                    value_label = ttk.Label(
                        self, text=str(value[i]), font=("Arial", 12)
                    )
                    value_label.grid(
                        row=counter, column=1, padx=1, pady=1, sticky=W
                    )
                    counter += 1
            else:
                value_label = ttk.Label(
                    self, text=str(value), font=("Arial", 12)
                )
                value_label.grid(
                    row=counter, column=1, padx=1, pady=1, sticky=W
                )
                counter += 1
