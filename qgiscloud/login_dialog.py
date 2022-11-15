import os

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui_login.ui'))


class LoginDialog(QDialog, FORM_CLASS):
    def __init__(self, auth_method, token_page_url=None,
                 registration_page_url=None, parent=None):
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
        if show_token_fields:
            text = ""
            if token_page_url:
                text += self.tr(
                    "Copy your token from <a href=\"{token_page_url}\">here</a>"
                ).format(token_page_url=token_page_url)

            if registration_page_url:
                if text:
                    text += "<br>"
                text += self.tr(
                    "First-time users register <a href=\"{registration_page_url}\">here</a>"
                ).format(registration_page_url=registration_page_url)

            if text:
                self.labelTokenPage.setText(text)
                self.labelTokenPage.show()
            else:
                self.labelTokenPage.hide()
        else:
            self.labelTokenPage.hide()

        # resize dialog window
        self.adjustSize()
        self.resize(270, self.height())
