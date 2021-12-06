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


const Vula_Indicator = new Lang.Class({
    Name: 'Vula.indicator',
    Extends: PanelMenu.Button,

       _init: function(){
           this.parent(0.0);

           let label = new St.Label({text: 'Vula'});
           this.actor.add_child(label);

           let menuItem = new PopupMenu.PopupMenuItem('Start Vula');
           menuItem.actor.connect('button-press-event', function() {
                try {
                    Util.spawn(['/usr/bin/vula', 'start']);
                }
                catch (error) {
                    Main.notify('Vula Notification', `An error occured while starting Vula: ${error}`);
                    return;
                }
               Main.notify('Vula Notification', 'Vula started');
            });

           this.menu.addMenuItem(menuItem);
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