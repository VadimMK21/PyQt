"""
Виджет для настройки подключения к Modbus устройству
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                             QGridLayout, QLabel, QComboBox, QLineEdit, 
                             QSpinBox, QPushButton, QFileDialog, QMessageBox)
from PyQt5.QtCore import pyqtSignal

from data.modbus_client import ConnectionConfig, create_tcp_config, create_rtu_config
from utils.file_operations import ConfigFileManager


class ConnectionWidget(QWidget):
    """Виджет настройки подключения"""
    
    connection_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        
        # Группа настроек подключения
        conn_group = QGroupBox("Настройки подключения Modbus")
        conn_layout = QGridLayout(conn_group)
        
        # Тип подключения
        self.conn_type = QComboBox()
        self.conn_type.addItems(["TCP", "RTU"])
        self.conn_type.currentTextChanged.connect(self.on_connection_type_changed)
        
        # TCP настройки
        self.host_edit = QLineEdit("127.0.0.1")
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(502)
        
        # RTU настройки
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.baudrate_combo.setCurrentText("38400")
        
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["N", "E", "O"])
        
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.addItems(["1", "2"])
        
        self.bytesize_combo = QComboBox()
        self.bytesize_combo.addItems(["7", "8"])
        self.bytesize_combo.setCurrentText("8")
        
        # Размещение элементов
        conn_layout.addWidget(QLabel("Тип:"), 0, 0)
        conn_layout.addWidget(self.conn_type, 0, 1)
        conn_layout.addWidget(QLabel("Хост/COM:"), 1, 0)
        conn_layout.addWidget(self.host_edit, 1, 1)
        conn_layout.addWidget(QLabel("Порт:"), 2, 0)
        conn_layout.addWidget(self.port_spin, 2, 1)
        conn_layout.addWidget(QLabel("Скорость:"), 3, 0)
        conn_layout.addWidget(self.baudrate_combo, 3, 1)
        conn_layout.addWidget(QLabel("Четность:"), 4, 0)
        conn_layout.addWidget(self.parity_combo, 4, 1)
        conn_layout.addWidget(QLabel("Стоп-биты:"), 5, 0)
        conn_layout.addWidget(self.stopbits_combo, 5, 1)
        conn_layout.addWidget(QLabel("Размер:"), 6, 0)
        conn_layout.addWidget(self.bytesize_combo, 6, 1)
        
        # Группа настроек чтения
        read_group = QGroupBox("Настройки чтения")
        read_layout = QGridLayout(read_group)
        
        # Должен отвечать за диапазон показываемых значений на графике
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(20, 10000)
        self.interval_spin.setValue(1000)
        self.interval_spin.setSuffix(" мс")
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(500, 5000)
        self.timeout_spin.setValue(1000)
        self.timeout_spin.setSuffix(" мс")
        
        read_layout.addWidget(QLabel("Интервал чтения:"), 0, 0)
        read_layout.addWidget(self.interval_spin, 0, 1)
        read_layout.addWidget(QLabel("Таймаут:"), 1, 0)
        read_layout.addWidget(self.timeout_spin, 1, 1)
        
        # Кнопки сохранения/загрузки конфигурации
        buttons_layout = QHBoxLayout()
        
        self.save_config_btn = QPushButton("Сохранить настройки")
        self.save_config_btn.clicked.connect(self.save_connection_config)
        
        self.load_config_btn = QPushButton("Загрузить настройки")
        self.load_config_btn.clicked.connect(self.load_connection_config)
        
        buttons_layout.addWidget(self.save_config_btn)
        buttons_layout.addWidget(self.load_config_btn)
        
        # Сборка виджета
        layout.addWidget(conn_group)
        layout.addWidget(read_group)
        layout.addLayout(buttons_layout)
        
        # Инициализация состояния
        self.on_connection_type_changed("TCP")
    
    def on_connection_type_changed(self, conn_type: str):
        """Обработчик изменения типа подключения"""
        is_tcp = conn_type == "TCP"
        
        # Включаем/выключаем соответствующие поля
        self.port_spin.setEnabled(is_tcp)
        self.baudrate_combo.setEnabled(not is_tcp)
        self.parity_combo.setEnabled(not is_tcp)
        self.stopbits_combo.setEnabled(not is_tcp)
        self.bytesize_combo.setEnabled(not is_tcp)
        
        # Меняем подсказку для поля хост/com
        if is_tcp:
            self.host_edit.setText("127.0.0.1")
        else:
            self.host_edit.setText("COM1")
        
        self.connection_changed.emit()
    
    def get_connection_config(self) -> ConnectionConfig:
        """Возвращает текущую конфигурацию подключения"""
        if self.conn_type.currentText() == "TCP":
            return create_tcp_config(
                host=self.host_edit.text(),
                port=self.port_spin.value(),
                timeout=self.timeout_spin.value() / 1000.0  # Конвертируем в секунды
            )
        else:
            return create_rtu_config(
                port=self.host_edit.text(),
                baudrate=int(self.baudrate_combo.currentText()),
                parity=self.parity_combo.currentText(),
                stopbits=int(self.stopbits_combo.currentText()),
                bytesize=int(self.bytesize_combo.currentText()),
                timeout=self.timeout_spin.value() / 1000.0  # Конвертируем в секунды
            )
    
    def set_connection_config(self, config: ConnectionConfig):
        """Устанавливает конфигурацию подключения"""
        # Устанавливаем тип подключения
        self.conn_type.setCurrentText(config.connection_type)
        
        # Общие настройки
        self.host_edit.setText(config.host)
        self.timeout_spin.setValue(int(config.timeout * 1000))  # Конвертируем в миллисекунды
        
        if config.connection_type == "TCP":
            self.port_spin.setValue(config.port)
        else:
            self.baudrate_combo.setCurrentText(str(config.baudrate))
            self.parity_combo.setCurrentText(config.parity)
            self.stopbits_combo.setCurrentText(str(config.stopbits))
            self.bytesize_combo.setCurrentText(str(config.bytesize))
    
    def get_read_interval(self) -> int:
        """Возвращает интервал чтения в миллисекундах""" # Должен отвечать за диапазон показываемых значений на графике
        return self.interval_spin.value()
    
    def set_read_interval(self, interval: int):
        """Устанавливает интервал чтения"""
        self.interval_spin.setValue(interval)
    
    def save_connection_config(self):
        """Сохраняет конфигурацию подключения в файл"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить настройки подключения",
            "connection_config.ini",
            "INI файлы (*.ini);;Все файлы (*)"
        )
        
        if filename:
            success = ConfigFileManager.save_connection_config(
                filename,
                self.conn_type.currentText(),
                self.host_edit.text(),
                self.port_spin.value(),
                int(self.baudrate_combo.currentText()),
                self.parity_combo.currentText(),
                int(self.stopbits_combo.currentText()),
                int(self.bytesize_combo.currentText())
            )
            
            if success:
                QMessageBox.information(
                    self, "Успех",
                    f"Настройки подключения сохранены в файл:\n{filename}"
                )
            else:
                QMessageBox.critical(
                    self, "Ошибка",
                    "Не удалось сохранить настройки подключения"
                )
    
    def load_connection_config(self):
        """Загружает конфигурацию подключения из файла"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Загрузить настройки подключения",
            "",
            "INI файлы (*.ini);;Все файлы (*)"
        )
        
        if filename:
            config_data = ConfigFileManager.load_connection_config(filename)
            
            if config_data:
                # Применяем загруженные настройки
                self.conn_type.setCurrentText(config_data['type'])
                self.host_edit.setText(config_data['host'])
                self.port_spin.setValue(config_data['port'])
                self.baudrate_combo.setCurrentText(str(config_data['baudrate']))
                self.parity_combo.setCurrentText(config_data['parity'])
                self.stopbits_combo.setCurrentText(str(config_data['stopbits']))
                self.bytesize_combo.setCurrentText(str(config_data['bytesize']))
                
                QMessageBox.information(
                    self, "Успех",
                    f"Настройки подключения загружены из файла:\n{filename}"
                )
            else:
                QMessageBox.critical(
                    self, "Ошибка",
                    "Не удалось загрузить настройки подключения"
                )
    
    def validate_settings(self) -> tuple[bool, str]:
        """Проверяет корректность настроек"""
        if self.conn_type.currentText() == "TCP":
            host = self.host_edit.text().strip()
            if not host:
                return False, "Не указан IP адрес"
            
            # Простая проверка IP адреса
            if not self._is_valid_ip(host):
                return False, "Некорректный IP адрес"
        else:
            port = self.host_edit.text().strip()
            if not port:
                return False, "Не указан COM порт"
            
            # Простая проверка COM порта
            if not port.upper().startswith('COM'):
                return False, "COM порт должен начинаться с 'COM'"
        
        return True, "Настройки корректны"
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Простая проверка IP адреса"""
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            
            for part in parts:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            
            return True
        except:
            return False
    
    def get_settings_summary(self) -> str:
        """Возвращает краткое описание текущих настроек"""
        if self.conn_type.currentText() == "TCP":
            return f"TCP {self.host_edit.text()}:{self.port_spin.value()}"
        else:
            return (f"RTU {self.host_edit.text()} "
                   f"{self.baudrate_combo.currentText()}bps "
                   f"{self.parity_combo.currentText()}-"
                   f"{self.stopbits_combo.currentText()}-"
                   f"{self.bytesize_combo.currentText()}")