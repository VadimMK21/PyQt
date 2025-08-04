"""
Виджет настройки регистров Modbus
"""
from typing import List
import random
from typing import Set, Tuple, Any

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QCheckBox, QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QSpinBox, QComboBox, QLineEdit,
                             QFileDialog, QMessageBox)
from PyQt5.QtCore import pyqtSignal

from config.register_config import RegisterConfig, create_default_registers
from utils.file_operations import ConfigFileManager


class RegisterWidget(QWidget):
    """Виджет для настройки регистров"""
    
    registers_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.registers = []
        self.plot_mode = "separate"
        self.setup_ui()
        self.load_default_registers()
        # Множество для хранения уже использованных RGB-цветов
        self.used_colors: Set[Tuple[int, int, int]] = set()

    def generate_random_rgb_color():
        """Генерирует один случайный RGB-цвет в виде кортежа."""
        # Генерируем три случайных целых числа от 0 до 255
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
    
        return (r, g, b)    


    def generate_unique_color(self) -> Any:
        """Генерирует случайный уникальный RGB-цвет."""

        # Генерируем новый цвет
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        color = (r, g, b)

        # Проверяем, был ли этот цвет уже использован
        while color in self.used_colors:
            # Если да, генерируем новый цвет
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            color = (r, g, b)
        
        # Добавляем новый уникальный цвет в множество
        self.used_colors.add(color)
        
        return color        
        
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        
        # Режим отображения графиков
        mode_group = QGroupBox("Режим отображения графиков")
        mode_layout = QHBoxLayout(mode_group)
        
        self.separate_radio = QCheckBox("Отдельные графики")
        self.grouped_radio = QCheckBox("Группировать по группам")
        self.separate_radio.setChecked(True)
        
        self.separate_radio.stateChanged.connect(self.on_mode_changed)
        self.grouped_radio.stateChanged.connect(self.on_mode_changed)
        
        mode_layout.addWidget(self.separate_radio)
        mode_layout.addWidget(self.grouped_radio)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Добавить регистр")
        self.add_btn.clicked.connect(self.add_register)
        
        self.remove_btn = QPushButton("Удалить регистр")
        self.remove_btn.clicked.connect(self.remove_register)
        
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_config)
        
        self.load_btn = QPushButton("Загрузить")
        self.load_btn.clicked.connect(self.load_config)
        
        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addWidget(self.remove_btn)
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.load_btn)
        
        # Таблица регистров
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Вкл", "Имя", "ID", "Адрес", "Кол-во", "Тип", "Группа", "Цвет"
        ])
        
        # Настройка заголовков таблицы
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Вкл
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # Имя
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Slave ID
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Адрес
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Кол-во
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Тип
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Группа
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Цвет
        
        # Подключение сигналов изменения
        self.table.itemChanged.connect(self.on_table_changed)
        
        # Сборка виджета
        layout.addWidget(mode_group)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.table)
    
    def load_default_registers(self):
        """Загружает регистры по умолчанию"""
        default_registers = create_default_registers()
        for reg in default_registers:
            self.registers.append(reg)
            self.add_table_row(reg)
    
    def on_mode_changed(self):
        """Обработчик изменения режима отображения"""
        sender = self.sender()
        
        if sender == self.separate_radio:
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
        
        self.registers_changed.emit()
    
    def add_register(self):
        """Добавляет новый регистр"""
        color = self.generate_unique_color()
        reg = RegisterConfig(f"Register_{len(self.registers)+1}",color=color, plot_group="Group1")
        self.registers.append(reg)
        self.add_table_row(reg)
        self.registers_changed.emit()
    
    def remove_register(self):
        """Удаляет выбранный регистр"""
        current_row = self.table.currentRow()
        if 0 <= current_row < len(self.registers):
            # Удаляем из списка и таблицы
            del self.registers[current_row]
            self.table.removeRow(current_row)
            self.registers_changed.emit()
    
    def add_table_row(self, reg_config: RegisterConfig):
        """Добавляет строку в таблицу"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Блокируем сигналы во время добавления виджетов
        self.table.blockSignals(True)
        
        # Checkbox для включения/выключения
        checkbox = QCheckBox()
        checkbox.setChecked(reg_config.enabled)
        checkbox.stateChanged.connect(self.on_widget_changed)
        self.table.setCellWidget(row, 0, checkbox)
        
        # Имя регистра
        name_item = QTableWidgetItem(reg_config.name)
        self.table.setItem(row, 1, name_item)
        
        # Slave ID
        slave_spin = QSpinBox()
        slave_spin.setRange(1, 255)
        slave_spin.setValue(reg_config.slave_id)
        slave_spin.valueChanged.connect(self.on_widget_changed)
        self.table.setCellWidget(row, 2, slave_spin)
        
        # Адрес
        addr_spin = QSpinBox()
        addr_spin.setRange(0, 65535)
        addr_spin.setValue(reg_config.address)
        addr_spin.valueChanged.connect(self.on_widget_changed)
        self.table.setCellWidget(row, 3, addr_spin)
        
        # Количество регистров
        count_spin = QSpinBox()
        count_spin.setRange(1, 4)
        count_spin.setValue(reg_config.count)
        count_spin.valueChanged.connect(self.on_widget_changed)
        self.table.setCellWidget(row, 4, count_spin)
        
        # Тип регистра
        type_combo = QComboBox()
        type_combo.addItems(["H_Float", "H_Int", "I_Float", "I_Int", "Coils", "Discrete"])
        # Устанавливаем текущий тип (с обратной совместимостью)
        if reg_config.reg_type == "Holding":
            type_combo.setCurrentText("H_Float")
        elif reg_config.reg_type == "Input":
            type_combo.setCurrentText("I_Float")
        else:
            type_combo.setCurrentText(reg_config.reg_type)
        type_combo.currentTextChanged.connect(self.on_widget_changed)
        self.table.setCellWidget(row, 5, type_combo)
        
        # Группа графика
        group_combo = QComboBox()
        group_combo.setEditable(True)
        # Получаем существующие группы
        existing_groups = list(set([reg.plot_group for reg in self.registers]))
        default_groups = ["Sensors", "Flow", "Control", "Status", "Group1"]
        all_groups = list(set(existing_groups + default_groups))
        group_combo.addItems(all_groups)
        group_combo.setCurrentText(reg_config.plot_group)
        group_combo.currentTextChanged.connect(self.on_widget_changed)
        self.table.setCellWidget(row, 6, group_combo)
        
        # Кнопка цвета
        color_btn = QPushButton()
        color_btn.setStyleSheet(f"background-color: {self.color_to_hex(reg_config.color)}; min-width: 30px;")
        color_btn.clicked.connect(lambda: self.change_color(row))
        self.table.setCellWidget(row, 7, color_btn)
        
        # Разблокируем сигналы
        self.table.blockSignals(False)
    
    def color_to_hex(self, color):
        """Конвертирует цвет в hex формат"""
        if isinstance(color, str):
            color_map = {
                'r': '#FF0000', 'g': '#00FF00', 'b': '#0000FF',
                'c': '#00FFFF', 'm': '#FF00FF', 'y': '#FFFF00',
                'w': '#FFFFFF', 'k': '#000000'
            }
            return color_map.get(color, '#FF0000')
        elif isinstance(color, tuple) and len(color) == 3:
            return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
        return '#FF0000'
    
    def change_color(self, row: int):
        """Изменяет цвет регистра"""
        if row >= len(self.registers):
            return
        
        #colors = ['r', 'g', 'b', 'c', 'm', 'y', (255, 165, 0), (255, 20, 147), (50, 205, 50)]
        #current_color = self.registers[row].color
        
        #try:
        #    current_idx = colors.index(current_color)
        #except ValueError:
        #    current_idx = 0
        
        #new_idx = (current_idx + 1) % len(colors)
        #new_color = colors[new_idx]

        new_color = self.generate_unique_color()
        
        self.registers[row].color = new_color
        
        # Обновляем кнопку цвета
        color_btn = self.table.cellWidget(row, 7)
        if color_btn:
            color_btn.setStyleSheet(f"background-color: {self.color_to_hex(new_color)}; min-width: 30px;")
        
        self.registers_changed.emit()
    
    def on_table_changed(self):
        """Обработчик изменения элементов таблицы"""
        self.update_registers_from_table()
        self.registers_changed.emit()
    
    def on_widget_changed(self):
        """Обработчик изменения виджетов в таблице"""
        self.update_registers_from_table()
        self.registers_changed.emit()
    
    def update_registers_from_table(self):
        """Обновляет список регистров из данных таблицы"""
        updated_registers = []
        
        for row in range(self.table.rowCount()):
            try:
                # Получаем виджеты
                checkbox = self.table.cellWidget(row, 0)
                name_item = self.table.item(row, 1)
                slave_spin = self.table.cellWidget(row, 2)
                addr_spin = self.table.cellWidget(row, 3)
                count_spin = self.table.cellWidget(row, 4)
                type_combo = self.table.cellWidget(row, 5)
                group_combo = self.table.cellWidget(row, 6)
                
                # Проверяем существование всех элементов
                if not all([checkbox, name_item, slave_spin, addr_spin, count_spin, type_combo, group_combo]):
                    continue
                
                # Получаем или создаем конфигурацию регистра
                if row < len(self.registers):
                    reg = self.registers[row]
                else:
                    reg = RegisterConfig()
                
                # Обновляем параметры
                reg.enabled = checkbox.isChecked()
                reg.name = name_item.text() or f"Register_{row+1}"
                reg.slave_id = slave_spin.value()
                reg.address = addr_spin.value()
                reg.count = count_spin.value()
                reg.reg_type = type_combo.currentText()
                reg.plot_group = group_combo.currentText()
                
                updated_registers.append(reg)
                
            except Exception as e:
                print(f"Ошибка обновления строки {row}: {e}")
                continue
        
        self.registers = updated_registers
    
    def get_all_registers(self) -> List[RegisterConfig]:
        """Возвращает все регистры"""
        self.update_registers_from_table()
        return self.registers.copy()
    
    def get_enabled_registers(self) -> List[RegisterConfig]:
        """Возвращает только включенные регистры"""
        self.update_registers_from_table()
        return [reg for reg in self.registers if reg.enabled]
    
    def get_plot_mode(self) -> str:
        """Возвращает режим отображения графиков"""
        return self.plot_mode
    
    def get_plot_groups(self) -> dict:
        """Возвращает словарь групп с регистрами"""
        groups = {}
        for reg in self.get_enabled_registers():
            if reg.plot_group not in groups:
                groups[reg.plot_group] = []
            groups[reg.plot_group].append(reg)
        return groups
    
    def save_config(self):
        """Сохраняет конфигурацию в файл"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить конфигурацию регистров",
            "registers_config.ini",
            "INI файлы (*.ini);;Все файлы (*)"
        )
        
        if filename:
            self.update_registers_from_table()
            success = ConfigFileManager.save_registers_config(filename, self.registers, self.plot_mode)
            
            if success:
                QMessageBox.information(
                    self, "Успех",
                    f"Конфигурация регистров сохранена в файл:\n{filename}"
                )
            else:
                QMessageBox.critical(
                    self, "Ошибка",
                    "Не удалось сохранить конфигурацию регистров"
                )
    
    def load_config(self):
        """Загружает конфигурацию из файла"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Загрузить конфигурацию регистров",
            "",
            "INI файлы (*.ini);;Все файлы (*)"
        )
        
        if filename:
            registers, plot_mode = ConfigFileManager.load_registers_config(filename)
            
            if registers is not None:
                # Очищаем текущую конфигурацию
                self.registers.clear()
                self.table.setRowCount(0)
                
                # Загружаем новую конфигурацию
                self.registers = registers
                self.plot_mode = plot_mode or "separate"
                
                # Обновляем режим отображения
                if self.plot_mode == "separate":
                    self.separate_radio.setChecked(True)
                    self.grouped_radio.setChecked(False)
                else:
                    self.separate_radio.setChecked(False)
                    self.grouped_radio.setChecked(True)
                
                # Заполняем таблицу
                for reg in self.registers:
                    self.add_table_row(reg)
                
                self.registers_changed.emit()
                
                QMessageBox.information(
                    self, "Успех",
                    f"Конфигурация регистров загружена из файла:\n{filename}"
                )
            else:
                QMessageBox.critical(
                    self, "Ошибка",
                    "Не удалось загрузить конфигурацию регистров"
                )