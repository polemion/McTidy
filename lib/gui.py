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

# Gui Module.

import wx, wx.adv as adv
from wx.lib.mixins.listctrl import CheckListCtrlMixin, ListCtrlAutoWidthMixin
from __main__ import settings, singletons, cache, images, temp

AppTitle = '%s (%s)' % (settings['app.title'], settings['app.version'][0])

dPos = wx.DefaultPosition
dSize = wx.DefaultSize


def CreateBitmap(imgName):
    """Return embeded image."""
    img = getattr(images, imgName).Bitmap
    return img


def setIcon(parent, image=None):
    """Set icon of caller window."""
    app_icon = wx.Icon()
    if image is None: image = CreateBitmap('McTidyICO')
    try: app_icon.CopyFromBitmap(image)
    except: return  # If for a reason the image is missing.
    parent.SetIcon(app_icon)


def getCols(wxList, mcList):
    """Grab list column widths."""
    colLen = range(wxList.GetColumnCount())
    colData = {wxList.GetColumn(col).GetText(): wxList.GetColumnWidth(col) for col in colLen}
    settings[mcList] = colData


class SysTray(adv.TaskBarIcon):
    """Systray icon."""
    chkCont = None

    def __init__(self, mainFrame):
        """Init."""
        adv.TaskBarIcon.__init__(self)
        self.mainFrame = mainFrame
        self.sysIcon()
        # Event
        self.Bind(adv.EVT_TASKBAR_LEFT_UP, self.OnSyTrayLeftClick)
        self.Bind(wx.EVT_MENU_CLOSE, self.onMenuClose)

    def sysIcon(self):
        """Init systray icon."""
        if not temp['hide']:
            icon = CreateBitmap('McTidyICO')
            self.icon = wx.Icon()
            self.icon.CopyFromBitmap(icon)
            self.SetIcon(self.icon, 'McTidy')

    def OnSyTrayLeftClick(self, event):
        """Restore app window."""
        self.mainFrame.Show()
        self.mainFrame.Restore()
        self.RemoveIcon()
        temp['app.state.iconized'] = False
        self.Destroy()

    def onMenuClose(self, event):
        """Actions on menu close."""
        if self.chkCont: settings['app.continuous.run'] = True

    def CreatePopupMenu(self):
        """Systray context menu."""
        # Disable menu actions when a dialog is shown
        for x in singletons.MainFrame.GetChildren():
            if x.IsShownOnScreen(): return
        # Stop continuous resize/pos on menu open
        self.chkCont = settings['app.continuous.run']
        if self.chkCont: settings['app.continuous.run'] = False
        # Menu items
        menu = wx.Menu()
        enabled = menu.AppendCheckItem(wx.NewId(), 'Enabled')
        menu.AppendSeparator()
        ronce = menu.Append(wx.NewId(), 'Run once')
        options = menu.Append(wx.NewId(), 'Options')
        about = menu.Append(wx.NewId(), 'About')
        menu.AppendSeparator()
        openApp = menu.Append(wx.NewId(), 'Open')
        quitApp = menu.Append(wx.NewId(), 'Exit')
        # Menu inits
        if self.chkCont: enabled.Check()
        # Menu actions
        def enabledm(event):
            if self.chkCont:
                settings['app.continuous.run'] = False
                enabled.Check(False)
            else:
                settings['app.continuous.run'] = True
                enabled.Check()
        def roncem(event): singletons.MainFrame.onContinuous()
        def optionsm(event): OptionsDialog(self.mainFrame).ShowModal()
        def aboutm(event): AboutDialog(self.mainFrame).ShowModal()
        def exitAppm(event): singletons.MainFrame.onExit(None)
        # Menu events
        self.Bind(wx.EVT_MENU, enabledm, enabled)
        self.Bind(wx.EVT_MENU, roncem, ronce)
        self.Bind(wx.EVT_MENU, optionsm, options)
        self.Bind(wx.EVT_MENU, aboutm, about)
        self.Bind(wx.EVT_MENU, self.OnSyTrayLeftClick, openApp)
        self.Bind(wx.EVT_MENU, exitAppm, quitApp)
        # Show menu
        return menu


class lCtrlAWMixin(ListCtrlAutoWidthMixin):
    """Auto col width resize mixin."""

    def __init__(self):
        """Init."""
        ListCtrlAutoWidthMixin.__init__(self)
        self.setResizeColumn('LAST')


