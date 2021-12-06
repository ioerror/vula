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

const { Atk, Gio, GObject, Shell, St } = imports.gi;
const Main = imports.ui.main;
const Mainloop = imports.mainloop;
const PanelMenu = imports.ui.panelMenu;
const Util = imports.misc.util;

const ExtensionUtils = imports.misc.extensionUtils;
const Me = ExtensionUtils.getCurrentExtension();

const IndicatorName = 'Vula';
const DisabledIcon = 'my-vula-off-symbolic';
const EnabledIcon = 'my-vula-on-symbolic';

let VulaIndicator;

const Vula = GObject.registerClass(
class Vula extends PanelMenu.Button {
    _init() {
        super._init(null, IndicatorName);

        this._icon = new St.Icon({
            style_class: 'system-status-icon',
        });
        this._icon.gicon = Gio.icon_new_for_string(`${Me.path}/icons/${DisabledIcon}.svg`);

        this.add_actor(this._icon);
        this.add_style_class_name('panel-status-button');
        let onPressed = () => {
            Util.spawn(['/usr/local/bin/vula', 'start']);
            _sendNotification("Button pressed");
        }
        this.connect('open-state-changed', onPressed);
    }

    _sendNotification(message) {
        Main.notify(message);
    }
});

function init() {}

function enable() {
    VulaIndicator = new Vula();
    Main.panel.addToStatusArea(IndicatorName, VulaIndicator);
}

function disable() {
    VulaIndicator.destroy();
    VulaIndicator = null;
}
