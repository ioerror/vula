import json
import tkinter as tk
from tkinter import ttk
from tkinter.constants import W

import i18n

from vula.frontend import _WIDTH, _HEIGHT, dataprovider
from vula.frontend.view import QRCodeLabel
from vula.peer import Descriptor


class Information(tk.Frame):
    data = dataprovider.DataProvider()

    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent, width=_WIDTH, height=_HEIGHT)
        # Make the frame resizeable
        self.pack_propagate(0)
        self.grid_propagate(0)

        label = ttk.Label(
            self, text=i18n.t("vula.my_verification_key"), font=("Arial", 20)
        )
        label.grid(row=0, column=0, padx=1, pady=1, sticky=W)
        self.display_qr_code()

    def display_qr_code(self):
        my_descriptors = {
            ip: Descriptor(d)
            for ip, d in json.loads(self.data.our_latest_descriptors()).items()
        }

        gridrow = 1
        for d in my_descriptors.values():
            vk = d.vk
            # Verification Key String Label
            label = ttk.Label(
                self,
                text=i18n.t("vula.my_vk_is") + ": {}".format(vk),
                font=("Arial", 12),
            )
            label.grid(row=gridrow, column=0, padx=1, pady=1, sticky=W)
            gridrow += 1

            # Verification Key QR Code Image
            qr_data = "local.vula:vk:" + str(vk)
            label = QRCodeLabel(parent=self, qr_data=qr_data, resize=1)
            label.grid(row=gridrow, column=0, padx=1, pady=1, sticky=W)
            gridrow += 1

            # Separator
            sep = ttk.Separator(self, orient='horizontal')
            sep.grid(row=gridrow, column=0, padx=1, pady=1, sticky=W)
            gridrow += 1

        for ip, desc in my_descriptors.items():
            # IP Label
            label = ttk.Label(
                self, text="Descriptor for {}: ".format(ip), font=("Arial", 12)
            )
            label.grid(row=gridrow, column=0, padx=1, pady=1, sticky=W)
            gridrow += 1

            # Separator
            sep = ttk.Separator(self, orient='horizontal')
            sep.grid(row=gridrow, column=0, padx=1, pady=1, sticky=W)
            gridrow += 1

            # Descriptor QR Code Image
            qr_data = "local.vula:desc:" + str(desc)
            label = QRCodeLabel(parent=self, qr_data=qr_data, resize=3)
            label.grid(row=gridrow, column=0, padx=1, pady=1, sticky=W)
            gridrow += 1
