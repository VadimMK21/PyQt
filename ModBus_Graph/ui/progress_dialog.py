from PyQt5.QtWidgets import QProgressDialog, QApplication
from PyQt5.QtCore import Qt

class ProgressDialog:
    """
    Context manager for showing progress during long operations
    """
    def __init__(self, title: str, message: str, maximum: int = 100):
        self.progress = QProgressDialog(message, "Cancel", 0, maximum)
        self.progress.setWindowTitle(title)
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setAutoClose(True)
        self.progress.setAutoReset(True)

    def __enter__(self):
        self.progress.show()
        QApplication.processEvents()
        return self.progress

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.progress.close()