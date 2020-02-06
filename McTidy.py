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

# Main

import wx, os, time, winreg, win32gui, win32con, sys, _pickle as cPickle, datetime, shutil
from argparse import ArgumentParser as argP
import lib.singletons as singletons, lib.images as images
from lib.settings import cache as cache, settings as settings, appVersion as appVersion
from lib.settings import temp as temp, defRuleset as defRuleset
from lib import gui as gui

# Constants
APPFILE = sys.argv[0]
MCTIDYDIR = os.path.dirname(APPFILE)
DPOS = wx.DefaultPosition
DSIZE = wx.DefaultSize
BOT = wx.BOTTOM
RIG = wx.RIGHT
LEF = wx.LEFT
TOP = wx.TOP


class log:
    """App logger."""
    maxsize = 1048576
    logfile = os.path.join(MCTIDYDIR, 'mctidy.log')
    appname = 'mcTidy'

    def __init__(self, msg=None):
        """Init."""
        if not os.path.exists(self.logfile): open(self.logfile, 'w').close()
        if os.path.getsize(self.logfile) >= self.maxsize: self.rstlog()
        self.logmsg(msg if msg is not None else
            '========> %s %s has started. <========' % (self.appname, settings['app.version'][0]))

    def logmsg(self, msg):
        """Add log entry"""
        with open(self.logfile, 'a') as rlog:
            rlog.writelines('\n%s: %s' % (str(datetime.datetime.now()), msg.strip()))

    def rstlog(self):
        """Rotate log file."""
        with open(self.logfile, 'r') as rlog:
            raw = rlog.readlines()
        raw.pop(0)
        with open(self.logfile, 'w') as rlog:
            rlog.write(''.join(raw))


class winBoot:
    """Autorun on windows boot."""

    def __init__(self):
        """Init."""
        self.appFile = APPFILE

    def autorunReg(self):
        """Windows autorun registry location."""
        return winreg.OpenKey(winreg.ConnectRegistry(None,winreg.HKEY_CURRENT_USER),
                    r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_ALL_ACCESS)

    def setOnBoot(self):
        """Add autorun entry to windows registry."""
        if self.exists(): self.unSetOnBoot()
        else:
            with self.autorunReg() as key:
                winreg.SetValueEx(key, r'McTidy', 0, winreg.REG_SZ, self.appFile)

    def unSetOnBoot(self):
        """Remove autorun entry from windows registry."""
        if self.exists():
            with self.autorunReg() as key:
                winreg.DeleteValue(key, r'McTidy')

    def exists(self, exists=True):
        """Check if the autorun entry exists."""
        with self.autorunReg() as key:
            try: winreg.QueryValueEx(key, r'McTidy')
            except WindowsError: exists = False
        return exists


class confLib:
    """Settings storage."""

    def __init__(self):
        """Init."""
        confFile = 'mctidy.pkl'
        self.confFile = os.path.join(singletons.appdir, confFile)

    def bckConf(self):
        """Backup configuration file."""
        shutil.copyfile(self.confFile, self.confFile+'.bck')

    def restoreBck(self):
        """Restore backup configuration file."""
        if os.path.isfile(self.confFile+'.bck'):  # Try to restore backup conf
            if os.path.isfile(self.confFile): os.remove(self.confFile)
            shutil.copyfile(self.confFile+'.bck', self.confFile)
            log('Configuration file (mctidy.pkl) is corrupted: Backup configuration was automatically restored.')
            return False
        else: return True

    def chkConf(self):
        """Check if settings exist."""
        if os.path.isfile(self.confFile):
            self.restore()

    def store(self):
        """Save altered settings."""
        with open(self.confFile, 'wb') as out:
            cPickle.dump(settings, out)

    def chkComp(self):
        """Check compatibility with older versions."""
        if float(self.raw['app.version'][0].replace('v', '')) < float(appVersion[0].replace('v', '')):
            toDel = ('windows.list.cols', 'snapshot.list.cols', 'exclusions.list.cols')
            for key in toDel: del self.raw[key]

    def restore(self, error=False):
        """Restore saved settings."""
        def rAct():
            with open(self.confFile, 'rb') as inp:
                self.raw = cPickle.load(inp)
            # Check compatibility with older versions
            self.chkComp()
            # Apply settings
            for x in self.raw: settings[x] = self.raw[x]
            # Backup conf
            self.bckConf()
        def eAct():
            log('Configuration file (mctidy.pkl) is corrupted: '
                'McTidy was unable to restore/locate a valid backup so the configuration has been reset'
                    ' to the default values.')
        try: rAct()
        except: error = self.restoreBck()  # Try to restore backup
        if error: eAct()  # All is lost
        else:
            try: rAct()
            except: eAct()


