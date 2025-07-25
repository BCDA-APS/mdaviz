from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QDialog

from mdaviz import APP_DESC
from mdaviz import APP_TITLE
from mdaviz import AUTHOR_LIST
from mdaviz import COPYRIGHT_TEXT
from mdaviz import DOCS_URL
from mdaviz import ISSUES_URL
from mdaviz import __version__
from mdaviz import utils


class AboutDialog(QDialog):
    """Load a generic About... Dialog as a .ui file."""

    # UI file name matches this module, different extension
    ui_file = utils.getUiFileName(__file__)

    def __init__(self, parent):
        self.parent = parent
        self.license_box = None
        self.settings = None

        super().__init__(parent)
        utils.myLoadUi(self.ui_file, baseinstance=self)
        self.setup()

    def setup(self):
        import os

        pid = os.getpid()

        self.setWindowTitle(f"About ... {APP_TITLE}")
        self.title.setText(APP_TITLE)
        self.version.setText(f"version {__version__}")
        self.description.setText(APP_DESC)
        self.authors.setText(", ".join(AUTHOR_LIST))
        self.copyright.setText(COPYRIGHT_TEXT)

        self.setStatus(f"About {APP_TITLE}, {pid=}")

        # handle the push buttons
        self.docs_pb.setToolTip(DOCS_URL)
        self.issues_pb.setToolTip(ISSUES_URL)
        self.docs_pb.clicked.connect(self.doDocsUrl)
        self.issues_pb.clicked.connect(self.doIssuesUrl)
        self.license_pb.clicked.connect(self.doLicense)

        self.setModal(False)

    def closeEvent(self, event):
        """
        called when user clicks the big [X] to quit
        """
        if self.license_box is not None:
            self.license_box.close()
        event.accept()  # let the window close

    def doUrl(self, url):
        """opening URL in default browser"""
        url = QUrl(url)
        service = QDesktopServices()
        service.openUrl(url)

    def doDocsUrl(self):
        """opening documentation URL in default browser"""
        self.setStatus("opening documentation URL in default browser")
        self.doUrl(DOCS_URL)

    def doIssuesUrl(self):
        """opening issues URL in default browser"""
        self.setStatus("opening issues URL in default browser")
        self.doUrl(ISSUES_URL)

    def doLicense(self):
        """show the license"""
        from mdaviz.licensedialog import LicenseDialog

        self.setStatus("opening License in new window")

        license = LicenseDialog(self)
        license.finished.connect(self.clearStatus)
        license.open()  # modal: must close licensedialog BEFORE aboutdialog

    def clearStatus(self):
        self.setStatus("")

    def setStatus(self, text):
        self.parent.setStatus(text)
