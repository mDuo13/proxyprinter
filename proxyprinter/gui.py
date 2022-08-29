import os
import sys
import webbrowser
from PySide6 import QtCore, QtWidgets, QtGui
from proxyprinter import ProxyPrinter


class ProxySetupGui(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
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
        fpicker2 = QtWidgets.QHBoxLayout(self)
        self.layout.addLayout(fpicker2)
        fpicker2.addWidget(self.out_file)
        fpicker2.addWidget(btn2)

        btn3 = QtWidgets.QPushButton("→ Build!")
        self.layout.addWidget(btn3)

        btn1.clicked.connect(self.pick_infile)
        btn2.clicked.connect(self.pick_outfile)
        btn3.clicked.connect(self.build)

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