class ruleSets:  # todo: Make a wizard, store restore ...
    """Rulesets actions."""

    def store(self):  # todo
        """Store ruleset."""
        # with open(....) as...

    def restore(self, rulesfile=None):  # todo
        """Restore ruleset."""
        # with open(....) as...
        settings['rulesets'] = defRuleset


class Snapshot:
    """Store/Restore factory for windows data."""

    def __init__(self):
        """Init."""
        if not os.path.isdir(singletons.snapdir):
            os.makedirs(singletons.snapdir)

    def store(self):
        """Store functions."""
        singletons.ActiveWinData.refresh()
        windows = [singletons.ActiveWinData.GetData()[:]]
        try:
            with open(self.snapStoreFile(), 'wb') as out:
                cPickle.dump(windows, out)
        except: return False
        return True

    @staticmethod
    def restore(snapFile):
        """Restore functions."""
        snapFile = os.path.join(singletons.snapdir, snapFile)
        if not os.path.isfile(snapFile): snapFile = snapFile.rstrip('  (Latest)')
        with open(snapFile, 'rb') as inp:
            raw = cPickle.load(inp)
        if len(raw) > 1:  # Compatibility layer for older versions
            settings['exclusions.win.list'].update((x[0], x[1]) for x in raw[1])
        return raw[0]

    def snapPool(self):
        """Return available snapshot files."""
        return [os.path.join(singletons.snapdir, 'snapshot%s.snap' % x) for x in range(settings['config.snapshots.num'])]

    def chkSnaps(self):
        """Check if any snapshot file exist."""
        snapPool = self.snapPool()[:]
        return any([True if os.path.isfile(x) else False for x in snapPool])

    def snapStoreFile(self):
        """Snapshots rotation."""
        snapPool = self.snapPool()[:]
        # Return first available slot
        for x in snapPool:
            if not os.path.isfile(x):
                return x
        # If none is found start rotation
        os.remove(snapPool[0])
        [os.rename(snapPool[x+1], snapPool[x]) for x in range(len(snapPool)) if x+1 < len(snapPool)]
        return snapPool[-1]


