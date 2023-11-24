import tkinter as tk

from vula.frontend.constants import (
    BACKGROUND_COLOR,
    BACKGROUND_COLOR_ERROR,
    FONT,
    FONT_SIZE_TEXT_XL,
    TEXT_COLOR_WHITE,
)


class PopupMessage:
    def showPopupMessage(title, text):
        popupRoot = tk.Toplevel()
        popupRoot.title(title)
        if title == "Error":
            backgroundcolor = BACKGROUND_COLOR_ERROR
        else:
            backgroundcolor = BACKGROUND_COLOR
        popupRoot.config(bg=backgroundcolor)
        popupRoot.after(2000, popupRoot.destroy)
        popupLabel = tk.Label(
            popupRoot,
            text=text,
            font=(FONT, FONT_SIZE_TEXT_XL),
            fg=TEXT_COLOR_WHITE,
            height=1,
            anchor="nw",
            bg=backgroundcolor,
            pady=10,
        )

        popupLabel.pack()
        popupRoot.geometry('400x50+400+525')
        popupRoot.mainloop()
        return
