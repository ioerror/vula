import tkinter as tk

from vula.frontend.constants import (
    BACKGROUND_COLOR,
    FONT,
    FONT_SIZE_TEXT_XL,
    FONT_SIZE_TEXT_XXL,
    TEXT_COLOR_WHITE,
)


class HelpOverlay(tk.Toplevel):
    def __init__(self, parent: tk.Tk) -> None:
        self.root = parent

    def openNewWindow(self) -> None:
        newWindow = tk.Toplevel(self.root)
        newWindow.wm_transient(self.root)

        # Root Window properties
        newWindow.title("Vula | Help")
        newWindow.geometry("530x530")
        newWindow.configure(bg=BACKGROUND_COLOR)

        # Create the Frames for diffrent sections
        text_frame = tk.Frame(
            newWindow, bg=BACKGROUND_COLOR, width=510, height=200, padx=20
        )

        # Create the grid for the root TK
        newWindow.grid_rowconfigure(0, weight=1)
        newWindow.grid_columnconfigure(0, weight=1)

        # Place the Frames on the grid
        text_frame.grid(row=0, sticky="nw")

        helpText = tk.Text(
            text_frame,
            bg=BACKGROUND_COLOR,
            fg=TEXT_COLOR_WHITE,
            font=(FONT, FONT_SIZE_TEXT_XL),
        )
        helpText.tag_configure("bold", font=(FONT, FONT_SIZE_TEXT_XXL, "bold"))
        helpText.insert("end", "Repair :\n", "bold")
        helpText.insert(
            "end", "Ensure that the system is configured correctly\n"
        )
        helpText.insert("end", "Rediscover :\n", "bold")
        helpText.insert(
            "end", "Tell organize to ask discover for more peers\n"
        )
        helpText.insert("end", "Release Gateway :\n", "bold")
        helpText.insert("end", "Stop using vula for the default route\n")
        helpText.pack()