class SnapshotsList:
    """Snapshots list."""
    SL_buffer = None

    def __init__(self):
        """Init."""
        self.snapshotBox = wx.StaticBox(self, wx.ID_ANY, 'Available Snapshots:')
        self.snapList = gui.mcListCtrl(self.snapshotBox, wx.ID_ANY, DPOS, DSIZE, wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.snapCols = settings['snapshot.list']
        self.snapColsWidths = settings['snapshot.list.cols']
        singletons.snapList = self
        # self.snapList.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.snapListMenu) todo: Add rename function.

    def snapListMenu(self, event):  # todo: Add rename function.
        """Windows list menu."""
        # Menu items
        menu = wx.Menu()
        rename = menu.Append(wx.ID_ANY, 'Rename')
        # Menu events
        self.snapList.Bind(wx.EVT_MENU, self.OnRename, rename)
        # Show menu
        self.snapList.PopupMenu(menu)
        menu.Destroy()

    def OnRename(self):  # Todo: Add rename function.
        """Rename item."""

    def initSnapList(self):
        """Init Snapshots list."""
        [self.snapList.InsertColumn(num, item, width=self.snapColsWidths[item]) for num, item in enumerate(self.snapCols)]
        self.showSnapList(self.snapFiles())

    def snapFiles(self):
        """Snapshot list factory."""
        return [(num, x, time.ctime(os.path.getmtime(os.path.join(singletons.snapdir, x))))
                for num, x in enumerate(os.listdir(singletons.snapdir)) if x.endswith('.snap')]

    def refreshS(self):
        """Refresh Snapshots List."""
        if self.snapFiles() != self.SL_buffer:
            self.snapList.DeleteAllItems()
            self.showSnapList(self.snapFiles())

    def showSnapList(self, snapFiles):
        """Show Snapshots list on GUI."""
        self.SL_buffer = snapFiles
        if not snapFiles: return
        end = len(snapFiles)-1
        for num, snap in enumerate(snapFiles):
                self.snapList.InsertItem(num, str(snap[0]))
                self.snapList.SetItem(num, 1, '%s  (Latest)'%str(snap[1]) if num == end else str(snap[1]))
                self.snapList.SetItem(num, 2, str(snap[2]))


class WindowsList:
    """Windows list."""
    WL_buffer = None

    def __init__(self):
        """Init."""
        singletons.winList = self
        self.activeBox = wx.StaticBox(self, wx.ID_ANY, 'Currently Active Windows:')
        self.winList = gui.mcListCtrl(self.activeBox, wx.ID_ANY, DPOS, DSIZE, wx.LC_REPORT)
        self.WinCols = settings['windows.list']
        self.WinColsWidth = settings['windows.list.cols']
        self.winList.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.winListMenu)
        self.winList.Bind(wx.EVT_KEY_DOWN, self.onChar)

    def winListMenu(self, event):
        """Windows list menu."""
        selected = self.idxSelected()[0]
        excluded = [x for x in selected if self.winList.GetItemTextColour(x) == wx.BLUE]
        # Menu items
        menu = wx.Menu()
        exclude = menu.Append(wx.ID_ANY, 'Add to Exclusions')
        include = menu.Append(wx.ID_ANY, 'Remove from Exclusions')
        select = menu.Append(wx.ID_ANY, 'Select All')
        menu.AppendSeparator()
        copy = menu.Append(wx.ID_ANY, 'Copy to clipboard...')
        # Menu events
        self.winList.Bind(wx.EVT_MENU, self.OnExclude, exclude)
        self.winList.Bind(wx.EVT_MENU, self.OnInclude, include)
        self.winList.Bind(wx.EVT_MENU, self.selectAll, select)
        self.winList.Bind(wx.EVT_MENU, self.onCopy, copy)
        # Show menu
        if len(excluded) == len(selected): exclude.Enable(False)
        elif len(excluded) == 0: include.Enable(False)
        self.winList.PopupMenu(menu)
        menu.Destroy()

    def onChar(self, event):
        """Keyboard shortcuts."""
        chars = {
            'A':  65,
            'B':  68
        }
        if event.GetUnicodeKey() in chars.values() and event.ControlDown():
            if event.GetUnicodeKey() == 65: self.selectAll()
            elif event.GetUnicodeKey() == 68: self.unSelectAll()
        else: event.Skip()

    def unSelectAll(self, event=None):
        """Unselect all items."""
        [self.winList.Select(idx, 0) for idx in self.idxScan(wx.LIST_STATE_SELECTED)]

    def selectAll(self, event=None):
        """Select all items."""
        [self.winList.Select(idx) for idx in self.idxScan(wx.LIST_STATE_DONTCARE)]

    def idxScan(self, state, idx=-1):
        """Scan the items state in the list."""
        while True:
            idx = self.winList.GetNextItem(idx, wx.LIST_NEXT_ALL, state)
            if idx == -1: break
            yield idx

    def initWinList(self):
        """Init Windows list."""
        [self.winList.InsertColumn(num, item, width=self.WinColsWidth[item]) for num, item in enumerate(self.WinCols)]
        windows = singletons.ActiveWinData.GetData()[:]
        self.showWinList(windows)

    def idxSelected(self):
        """Create a list of selected items."""
        WLItems, item = [], -1
        while True:
            item = self.winList.GetNextItem(item, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if item == -1: break
            last = item
            WLItems.append(item)
        return WLItems, last

    def onCopy(self, event):
        """Copy item(s) text to clipboard."""
        WLItems = self.idxSelected()[0]
        result = [' | '.join([x for x in settings['windows.list']])]
        result.extend([('"%s", "%s", %s, %s'%(self.winList.GetItemText(x),self.winList.GetItemText(x,1),
            self.winList.GetItemText(x,2), self.winList.GetItemText(x,3))) for x in WLItems])
        result = '\r\n'.join((x for x in result))
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(result))
            wx.TheClipboard.Close()

    def OnExclude(self, event):
        """Add item to exclude list."""
        WLItems, last = self.idxSelected()
        settings['exclusions.win.list'].update(
            [(self.winList.GetItemText(x), self.winList.GetItemText(x,1)) for x in WLItems])
        self.refresh(force=True)
        self.winList.Focus(last)

    def OnInclude(self, event):
        """Remove item from exclude list."""
        WLItems, last = self.idxSelected()
        settings['exclusions.win.list'].difference_update(
            [(self.winList.GetItemText(x), self.winList.GetItemText(x, 1)) for x in WLItems])
        self.refresh(force=True)
        self.winList.Focus(last)

    def doFilter(self, wl_filter, rawlist):
        """Apply filter to Windows List and return."""
        if not settings['config.filter.caps']:  # Filter: no caps
            result = [x for x in rawlist if wl_filter.lower() in x[0].lower()]         # By title
            result.extend([x for x in rawlist if wl_filter.lower() in x[3].lower()])   # Extend with by class
        else:  # Filter: with caps
            result = [x for x in rawlist if wl_filter in x[0]]         # By title
            result.extend([x for x in rawlist if wl_filter in x[3]])   # Extend with by class
        return result

    def refresh(self, wl_filter=None, force=False):
        """Refresh Windows List."""
        singletons.ActiveWinData.refresh()
        windows = singletons.ActiveWinData.GetData()[:]
        if wl_filter is not None: windows = self.doFilter(wl_filter, windows)
        if windows != self.WL_buffer or force:
            self.winList.DeleteAllItems()
            self.showWinList(windows)

    def showWinList(self, windows):
        """Show Windows list on GUI."""
        self.WL_buffer = windows
        if not windows: return
        for num, win in enumerate(windows):
            self.winList.InsertItem(num, win[0])        # Name
            self.winList.SetItem(num, 1, win[3])        # Class
            self.winList.SetItem(num, 2, str(win[1]))   # Location
            self.winList.SetItem(num, 3, str(win[2]))   # Size
            # Apply exclusions color
            if (win[0], win[3]) in settings['exclusions.win.list']:
                try: self.winList.SetItemTextColour(num, wx.BLUE)
                except: pass  # Happens in windows


