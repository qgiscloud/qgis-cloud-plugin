from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)

class OverwriteOrAppendDialog(QDialog):
    def __init__(self,  schema,  table):
        super().__init__()
        self.setWindowTitle(self.tr("Table exists"))
        self.setMinimumWidth(300)

        self.choice = None  # "overwrite", "append", or None

        # Layouts
        layout = QVBoxLayout()
        label = QLabel(self.tr("The table {}.{} already exists. What would you like to do?".format(schema,  table)))
        layout.addWidget(label)

        # Button-Leiste
        button_layout = QHBoxLayout()

        btn_overwrite = QPushButton(self.tr("Overwrite"))
        btn_append = QPushButton(self.tr("Append"))
        btn_cancel = QPushButton(self.tr("Cancel"))

        btn_overwrite.clicked.connect(self.choose_overwrite)
        btn_append.clicked.connect(self.choose_append)
        btn_cancel.clicked.connect(self.reject) 

        button_layout.addWidget(btn_overwrite)
        button_layout.addWidget(btn_append)
        button_layout.addWidget(btn_cancel)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def choose_overwrite(self):
        self.choice = "overwrite"
        self.accept()

    def choose_append(self):
        self.choice = "append"
        self.accept()
