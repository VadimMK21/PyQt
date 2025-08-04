import sys
import csv
import time
import threading
import configparser
from datetime import datetime
from collections import deque
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QWidget, QPushButton, QLabel, 
                             QLineEdit, QSpinBox, QComboBox, QCheckBox,
                             QGroupBox, QGridLayout, QTextEdit, QTableWidget,
                             QTableWidgetItem, QHeaderView, QTabWidget,
                             QScrollArea, QSplitter, QFrame, QDoubleSpinBox,
                             QMessageBox, QFileDialog)
from PyQt5.QtCore import QTimer, pyqtSignal, QObject, Qt
from PyQt5.QtGui import QFont, QColor
import pyqtgraph as pg
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.client.mixin import ModbusClientMixin
import numpy as np
import random

class RegisterConfig:
    def __init__(self, name="Register", slave_id=1, address=0, count=1, reg_type="Holding", enabled=True, color=None, plot_group="Group1"):
        self.name = name
        self.slave_id = slave_id
        self.address = address
        self.count = count
        self.reg_type = reg_type
        self.enabled = enabled
        self.color = color or self.generate_random_color()
        self.plot_group = plot_group
        self.data = deque(maxlen=10000)  # Увеличиваем размер буфера для прокрутки
        self.time_data = deque(maxlen=10000)  # Увеличиваем размер буфера для прокрутки
        
    def generate_random_color(self):
        colors = ['r', 'g', 'b', 'c', 'm', 'y', 'w', (255, 165, 0), (255, 20, 147), (50, 205, 50)]
        return random.choice(colors)

class WriteRegisterConfig:
    def __init__(self, name="WriteReg", slave_id=1, address=0, reg_type="Holding", value=0):
        self.name = name
        self.slave_id = slave_id
        self.address = address
        self.reg_type = reg_type
        self.value = value

class DataLogger(QObject):
    data_received = pyqtSignal(str, float, str)  # register_name, value, timestamp
    write_completed = pyqtSignal(str, bool, str)  # register_name, success, message
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.is_running = False
        self.csv_file = None
        self.csv_writer = None
        self.registers = {}  # dict of RegisterConfig objects
        
    def add_register(self, reg_config):
        self.registers[reg_config.name] = reg_config
        
    def remove_register(self, name):
        if name in self.registers:
            del self.registers[name]
            
    def update_register(self, old_name, reg_config):
        if old_name in self.registers:
            del self.registers[old_name]
        self.registers[reg_config.name] = reg_config
        
    def connect_modbus(self, connection_type, host, port, baudrate, parity, stopbits, bytesize):
        try:
            if connection_type == "TCP":
                self.client = ModbusTcpClient(host, port=port)
            else:  # RTU
                self.client = ModbusSerialClient(
                    port=host,
                    baudrate=baudrate,
                    parity=parity,
                    stopbits=stopbits,
                    bytesize=bytesize,
                    timeout=1
                )
            
            connection = self.client.connect()
            return connection
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False
    
    def start_logging(self, csv_filename):
        self.csv_file = open(csv_filename, 'w', newline='', encoding='utf-8')
        self.csv_writer = csv.writer(self.csv_file)
        
        # Заголовки CSV: Timestamp + имена всех регистров
        headers = ['Timestamp'] + [reg.name for reg in self.registers.values() if reg.enabled]
        self.csv_writer.writerow(headers)
        self.csv_file.flush()
        self.is_running = True
    
    def stop_logging(self):
        self.is_running = False
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
    
    def read_register(self, reg_config):
        if not self.client or not self.is_running or not reg_config.enabled:
            return None
        
        try:
            if reg_config.reg_type == "H_Float":
                data_type=ModbusClientMixin.DATATYPE.FLOAT32
                result = self.client.read_holding_registers(reg_config.address, count=reg_config.count, device_id=reg_config.slave_id)

            elif reg_config.reg_type == "H_Int":
                data_type=ModbusClientMixin.DATATYPE.INT32
                result = self.client.read_holding_registers(reg_config.address, count=reg_config.count, device_id=reg_config.slave_id)

            elif reg_config.reg_type == "I_Float":
                data_type=ModbusClientMixin.DATATYPE.FLOAT32
                result = self.client.read_input_registers(reg_config.address, count=reg_config.count, device_id=reg_config.slave_id)

            elif reg_config.reg_type == "I_Int":
                data_type=ModbusClientMixin.DATATYPE.INT32
                result = self.client.read_input_registers(reg_config.address, count=reg_config.count, device_id=reg_config.slave_id)

            elif reg_config.reg_type == "Coils":
                result = self.client.read_coils(reg_config.address, count=reg_config.count, device_id=reg_config.slave_id)
            else:  # Discrete
                result = self.client.read_discrete_inputs(reg_config.address, count=reg_config.count, device_id=reg_config.slave_id)
            
            if result.isError():
                return None
            
            if reg_config.reg_type in ["Coils", "Discrete"]:
                return float(result.bits[0])
            else:
                if reg_config.count == 1:
                    return float(result.registers[0])
                else:
                    registers_float = ModbusSerialClient.convert_from_registers(
                    value=result,
                    data_type=data_type,
                    word_order="big")
                    return registers_float
        except Exception as e:
            print(f"Ошибка чтения регистра {reg_config.name}: {e}")
            return None
    
    def write_register(self, write_config):
        """Записывает значение в регистр"""
        if not self.client:
            self.write_completed.emit(write_config.name, False, "Нет подключения к Modbus")
            return
        
        try:
            success = False
            message = ""
            
            if write_config.reg_type == "I_Float":

                registers_float = ModbusSerialClient.convert_to_registers(
                value=write_config.value,
                data_type=ModbusClientMixin.DATATYPE.FLOAT32,
                word_order="big")
    
                result = self.client.write_registers(write_config.address, values=registers_float, device_id=write_config.slave_id)
                
                if not result.isError():
                    success = True
                    message = f"Успешно записано {write_config.value} в Holding_Float регистр {write_config.address}"
                else:
                    message = f"Ошибка записи в Holding_Float регистр: {result}"

            elif write_config.reg_type == "I_Int":
                registers_int = ModbusSerialClient.convert_to_registers(
                value=int(write_config.value),
                data_type=ModbusClientMixin.DATATYPE.INT32,
                word_order="big")

                print(write_config.value)
                print(int(write_config.value))
                print(registers_int)

                result = self.client.write_registers(write_config.address, values=registers_int, device_id=write_config.slave_id)
                
                if not result.isError():
                    success = True
                    message = f"Успешно записано {write_config.value} в Holding_Int регистр {write_config.address}"
                else:
                    message = f"Ошибка записи в Holding_Int регистр: {result}"
                    
            elif write_config.reg_type == "Coils":
                result = self.client.write_coil(write_config.address, bool(write_config.value), slave=write_config.slave_id)
                if not result.isError():
                    success = True
                    message = f"Успешно записано {bool(write_config.value)} в Coil {write_config.address}"
                else:
                    message = f"Ошибка записи в Coil: {result}"
            else:
                message = f"Тип регистра {write_config.reg_type} не поддерживает запись"
            
            self.write_completed.emit(write_config.name, success, message)
            
        except Exception as e:
            error_message = f"Исключение при записи в {write_config.name}: {e}"
            self.write_completed.emit(write_config.name, False, error_message)
    
    def read_all_registers(self):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        values = {}
        
        for reg_name, reg_config in self.registers.items():
            if reg_config.enabled:
                value = self.read_register(reg_config)
                if value is not None:
                    values[reg_name] = value
                    self.data_received.emit(reg_name, value, timestamp)
        
        # Записываем в CSV
        if self.csv_writer and values:
            row = [timestamp]
            for reg in self.registers.values():
                if reg.enabled:
                    row.append(values.get(reg.name, ''))
            self.csv_writer.writerow(row)
            self.csv_file.flush()