class SetWindows:
    """Apply Windows pos and sizes."""

    def __init__(self, winData):
        """Init."""
        self.winData = winData
        self.setChanges()

    def setChanges(self):
        """Apply windows changes."""
        winDict = {x[0]: (x[1], x[2]) for x in self.winData}
        for win in winDict.keys():
            (x, y), (w, h) = winDict[win]
            try:
                handle = win32gui.FindWindow(None, win)
                win32gui.MoveWindow(handle, x, y, w, h, True)
            except: continue


class WinState:
    """Factory for windows values."""
    WinData = []

    def __init__(self):
        """Init."""
        self.exclude = settings['config.excludes']
        self.exclude.extend([x for x in self.exclusions()])

    def exclusions(self):
        """Windows exclusions lists."""
        # Remove MS hidden windows
        msApps = ['Microsoft Store', 'Windows Shell Experience Host']
        # Remove self window
        app = ['%s (%s)' % (settings['app.title'], settings['app.version'][0]), 'McTidy options',
               'McTidy Exclusions', 'McTidy %s, by Dimitrios Koukas.'%settings['app.version'][0]]
        return app + msApps

    def refresh(self):
        """Refreshes windows values."""
        self.WinData = []
        win32gui.EnumWindows(self.callback, None)

    def GetData(self):
        """Returns windows values."""
        if not self.WinData: self.refresh()
        self.WinData.sort()
        return self.WinData

    def callback(self, hWnd, _):
        """Disassemble windows info."""
        rect = win32gui.GetWindowRect(hWnd)
        x = rect[0]  # Location: x axis
        y = rect[1]  # Location: y axis
        if (x, y) == (0, 0) or (x, y) == (-32000, -32000): return
        w = rect[2] - x  # Size: x axis
        h = rect[3] - y  # Size: y axis
        if self.isRealWindow(hWnd):  # Window Name: win32gui.GetWindowText(hWnd)
            # Apply exclusions filter
            if not win32gui.GetWindowText(hWnd) in self.exclude:
                try: winClass = win32gui.GetClassName(hWnd)  # Window Class
                except: winClass = 'Invalid'
                # Assemble window package data
                self.WinData.append((win32gui.GetWindowText(hWnd), (x, y), (w, h), winClass))

    def isRealWindow(self, hWnd):  # Thanks DzinX from stackoverflow.
        """Return True if given window is a real Windows application window."""
        if not win32gui.IsWindowVisible(hWnd) or win32gui.GetParent(hWnd) != 0: return False
        hasNoOwner = win32gui.GetWindow(hWnd, win32con.GW_OWNER) == 0
        lExStyle = win32gui.GetWindowLong(hWnd, win32con.GWL_EXSTYLE)
        if (((lExStyle & win32con.WS_EX_TOOLWINDOW) == 0 and hasNoOwner) or (
                (lExStyle & win32con.WS_EX_APPWINDOW != 0) and not hasNoOwner)):
            if win32gui.GetWindowText(hWnd): return True
        return False