class mcListCtrl(wx.ListCtrl, lCtrlAWMixin):
    """ListCtrl with ListCtrlAutoWidthMixin mixin."""

    def __init__(self, parent, wxid, pos, size, style=wx.LC_REPORT):
        """Init."""
        wx.ListCtrl.__init__(self, parent, id=wxid, pos=pos, size=size, style=style)
        lCtrlAWMixin.__init__(self)


class ChkListCtrl(wx.ListCtrl, CheckListCtrlMixin, lCtrlAWMixin):
    """CheckListCtrl with ListCtrlAutoWidthMixin mixin."""
    checkList = None

    def __init__(self, parent, wxid, pos, size, style=wx.LC_REPORT):
        """Init."""
        wx.ListCtrl.__init__(self, parent, id=wxid, pos=pos, size=size, style=style)
        CheckListCtrlMixin.__init__(self)
        lCtrlAWMixin.__init__(self)
        self.setResizeColumn(0)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemChk)
        self.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.listMenu)
        self.Bind(wx.EVT_KEY_DOWN, self.onChar)

    def listMenu(self, event):
        """Windows list menu."""
        # Menu items
        menu = wx.Menu()
        select = menu.Append(wx.ID_ANY, 'Select All')
        menu.AppendSeparator()
        checkall = menu.Append(wx.ID_ANY, 'Check All')
        uncheckall = menu.Append(wx.ID_ANY, 'Uncheck All')
        # Menu events
        self.Bind(wx.EVT_MENU, self.selectAll, select)
        self.Bind(wx.EVT_MENU, self.checkAll, checkall)
        self.Bind(wx.EVT_MENU, self.unCheckAll, uncheckall)
        # Show menu
        self.PopupMenu(menu)
        menu.Destroy()

    def onChar(self, event):
        """Keyboard shortcuts."""
        chars = {
            'a':  65,
            'b':  68
        }
        if event.GetUnicodeKey() in chars.values() and event.ControlDown():
            if event.GetUnicodeKey() == 65: self.selectAll()
            elif event.GetUnicodeKey() == 68: self.unSelectAll()
        else: event.Skip()

    def unCheckAll(self, event):
        """Uncheck all items."""
        [self.ToggleItem(idx) for idx in self.idxScan(wx.LIST_STATE_DONTCARE) if self.IsChecked(idx)]

    def checkAll(self, event):
        """Check all items."""
        [self.ToggleItem(idx) for idx in self.idxScan(wx.LIST_STATE_DONTCARE) if not self.IsChecked(idx)]

    def unSelectAll(self, event=None):
        """Unselect all items."""
        [self.Select(idx, 0) for idx in self.idxScan(wx.LIST_STATE_SELECTED)]

    def selectAll(self, event=None):
        """Select all items."""
        [self.Select(idx) for idx in self.idxScan(wx.LIST_STATE_DONTCARE)]

    def OnItemChk(self, event):
        """On item activation."""
        [self.ToggleItem(idx) for idx in self.idxScan(wx.LIST_STATE_SELECTED)]

    def idxScan(self, state, idx=-1):
        """Scan the list."""
        while True:
            idx = self.GetNextItem(idx, wx.LIST_NEXT_ALL, state)
            if idx == -1: break
            yield idx

    def OnCheckItem(self, index, flag):
        """Actions to do when item is checked."""
        if self.checkList is None: self.checkList = []
        if flag: self.checkList.append(index)
        elif index in self.checkList: self.checkList.remove(index)


def ErrorDialog(parent, message, title='Error', style=(wx.OK|wx.ICON_HAND)):
    """Dialog for displaying error messages."""
    singletons.log(message)
    return Message(parent, message, title, style)


def Message(parent, message, title='', style=wx.OK):
    """The basis for showing McTidy dialogs."""
    dialog = wx.MessageDialog(parent, message, title, style)
    result = dialog.ShowModal()
    dialog.Destroy()
    return result


class AboutDialog(wx.Dialog):
    """A simple about dialog."""
    chkAuto = False

    def __init__(self, parent, style=wx.DEFAULT_DIALOG_STYLE|wx.STAY_ON_TOP):
        """Init."""
        title = 'McTidy %s, Copyright (C) Dimitrios Koukas.'%settings['app.version'][0]
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=title, pos=dPos, size=wx.Size(360, 620), style=style)
        setIcon(self)
        self.SetSizeHints(wx.Size(254, 331), wx.Size(254, 331))
        # Content
        McTidy = wx.StaticBitmap(self, wx.ID_ANY, CreateBitmap('aboutIMG'), dPos, dSize, 0)
        # Layout
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(McTidy, 1, wx.EXPAND, 5)
        self.SetSizer(mainSizer)
        self.Layout()
        self.Centre(wx.BOTH)
        # Events
        self.Bind(wx.EVT_MOVE_START, self.onStartMove)
        self.Bind(wx.EVT_MOVE_END, self.onStopMove)

    def onStartMove(self, event):
        """On starting to move about."""
        if settings['app.continuous.run']:
            settings['app.continuous.run'] = False
            self.chkAuto = True

    def onStopMove(self, event):
        """On finishing moving the about."""
        if self.chkAuto:
            settings['app.continuous.run'] = True
            self.chkAuto = False