class WriteRegistersWindow(QMainWindow):
    def __init__(self, logger, parent=None):
        super().__init__(parent)
        self.logger = logger
        self.write_registers = []
        self.logger.write_completed.connect(self.on_write_completed)
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Запись в регистры Modbus")
        self.setGeometry(200, 200, 1000, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Заголовок
        title_label = QLabel("Запись в регистры Modbus")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        self.add_write_btn = QPushButton("Добавить")
        self.add_write_btn.clicked.connect(self.add_write_register)
        self.remove_write_btn = QPushButton("Удалить")
        self.remove_write_btn.clicked.connect(self.remove_write_register)
        
        # Кнопки сохранения/загрузки конфигурации записи
        self.save_write_config_btn = QPushButton("Сохранить")
        self.save_write_config_btn.clicked.connect(self.save_write_config)
        self.load_write_config_btn = QPushButton("Загрузить")
        self.load_write_config_btn.clicked.connect(self.load_write_config)
        
        buttons_layout.addWidget(self.add_write_btn)
        buttons_layout.addWidget(self.remove_write_btn)
        buttons_layout.addWidget(self.save_write_config_btn)
        buttons_layout.addWidget(self.load_write_config_btn)
        buttons_layout.addStretch()
        
        # Таблица регистров для записи
        self.write_table = QTableWidget()
        self.write_table.setColumnCount(7)
        self.write_table.setHorizontalHeaderLabels([
            "Имя", "Slave ID", "Адрес", "Тип", "Значение", "Записать", "Чтение"
        ])
        
        header = self.write_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        # Добавляем несколько регистров по умолчанию
        self.add_default_write_registers()
        
        # Область результатов
        results_group = QGroupBox("Результаты записи")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(200)
        self.results_text.setReadOnly(True)
        
        # Кнопка очистки результатов
        clear_results_btn = QPushButton("Очистить результаты")
        clear_results_btn.clicked.connect(self.clear_results)
        
        results_layout.addWidget(self.results_text)
        results_layout.addWidget(clear_results_btn)
        
        layout.addLayout(buttons_layout)
        layout.addWidget(self.write_table)
        layout.addWidget(results_group)
        
    def add_default_write_registers(self):
        """Добавляет несколько регистров для записи по умолчанию"""
        default_writes = [
            WriteRegisterConfig("setpoint_write", 10, 1539, "Holding", 25.0),
            WriteRegisterConfig("enable_output", 10, 2000, "Coils", 1),
            WriteRegisterConfig("manual_output", 10, 3000, "Holding", 50.0)
        ]
        
        for write_reg in default_writes:
            self.write_registers.append(write_reg)
            self.add_write_table_row(write_reg)
    
    def add_write_register(self):
        """Добавляет новый регистр для записи"""
        write_reg = WriteRegisterConfig(f"WriteReg_{len(self.write_registers)+1}")
        self.write_registers.append(write_reg)
        self.add_write_table_row(write_reg)
        
    def remove_write_register(self):
        """Удаляет выбранный регистр для записи"""
        current_row = self.write_table.currentRow()
        if current_row >= 0 and current_row < len(self.write_registers):
            self.write_table.removeRow(current_row)
            del self.write_registers[current_row]
    
    def add_write_table_row(self, write_config):
        """Добавляет строку в таблицу записи"""
        row = self.write_table.rowCount()
        self.write_table.insertRow(row)
        
        # Имя
        name_item = QTableWidgetItem(write_config.name)
        self.write_table.setItem(row, 0, name_item)
        
        # Slave ID
        slave_spin = QSpinBox()
        slave_spin.setRange(1, 255)
        slave_spin.setValue(write_config.slave_id)
        self.write_table.setCellWidget(row, 1, slave_spin)
        
        # Адрес
        addr_spin = QSpinBox()
        addr_spin.setRange(0, 65535)
        addr_spin.setValue(write_config.address)
        self.write_table.setCellWidget(row, 2, addr_spin)
        
        # Тип регистра (только те, в которые можно писать)
        type_combo = QComboBox()
        type_combo.addItems(["I_Float", "I_Int", "Coils"])
        type_combo.setCurrentText(write_config.reg_type)
        self.write_table.setCellWidget(row, 3, type_combo)
        
        # Значение
        if write_config.reg_type == "Coils":
            value_combo = QComboBox()
            value_combo.addItems(["0", "1"])
            value_combo.setCurrentText(str(int(write_config.value)))
            self.write_table.setCellWidget(row, 4, value_combo)
        else:
            value_spin = QDoubleSpinBox()
            value_spin.setRange(-999999.999, 999999.999)
            value_spin.setDecimals(3)
            value_spin.setValue(write_config.value)
            self.write_table.setCellWidget(row, 4, value_spin)
        
        # Кнопка записи
        write_btn = QPushButton("Записать")
        write_btn.clicked.connect(lambda _, r=row: self.write_single_register(r))
        self.write_table.setCellWidget(row, 5, write_btn)

        # Кнопка чтения
        read_btn = QPushButton("Чтение")
        read_btn.clicked.connect(lambda _, r=row: self.read_single_register(r))
        self.write_table.setCellWidget(row, 6, read_btn)
        
        # Обновляем виджет значения при изменении типа
        type_combo.currentTextChanged.connect(lambda _, r=row: self.update_value_widget(r))
    
    def update_value_widget(self, row):
        """Обновляет виджет значения в зависимости от типа регистра"""
        type_combo = self.write_table.cellWidget(row, 3)
        if not type_combo:
            return
            
        reg_type = type_combo.currentText()
        current_value = 0
        
        # Получаем текущее значение
        current_widget = self.write_table.cellWidget(row, 4)
        if isinstance(current_widget, QDoubleSpinBox):
            current_value = current_widget.value()
        elif isinstance(current_widget, QComboBox):
            current_value = int(current_widget.currentText())
        
        # Создаем новый виджет
        if reg_type == "Coils":
            value_combo = QComboBox()
            value_combo.addItems(["0", "1"])
            value_combo.setCurrentText(str(int(current_value) if current_value else "0"))
            self.write_table.setCellWidget(row, 4, value_combo)
        else:
            value_spin = QDoubleSpinBox()
            value_spin.setRange(-999999.999, 999999.999)
            value_spin.setDecimals(3)
            value_spin.setValue(float(current_value))
            self.write_table.setCellWidget(row, 4, value_spin)
    
    def write_single_register(self, row):
        """Записывает значение в один регистр"""
        if row >= len(self.write_registers):
            return
            
        # Обновляем конфигурацию из таблицы
        self.update_write_config_from_table(row)
        
        write_config = self.write_registers[row]
        
        # Выполняем запись в отдельном потоке, чтобы не блокировать UI
        self.add_result(f"Запись в {write_config.name}...")
        self.logger.write_register(write_config)
    
    def read_single_register(self, row):
        """Читает значение одного регистра и отображает результат"""
        if row >= len(self.write_registers):
            return
        self.update_write_config_from_table(row)
        read_config = self.write_registers[row]
        # Используем DataLogger.read_register напрямую (без логирования)
        value = self.logger.read_register(read_config)
        timestamp = datetime.now().strftime("%H:%M:%S")
        if value is not None:
            self.add_result(f"[{timestamp}] Прочитано из {read_config.name}: {value}")
        else:
            self.add_result(f"[{timestamp}] Ошибка чтения из {read_config.name}")
    
    def update_write_config_from_table(self, row):
        """Обновляет конфигурацию записи из данных таблицы"""
        if row >= len(self.write_registers):
            return
            
        write_config = self.write_registers[row]
        
        # Получаем данные из виджетов
        name_item = self.write_table.item(row, 0)
        slave_spin = self.write_table.cellWidget(row, 1)
        addr_spin = self.write_table.cellWidget(row, 2)
        type_combo = self.write_table.cellWidget(row, 3)
        value_widget = self.write_table.cellWidget(row, 4)
        
        if name_item:
            write_config.name = name_item.text()
        if slave_spin:
            write_config.slave_id = slave_spin.value()
        if addr_spin:
            write_config.address = addr_spin.value()
        if type_combo:
            write_config.reg_type = type_combo.currentText()
        
        if value_widget:
            if isinstance(value_widget, QDoubleSpinBox):
                write_config.value = value_widget.value()
            elif isinstance(value_widget, QComboBox):
                write_config.value = int(value_widget.currentText())
    
    def on_write_completed(self, register_name, success, message):
        """Обработчик завершения записи"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "✓" if success else "✗"
        self.add_result(f"[{timestamp}] {status} {message}")
        
        if not success:
            QMessageBox.warning(self, "Ошибка записи", message)
    
    def add_result(self, message):
        """Добавляет сообщение в область результатов"""
        self.results_text.append(message)
        # Прокручиваем к последнему сообщению
        scrollbar = self.results_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_results(self):
        """Очищает область результатов"""
        self.results_text.clear()
    
    def save_write_config_to_ini(self, filename):
        """Сохраняет конфигурацию регистров для записи в INI файл"""
        config = configparser.ConfigParser()
        
        # Сохраняем каждый регистр для записи
        for i, write_reg in enumerate(self.write_registers):
            section_name = f'WriteRegister_{i}'
            config[section_name] = {
                'name': write_reg.name,
                'slave_id': str(write_reg.slave_id),
                'address': str(write_reg.address),
                'reg_type': write_reg.reg_type,
                'value': str(write_reg.value)
            }
        
        # Сохраняем общее количество регистров для записи
        config['General'] = {
            'write_register_count': str(len(self.write_registers))
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            return True
        except Exception as e:
            print(f"Ошибка сохранения конфигурации записи: {e}")
            return False
    
    def load_write_config_from_ini(self, filename):
        """Загружает конфигурацию регистров для записи из INI файла"""
        config = configparser.ConfigParser()
        
        try:
            config.read(filename, encoding='utf-8')
            
            # Очищаем текущие регистры для записи
            self.write_registers.clear()
            self.write_table.setRowCount(0)
            
            # Загружаем регистры для записи
            if 'General' in config:
                register_count = int(config['General'].get('write_register_count', 0))
                
                for i in range(register_count):
                    section_name = f'WriteRegister_{i}'
                    if section_name in config:
                        section = config[section_name]
                        
                        # Создаем объект WriteRegisterConfig
                        write_reg = WriteRegisterConfig(
                            name=section.get('name', f'WriteReg_{i+1}'),
                            slave_id=int(section.get('slave_id', 1)),
                            address=int(section.get('address', 0)),
                            reg_type=section.get('reg_type', 'Holding'),
                            value=float(section.get('value', 0))
                        )
                        
                        self.write_registers.append(write_reg)
                        self.add_write_table_row(write_reg)
            
            return True
            
        except Exception as e:
            print(f"Ошибка загрузки конфигурации записи: {e}")
            return False
    
    def save_write_config(self):
        """Обработчик кнопки сохранения конфигурации записи"""
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Сохранить конфигурацию регистров для записи", 
            "", 
            "INI файлы (*.ini);;Все файлы (*)"
        )
        
        if filename:
            if self.save_write_config_to_ini(filename):
                QMessageBox.information(self, "Успех", f"Конфигурация записи сохранена в файл:\n{filename}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить конфигурацию записи")
    
    def load_write_config(self):
        """Обработчик кнопки загрузки конфигурации записи"""
        filename, _ = QFileDialog.getOpenFileName(
            self, 
            "Загрузить конфигурацию регистров для записи", 
            "", 
            "INI файлы (*.ini);;Все файлы (*)"
        )
        
        if filename:
            if self.load_write_config_from_ini(filename):
                QMessageBox.information(self, "Успех", f"Конфигурация записи загружена из файла:\n{filename}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось загрузить конфигурацию записи")

class RegisterConfigWidget(QWidget):
    register_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.registers = []
        self.plot_mode = "separate"  # "separate" или "grouped"
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Режим отображения графиков
        mode_group = QGroupBox("Режим отображения")
        mode_layout = QHBoxLayout(mode_group)
        
        self.separate_radio = QCheckBox("Отдельные графики")
        self.grouped_radio = QCheckBox("Группировать по группам")
        self.separate_radio.setChecked(True)
        
        self.separate_radio.stateChanged.connect(self.on_mode_changed)
        self.grouped_radio.stateChanged.connect(self.on_mode_changed)
        
        mode_layout.addWidget(self.separate_radio)
        mode_layout.addWidget(self.grouped_radio)
        mode_layout.addStretch()
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.add_btn.clicked.connect(self.add_register)
        self.remove_btn = QPushButton("Удалить")
        self.remove_btn.clicked.connect(self.remove_register)
        
        # Кнопки сохранения/загрузки конфигурации
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_config)
        self.load_btn = QPushButton("Загрузить")
        self.load_btn.clicked.connect(self.load_config)
        
        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addWidget(self.remove_btn)
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.load_btn)
        buttons_layout.addStretch()
        
        # Таблица регистров
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Вкл", "Имя", "Slave ID", "Адрес", "Coin", "Тип", "Группа", "Цвет"
        ])
        
        # Подключаем сигнал изменения элементов таблицы
        self.table.itemChanged.connect(self.on_register_changed)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        
        layout.addWidget(mode_group)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.table)
        
        # Добавим несколько регистров по умолчанию
        self.add_default_registers()
        
    def add_default_registers(self):
        default_regs = [
            RegisterConfig("output", 10, 3335, 2, "Holding", True, 'r', "Sensors"),
            RegisterConfig("pv", 10, 1284, 2, "Holding", True, 'g', "Sensors"),
            RegisterConfig("setpoint", 10, 1539, 2, "Holding", True, 'b', "Flow")
        ]
        
        for reg in default_regs:
            self.registers.append(reg)
            self.add_table_row(reg)
    
    def on_mode_changed(self):
        # Убеждаемся, что только один режим активен
        if self.sender() == self.separate_radio:
            if self.separate_radio.isChecked():
                self.grouped_radio.setChecked(False)
                self.plot_mode = "separate"
        else:
            if self.grouped_radio.isChecked():
                self.separate_radio.setChecked(False)
                self.plot_mode = "grouped"
        
        # Если оба не выбраны, включаем отдельные графики
        if not self.separate_radio.isChecked() and not self.grouped_radio.isChecked():
            self.separate_radio.setChecked(True)
            self.plot_mode = "separate"
            
        self.register_changed.emit()
    
    def add_register(self):
        reg = RegisterConfig(f"Register_{len(self.registers)+1}", plot_group="Group1")
        self.registers.append(reg)
        self.add_table_row(reg)
        self.register_changed.emit()
        
    def remove_register(self):
        current_row = self.table.currentRow()
        if current_row >= 0 and current_row < len(self.registers):
            # Удаляем строку из таблицы
            self.table.removeRow(current_row)
            # Удаляем регистр из списка
            del self.registers[current_row]
            # Сигнализируем об изменении
            self.register_changed.emit()
    
    def add_table_row(self, reg_config):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Checkbox для включения/выключения
        checkbox = QCheckBox()
        checkbox.setChecked(reg_config.enabled)
        checkbox.stateChanged.connect(self.on_register_changed)
        self.table.setCellWidget(row, 0, checkbox)
        
        # Имя
        name_item = QTableWidgetItem(reg_config.name)
        self.table.setItem(row, 1, name_item)
        
        # Slave ID
        slave_spin = QSpinBox()
        slave_spin.setRange(1, 255)
        slave_spin.setValue(reg_config.slave_id)
        slave_spin.valueChanged.connect(self.on_register_changed)
        self.table.setCellWidget(row, 2, slave_spin)
        
        # Адрес
        addr_spin = QSpinBox()
        addr_spin.setRange(0, 65535)
        addr_spin.setValue(reg_config.address)
        addr_spin.valueChanged.connect(self.on_register_changed)
        self.table.setCellWidget(row, 3, addr_spin)
        
        # Количество
        count_spin = QSpinBox()
        count_spin.setRange(1, 4)
        count_spin.setValue(reg_config.count)
        count_spin.valueChanged.connect(self.on_register_changed)
        self.table.setCellWidget(row, 4, count_spin)
        
        # Тип регистра
        type_combo = QComboBox()
        type_combo.addItems(["Holding", "Input", "Coils", "Discrete"])
        type_combo.setCurrentText(reg_config.reg_type)
        type_combo.currentTextChanged.connect(self.on_register_changed)
        self.table.setCellWidget(row, 5, type_combo)
        
        # Группа графика
        group_combo = QComboBox()
        group_combo.setEditable(True)
        # Получаем существующие группы безопасно
        try:
            existing_groups = list(set([reg.plot_group for reg in self.registers if hasattr(reg, 'plot_group')]))
        except:
            existing_groups = []
        default_groups = ["Sensors", "Flow", "Control", "Status"]
        all_groups = list(set(existing_groups + default_groups))
        group_combo.addItems(all_groups)
        group_combo.setCurrentText(reg_config.plot_group)
        group_combo.currentTextChanged.connect(self.on_register_changed)
        self.table.setCellWidget(row, 6, group_combo)
        
        # Цвет (кнопка)
        color_btn = QPushButton()
        color_btn.setStyleSheet(f"background-color: {self.color_to_hex(reg_config.color)}; min-width: 30px;")
        color_btn.clicked.connect(lambda: self.change_color(row))
        self.table.setCellWidget(row, 7, color_btn)
    
    def color_to_hex(self, color):
        if isinstance(color, str):
            color_map = {'r': '#FF0000', 'g': '#00FF00', 'b': '#0000FF', 
                        'c': '#00FFFF', 'm': '#FF00FF', 'y': '#FFFF00', 'w': '#FFFFFF'}
            return color_map.get(color, '#FF0000')
        elif isinstance(color, tuple):
            return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
        return '#FF0000'
    
    def change_color(self, row):
        if row >= len(self.registers):
            return
            
        colors = ['r', 'g', 'b', 'c', 'm', 'y', (255, 165, 0), (255, 20, 147), (50, 205, 50)]
        current_color = self.registers[row].color
        current_idx = colors.index(current_color) if current_color in colors else 0
        new_idx = (current_idx + 1) % len(colors)
        new_color = colors[new_idx]
        
        self.registers[row].color = new_color
        color_btn = self.table.cellWidget(row, 7)
        if color_btn:
            color_btn.setStyleSheet(f"background-color: {self.color_to_hex(new_color)}; min-width: 30px;")

        self.register_changed.emit()
    
    def on_register_changed(self):
        # Временно отключаем сигнал для предотвращения рекурсии
        self.table.blockSignals(True)
        self.update_registers_from_table()
        self.table.blockSignals(False)
        self.register_changed.emit()
    
    def update_registers_from_table(self):
        # Обновляем список регистров в соответствии с таблицей
        updated_registers = []
        
        for row in range(self.table.rowCount()):
            try:
                # Получаем виджеты из строки
                checkbox = self.table.cellWidget(row, 0)
                name_item = self.table.item(row, 1)
                slave_spin = self.table.cellWidget(row, 2)
                addr_spin = self.table.cellWidget(row, 3)
                count_spin = self.table.cellWidget(row, 4)
                type_combo = self.table.cellWidget(row, 5)
                group_combo = self.table.cellWidget(row, 6)
                
                # Проверяем, что все виджеты существуют
                if not all([checkbox, name_item, slave_spin, addr_spin, count_spin, type_combo, group_combo]):
                    continue
                
                # Создаем или обновляем конфигурацию регистра
                if row < len(self.registers):
                    reg = self.registers[row]
                else:
                    reg = RegisterConfig()
                    
                # Обновляем параметры из таблицы
                reg.enabled = checkbox.isChecked()
                reg.name = name_item.text() if name_item.text() else f"Register_{row+1}"
                reg.slave_id = slave_spin.value()
                reg.address = addr_spin.value()
                reg.count = count_spin.value()
                reg.reg_type = type_combo.currentText()
                reg.plot_group = group_combo.currentText()
                
                updated_registers.append(reg)
                
            except (AttributeError, IndexError) as e:
                print(f"Ошибка обновления строки {row}: {e}")
                continue
        
        # Обновляем список регистров
        self.registers = updated_registers
    
    def get_registers(self):
        self.update_registers_from_table()
        return [reg for reg in self.registers if reg.enabled]
    
    def get_plot_mode(self):
        return self.plot_mode
    
    def get_plot_groups(self):
        """Возвращает словарь групп с их регистрами"""
        groups = {}
        for reg in self.get_registers():
            if reg.plot_group not in groups:
                groups[reg.plot_group] = []
            groups[reg.plot_group].append(reg)
        return groups
    
    def save_config_to_ini(self, filename):
        """Сохраняет конфигурацию регистров в INI файл"""
        config = configparser.ConfigParser()
        
        # Сохраняем режим отображения
        config['Display'] = {
            'mode': self.plot_mode
        }
        
        # Сохраняем каждый регистр
        for i, reg in enumerate(self.registers):
            section_name = f'Register_{i}'
            config[section_name] = {
                'name': reg.name,
                'slave_id': str(reg.slave_id),
                'address': str(reg.address),
                'count': str(reg.count),
                'reg_type': reg.reg_type,
                'enabled': str(reg.enabled),
                'plot_group': reg.plot_group,
                'color': str(reg.color)
            }
        
        # Сохраняем общее количество регистров
        config['General'] = {
            'register_count': str(len(self.registers))
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            return True
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
            return False
    
    def load_config_from_ini(self, filename):
        """Загружает конфигурацию регистров из INI файла"""
        config = configparser.ConfigParser()
        
        try:
            config.read(filename, encoding='utf-8')
            
            # Очищаем текущие регистры
            self.registers.clear()
            self.table.setRowCount(0)
            
            # Загружаем режим отображения
            if 'Display' in config:
                mode = config['Display'].get('mode', 'separate')
                if mode == 'separate':
                    self.separate_radio.setChecked(True)
                    self.grouped_radio.setChecked(False)
                else:
                    self.separate_radio.setChecked(False)
                    self.grouped_radio.setChecked(True)
                self.plot_mode = mode
            
            # Загружаем регистры
            if 'General' in config:
                register_count = int(config['General'].get('register_count', 0))
                
                for i in range(register_count):
                    section_name = f'Register_{i}'
                    if section_name in config:
                        section = config[section_name]
                        
                        # Создаем объект RegisterConfig
                        reg = RegisterConfig(
                            name=section.get('name', f'Register_{i+1}'),
                            slave_id=int(section.get('slave_id', 1)),
                            address=int(section.get('address', 0)),
                            count=int(section.get('count', 1)),
                            reg_type=section.get('reg_type', 'Holding'),
                            enabled=section.getboolean('enabled', True),
                            color=section.get('color', 'r'),
                            plot_group=section.get('plot_group', 'Group1')
                        )
                        
                        self.registers.append(reg)
                        self.add_table_row(reg)
            
            self.register_changed.emit()
            return True
            
        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
            return False
    
    def save_config(self):
        """Обработчик кнопки сохранения конфигурации"""
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Сохранить конфигурацию регистров", 
            "", 
            "INI файлы (*.ini);;Все файлы (*)"
        )
        
        if filename:
            if self.save_config_to_ini(filename):
                QMessageBox.information(self, "Успех", f"Конфигурация сохранена в файл:\n{filename}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить конфигурацию")
    
    def load_config(self):
        """Обработчик кнопки загрузки конфигурации"""
        filename, _ = QFileDialog.getOpenFileName(
            self, 
            "Загрузить конфигурацию регистров", 
            "", 
            "INI файлы (*.ini);;Все файлы (*)"
        )
        
        if filename:
            if self.load_config_from_ini(filename):
                QMessageBox.information(self, "Успех", f"Конфигурация загружена из файла:\n{filename}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось загрузить конфигурацию")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Register Modbus Real-Time Logger")
        self.setGeometry(100, 100, 1400, 900)
        
        # Логгер данных
        self.logger = DataLogger()
        self.logger.data_received.connect(self.update_plot)
        
        # Таймер для чтения данных
        self.read_timer = QTimer()
        self.read_timer.timeout.connect(self.read_all_data)
        
        # Графики для каждого регистра
        self.plot_curves = {}
        
        # Настройки прокрутки
        self.scroll_window_size = 60  # Размер окна прокрутки в секундах
        
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной splitter
        main_splitter = QSplitter(Qt.Horizontal)
        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.addWidget(main_splitter)
        
        # Левая панель настроек
        left_widget = QWidget()
        left_widget.setMaximumWidth(450)
        left_layout = QVBoxLayout(left_widget)
        
        # Вкладки настроек
        tabs = QTabWidget()
        
        # Вкладка подключения
        conn_tab = QWidget()
        conn_layout = QVBoxLayout(conn_tab)
        
        conn_group = QGroupBox("Подключение Modbus")
        conn_group_layout = QGridLayout(conn_group)
        
        self.conn_type = QComboBox()
        self.conn_type.addItems(["TCP", "RTU"])
        self.conn_type.currentTextChanged.connect(self.on_connection_type_changed)
        
        self.host_edit = QLineEdit("127.0.0.1")
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(502)
        
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
        
        conn_group_layout.addWidget(QLabel("Тип:"), 0, 0)
        conn_group_layout.addWidget(self.conn_type, 0, 1)
        conn_group_layout.addWidget(QLabel("Хост/COM:"), 1, 0)
        conn_group_layout.addWidget(self.host_edit, 1, 1)
        conn_group_layout.addWidget(QLabel("Порт:"), 2, 0)
        conn_group_layout.addWidget(self.port_spin, 2, 1)
        conn_group_layout.addWidget(QLabel("Скорость:"), 3, 0)
        conn_group_layout.addWidget(self.baudrate_combo, 3, 1)
        conn_group_layout.addWidget(QLabel("Четность:"), 4, 0)
        conn_group_layout.addWidget(self.parity_combo, 4, 1)
        conn_group_layout.addWidget(QLabel("Стоп-биты:"), 5, 0)
        conn_group_layout.addWidget(self.stopbits_combo, 5, 1)
        conn_group_layout.addWidget(QLabel("Размер:"), 6, 0)
        conn_group_layout.addWidget(self.bytesize_combo, 6, 1)
        
        # Интервал чтения
        interval_group = QGroupBox("Настройки чтения")
        interval_layout = QGridLayout(interval_group)
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(100, 10000)
        self.interval_spin.setValue(1000)
        self.interval_spin.setSuffix(" мс")
        
        # Настройка размера окна прокрутки
        self.scroll_window_spin = QSpinBox()
        self.scroll_window_spin.setRange(10, 600)
        self.scroll_window_spin.setValue(60)
        self.scroll_window_spin.setSuffix(" сек")
        self.scroll_window_spin.valueChanged.connect(self.on_scroll_window_changed)
        
        interval_layout.addWidget(QLabel("Интервал:"), 0, 0)
        interval_layout.addWidget(self.interval_spin, 0, 1)
        interval_layout.addWidget(QLabel("Окно прокрутки:"), 1, 0)
        interval_layout.addWidget(self.scroll_window_spin, 1, 1)
        
        # Управление
        control_group = QGroupBox("Управление")
        control_layout = QVBoxLayout(control_group)
        
        self.connect_btn = QPushButton("Подключить")
        self.connect_btn.clicked.connect(self.toggle_connection)
        
        self.start_btn = QPushButton("Начать логирование")
        self.start_btn.clicked.connect(self.toggle_logging)
        self.start_btn.setEnabled(False)
        
        self.clear_btn = QPushButton("Очистить графики")
        self.clear_btn.clicked.connect(self.clear_plots)
        
        self.reset_zoom_btn = QPushButton("Сбросить масштаб")
        self.reset_zoom_btn.clicked.connect(self.reset_plot_zoom)
        
        control_layout.addWidget(self.connect_btn)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.clear_btn)
        control_layout.addWidget(self.reset_zoom_btn)
        
        conn_layout.addWidget(conn_group)
        conn_layout.addWidget(interval_group)
        conn_layout.addWidget(control_group)
        conn_layout.addStretch()
        
        # Вкладка регистров
        self.register_config_widget = RegisterConfigWidget()
        self.register_config_widget.register_changed.connect(self.on_registers_changed)
        
        # Вкладка записи - теперь отдельное окно
        self.write_registers_window = WriteRegistersWindow(self.logger, self)
        
        tabs.addTab(conn_tab, "Подключение")
        tabs.addTab(self.register_config_widget, "Регистры")
        
        # Кнопка для открытия окна записи
        self.write_registers_btn = QPushButton("Открыть окно записи")
        self.write_registers_btn.clicked.connect(self.open_write_registers_window)
        
        # Статус
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(150)
        self.status_text.setReadOnly(True)
        
        left_layout.addWidget(tabs)
        left_layout.addWidget(self.write_registers_btn)
        left_layout.addWidget(QLabel("Статус:"))
        left_layout.addWidget(self.status_text)
        
        # Правая панель с графиками
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Скролл для графиков
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.plots_layout = QVBoxLayout(scroll_widget)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Информационная панель
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.StyledPanel)
        info_layout = QHBoxLayout(info_frame)
        
        self.connected_registers_label = QLabel("Активных регистров: 0")
        self.total_points_label = QLabel("Всего точек: 0")
        
        info_layout.addWidget(self.connected_registers_label)
        info_layout.addStretch()
        info_layout.addWidget(self.total_points_label)
        
        right_layout.addWidget(scroll_area)
        right_layout.addWidget(info_frame)
        
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([450, 950])
        
        self.on_connection_type_changed("TCP")
        self.create_plots()
        
    def on_connection_type_changed(self, conn_type):
        is_tcp = conn_type == "TCP"
        self.port_spin.setEnabled(is_tcp)
        self.baudrate_combo.setEnabled(not is_tcp)
        self.parity_combo.setEnabled(not is_tcp)
        self.stopbits_combo.setEnabled(not is_tcp)
        self.bytesize_combo.setEnabled(not is_tcp)
        
        if is_tcp:
            self.host_edit.setPlaceholderText("IP адрес")
        else:
            self.host_edit.setPlaceholderText("COM порт (например, COM1)")
    
    def on_registers_changed(self):
        self.create_plots()
    
    def create_plots(self):
        # Очищаем старые графики
        for i in reversed(range(self.plots_layout.count())):
            child = self.plots_layout.takeAt(i).widget()
            if child:
                child.setParent(None)
        
        self.plot_curves = {}
        
        plot_mode = self.register_config_widget.get_plot_mode()
        
        if plot_mode == "separate":
            self.create_separate_plots()
        else:
            self.create_grouped_plots()
        
        # Обновляем информацию
        registers = self.register_config_widget.get_registers()
        self.connected_registers_label.setText(f"Активных регистров: {len(registers)}")
        
        # Обновляем конфигурацию логгера
        self.logger.registers = {}
        for reg in self.register_config_widget.registers:
            self.logger.add_register(reg)
    
    def create_separate_plots(self):
        """Создает отдельный график для каждого регистра"""
        registers = self.register_config_widget.get_registers()
        
        for reg in registers:
            if reg.enabled:
                plot_widget = pg.PlotWidget(title=f"{reg.name} (Slave:{reg.slave_id}, Addr:{reg.address})")
                plot_widget.setLabel('left', 'Значение')
                plot_widget.setLabel('bottom', 'Время (сек)')
                plot_widget.showGrid(x=True, y=True)
                plot_widget.setMinimumHeight(200)
                
                # Настраиваем автоматическую прокрутку
                plot_widget.setAutoVisible(y=True)
                plot_widget.enableAutoRange(axis='y')
                plot_widget.disableAutoRange(axis='x')  # Отключаем авто-масштабирование по X
                
                curve = plot_widget.plot(pen=pg.mkPen(color=reg.color, width=2))
                self.plot_curves[reg.name] = {
                    'curve': curve,
                    'widget': plot_widget,
                    'config': reg
                }
                
                self.plots_layout.addWidget(plot_widget)
    
    def create_grouped_plots(self):
        """Создает график для каждой группы с несколькими кривыми"""
        groups = self.register_config_widget.get_plot_groups()
        
        for group_name, registers in groups.items():
            if not registers:
                continue
                
            # Создаем график для группы
            plot_widget = pg.PlotWidget(title=f"Группа: {group_name}")
            plot_widget.setLabel('left', 'Значение')
            plot_widget.setLabel('bottom', 'Время (сек)')
            plot_widget.showGrid(x=True, y=True)
            plot_widget.setMinimumHeight(250)
            
            # Настраиваем автоматическую прокрутку
            plot_widget.setAutoVisible(y=True)
            plot_widget.enableAutoRange(axis='y')
            plot_widget.disableAutoRange(axis='x')  # Отключаем авто-масштабирование по X
            
            # Добавляем легенду
            plot_widget.addLegend()
            
            # Создаем кривую для каждого регистра в группе
            for reg in registers:
                curve = plot_widget.plot(
                    pen=pg.mkPen(color=reg.color, width=2), 
                    name=reg.name
                )
                self.plot_curves[reg.name] = {
                    'curve': curve,
                    'widget': plot_widget,
                    'config': reg,
                    'group': group_name
                }
            
            self.plots_layout.addWidget(plot_widget)
    
    def add_status(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")
    
    def toggle_connection(self):
        if self.logger.client is None:
            self.add_status("Попытка подключения...")
            
            success = self.logger.connect_modbus(
                self.conn_type.currentText(),
                self.host_edit.text(),
                self.port_spin.value(),
                int(self.baudrate_combo.currentText()),
                self.parity_combo.currentText(),
                int(self.stopbits_combo.currentText()),
                int(self.bytesize_combo.currentText())
            )
            
            if success:
                self.connect_btn.setText("Отключить")
                self.start_btn.setEnabled(True)
                self.add_status("Подключение установлено")
            else:
                self.add_status("Ошибка подключения")
        else:
            if self.logger.is_running:
                self.toggle_logging()
            
            self.logger.client.close()
            self.logger.client = None
            self.connect_btn.setText("Подключить")
            self.start_btn.setEnabled(False)
            self.add_status("Отключено")
    
    def toggle_logging(self):
        if not self.logger.is_running:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"modbus_multi_data_{timestamp}.csv"
            
            self.logger.start_logging(csv_filename)
            self.read_timer.start(self.interval_spin.value())
            
            self.start_btn.setText("Остановить логирование")
            self.add_status(f"Логирование начато. Файл: {csv_filename}")
        else:
            self.read_timer.stop()
            self.logger.stop_logging()
            
            self.start_btn.setText("Начать логирование")
            self.add_status("Логирование остановлено")
    
    def read_all_data(self):
        self.logger.read_all_registers()
    
    def update_plot(self, register_name, value, timestamp):
        if register_name in self.plot_curves:
            plot_info = self.plot_curves[register_name]
            reg_config = plot_info['config']
            plot_widget = plot_info['widget']
            
            # Добавляем данные
            current_time = time.time()
            reg_config.time_data.append(current_time)
            reg_config.data.append(value)
            
            # Обновляем график
            if len(reg_config.time_data) > 1:
                time_array = np.array(reg_config.time_data)
                time_relative = time_array - time_array[0]
                plot_info['curve'].setData(time_relative, list(reg_config.data))
                
                # Автоматическая прокрутка влево
                if len(reg_config.time_data) > 100:  # Начинаем прокрутку после 100 точек
                    # Устанавливаем видимый диапазон по X с настраиваемым размером окна
                    window_size = min(self.scroll_window_size, time_relative[-1])
                    plot_widget.setXRange(time_relative[-1] - window_size, time_relative[-1])
        
        # Обновляем общую статистику
        total_points = sum(len(reg.data) for reg in self.logger.registers.values())
        self.total_points_label.setText(f"Всего точек: {total_points}")
    
    def clear_plots(self):
        for reg in self.logger.registers.values():
            reg.time_data.clear()
            reg.data.clear()
        
        for plot_info in self.plot_curves.values():
            plot_info['curve'].clear()
        
        self.total_points_label.setText("Всего точек: 0")
        self.add_status("Графики очищены")

    def open_write_registers_window(self):
        self.write_registers_window.show()
        self.write_registers_window.raise_()
        self.write_registers_window.activateWindow()

    def on_scroll_window_changed(self):
        self.scroll_window_size = self.scroll_window_spin.value()
        self.add_status(f"Размер окна прокрутки установлен на: {self.scroll_window_size} сек")

    def reset_plot_zoom(self):
        """Сбрасывает масштаб всех графиков к полному виду данных"""
        for plot_info in self.plot_curves.values():
            plot_widget = plot_info['widget']
            reg_config = plot_info['config']
            
            if len(reg_config.time_data) > 1:
                time_array = np.array(reg_config.time_data)
                time_relative = time_array - time_array[0]
                
                # Устанавливаем полный диапазон данных
                plot_widget.setXRange(time_relative[0], time_relative[-1])
                plot_widget.enableAutoRange(axis='y')  # Автомасштабирование по Y
                plot_widget.disableAutoRange(axis='x')  # Отключаем авто-масштабирование по X
            else:
                # Если данных нет, сбрасываем к стандартному диапазону
                plot_widget.setXRange(0, 1)
                plot_widget.setYRange(0, 1)
        
        self.add_status("Масштаб графиков сброшен к полному виду")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    pg.setConfigOptions(antialias=True)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())