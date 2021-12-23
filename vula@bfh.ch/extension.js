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

const Main = imports.ui.main;

const PanelMenu = imports.ui.panelMenu;
const PopupMenu = imports.ui.popupMenu;

const St = imports.gi.St;

const Lang = imports.lang;
const Util = imports.misc.util;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;

const ExtensionUtils = imports.misc.extensionUtils;
const Me = ExtensionUtils.getCurrentExtension();



const Vula_Indicator = new Lang.Class({
    Name: 'Vula.indicator',
    Extends: PanelMenu.Button,

       _init: function(){
            const vulaPath = '/usr/bin/vula';
            this.parent(0.0);
            this._icon = new St.Icon({style_class: 'system-status-icon',});
            this._icon.gicon = Gio.icon_new_for_string(`${Me.path}/icons/VULA.svg`);
            this.add_actor(this._icon);

            // Toggle button start/stop Vula
            let switchmenuitem = new PopupMenu.PopupSwitchMenuItem('Start Vula', false);
            switchmenuitem.actor.connect('toggled', Lang.bind(this, function(object, value){
                try {
                    if(value) {
                        this._icon.gicon = Gio.icon_new_for_string(`${Me.path}/icons/VULA_ACTIVE.svg`);
                        Util.spawn([vulaPath, 'start']);
                        Main.notify('Vula Notification', 'Vula started');
                    } else {
                        this._icon.gicon = Gio.icon_new_for_string(`${Me.path}/icons/VULA.svg`);
                        Util.spawn(['/bin/systemctl', 'stop', 'vula.slice']);
                        Main.notify('Vula Notification', 'Vula stopped');
                    }
                }
                catch (error) {
                    Main.notify('Vula Notification', `An error occured while starting Vula: ${error}`);
                    return;
                }
            }));

            // Vula Repair
            let vulaRepairMenuItem = new PopupMenu.PopupMenuItem("Repair Vula", {});
            vulaRepairMenuItem.actor.connect('activate', Lang.bind(this, function(){
                try {
                    Util.spawn([vulaPath, 'repair']);
		            Main.notify('Vula Notification', 'Vula repaired');
                }
                catch (error) {
                    Main.notify('Vula Notification', `An error occured while repairing Vula: ${error}`);
                    return;
                }
		    }));


            // Vula Status
            let vulaStatusItem = new PopupMenu.PopupMenuItem("Get Vula Status", {});
            vulaStatusItem.actor.connect('activate', Lang.bind(this, function(){
                try {
                    let stuff = GLib.spawn_command_line_sync(vulaPath + " status")[1].toString();
                    log ('stuff: ' + stuff);
                    Main.notify('Vula Notification', stuff);
                }
                catch (error) {
                    Main.notify('Vula Notification', `An error occured while getting Vula status: ${error}`);
                    return;
                }
		    }));
            

            // add Items to menu
            this.menu.addMenuItem(switchmenuitem);
            this.menu.addMenuItem(vulaRepairMenuItem);
            this.menu.addMenuItem(vulaStatusItem);

            this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem);
       }
 });

function init() {
    log ('Vula extension initalized');
};

function enable() {
     log ('Vula extension enabled');
     let _indicator =  new Vula_Indicator();
     Main.panel._addToPanelBox('Vula', _indicator, 1, Main.panel._rightBox);
};

function disable(){
     log ('Vula extension disabled');
     _indicator.destroy();
};