class MainFrame(wx.Frame, WindowsList, SnapshotsList):
    """Gui Main Frame."""
    filterTXT = ''
    buffered = False

    def __init__(self, parent, title, pos, size, ftray=False, style=wx.DEFAULT_FRAME_STYLE|wx.STAY_ON_TOP|wx.TAB_TRAVERSAL):
        """Init."""
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=title, pos=pos, size=size, style=style)
        WindowsList.__init__(self)
        SnapshotsList.__init__(self)
        gui.setIcon(self)
        self.SetSizeHints(wx.Size(530, 470), DSIZE)
        self.StartToTray = ftray if ftray else settings['config.start.systray']
        self.timer = wx.Timer(self, wx.NewId())
        self.hotKeyId = wx.ID_ANY
        if pos == (-1, -1): self.Centre(wx.BOTH)

        if True:  # Content
            # Search Field
            self.filterText = wx.StaticText(self.activeBox, wx.ID_ANY, 'Filter Windows:', DPOS, DSIZE, 0)
            self.filter = wx.TextCtrl(self.activeBox, wx.ID_ANY, '', DPOS, wx.Size(-1, 20), wx.TE_NO_VSCROLL)
            self.caps_cbox = wx.CheckBox(self.activeBox, wx.ID_ANY, 'Caps on? ', DPOS, DSIZE, wx.ALIGN_RIGHT)
            # Snapshots Buttons
            self.restore_btn = wx.Button(self.snapshotBox, wx.ID_ANY, 'Restore Snapshot', DPOS, wx.Size(-1, 21), 0)
            self.exclude_btn = wx.Button(self.snapshotBox, wx.ID_ANY, 'Exclusions List', DPOS, wx.Size(-1, 21), 0)
            self.grab_btn = wx.Button(self.snapshotBox, wx.ID_ANY, 'Take Snapshot', DPOS, wx.Size(-1, 21), 0)
            # Main Buttons
            self.opt_btn = wx.Button(self, wx.ID_ANY, 'Options...', DPOS, wx.Size(70, 22), 0)
            self.hide_btn = wx.Button(self, wx.ID_OK, 'Hide', DPOS, wx.Size(70, 22), 0)
            self.exit_btn = wx.Button(self, wx.ID_EXIT, 'Exit', DPOS, wx.Size(70, 22), 0)
            self.about_btn = wx.Button(self, wx.ID_ABOUT, '?', DPOS, wx.Size(22, 22), 0)

        if True:  # Layout
            activeSizer = wx.StaticBoxSizer(self.activeBox, wx.VERTICAL)
            activeBSizer = wx.BoxSizer(wx.HORIZONTAL)
            activeBSizer.AddMany([(self.filterText,0,wx.ALIGN_CENTER|RIG,5),
                                  (self.filter,1,RIG|LEF,5), (self.caps_cbox, 0, wx.ALIGN_CENTER_VERTICAL|LEF, 5)])
            activeSizer.SetMinSize(wx.Size(-1, 300))
            activeSizer.AddMany([(self.winList, 1, wx.EXPAND, 5),(activeBSizer, 0, wx.EXPAND|TOP|RIG|LEF, 5)])
            snapBSizer = wx.BoxSizer(wx.HORIZONTAL)
            snapBSizer.AddMany([(self.restore_btn, 0, wx.ALL, 5),(self.exclude_btn, 0, wx.ALL, 5),(self.grab_btn, 0, wx.ALL, 5)])
            snapshotSizer = wx.StaticBoxSizer(self.snapshotBox, wx.VERTICAL)
            snapshotSizer.SetMinSize(wx.Size(-1, 170))
            snapshotSizer.AddMany([(self.snapList, -1, wx.EXPAND, 5),(snapBSizer, 0, wx.ALIGN_CENTER_HORIZONTAL, 5)])
            btnSizer = wx.BoxSizer(wx.HORIZONTAL)
            btnSizer.SetMinSize(wx.Size(-1, 25))
            btnSizer.AddMany([(self.opt_btn, 0, wx.ALL, 5),
                (self.hide_btn, 0, wx.ALL, 5), (self.exit_btn, 0, wx.ALL, 5), (self.about_btn, 0, wx.ALL, 5)])
            MainSizer = wx.BoxSizer(wx.VERTICAL)
            MainSizer.AddMany([(activeSizer, 1, wx.EXPAND|TOP|RIG|LEF, 5),
                (snapshotSizer,0,TOP|RIG|LEF|wx.EXPAND,5), (btnSizer,0,wx.ALIGN_CENTER_HORIZONTAL,5)])
            self.filterText.Wrap(-1)
            self.SetSizer(MainSizer)
            self.Layout()

        if True:  # Events
            self.Bind(wx.EVT_TIMER, self.onUpdate, self.timer)
            self.Bind(wx.EVT_HOTKEY, self.actHotKey, id=self.hotKeyId)
            self.Bind(wx.EVT_CLOSE, self.onClose)
            self.Bind(wx.EVT_CHECKBOX, self.chkBox)
            self.Bind(wx.EVT_MOVE_START, self.onStartMove)
            self.Bind(wx.EVT_MOVE_END, self.onStopMove)
            self.filter.Bind(wx.EVT_TEXT, self.onTyping)
            self.restore_btn.Bind(wx.EVT_BUTTON, self.onLoadSnaphot)
            self.exclude_btn.Bind(wx.EVT_BUTTON, self.onExclude)
            self.grab_btn.Bind(wx.EVT_BUTTON, self.onGrabSnaphot)
            self.opt_btn.Bind(wx.EVT_BUTTON, self.onOptions)
            self.hide_btn.Bind(wx.EVT_BUTTON, self.onSystray)
            self.exit_btn.Bind(wx.EVT_BUTTON, self.onExit)
            self.about_btn.Bind(wx.EVT_BUTTON, self.onAbout)
        self.initSettings()

    def initSettings(self):
        """Init basic settings."""
        self.SetBackgroundColour(wx.Colour(240, 240, 240))
        self.initWinList()  # Init Windows list
        self.initSnapList()  # Init Snapshot list
        self.regHotKey()
        self.timer.Start(50)
        self.restore_btn.Disable()
        self.caps_cbox.SetValue(settings['config.filter.caps'])
        self.chkInitArgs()

    def chkInitArgs(self):
        """Check and act on parsed command line args."""
        if temp['start.countdown'] is not None:
            self.se_timer = wx.Timer(self, wx.NewId())
            self.se_timer.Start(temp['start.countdown']*1000)
            settings['app.continuous.run'] = True
            self.Bind(wx.EVT_TIMER, self.argEnabled, self.se_timer)

    def argEnabled(self, event):
        """Argument: Counter for auto window tidying."""
        self.se_timer.Stop()
        settings['app.continuous.run'] = False
        if temp['auto.quit']: self.onExit(None)

    def onStartMove(self, event):
        """On starting to move mainframe."""
        self.timer.Stop()

    def onStopMove(self, event):
        """On finishing moving the mainframe."""
        self.timer.Start(50)

    def onOptions(self, event):
        """Call options dialog."""
        self.timer.Stop()
        gui.OptionsDialog(self).ShowModal()
        self.timer.Start(50)

    def onAbout(self, event):
        """The maid.."""
        self.timer.Stop()
        gui.AboutDialog(self).ShowModal()
        self.timer.Start(50)

    def regHotKey(self, reset=False):
        """Register hotkey."""
        if reset: self.UnregisterHotKey(self.hotKey)
        self.hotKey = settings['config.hotkey.latest'][0]
        self.RegisterHotKey(self.hotKeyId, wx.MOD_CONTROL, self.hotKey)

    def actHotKey(self, event):
        """Hotkey actions"""
        self.onLoadSnaphot('latest')

    def onSystray(self, event=None):
        """Sent app to systray."""
        if event == 'start': self.StartToTray = False
        temp['app.state.iconized'] = True
        self.sysTray = gui.SysTray(self)
        self.Hide()

    def onLoadSnaphot(self, event):
        """Restore windows pos and sizes from snapshot file."""
        # If no new snapshots taken, apply buffered and return
        if self.buffered and not settings['active.ruleset']:
            # Apply windows settings
            SetWindows(settings['snapshots.cache'])
            settings['active.ruleset'] = False
            return
        # Check if any snapshots have ever been taken
        if not singletons.snapshot.chkSnaps():
            singletons.snapshot.store()
            singletons.snapList.refreshS()
        # Get raw window list
        if event == 'latest':
            raw = singletons.snapshot.restore(self.snapList.GetItemText(self.snapList.GetItemCount() - 1, 1))
        else: raw = singletons.snapshot.restore(self.snapList.GetItemText(self.snapList.GetFocusedItem(), 1))
        # Get unwanted windows
        rulesRaw = settings['rulesets'][settings['active.ruleset']] # Import Ruleset items
        ruleSetClass = [x[1] for x in rulesRaw if x[0] == 'class']  # Ruleset: By class list
        ruleSetTitle = [x[1] for x in rulesRaw if x[0] == 'title']  # Ruleset: By title list
        # Remove exclusions
        preexcl = [x for x in raw if not (x[0], x[3]) in settings['exclusions.win.list']]
        # Remove ruleset titles
        prerules = [x for x in preexcl if not x[0] in ruleSetTitle]
        # Remove ruleset classes
        result = [x for x in prerules if not x[3] in ruleSetClass]
        # Cache windows settings
        settings['snapshots.cache'] = result
        self.buffered = True
        # Apply windows settings
        SetWindows(result)
        # Refresh GUI
        singletons.winList.refresh(force=True)

    def onExclude(self, event):
        """Open exclude list."""
        gui.ExcludesDialog(self, settings['exclusions.list.size']).ShowModal()
        singletons.winList.refresh(force=True)

    def onGrabSnaphot(self, event):
        """Store current windows pos and sizes."""
        if singletons.snapshot.store():
            self.buffered = False
            singletons.snapList.refreshS()

    def chkBox(self, event):
        """Enables caps on filter."""
        settings['config.filter.caps'] = self.caps_cbox.GetValue()

    def onUpdate(self, event):
        """GUI timed events."""
        # Disable restore button if no snapshot is selected
        if self.snapList.GetFocusedItem() == -1 and not temp['app.state.iconized']:
            if self.restore_btn.IsEnabled(): self.restore_btn.Disable()
        else:
            if not self.restore_btn.IsEnabled(): self.restore_btn.Enable()
        # Window filter and window status updating
        if not temp['app.state.iconized']:
            if not self.filter.GetValue().strip(): self.refresh()
            else: self.refresh(self.filterTXT)
        # Sent to tray on start (if set)
        if self.StartToTray: self.onSystray('start')
        # If set to continuous auto arrange/pos
        if settings['app.continuous.run'] and not self.IsShown(): self.onContinuous()
        # Check if hotkey is changed
        if self.hotKey != settings['config.hotkey.latest'][0]: self.regHotKey(True)
        # Check if any snapshot item is selected
        if self.snapList.GetFocusedItem() == wx.NOT_FOUND:
            if self.restore_btn.IsEnabled(): self.restore_btn.Disable()
        else:
            if not self.restore_btn.IsEnabled(): self.restore_btn.Enable()

    def onContinuous(self, event=None):
        """Auto arrange/pos."""
        if settings['snapshots.cache'] is None: self.onLoadSnaphot('latest')
        else: SetWindows(settings['snapshots.cache'])

    def onTyping(self, event):
        """Catch typing in the Filter field."""
        self.filterTXT = self.filter.GetValue()

    def onClose(self, event):
        """Exit button event."""
        if settings['config.systray.onclose']: self.onSystray()
        else: self.onExit(None)

    def saveSettings(self):
        """Clean and Save settings."""
        # Main window settings
        settings['mainframe.pos'] = self.GetPosition()
        settings['mainframe.size'] = self.GetSize()
        # Windows list settings
        gui.getCols(self.winList, 'windows.list.cols')
        # Snapshot list settings
        gui.getCols(self.snapList, 'snapshot.list.cols')
        # Clean
        settings['snapshots.cache'] = None
        settings['app.continuous.run'] = False
        # Save
        singletons.confLib.store()

    def onExit(self, event):
        """Exit actions."""
        self.saveSettings()
        if settings['config.systray.onclose']:
            try:
                self.sysTray.RemoveIcon()
                self.sysTray.Destroy()
            except: pass
        self.timer.Stop()
        log('Exiting.')
        self.Destroy()


