import os

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui_login.ui'))


class LoginDialog(QDialog, FORM_CLASS):
    def __init__(self, auth_method, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        # toggle fields according to auth method
        show_token_fields = auth_method == 'token'
        show_login_fields = not show_token_fields

        self.labelUser.setVisible(show_login_fields)
        self.editUser.setVisible(show_login_fields)
        self.labelPassword.setVisible(show_login_fields)
        self.editPassword.setVisible(show_login_fields)
        self.labelToken.setVisible(show_token_fields)
        self.editToken.setVisible(show_token_fields)

        # resize dialog window
        self.adjustSize()
        self.resize(270, self.height())
