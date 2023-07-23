#!/usr/bin/env python
import os
import re
import sys
import webbrowser
from collections import OrderedDict

from PySide6 import QtCore, QtWidgets, QtGui

from .proxyprinter import ProxyPrinter, SheetSettings


class ProxySetupGui(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.sheet_settings = None

        self.layout = QtWidgets.QVBoxLayout(self)
        self.in_file = QtWidgets.QLineEdit("", self)
        self.in_file.setPlaceholderText("Select the spreadsheet with your proxies")
        self.in_file.setReadOnly(True)
        btn1 = QtWidgets.QPushButton("Choose input file")
        fpicker1 = QtWidgets.QHBoxLayout()
        self.layout.addLayout(fpicker1)
        fpicker1.addWidget(self.in_file)
        fpicker1.addWidget(btn1)

        self.out_file = QtWidgets.QLineEdit("", self)
        self.out_file.setPlaceholderText("Choose where to write your proxies")
        btn2 = QtWidgets.QPushButton("Choose output file")
        fpicker2 = QtWidgets.QHBoxLayout()
        self.layout.addLayout(fpicker2)
        fpicker2.addWidget(self.out_file)
        fpicker2.addWidget(btn2)

        btn3 = QtWidgets.QPushButton("→ &Build!")
        self.layout.addWidget(btn3)

        btn1.clicked.connect(self.pick_infile)
        btn2.clicked.connect(self.pick_outfile)
        btn3.clicked.connect(self.build)

        settingsbox = QtWidgets.QGroupBox("Settings")
        lo_sb = QtWidgets.QVBoxLayout()
        settingsbox.setLayout(lo_sb)
        self.layout.addWidget(settingsbox)
        
        setting_1 = QtWidgets.QHBoxLayout()
        lbl_copy = QtWidgets.QLabel("Copyright")
        self.copyright = QtWidgets.QLineEdit("", self)
        lbl_copy.setBuddy(self.copyright)
        setting_1.addWidget(lbl_copy)
        setting_1.addWidget(self.copyright)
        lo_sb.addLayout(setting_1)

        setting_2 = QtWidgets.QHBoxLayout()
        lbl_css = QtWidgets.QLabel("Add'l CSS File Name")
        self.css_file = QtWidgets.QLineEdit("", self)
        lbl_css.setBuddy(self.css_file)
        setting_2.addWidget(lbl_css)
        setting_2.addWidget(self.css_file)
        lo_sb.addLayout(setting_2)

        setting_3 = QtWidgets.QHBoxLayout()
        lbl_baseurl = QtWidgets.QLabel("Base URL (for TTS images)")
        self.base_url = QtWidgets.QLineEdit("", self)
        lbl_baseurl.setBuddy(self.base_url)
        setting_3.addWidget(lbl_baseurl)
        setting_3.addWidget(self.base_url)
        lo_sb.addLayout(setting_3)

        self.toggles = []
        for tog in ("Include default CSS", "Colorize Traits", "Add Zip button for Tabletop Simulator export"):
            btn_tog = QtWidgets.QCheckBox(tog, self)
            btn_tog.setChecked(True)
            lo_sb.addWidget(btn_tog)
            self.toggles.append(btn_tog)
        
        richfields = QtWidgets.QGroupBox("Rich Fields")
        lo_rf = QtWidgets.QVBoxLayout()
        richfields.setLayout(lo_rf)
        lo_rfl = QtWidgets.QHBoxLayout()
        lo_rf.addLayout(lo_rfl)
        self.layout.addWidget(richfields)
        self.rf_list = QtWidgets.QListWidget(self)
        self.rf_list.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        lo_rfl.addWidget(self.rf_list)
        lo_rfb = QtWidgets.QVBoxLayout()
        btn4 = QtWidgets.QPushButton("+ Add")
        lo_rfb.addWidget(btn4)
        btn5 = QtWidgets.QPushButton("- Remove")
        lo_rfb.addWidget(btn5)
        lo_rfl.addLayout(lo_rfb)
        btn4.clicked.connect(self.add_rich_field)
        btn5.clicked.connect(self.rm_rich_field)

        self.rfsubs = QtWidgets.QTableWidget(self)
        self.rfsubs.setColumnCount(2)
        self.rfsubs.setRowCount(1)
        self.rfsubs.setHorizontalHeaderLabels(("Find (regular expression)", "Replace (HTML, use \\1, \\2, etc for backreferences)"))
        self.rfsubs.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.rfsubs.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.rfsubs.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        lo_rfsb = QtWidgets.QVBoxLayout()
        btn6 = QtWidgets.QPushButton("+ Add")
        btn6.clicked.connect(self.add_rfsub)
        lo_rfsb.addWidget(btn6)
        btn7 = QtWidgets.QPushButton("- Remove")
        btn7.clicked.connect(self.rm_rfsub)
        lo_rfsb.addWidget(btn7)
        lo_rfs = QtWidgets.QHBoxLayout()
        lo_rf.addWidget(QtWidgets.QLabel("Rich Field Processing"))
        lo_rfs.addWidget(self.rfsubs)
        lo_rfs.addLayout(lo_rfsb)
        lo_rf.addLayout(lo_rfs)

        #TODO: text sizing settings
        #TODO: save settings to sheet

    @QtCore.Slot()
    def pick_infile(self):
        dlg = QtWidgets.QFileDialog(self,
                directory=os.path.expanduser('~'),
                filter="ODS Spreadsheet (*.ods)")
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        if dlg.exec():
            fnames = dlg.selectedFiles()
            if len(fnames) == 1:
                self.in_file.setText(fnames[0])
                self.preload_sheet(fnames[0])

    @QtCore.Slot()
    def pick_outfile(self):
        dlg = QtWidgets.QFileDialog(self,
                directory=os.path.expanduser('~'),
                filter="HTML file (*.html, *.htm)")
        dlg.setFileMode(QtWidgets.QFileDialog.AnyFile)
        dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        if dlg.exec():
            fnames = dlg.selectedFiles()
            if len(fnames) == 1:
                chosen_name = fnames[0]
                if chosen_name[-5:] != ".html" and chosen_name[-4:] != ".htm":
                    chosen_name = chosen_name+".html"
                self.out_file.setText(chosen_name)
    
    def preload_sheet(self, fname):
        """
        Read ahead to populate some UI elements with details from the sheet
        after the user picks an input file.
        """

        self.sheet_settings = SheetSettings(fname)
        self.copyright.setText(self.sheet_settings.copyowner or "")
        self.css_file.setText(self.sheet_settings.addcss or "")
        
        # Populate rich fields UI
        self.rf_list.clear()
        for rf in self.sheet_settings.rich_fields:
            self.rf_list.addItem(rf)
        self.rfsubs.clear()
        self.rfsubs.setHorizontalHeaderLabels(("Find (regular expression)", "Replace (HTML, use \\1, \\2, etc for backreferences)"))
        self.rfsubs.setRowCount(len(self.sheet_settings.text_subs.keys())+1)
        for i, (pattern, replacement) in enumerate(self.sheet_settings.text_subs.items()):
            self.rfsubs.setItem(i, 0, QtWidgets.QTableWidgetItem(pattern.pattern))
            self.rfsubs.setItem(i, 1, QtWidgets.QTableWidgetItem(replacement))

    @QtCore.Slot()
    def build(self):
        in_file = self.in_file.text()
        out_file = self.out_file.text()
        if not in_file.strip() or not out_file.strip():
            return
        self.read_settings()
        pp = ProxyPrinter(*self.sheet_settings)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write( pp.render_all() )
        webbrowser.open(f"file://{out_file}")
    
    def read_settings(self):
        """
        Update the in-memory sheet_settings based on values in the UI.
        """
        self.sheet_settings.copyowner = self.copyright.text()
        self.sheet_settings.addcss = self.css_file.text()
        self.sheet_settings.base_url = self.base_url.text()

        self.sheet_settings.defaultcss = self.toggles[0].isChecked()
        self.sheet_settings.colorize = self.toggles[1].isChecked()
        self.sheet_settings.addzipbutton = self.toggles[2].isChecked()

        self.sheet_settings.rich_fields = [self.rf_list.item(r).text() for r in range(self.rf_list.count())]
        ts = OrderedDict()
        for row in range(self.rfsubs.rowCount()):
            pat_item = self.rfsubs.item(row, 0)
            if not pat_item:
                continue
            pat_text = pat_item.text()
            if not pat_text:
                continue
            pat = re.compile(pat_text) #TODO: try/except?
            repl_item = self.rfsubs.item(row, 1)
            if not repl_item:
                continue
            ts[pat] = repl_item.text()
        self.sheet_settings.text_subs = ts


    
    @QtCore.Slot()
    def add_rich_field(self):
        if self.sheet_settings:
            available_fields = self.sheet_settings.all_fields()
        else:
            available_fields = []
        text, ok = QtWidgets.QInputDialog.getItem(self, "Field Name",
                                "Field:", available_fields, editable=True)
        
        if ok and text:
            self.rf_list.addItem(text)

    @QtCore.Slot()
    def rm_rich_field(self):
        sel_items = self.rf_list.selectedItems()
        for item in sel_items:
            self.rf_list.takeItem(self.rf_list.row(item))

    @QtCore.Slot()
    def add_rfsub(self):
        self.rfsubs.insertRow(self.rfsubs.rowCount())
        
    @QtCore.Slot()
    def rm_rfsub(self):
        sel_items = self.rfsubs.selectedItems()
        sel_rows = [self.rfsubs.row(item) for item in sel_items]
        sel_rows = sorted(list(set(sel_rows)), reverse=True) # unique selected rows in descending order
        for r in sel_rows:
            self.rfsubs.removeRow(r)

def main():
    app = QtWidgets.QApplication([])

    widget = ProxySetupGui()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()