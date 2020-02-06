# -*- coding: utf-8 -*-

# McTidy the Scottish Maid...
# Copyright (C) <2018~>  <Dimitrios Koukas>

#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published
#   by the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.

#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.

#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Settings Module.

import wx

appVersion = ['v1.14', 2019, '9/2019']

cache = {'data': None}

temp = {

    'start.countdown': None,
    'auto.quit': False,
    'hide': False,
    'app.state.iconized': False  # For some reason wx doesn't detect this.

}

defRuleset = {

        'Default': (('class', 'WindowsForms10.Window.8.app.0.2bf8098_r6_ad1'),),
        'No Ruleset': ()

}

settings = {

    # Mainframe
    'app.title': 'McTidy, the Scottish maid.',
    'app.version': appVersion,
    'mainframe.pos': wx.DefaultPosition,
    'mainframe.size': wx.Size(530, 470),

    # Settings
    'config.filter.caps': False,
    'config.excludes': [],
    'app.continuous.run': False,

    # Snapshot
    'snapshots.cache': None,

    # Excluded Windows
    'exclusions.win.list': set(),

    # Ruleset
    'active.ruleset': 'Default',
    'active.ruleset.items': [],
    'rulesets.refresh': False,
    'rulesets': [],

    # Config
    'config.systray.onclose': True,
    'config.start.systray': False,
    'config.autorun': False,
    'config.hotkey.latest': (83, 's'),
    'config.snapshots.num': 4,

    # Windows List
    'windows.list': ('Window Name', 'Class', 'Location', 'Size'),
    'windows.list.cols': {
                    'Window Name': 210,
                    'Class': 100,
                    'Location': 75,
                    'Size': 90
    },

    # Snapshot List
    'snapshot.list': ('#', 'Available Snapshots', 'Date'),
    'snapshot.list.cols': {
                    '#': 25,
                    'Available Snapshots': 300,
                    'Date': 165
    },

    # Exclusions List
    'exclusions.list.size': wx.Size(400, 346),
    'exclusions.list': ('Window Name', 'Class'),
    'exclusions.list.cols': {
                    'Window Name': 220,
                    'Class': 150
    }

}
