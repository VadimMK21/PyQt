from PyQt5.QtCore import QThread, pyqtSignal
from typing import Dict, Any, Optional
import time

class ModbusReaderThread(QThread):
    """
    Background thread for reading Modbus registers
    """
    data_ready = pyqtSignal(dict)  # Signal emitted when new data is available
    error_occurred = pyqtSignal(str)  # Signal emitted on errors
    
    def __init__(self, modbus_client, register_manager, polling_interval: float = 1.0):
        super().__init__()
        self.modbus_client = modbus_client
        self.register_manager = register_manager
        self.polling_interval = polling_interval
        self._is_running = False

    def run(self):
        """Main thread loop"""
        self._is_running = True
        
        while self._is_running:
            try:
                # Read all enabled registers
                data = {}
                for reg_name, reg_config in self.register_manager.get_enabled_registers().items():
                    try:
                        value = self.modbus_client.read_register(
                            reg_config.slave_id,
                            reg_config.address,
                            reg_config.reg_type
                        )
                        data[reg_name] = value
                    except Exception as e:
                        self.error_occurred.emit(f"Error reading register {reg_name}: {str(e)}")
                        continue

                # Emit collected data
                if data:
                    self.data_ready.emit(data)

                # Wait for next polling interval
                time.sleep(self.polling_interval)
                
            except Exception as e:
                self.error_occurred.emit(f"Error in reader thread: {str(e)}")
                break

    def stop(self):
        """Stop the reader thread"""
        self._is_running = False
        self.wait()  # Wait for thread to finish