class main:
    """Let the fun begin..."""

    def __init__(self):
        """Init."""
        log()
        self.parseArgs()
        self.initSettings()
        self.initGUI()

    def parseArgs(self):
        """Parse start-up switches."""
        parser = argP(prog='McTidy', description='McTidy, the Scottish Maid.')
        parser.add_argument('-se', type=int, nargs='?', const=10,
                            help='McTidy will start tidying windows on program execution. Optionally '
                                 'add a number of seconds at which McTidy will stop auto-arranging windows '
                                 '(by default will stop in 10").')
        parser.add_argument('-q', action='store_true', help='McTidy will auto-quit after 10" '
                            '(if combined with -se argument it will use the seconds defined in it).')
        parser.add_argument('-si', action='store_true', help='McTidy will start hidden (Even from systray).')
        args = parser.parse_args()
        temp['start.countdown'] = self.timer = 10 if args.q and args.se is None else args.se
        temp['auto.quit'] = True if args.q else False
        temp['hide'] = args.si

    def initSettings(self):
        """Init Configuration."""
        singletons.log = log
        singletons.appdir = MCTIDYDIR
        singletons.snapdir = os.path.join(singletons.appdir, 'snapshots')
        singletons.snapshot = Snapshot()
        singletons.confLib = confLib()
        singletons.winboot = winBoot()
        singletons.rulesets = ruleSets()
        singletons.ActiveWinData = WinState()

    def initGUI(self):
        """Init GUI."""
        singletons.confLib.chkConf()
        settings['app.version'] = appVersion
        ftray = True if self.timer else False
        pos = settings['mainframe.pos']
        size = settings['mainframe.size']
        singletons.rulesets.restore()
        app = wx.App()
        singletons.MainFrame = MainFrame(None, gui.AppTitle, pos, size, ftray)
        if not settings['config.start.systray']: singletons.MainFrame.Show()
        app.MainLoop()
        log('========> mcTidy %s has exited. <========' % settings['app.version'][0])

if __name__ == '__main__':
    main()
