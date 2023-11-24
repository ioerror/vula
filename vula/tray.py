import sys
from base64 import b64decode
from io import BytesIO
from threading import Thread
from time import sleep
from typing import Any, List, NoReturn, Optional

import click
from gi.repository import GLib
from PIL import Image
from pydbus import SystemBus
from Xlib.error import DisplayNameError

from vula.common import escape_ansi
from vula.constants import (
    _ORGANIZE_DBUS_NAME,
    _ORGANIZE_DBUS_PATH,
    _TRAY_UPDATE_INTERVAL,
)
from vula.frontend import ui


@click.command(short_help="Start the system tray icon.")
def main() -> None:  # noqa: 901
    try:
        from pystray import Icon, Menu, MenuItem
    except ModuleNotFoundError:
        print("vula tray requires the pystray library.")
        sys.exit(1)
    except DisplayNameError:
        print("No display available.")
        sys.exit(2)

    class Tray(object):
        _gui_thread: Optional[Thread] = None
        _update_thread: Optional[Thread] = None
        icon: Icon
        organize_bus: Any
        systemd_bus: Any

        def __init__(self):
            try:
                self.system_bus = SystemBus()
                self.organize_dbus = self.system_bus.get(
                    _ORGANIZE_DBUS_NAME, _ORGANIZE_DBUS_PATH
                )
                self.systemd_bus = self.system_bus.get(".systemd1")
            except GLib.Error:
                print("Vula is not running.")
                sys.exit(3)

        def _get_icon(self) -> Image:
            """
            Return the icon for the system tray entry.

            It uses the Vula logo as a base64 encoded string.
            """
            base64_icon: str = "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"  # noqa: E501
            return Image.open(BytesIO(b64decode(base64_icon)))

        def _get_status_menu_items(self) -> List[MenuItem]:
            """
            Returns a list of menu items indicating the status of the different
            Vula services.

            >>> tray = Tray()
            >>> items = tray._get_status_menu_items()
            >>> len(items)
            3
            """
            services: List[str] = ["publish", "discover", "organize"]
            menu_items: List[MenuItem] = []

            # Fetch the service status using the systemd D-Bus API
            for service in services:
                # Check the status of the service and create a menu item
                unit_name = "vula-%s.service" % service
                try:
                    unit_object_path = self.systemd_bus.GetUnit(unit_name)
                    unit = self.system_bus.get(".systemd1", unit_object_path)
                    status = unit.ActiveState
                except GLib.Error:
                    status = "inactive"

                menu_items.append(
                    MenuItem("%s: %s" % (service, status), None, enabled=False)
                )

            return menu_items

        def _get_peer_menu_item(self) -> MenuItem:
            """
            Returns the peer menu item. If there are any peers available a
            submenu with peers is shown.
            """
            peer_menu_items: List[MenuItem] = []
            peer_ids: List[str] = self.organize_dbus.peer_ids("all")
            for peer_id in peer_ids:
                # Get the peer information and remove formatting characters
                peer_show: str = self.organize_dbus.show_peer(peer_id)
                peer_information: List[str] = escape_ansi(peer_show).split(
                    "\n"
                )

                if len(peer_information) >= 4:
                    menu_item_text = "%s\n%s\n%s\n%s" % (
                        peer_information[0],
                        peer_information[1],
                        peer_information[2],
                        peer_information[3],
                    )
                else:
                    menu_item_text = (
                        "peer: %s\n  No status information available" % peer_id
                    )

                peer_menu_items.append(
                    MenuItem(
                        menu_item_text,
                        None,
                        enabled=False,
                    )
                )

            number_of_peers: int = len(peer_menu_items)
            peer_menu_item: MenuItem = MenuItem(
                "%s %s"
                % (
                    number_of_peers,
                    "peer" if number_of_peers == 1 else "peers",
                ),
                Menu(*peer_menu_items) if number_of_peers > 0 else None,
                enabled=number_of_peers > 0,
            )

            return peer_menu_item

        def _rediscover(self):
            """
            Calls organize.rediscover() over D-BUS.
            """
            self.organize_dbus.rediscover()

        def _release_gateway(self):
            """
            Calls organize.release_gateway() over D-BUS.
            """
            self.organize_dbus.release_gateway()

        def _repair(self):
            """
            Calls organize.repair() over D-BUS.
            """
            self.organize_dbus.sync(False)

        def _get_actions_menu_item(self) -> MenuItem:
            """
            Returns the action menu item with a submenu containing the actions.

            >>> tray = Tray()
            >>> items = tray._get_actions_menu_item()
            >>> len(items.submenu.items)
            3
            """
            action_menu_items = [
                MenuItem("Rediscover", self._rediscover),
                MenuItem("Repair", self._repair),
                MenuItem("Release Gateway", self._release_gateway),
            ]

            return MenuItem(
                "Actions",
                Menu(*action_menu_items),
            )

        def _remove_tray_icon(self) -> None:
            """
            Removes the system tray icon.
            """
            self.icon.stop()

        def _open_gui(self) -> None:
            """
            Opens the Vula GUI in a separate thread.
            """
            if self._gui_thread is not None and self._gui_thread.is_alive():
                return

            self._gui_thread = Thread(target=lambda: ui.main())
            self._gui_thread.start()

        def _get_open_gui_menu_item(self) -> MenuItem:
            """
            Returns the menu item that is used for opening the GUI.
            """
            return MenuItem("Open GUI...", self._open_gui)

        def _get_menu_items(self) -> List[MenuItem]:
            """
            Returns the menu items that will be shown in the system tray icon.

            >>> tray = Tray()
            >>> items = tray._get_menu_items()
            >>> len(items)
            7
            """
            return [
                *self._get_status_menu_items(),
                self._get_peer_menu_item(),
                self._get_actions_menu_item(),
                self._get_open_gui_menu_item(),
                MenuItem("Quit", self._remove_tray_icon),
            ]

        def _update_icon(self) -> NoReturn:
            """
            Updates the menu items in the system tray icon.
            """
            while True:
                self.icon.update_menu()
                sleep(_TRAY_UPDATE_INTERVAL)

        def _setup_icon(self, icon: Icon) -> None:
            """
            Setup the system tray icon by making it visible and starting a
            thread to keep it updated.

            An update thread is needed because the menu doesn't get updated
            when you open it but only when you click on actions inside the
            menu. When we display "external" information such as the peers and
            vula status, we need to keep the menu updated ourselves or else we
            might show outdated information.
            """
            self.icon = icon
            self.icon.visible = True
            self._update_thread = Thread(target=lambda: self._update_icon())
            self._update_thread.daemon = True
            self._update_thread.start()

        def show(self) -> None:
            """
            Show the system tray icon.
            """
            icon: Icon = Icon(
                "Vula",
                title="Vula",
                icon=self._get_icon(),
                menu=Menu(self._get_menu_items),
            )

            icon.run(self._setup_icon)

    tray: Tray = Tray()
    tray.show()


if __name__ == "__main__":
    main()
