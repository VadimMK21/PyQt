from threading import Lock
from typing import Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal
from datetime import datetime

class ThreadSafeDataHandler(QObject):
    """
    Thread-safe handler for Modbus data operations
    """
    data_updated = pyqtSignal(dict)  # Signal for data updates
    error_occurred = pyqtSignal(str)  # Signal for error notifications

    def __init__(self):
        super().__init__()
        self._lock = Lock()
        self._data = {}
        self._is_running = False
        self._max_data_points = 1000  # Maximum number of data points to store

    def start(self) -> None:
        """Start data collection"""
        with self._lock:
            self._is_running = True

    def stop(self) -> None:
        """Stop data collection"""
        with self._lock:
            self._is_running = False

    def is_running(self) -> bool:
        """Check if data collection is running"""
        with self._lock:
            return self._is_running

    def update_data(self, register_name: str, value: Any) -> None:
        """
        Thread-safe update of register data
        """
        with self._lock:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            if register_name not in self._data:
                self._data[register_name] = []
                
            self._data[register_name].append({
                'timestamp': timestamp,
                'value': value
            })
            
            # Cleanup old data points if needed
            if len(self._data[register_name]) > self._max_data_points:
                self._data[register_name] = self._data[register_name][-self._max_data_points:]

        # Emit signal with new data
        self.data_updated.emit({register_name: value})

    def get_data(self, register_name: str) -> list:
        """
        Thread-safe data retrieval
        """
        with self._lock:
            return self._data.get(register_name, [])

    def clear_data(self) -> None:
        """
        Thread-safe data cleanup
        """
        with self._lock:
            self._data.clear()

    def set_max_data_points(self, max_points: int) -> None:
        """
        Set maximum number of data points to store per register
        """
        if max_points < 1:
            raise ValueError("Maximum data points must be positive")
            
        with self._lock:
            self._max_data_points = max_points
            # Cleanup existing data if needed
            for register_name in self._data:
                if len(self._data[register_name]) > max_points:
                    self._data[register_name] = self._data[register_name][-max_points:]