class OptionsDialog(wx.Dialog):
    """Options dialog."""
    keycode = None
    recentHotLast = None
    chkAuto = False

    def __init__(self, parent, title='McTidy options', style=wx.DEFAULT_DIALOG_STYLE):
        """Init."""
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=title, pos=dPos, size=wx.Size(345, 280), style=style)
        self.SetSizeHints(-1, -1)
        setIcon(self)
        self.rulesetsList = [x for x in settings['rulesets']]

        if True:  # Content
            # General
            GenBox = wx.StaticBox(self, wx.ID_ANY, 'General:')
            self.autoRun = wx.CheckBox(GenBox, wx.ID_ANY, 'Autorun McTidy on Windows boot.%s'%(' '*34), dPos, dSize, wx.ALIGN_RIGHT)
            self.minStart = wx.CheckBox(GenBox, wx.ID_ANY, 'Start minimized (System tray).%s'%(' '*44), dPos, dSize, wx.ALIGN_RIGHT)
            self.minDesk = wx.CheckBox(GenBox,wx.ID_ANY,'Minimise to tray instead of closing.%s'%(' '*35),dPos,dSize,wx.ALIGN_RIGHT)
            # Hotkeys
            HotBox = wx.StaticBox(self, wx.ID_ANY, 'Hotkeys:')
            self.hotTxtA0 = wx.StaticText(HotBox, wx.ID_ANY, 'Use most recent snapshot:', dPos, dSize, 0)
            self.hotTxtA1 = wx.StaticText(HotBox, wx.ID_ANY, 'Ctrl + ', dPos, dSize, 0)
            self.recentHot = wx.TextCtrl(HotBox, wx.ID_ANY, '', dPos, wx.Size(80, 20), wx.TE_CENTRE)
            # Rulesets
            RuleBox = wx.StaticBox(self, wx.ID_ANY, 'Rulesets:')
            self.RuleTxt = wx.StaticText(RuleBox, wx.ID_ANY, 'Active Ruleset:', dPos, dSize, 0)
            self.Rulesets = wx.Choice(RuleBox, wx.ID_ANY, dPos, dSize, self.rulesetsList, wx.CB_SORT)
            # Snapshots
            SnapBox = wx.StaticBox(self, wx.ID_ANY, 'Snapshots:')
            self.SnapSlotTxt = wx.StaticText(SnapBox, wx.ID_ANY, 'Maximum number of Snapshot slots:', dPos, dSize, 0)
            self.SnapSlots = wx.SpinCtrl(SnapBox, wx.ID_ANY, '0', dPos, wx.Size(50, 20), wx.SP_ARROW_KEYS, 1, 20, 1)
            # Main buttons
            self.okBtn = wx.Button(self, wx.ID_OK, 'OK', dPos, wx.Size(70, 22), 0)
            self.cancelBtn = wx.Button(self, wx.ID_CANCEL, 'Cancel', dPos, wx.Size(70, 22), 0)

        self.initSettings()

        if True:  # Layout
            [x.Wrap(-1) for x in (self.hotTxtA0,self.hotTxtA1,self.SnapSlotTxt)]
            GenSizer = wx.StaticBoxSizer(GenBox, wx.VERTICAL)
            GenSizer.AddMany([(self.autoRun, 0, wx.TOP|wx.BOTTOM, 5),
                              (self.minStart, 0, wx.BOTTOM|wx.TOP, 5),(self.minDesk, 0, wx.TOP|wx.BOTTOM, 5)])
            hotSizer = wx.StaticBoxSizer(HotBox, wx.HORIZONTAL)
            hotSizer.AddMany([(self.hotTxtA0, 1, wx.ALIGN_CENTER|wx.LEFT, 5),
                              (self.hotTxtA1, 0, wx.ALIGN_CENTER, 5), (self.recentHot, 0, 0, 5)])
            SnapSlotsSizer = wx.BoxSizer(wx.HORIZONTAL)
            SnapSlotsSizer.AddMany([(self.SnapSlotTxt, 1, wx.ALIGN_CENTER|wx.LEFT, 5),(self.SnapSlots, 0, 0, 5)])
            snapSizer = wx.StaticBoxSizer(SnapBox, wx.VERTICAL)
            snapSizer.Add(SnapSlotsSizer, 0, wx.EXPAND, 5)
            ruleSizer = wx.StaticBoxSizer(RuleBox, wx.HORIZONTAL)
            ruleSizer.AddMany([(self.RuleTxt, 1, wx.ALIGN_CENTER|wx.LEFT, 5), (self.Rulesets, 0, wx.ALIGN_CENTER, 5)])
            btnSizer = wx.BoxSizer(wx.HORIZONTAL)
            btnSizer.AddMany([(self.okBtn, 0, wx.RIGHT|wx.LEFT, 5),(self.cancelBtn, 0, wx.RIGHT|wx.LEFT, 5)])
            mainSizer = wx.BoxSizer(wx.VERTICAL)
            mainSizer.AddMany([(GenSizer, 0, wx.EXPAND|wx.ALL, 5),(hotSizer, 0, wx.EXPAND|wx.ALL, 5),
                (snapSizer, 0, wx.EXPAND|wx.ALL, 5),(ruleSizer, 0, wx.EXPAND|wx.ALL, 5),(btnSizer, 0, wx.ALIGN_CENTER, 5)])
            self.SetSizer(mainSizer)
            self.Layout()
            self.Centre(wx.BOTH)

        if True:  # Disabled items todo: Enable this
            SnapBox.Hide()
            self.SnapSlotTxt.Disable()
            self.SnapSlots.Disable()

        if True:  # Events
            self.okBtn.Bind(wx.EVT_BUTTON, self.onOk)
            self.recentHot.Bind(wx.EVT_KEY_DOWN, self.onText)
            self.recentHot.Bind(wx.EVT_LEFT_DOWN, self.onMouse)
            self.Bind(wx.EVT_MOVE_START, self.onStartMove)
            self.Bind(wx.EVT_MOVE_END, self.onStopMove)

    def onStartMove(self, event):
        """On starting to move settings."""
        if settings['app.continuous.run']:
            settings['app.continuous.run'] = False
            self.chkAuto = True

    def onStopMove(self, event):
        """On finishing moving the settings."""
        if self.chkAuto:
            settings['app.continuous.run'] = True
            self.chkAuto = False

    def onMouse(self, event):
        self.recentHot.SetValue('')
        event.Skip()

    def initSettings(self):
        """Initial settings."""
        # General
        self.minStart.SetValue(settings['config.start.systray'])
        self.autoRun.SetValue(settings['config.autorun'])
        self.minDesk.SetValue(settings['config.systray.onclose'])
        # Hotkeys
        self.keycode = settings['config.hotkey.latest'][0]
        self.recentHot.SetValue(settings['config.hotkey.latest'][1])
        self.recentHot.SetMaxLength(1)
        # Rulesets
        self.activeRuleset = self.Rulesets.FindString(settings['active.ruleset'], True)
        if self.activeRuleset == wx.NOT_FOUND:
            self.activeRuleset = self.Rulesets.FindString('Default')
        self.Rulesets.SetSelection(self.activeRuleset)
        # Snapshots
        self.SnapSlots.SetValue(settings['config.snapshots.num'])

    def setSettings(self):
        """Save defined settings."""
        # General
        settings['config.start.systray'] = self.minStart.GetValue()
        settings['config.autorun'] = self.autoRun.GetValue()
        settings['config.systray.onclose'] = self.minDesk.GetValue()
        # Hotkeys
        settings['config.hotkey.latest'] = (self.keycode, self.recentHot.GetValue())
        # Snapshots
        settings['config.snapshots.num'] = self.SnapSlots.GetValue()
        # Rulesets
        if self.Rulesets.GetString(self.Rulesets.GetSelection()) != settings['active.ruleset']:
            settings['rulesets.refresh'] = True
        settings['active.ruleset'] = self.Rulesets.GetString(self.Rulesets.GetSelection())
        # Actions
        if self.autoRun.IsChecked(): singletons.winboot.setOnBoot()
        else: singletons.winboot.unSetOnBoot()

    def onText(self, event):
        """Check hotkey field(s)."""
        self.keycode = event.GetKeyCode()
        self.okBtn.SetFocus()
        event.Skip()

    def onOk(self, event):
        """On ok button event."""
        self.setSettings()
        self.exit()

    def exit(self):
        """Dialog exit actions."""
        self.Destroy()


