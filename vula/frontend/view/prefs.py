import gettext
import tkinter as tk
from tkinter import (
    Button,
    Canvas,
    Event,
    Frame,
    Label,
    PhotoImage,
    Scrollbar,
    Text,
    Widget,
)
from tkinter.constants import W

from vula.frontend import DataProvider, PrefsType
from vula.frontend.constants import (
    BACKGROUND_COLOR,
    BACKGROUND_COLOR_CARD,
    FONT,
    FONT_SIZE_HEADER_2,
    FONT_SIZE_TEXT_XL,
    IMAGE_BASE_PATH,
    TEXT_COLOR_BLACK,
    TEXT_COLOR_GREEN,
    TEXT_COLOR_GREY,
    TEXT_COLOR_HEADER_2,
    TEXT_COLOR_RED,
    TEXT_COLOR_WHITE,
)
from vula.frontend.overlay import PopupMessage

_ = gettext.gettext


class Prefs(Frame):
    data = DataProvider()

    def __init__(self, frame: Frame) -> None:
        self.show_editable: bool = False
        self.prefs: PrefsType = []
        self.widgets: Widget = {}
        self.frame: Frame = frame

        self.display_header()
        self.display_frames()

        self.get_prefs()
        self.display_prefs()
        self.hide_save_cancel()

    def display_frames(self) -> None:

        # Frames, Canvas and Scrollbars
        self.top_frame = Frame(
            self.frame,
            bg=BACKGROUND_COLOR,
            width=597,
            padx=30,
            pady=10,
            highlightbackground=BACKGROUND_COLOR,
            highlightcolor=BACKGROUND_COLOR,
            highlightthickness=1,
        )

        self.bottom_frame = Frame(
            self.frame,
            bg=BACKGROUND_COLOR,
            width=597,
            height=97,
            padx=30,
            pady=10,
            highlightbackground=BACKGROUND_COLOR,
            highlightcolor=BACKGROUND_COLOR,
            highlightthickness=1,
        )

        self.pref_canvas = Canvas(
            self.top_frame,
            background=BACKGROUND_COLOR_CARD,
            highlightbackground=BACKGROUND_COLOR_CARD,
            highlightcolor=BACKGROUND_COLOR_CARD,
            highlightthickness=1,
        )

        self.yscrollbar = Scrollbar(
            self.top_frame,
            orient="vertical",
            command=self.pref_canvas.yview,
            relief="flat",
        )
        self.pref_content_frame = Frame(
            self.pref_canvas,
            bg=BACKGROUND_COLOR_CARD,
            highlightbackground=BACKGROUND_COLOR_CARD,
            highlightcolor=BACKGROUND_COLOR_CARD,
            highlightthickness=1,
        )

        # Packing and configuring
        self.pref_canvas.pack(side="left", fill="y", expand="yes")

        self.yscrollbar.pack(side="right", fill="y")

        self.pref_canvas.configure(yscrollcommand=self.yscrollbar.set)
        self.pref_canvas.bind(
            '<Configure>',
            lambda e: self.pref_canvas.configure(
                scrollregion=self.pref_content_frame.bbox('all')
            ),
        )

        self.pref_canvas.create_window(
            (0, 0), window=self.pref_content_frame, anchor="nw"
        )

        self.top_frame.pack(
            fill="both", expand="yes", padx=(0, 50), pady=(50, 0), side="top"
        )
        self.bottom_frame.pack(side="left")

        self.top_frame.columnconfigure(0, weight=1)

        # Buttons
        self.button_image_edit = PhotoImage(file=IMAGE_BASE_PATH + 'edit.png')

        self.button_image_save_blue = PhotoImage(
            file=IMAGE_BASE_PATH + 'save_blue.png'
        )

        self.button_image_cancel = PhotoImage(
            file=IMAGE_BASE_PATH + 'cancel.png'
        )

        self.btn_edit = Button(
            master=self.bottom_frame,
            image=self.button_image_edit,
            command=lambda: self.set_editable(),
            borderwidth=0,
            highlightthickness=0,
            relief="sunken",
            background=BACKGROUND_COLOR,
            activebackground=BACKGROUND_COLOR,
            activeforeground=BACKGROUND_COLOR,
        )
        self.btn_save = Button(
            self.bottom_frame,
            image=self.button_image_save_blue,
            command=lambda: self.save_prefs(),
            borderwidth=0,
            highlightthickness=0,
            relief="sunken",
            background=BACKGROUND_COLOR,
            activebackground=BACKGROUND_COLOR,
            activeforeground=BACKGROUND_COLOR,
        )
        self.btn_cancel = Button(
            self.bottom_frame,
            image=self.button_image_cancel,
            command=lambda: self.cancel(),
            borderwidth=0,
            highlightthickness=0,
            relief="sunken",
            background=BACKGROUND_COLOR,
            activebackground=BACKGROUND_COLOR,
            activeforeground=BACKGROUND_COLOR,
        )
        self.btn_edit.pack(side="left", padx=10, pady=10)

    def display_header(self) -> None:
        self.title_frame = Frame(
            self.frame, bg=BACKGROUND_COLOR, padx=30, width=400, height=40
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
            text="Settings",
            fill=TEXT_COLOR_HEADER_2,
            font=(FONT, FONT_SIZE_HEADER_2),
        )
        self.title_frame.grid(row=0, column=0, pady=(10, 0), sticky="w")

    def get_prefs(self) -> None:
        self.prefs: PrefsType = self.data.get_prefs()

    def toggle(self, event: Event) -> None:
        """
        Toggle bool button value
        """
        if event.widget["text"] == "True":
            event.widget.config(text="False", bg=TEXT_COLOR_RED)
        elif event.widget["text"] == "False":
            event.widget.config(text="True", bg=TEXT_COLOR_GREEN)

    def bool_on_enter(self, event: Event) -> None:
        if event.widget["text"] == "True":
            event.widget.config(bg=TEXT_COLOR_BLACK)
        else:
            event.widget.config(bg=TEXT_COLOR_BLACK)

    def bool_on_leave(self, event: Event) -> None:
        if event.widget["text"] == "True":
            event.widget.config(bg=TEXT_COLOR_GREEN)
        else:
            event.widget.config(bg=TEXT_COLOR_RED)

    def save_prefs(self) -> None:
        for pref, values in self.prefs.items():
            # list based prefs
            if type(values) == list:
                current_list = self.widgets[pref].get("1.0", "end").split()
                for value in current_list:
                    if value not in self.prefs[pref]:
                        res = self.data.add_pref(pref, value)
                        if self.show_error(res) == 1:
                            return
                for value in values:
                    if value not in current_list:
                        res = self.data.remove_pref(pref, value)
                        if self.show_error(res) == 1:
                            return
            # boolean based prefs
            elif type(values) == bool:
                bool_value = str(self.widgets[pref]["text"])
                res = self.data.set_pref(pref, bool_value)
                if self.show_error(res) == 1:
                    return
            # int based prefs
            elif type(values) == int:
                int_value = str(self.widgets[pref].get("1.0", "end"))
                res = self.data.set_pref(pref, int_value)
                if self.show_error(res) == 1:
                    return

        self.get_prefs()
        self.show_editable = False
        self.hide_save_cancel()
        self.update_all()

    def show_error(self, res: str) -> int:
        """
        Show error message if needed and return a status code 0 or 1

        >>> Prefs.show_error(Prefs, 'Test')
        0
        """
        if res and "error:" in res:
            PopupMessage.showPopupMessage(
                "Error", "Preference could not be saved"
            )
            return 1
        else:
            return 0

    def cancel(self) -> None:
        self.get_prefs()
        self.show_editable = False
        self.update_all()
        self.hide_save_cancel()

    def set_editable(self) -> None:
        """
        Set pref variables as editable and update the prefs view
        """
        self.show_editable = True
        self.update_all()
        self.show_save_cancel()

    def update_all(self) -> None:
        """
        Remove everything from the prefs view and display the new state
        """
        for label in self.pref_content_frame.grid_slaves():
            label.grid_forget()
        self.pref_canvas.destroy()
        self.yscrollbar.destroy()
        self.top_frame.destroy()
        self.bottom_frame.destroy()
        self.display_frames()
        self.display_prefs()

    def show_save_cancel(self) -> None:
        self.btn_edit.pack_forget()
        self.btn_cancel.pack(side="left", padx=10, pady=10)
        self.btn_save.pack(side="left", padx=10, pady=10)

    def hide_save_cancel(self) -> None:
        self.btn_edit.pack(side="left", padx=10, pady=10)
        self.btn_save.pack_forget()
        self.btn_cancel.pack_forget()

    def display_prefs(self) -> None:
        # row counter
        counter: int = 1

        # Loop over all preferences and display them
        for pref, value in self.prefs.items():
            # show preference descriptions on the left
            pref_label = Label(
                self.pref_content_frame,
                text=_(str(pref)) + ":",
                font=(FONT, FONT_SIZE_TEXT_XL),
                fg=TEXT_COLOR_WHITE,
                height=1,
                anchor="nw",
                bg=BACKGROUND_COLOR_CARD,
            )
            pref_label.grid(row=counter, column=0, padx=2, pady=2, sticky="nw")

            # list based preferences
            if type(value) == list:

                if self.show_editable:
                    value_text = Text(
                        self.pref_content_frame,
                        height=len(value),
                        width=20,
                        bg=BACKGROUND_COLOR_CARD,
                        fg=TEXT_COLOR_GREY,
                        highlightbackground=BACKGROUND_COLOR_CARD,
                        insertbackground=TEXT_COLOR_WHITE,
                    )
                    self.widgets[pref] = value_text
                    for i in range(len(value)):
                        value_text.insert(tk.END, value[i] + "\n")

                    value_text.grid(
                        row=counter, column=1, padx=1, pady=1, sticky=W
                    )
                    counter += 1

                else:
                    if len(value) == 0:
                        value_label = Label(
                            self.pref_content_frame,
                            text="None",
                            font=(FONT, FONT_SIZE_TEXT_XL),
                            bg=BACKGROUND_COLOR_CARD,
                            fg=TEXT_COLOR_WHITE,
                        )
                        value_label.grid(
                            row=counter, column=1, padx=1, pady=1, sticky=W
                        )
                        counter += 1
                    for i in range(len(value)):
                        value_label = Label(
                            self.pref_content_frame,
                            text=str(value[i]),
                            font=(FONT, FONT_SIZE_TEXT_XL),
                            bg=BACKGROUND_COLOR_CARD,
                            fg=TEXT_COLOR_WHITE,
                        )
                        value_label.grid(
                            row=counter, column=1, padx=1, pady=1, sticky=W
                        )
                        counter += 1

            # bool based preferences (as string)
            elif type(value) == bool:
                if str(value) == "True":
                    color = TEXT_COLOR_GREEN
                    font_color = TEXT_COLOR_GREEN
                    font_color_button = TEXT_COLOR_WHITE

                if str(value) == "False":
                    color = TEXT_COLOR_RED
                    font_color = TEXT_COLOR_RED
                    font_color_button = TEXT_COLOR_WHITE

                if self.show_editable:
                    btn_bool = Button(
                        self.pref_content_frame,
                        text=(str(value)),
                        width=5,
                        height=1,
                        bg=color,
                        fg=font_color_button,
                        highlightbackground=BACKGROUND_COLOR_CARD,
                        highlightcolor=BACKGROUND_COLOR_CARD,
                        borderwidth=0,
                        highlightthickness=0,
                        relief="flat",
                    )
                    btn_bool.widgetName = [pref]
                    self.widgets[pref] = btn_bool
                    btn_bool.grid(
                        row=counter, column=1, padx=1, pady=1, sticky=W
                    )

                    btn_bool.bind("<Leave>", self.bool_on_leave)
                    btn_bool.bind("<Enter>", self.bool_on_enter)
                    btn_bool.bind("<Button-1>", self.toggle)
                else:
                    label = Label(
                        self.pref_content_frame,
                        text=str(value),
                        font=(FONT, FONT_SIZE_TEXT_XL),
                        bg=BACKGROUND_COLOR_CARD,
                        fg=font_color,
                    )
                    label.grid(row=counter, column=1, padx=1, pady=1, sticky=W)

                counter += 1

            # int based preference
            elif type(value) == int:

                if self.show_editable:
                    value_text = Text(
                        self.pref_content_frame,
                        height=1,
                        width=20,
                        bg=BACKGROUND_COLOR_CARD,
                        fg=TEXT_COLOR_GREY,
                        highlightbackground=BACKGROUND_COLOR_CARD,
                        highlightcolor=BACKGROUND_COLOR_CARD,
                        insertbackground=TEXT_COLOR_WHITE,
                    )
                    self.widgets[pref] = value_text
                    value_text.grid(
                        row=counter, column=1, padx=1, pady=1, sticky=W
                    )
                    value_text.insert(tk.END, value)
                else:
                    label = Label(
                        self.pref_content_frame,
                        text=str(value),
                        font=(FONT, FONT_SIZE_TEXT_XL),
                        bg=BACKGROUND_COLOR_CARD,
                        fg=TEXT_COLOR_WHITE,
                    )
                    label.grid(row=counter, column=1, padx=1, pady=1, sticky=W)
                counter += 1


if __name__ == "__main__":
    import doctest

    doctest.testmod()
