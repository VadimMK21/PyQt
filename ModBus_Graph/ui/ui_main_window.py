from PyQt5.QtWidgets import QMainWindow
from data.thread_safe import ThreadSafeDataHandler
from data.worker import ModbusReaderThread
from ui.progress_dialog import ProgressDialog
from utils.resource_manager import ResourceManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initialize thread-safe data handler
        self.data_handler = ThreadSafeDataHandler()
        # Initialize resource manager
        self.resource_manager = ResourceManager()
        
        # Create and register Modbus reader thread
        self.reader_thread = ModbusReaderThread(
            self.modbus_client,
            self.register_manager
        )
        self.resource_manager.register(
            self.reader_thread,
            lambda t: t.stop() if t.isRunning() else None
        )
        
        # Connect signals
        self.reader_thread.data_ready.connect(self.data_handler.update_data)
        self.reader_thread.error_occurred.connect(self.handle_error)
        self.data_handler.data_updated.connect(self.update_ui)

    def start_logging(self):
        """Start data logging with progress indication"""
        with ProgressDialog("Starting", "Initializing logging...") as progress:
            progress.setValue(50)
            self.data_handler.start()
            self.reader_thread.start()
            progress.setValue(100)

    def stop_logging(self):
        """Stop data logging"""
        with ProgressDialog("Stopping", "Stopping logging...") as progress:
            progress.setValue(50)
            self.reader_thread.stop()
            self.data_handler.stop()
            progress.setValue(100)

    def handle_error(self, error_msg: str):
        """Handle errors from worker thread"""
        # Implement error handling (e.g., show message box)
        pass

    def update_ui(self, data: dict):
        """Update UI with new data"""
        # Implement UI update logic
        pass

    def closeEvent(self, event):
        """Handle window close event"""
        self.resource_manager.cleanup()
        super().closeEvent(event)