class ExcludesDialog(wx.Dialog):
    """Exclusions dialog."""
    chkAuto = False

    def __init__(self, parent, size, title='McTidy Exclusions', style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER):
        """Init."""
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=title, pos=dPos, size=size, style=style)
        setIcon(self)
        self.SetSizeHints(-1, -1)
        self.ExcCols = settings['exclusions.list']
        self.ExcColsWidths = settings['exclusions.list.cols']
        self.excdata = list(settings['exclusions.win.list'])
        self.timer = wx.Timer(self)
        self.oSize = size

        if True:  # Content
            # Exclusions list
            exclBox = wx.StaticBox(self, wx.ID_ANY, 'Exclusions List:')
            self.excludes = ChkListCtrl(exclBox, wx.ID_ANY, dPos, dSize, wx.LC_REPORT)
            # Buttons
            self.rmvBtn = wx.Button(self, wx.ID_OK, 'Remove Selected', dPos, wx.Size(100, 22), 0)
            self.cnlBtn = wx.Button(self, wx.ID_CANCEL, 'Cancel', dPos, wx.Size(70, 22), 0)

        if True:  # Layout
            exclSizer = wx.StaticBoxSizer(exclBox, wx.VERTICAL)
            exclSizer.Add(self.excludes, 1, wx.EXPAND, 5)
            btnSizer = wx.BoxSizer(wx.HORIZONTAL)
            btnSizer.AddMany([(self.rmvBtn, 0, wx.RIGHT|wx.LEFT, 5), (self.cnlBtn, 0, wx.RIGHT|wx.LEFT, 5)])
            mainSizer = wx.BoxSizer(wx.VERTICAL)
            mainSizer.AddMany([(exclSizer, 1,
                wx.EXPAND|wx.TOP|wx.RIGHT|wx.LEFT, 5), (btnSizer, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)])
            self.SetSizer(mainSizer)
            self.Layout()
            self.Centre(wx.BOTH)

        if True:  # Events
            self.Bind(wx.EVT_TIMER, self.onUpdate, self.timer)
            self.Bind(wx.EVT_CLOSE, self.onClose)
            self.cnlBtn.Bind(wx.EVT_BUTTON, self.onClose)
            self.rmvBtn.Bind(wx.EVT_BUTTON, self.onRemove)
            self.Bind(wx.EVT_MOVE_START, self.onStartMove)
            self.Bind(wx.EVT_MOVE_END, self.onStopMove)

        self.initExcList()

    def onStartMove(self, event):
        """On starting to move exclusions."""
        if settings['app.continuous.run']:
            settings['app.continuous.run'] = False
            self.chkAuto = True

    def onStopMove(self, event):
        """On finishing moving the exclusions."""
        if self.chkAuto:
            settings['app.continuous.run'] = True
            self.chkAuto = False

    def initExcList(self):
        """Init Exclusions list."""
        self.timer.Start(50)
        self.rmvBtn.Disable()
        [self.excludes.InsertColumn(num, item, width=self.ExcColsWidths[item]) for num, item in enumerate(self.ExcCols)]
        self.showExcList()

    def showExcList(self):
        """Show Exclusions list on GUI."""
        for num, win in enumerate(self.excdata):
            self.excludes.InsertItem(num, win[0])   # Name
            self.excludes.SetItem(num, 1, win[1])   # Class

    def onUpdate(self, event):
        """Check if any item is checked."""
        if self.excludes.checkList:
            if not self.rmvBtn.IsEnabled(): self.rmvBtn.Enable()
        elif self.rmvBtn.IsEnabled(): self.rmvBtn.Disable()
        # Scrollbar hack
        if self.oSize is not None:
            self.SetSize([x + 1 for x in self.oSize])
            self.SetSize(self.oSize)
            self.oSize = None

    def onRemove(self, event):
        """Return modified exclusions list."""
        if self.excludes.checkList is not None:
            removed = [self.excdata[x] for x in self.excludes.checkList]
            settings['exclusions.win.list'].difference_update(removed)
            self.excludes.checkList = None
        self.onClose(None)

    def onClose(self, event):
        """Exit event."""
        settings['exclusions.list.size'] = self.GetSize()
        getCols(self.excludes, 'exclusions.list.cols')
        self.timer.Stop()
        self.Destroy()
