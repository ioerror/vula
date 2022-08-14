/**
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
**/

'use strict';

const MAIN = imports.ui.main;
const PANELMENU = imports.ui.panelMenu;
const POPUPMENU = imports.ui.popupMenu;
const ST = imports.gi.St;
const LANG = imports.lang;
const UTIL = imports.misc.util;
const GIO = imports.gi.Gio;
const GLIB = imports.gi.GLib;
const EXTENSIONUTILS = imports.misc.extensionUtils;
const ME = EXTENSIONUTILS.getCurrentExtension();
let _indicator;
const VULA_INDICATOR = new LANG.Class({
    Name: 'Vula.indicator',
    Extends: PANELMENU.Button,

    _init: () => {
        const VULA_BINARY = '/usr/bin/vula';
        this.parent(0.0);
        this._icon = new ST.Icon({ style_class: 'system-status-icon', });
        this._icon.gicon = GIO.icon_new_for_string(`${ME.path}/icons/VULA.svg`);
        this.add_actor(this._icon);

        // Toggle button start/stop Vula
        let switchmenuitem = new POPUPMENU.PopupSwitchMenuItem('Enable Vula', false);
        switchmenuitem.actor.connect('toggled', LANG.bind(this, function (object, value) {
            try {
                if (value) {
                    this._icon.gicon = GIO.icon_new_for_string(`${ME.path}/icons/VULA_ACTIVE.svg`);
                    UTIL.spawn([VULA_BINARY, 'start']);
                    MAIN.notify('Vula Notification', 'Vula started');
                } else {
                    this._icon.gicon = GIO.icon_new_for_string(`${ME.path}/icons/VULA.svg`);
                    UTIL.spawn(['/bin/systemctl', 'stop', 'vula.slice']);
                    MAIN.notify('Vula Notification', 'Vula stopped');
                }
            } catch (error) {
                MAIN.notify('Vula Notification', `An error occured while starting Vula: ${error}`);
                return;
            }
        }));

        // Vula Repair Button
        let vulaRepairMenuItem = new POPUPMENU.PopupMenuItem("Repair Vula", {});
        vulaRepairMenuItem.actor.connect('activate', LANG.bind(this, function () {
            try {
                UTIL.spawn([VULA_BINARY, 'repair']);
                MAIN.notify('Vula Notification', 'Vula repaired');
            } catch (error) {
                MAIN.notify('Vula Notification', `An error occured while repairing Vula: ${error}`);
                return;
            }
        }));

        // Vula Rediscover Button
        let vulaRediscoverMenuItem = new POPUPMENU.PopupMenuItem("Rediscover", {});
        vulaRediscoverMenuItem.actor.connect('activate', LANG.bind(this, function () {
            try {
                let processOutput = GLIB.spawn_command_line_sync(VULA_BINARY + " rediscover")[1].toString();
                MAIN.notify('Vula Notification', processOutput);
            } catch (error) {
                MAIN.notify('Vula rediscover', `An error occured while rediscovering: ${error}`);
                return;
            }
        }));

        // Vula Status Button
        let vulaStatusItem = new POPUPMENU.PopupMenuItem("Vula status", {});
        let status = new POPUPMENU.PopupMenuItem("", {});
        vulaStatusItem.actor.connect('activate', LANG.bind(this, function () {
            try {
                status.destroy()
                let processOutput = GLIB.spawn_command_line_sync(VULA_BINARY + " status")[1].toString();
                status = new POPUPMENU.PopupMenuItem(processOutput, {});
                this.menu.addMenuItem(status)
            } catch (error) {
                MAIN.notify('Vula Notification', `An error occured while getting Vula status: ${error}`);
                return;
            }
        }));

        // Vula VK Button
        let getVkItem = new POPUPMENU.PopupMenuItem("Show verification key", {});
        getVkItem.actor.connect('activate', LANG.bind(this, function () {
            try {
                status.destroy()
                let vulaCommand = VULA_BINARY + " verify my-vk";
                let gnomeCommand = vulaCommand + "; exec bash";
                let arg = `gnome-terminal -- bash -c "${gnomeCommand}"`;
                GLIB.spawn_command_line_sync(arg);

            } catch (error) {
                MAIN.notify('Vula Notification', `An error occured while getting Vula verification-key: ${error}`);
                return;
            }
        }));

        // Vula descriptor Button
        let getDescriptorItem = new POPUPMENU.PopupMenuItem("Show descriptor key", {});
        getDescriptorItem.actor.connect('activate', LANG.bind(this, function () {
            try {
                status.destroy()
                let vulaCommand = VULA_BINARY + " verify my-descriptor";
                let gnomeCommand = vulaCommand + "; exec bash";
                let arg = `gnome-terminal --maximize -- bash -c "${gnomeCommand}"`;
                GLIB.spawn_command_line_sync(arg);

            } catch (error) {
                MAIN.notify('Vula Notification', `An error occured while getting Vula descriptor: ${error}`);
                return;
            }
        }));

        // Add Items to menu
        this.menu.addMenuItem(switchmenuitem);
        this.menu.addMenuItem(vulaRepairMenuItem);
        this.menu.addMenuItem(vulaRediscoverMenuItem);
        this.menu.addMenuItem(new POPUPMENU.PopupSeparatorMenuItem);
        this.menu.addMenuItem(vulaStatusItem);
        this.menu.addMenuItem(getVkItem);
        this.menu.addMenuItem(getDescriptorItem);
        this.menu.addMenuItem(new POPUPMENU.PopupSeparatorMenuItem);
    }
});

function init() {
    log('Vula extension initalized');
};

function enable() {
    log('Vula extension enabled');
    _indicator = new VULA_INDICATOR();
    MAIN.panel._addToPanelBox('Vula', _indicator, 1, MAIN.panel._rightBox);
};

function disable() {
    log('Vula extension disabled');
    _indicator.destroy();
};

