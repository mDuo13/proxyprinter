#!/usr/bin/env python
import os
import sys
import webbrowser
from PySide6 import QtCore, QtWidgets, QtGui
from proxyprinter import ProxyPrinter, SheetSettings


class ProxySetupGui(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.sheet_settings = None

        self.layout = QtWidgets.QVBoxLayout(self)
        self.in_file = QtWidgets.QLineEdit("", self)
        self.in_file.setPlaceholderText("Select the spreadsheet with your proxies")
        self.in_file.setReadOnly(True)
        btn1 = QtWidgets.QPushButton("Choose input file")
        fpicker1 = QtWidgets.QHBoxLayout(self)
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

        btn3 = QtWidgets.QPushButton("→ Build!")
        self.layout.addWidget(btn3)

        btn1.clicked.connect(self.pick_infile)
        btn2.clicked.connect(self.pick_outfile)
        btn3.clicked.connect(self.build)

        settingsbox = QtWidgets.QGroupBox("Settings")
        lo_sb = QtWidgets.QVBoxLayout()
        settingsbox.setLayout(lo_sb)
        self.layout.addWidget(settingsbox)
        
        setting_1 = QtWidgets.QHBoxLayout(self)
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

        richfields = QtWidgets.QGroupBox("Rich Fields")
        lo_rf = QtWidgets.QHBoxLayout()
        richfields.setLayout(lo_rf)
        self.rf_list = QtWidgets.QListWidget(self)
        lo_rf.addWidget(self.rf_list)

        self.layout.addWidget(richfields)

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
        #print(*self.sheet_settings)
        
        # Populate rich fields UI
        for rf in self.sheet_settings.rich_fields:
            self.rf_list.addItem(rf)

    @QtCore.Slot()
    def build(self):
        in_file = self.in_file.text()
        out_file = self.out_file.text()
        pp = ProxyPrinter(in_file)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write( pp.render_all() )
        webbrowser.open(f"file://{out_file}")

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = ProxySetupGui()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
