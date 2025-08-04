# config/__init__.py
"""
Модуль конфигурации для Modbus Logger
"""

from .register_config import (
    RegisterConfig,
    WriteRegisterConfig,
    RegisterManager,
    create_default_registers,
    create_default_write_registers
)

__all__ = [
    'RegisterConfig',
    'WriteRegisterConfig', 
    'RegisterManager',
    'create_default_registers',
    'create_default_write_registers'
]

# =============================================================================

# data/__init__.py
"""
Модуль данных и логирования для Modbus Logger
"""

from .logger import DataLogger, ModbusReader, ModbusWriter, CSVLogger
from .modbus_client import ModbusClientManager, ConnectionConfig, create_tcp_config, create_rtu_config

__all__ = [
    'DataLogger',
    'ModbusReader',
    'ModbusWriter', 
    'CSVLogger',
    'ModbusClientManager',
    'ConnectionConfig',
    'create_tcp_config',
    'create_rtu_config'
]

# =============================================================================

# ui/__init__.py
"""
Модуль пользовательского интерфейса для Modbus Logger
"""

from .main_window import MainWindow
from .connection_widget import ConnectionWidget
from .register_widget import RegisterWidget
from .plot_widget import PlotManager, PlotControlWidget
from .write_window import WriteRegistersWindow

__all__ = [
    'MainWindow',
    'ConnectionWidget',
    'RegisterWidget',
    'PlotManager',
    'PlotControlWidget',
    'WriteRegistersWindow'
]

# =============================================================================

# utils/__init__.py
"""
Утилиты для Modbus Logger
"""

from .file_operations import ConfigFileManager, CSVExporter

__all__ = [
    'ConfigFileManager',
    'CSVExporter'
]