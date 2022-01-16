import tempfile
import tkinter as tk
from tkinter import ttk

try:
    import qrcode
except ImportError:
    qrcode = None


class QRCodeLabel(ttk.Label):
    def __init__(self, parent, qr_data, resize):
        with tempfile.NamedTemporaryFile(
            prefix="vula-ui", suffix="qr-code"
        ) as tmp_file:
            tmp_file_name = tmp_file.name
            super().__init__(parent)
            qr = qrcode.QRCode()
            qr.add_data(data=qr_data)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(tmp_file_name)
            self.image = tk.PhotoImage(file=tmp_file_name)
            self.image = self.image.subsample(resize, resize)
            self.configure(image=self.image)
