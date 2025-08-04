"""
Окно для записи значений в регистры Modbus
"""
from datetime import datetime
from typing import List

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QTableWidget, QTableWidgetItem, QPushButton,
                             QHeaderView, QSpinBox, QComboBox, QDoubleSpinBox,
                             QTextEdit, QGroupBox, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from config.register_config import WriteRegisterConfig, create_default_write_registers
from utils.file_operations import ConfigFileManager


class WriteRegistersWindow(QMainWindow):
    """Окно для записи в регистры Modbus"""
    
    def __init__(self, logger, parent=None):
        super().__init__(parent)
        self.logger = logger
        self.write_registers: List[WriteRegisterConfig] = []
        
        # Подключаем сигнал завершения записи
        self.logger.write_completed.connect(self.on_write_completed)
        
        self.setup_ui()
        self.load_default_write_registers()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
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
        
        self.save_config_btn = QPushButton("Сохранить")
        self.save_config_btn.clicked.connect(self.save_write_config)
        
        self.load_config_btn = QPushButton("Загрузить")
        self.load_config_btn.clicked.connect(self.load_write_config)
        
        buttons_layout.addWidget(self.add_write_btn)
        buttons_layout.addWidget(self.remove_write_btn)
        buttons_layout.addWidget(self.save_config_btn)
        buttons_layout.addWidget(self.load_config_btn)
        buttons_layout.addStretch()
        
        # Таблица регистров для записи
        self.setup_write_table()
        
        # Область результатов
        self.setup_results_area()
        
        # Сборка интерфейса
        layout.addLayout(buttons_layout)
        layout.addWidget(self.write_table)
        layout.addWidget(self.results_group)
    
    def setup_write_table(self):
        """Настройка таблицы регистров для записи"""
        self.write_table = QTableWidget()
        self.write_table.setColumnCount(7)
        self.write_table.setHorizontalHeaderLabels([
            "Имя", "Slave ID", "Адрес", "Тип", "Значение", "Записать", "Прочитать"
        ])
        
        # Настройка заголовков
        header = self.write_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)       # Имя
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Slave ID
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Адрес
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Тип
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Значение
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Записать
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Прочитать
    
    def setup_results_area(self):
        """Настройка области результатов"""
        self.results_group = QGroupBox("Результаты операций")
        results_layout = QVBoxLayout(self.results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(200)
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Consolas", 9))
        
        # Кнопка очистки результатов
        clear_results_btn = QPushButton("Очистить результаты")
        clear_results_btn.clicked.connect(self.clear_results)
        
        results_layout.addWidget(self.results_text)
        results_layout.addWidget(clear_results_btn)
    
    def load_default_write_registers(self):
        """Загружает регистры для записи по умолчанию"""
        default_writes = create_default_write_registers()
        
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
        if 0 <= current_row < len(self.write_registers):
            self.write_table.removeRow(current_row)
            del self.write_registers[current_row]
    
    def add_write_table_row(self, write_config: WriteRegisterConfig):
        """Добавляет строку в таблицу записи"""
        row = self.write_table.rowCount()
        self.write_table.insertRow(row)
        
        # Имя регистра
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
        type_combo.currentTextChanged.connect(lambda: self.update_value_widget(row))
        self.write_table.setCellWidget(row, 3, type_combo)
        
        # Значение (зависит от типа)
        self.create_value_widget(row, write_config)
        
        # Кнопка записи
        write_btn = QPushButton("Записать")
        write_btn.clicked.connect(lambda: self.write_single_register(row))
        self.write_table.setCellWidget(row, 5, write_btn)
        
        # Кнопка чтения
        read_btn = QPushButton("Прочитать")
        read_btn.clicked.connect(lambda: self.read_single_register(row))
        self.write_table.setCellWidget(row, 6, read_btn)
    
    def create_value_widget(self, row: int, write_config: WriteRegisterConfig):
        """Создает виджет для значения в зависимости от типа"""
        if write_config.reg_type == "Coils":
            value_combo = QComboBox()
            value_combo.addItems(["0", "1"])
            value_combo.setCurrentText(str(int(write_config.value)))
            self.write_table.setCellWidget(row, 4, value_combo)
        elif write_config.reg_type == "I_Int":
            value_spin = QDoubleSpinBox()
            value_spin.setRange(-999999, 999999)
            value_spin.setDecimals(0)
            value_spin.setValue(write_config.value)
            self.write_table.setCellWidget(row, 4, value_spin)
        else:
            value_spin = QDoubleSpinBox()
            value_spin.setRange(-999999.999, 999999.999)
            value_spin.setDecimals(3)
            value_spin.setValue(write_config.value)
            self.write_table.setCellWidget(row, 4, value_spin)
    
    def update_value_widget(self, row: int):
        """Обновляет виджет значения при изменении типа регистра"""
        type_combo = self.write_table.cellWidget(row, 3)
        if not type_combo:
            return
        
        reg_type = type_combo.currentText()
        
        # Получаем текущее значение
        current_value = 0
        current_widget = self.write_table.cellWidget(row, 4)
        if isinstance(current_widget, QDoubleSpinBox):
            current_value = current_widget.value()
        elif isinstance(current_widget, QComboBox):
            current_value = int(current_widget.currentText())
        
        # Создаем новый виджет в зависимости от типа
        if reg_type == "Coils":
            value_combo = QComboBox()
            value_combo.addItems(["0", "1"])
            value_combo.setCurrentText(str(int(current_value) if current_value else "0"))
            self.write_table.setCellWidget(row, 4, value_combo)
        elif reg_type =="I_Int":
            value_spin = QDoubleSpinBox()
            value_spin.setRange(-999999, 999999)
            value_spin.setDecimals(0)
            value_spin.setValue(int(current_value))
            self.write_table.setCellWidget(row, 4, value_spin)
        else:
            value_spin = QDoubleSpinBox()
            value_spin.setRange(-999999.999, 999999.999)
            value_spin.setDecimals(3)
            value_spin.setValue(float(current_value))
            self.write_table.setCellWidget(row, 4, value_spin)
    
    def write_single_register(self, row: int):
        """Записывает значение в один регистр"""
        if row >= len(self.write_registers):
            return
        
        # Обновляем конфигурацию из таблицы
        self.update_write_config_from_table(row)
        
        write_config = self.write_registers[row]
        
        # Выполняем запись
        self.add_result(f"Запись в {write_config.name}...")
        self.logger.write_register(write_config)
    
    def read_single_register(self, row: int):
        """Читает значение одного регистра"""
        if row >= len(self.write_registers):
            return
        
        self.update_write_config_from_table(row)
        read_config = self.write_registers[row]
        
        # Создаем временную конфигурацию для чтения
        from config.register_config import RegisterConfig
        temp_config = RegisterConfig(
            name=read_config.name,
            slave_id=read_config.slave_id,
            address=read_config.address,
            count=2 if read_config.reg_type in ["I_Float", "I_Int"] else 1,
            reg_type=read_config.reg_type,
            enabled=True
        )
        
        # Читаем значение
        if self.logger.reader:
            value = self.logger.reader.read_register(temp_config)
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if value is not None:
                self.add_result(f"[{timestamp}] Прочитано из {read_config.name}: {value}")
                
                # Обновляем значение в таблице
                value_widget = self.write_table.cellWidget(row, 4)
                if isinstance(value_widget, QDoubleSpinBox):
                    value_widget.setValue(float(value))
                elif isinstance(value_widget, QComboBox):
                    value_widget.setCurrentText(str(int(value)))
            else:
                self.add_result(f"[{timestamp}] Ошибка чтения из {read_config.name}")
        else:
            self.add_result("Ошибка: нет подключения к Modbus")
    
    def update_write_config_from_table(self, row: int):
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
    
    def on_write_completed(self, register_name: str, success: bool, message: str):
        """Обработчик завершения записи"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "✓" if success else "✗"
        self.add_result(f"[{timestamp}] {status} {message}")
        
        if not success:
            QMessageBox.warning(self, "Ошибка записи", message)
    
    def add_result(self, message: str):
        """Добавляет сообщение в область результатов"""
        self.results_text.append(message)
        # Прокручиваем к последнему сообщению
        scrollbar = self.results_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_results(self):
        """Очищает область результатов"""
        self.results_text.clear()
    
    def save_write_config(self):
        """Сохраняет конфигурацию регистров для записи"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить конфигурацию регистров для записи",
            "write_registers_config.ini",
            "INI файлы (*.ini);;Все файлы (*)"
        )
        
        if filename:
            # Обновляем конфигурации из таблицы
            for row in range(len(self.write_registers)):
                self.update_write_config_from_table(row)
            
            success = ConfigFileManager.save_write_registers_config(filename, self.write_registers)
            
            if success:
                QMessageBox.information(
                    self, "Успех",
                    f"Конфигурация записи сохранена в файл:\n{filename}"
                )
            else:
                QMessageBox.critical(
                    self, "Ошибка",
                    "Не удалось сохранить конфигурацию записи"
                )
    
    def load_write_config(self):
        """Загружает конфигурацию регистров для записи"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Загрузить конфигурацию регистров для записи",
            "",
            "INI файлы (*.ini);;Все файлы (*)"
        )
        
        if filename:
            write_registers = ConfigFileManager.load_write_registers_config(filename)
            
            if write_registers is not None:
                # Очищаем текущую конфигурацию
                self.write_registers.clear()
                self.write_table.setRowCount(0)
                
                # Загружаем новую конфигурацию
                self.write_registers = write_registers
                
                # Заполняем таблицу
                for write_reg in self.write_registers:
                    self.add_write_table_row(write_reg)                
                
                QMessageBox.information(
                    self, "Успех",
                    f"Конфигурация записи загружена из файла:\n{filename}"
                )
            else:
                QMessageBox.critical(
                    self, "Ошибка",
                    "Не удалось загрузить конфигурацию записи"
                )
    
    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        # Просто скрываем окно вместо закрытия
        self.hide()
        event.ignore()