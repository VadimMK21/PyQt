"""
Главное окно приложения Modbus Logger
"""
import sys
from datetime import datetime
from typing import Optional

from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                             QPushButton, QLabel, QTextEdit, QSplitter, QFrame,
                             QMessageBox, QApplication)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont

from data.logger import DataLogger
from data.modbus_client import ModbusClientManager, ConnectionConfig
from ui.connection_widget import ConnectionWidget
from ui.register_widget import RegisterWidget
from ui.main_window import PlotManager
from ui.write_window import WriteRegistersWindow
from utils.file_operations import ConfigFileManager


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Register Modbus Real-Time Logger v2.0")
        self.setGeometry(100, 100, 1400, 900)
        
        # Основные компоненты
        self.modbus_manager = ModbusClientManager()
        self.logger = DataLogger()
        self.plot_manager = PlotManager()
        
        # Таймер для чтения данных
        self.read_timer = QTimer()
        self.read_timer.timeout.connect(self.read_all_data)
        
        # UI компоненты
        self.connection_widget: Optional[ConnectionWidget] = None
        self.register_widget: Optional[RegisterWidget] = None
        self.write_window: Optional[WriteRegistersWindow] = None
        
        # Состояние
        self.is_logging = False
        self.is_connected = False
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной splitter
        main_splitter = QSplitter(Qt.Horizontal)
        central_widget_layout = QVBoxLayout(central_widget)
        central_widget_layout.addWidget(main_splitter)
        
        # Левая панель настроек
        left_widget = self.create_left_panel()
        left_widget.setMaximumWidth(450)
        
        # Правая панель с графиками
        right_widget = self.create_right_panel()
        
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([450, 950])
    
    def create_left_panel(self) -> QWidget:
        """Создает левую панель с настройками"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Виджет подключения
        self.connection_widget = ConnectionWidget()
        
        # Виджет конфигурации регистров
        self.register_widget = RegisterWidget()
        
        # Кнопки управления
        control_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("Подключить")
        self.connect_btn.clicked.connect(self.toggle_connection)
        
        self.start_btn = QPushButton("Начать логирование")
        self.start_btn.clicked.connect(self.toggle_logging)
        self.start_btn.setEnabled(False)
        
        self.clear_btn = QPushButton("Очистить графики")
        self.clear_btn.clicked.connect(self.clear_plots)
        
        control_layout.addWidget(self.connect_btn)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.clear_btn)
        
        # Кнопка окна записи
        self.write_btn = QPushButton("Открыть окно записи")
        self.write_btn.clicked.connect(self.open_write_window)
        
        # Статус
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(150)
        self.status_text.setReadOnly(True)
        self.status_text.setFont(QFont("Consolas", 9))
        
        # Сборка левой панели
        left_layout.addWidget(self.connection_widget)
        left_layout.addWidget(self.register_widget)
        left_layout.addLayout(control_layout)
        left_layout.addWidget(self.write_btn)
        left_layout.addWidget(QLabel("Статус:"))
        left_layout.addWidget(self.status_text)
        
        return left_widget
    
    def create_right_panel(self) -> QWidget:
        """Создает правую панель с графиками"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Менеджер графиков
        plot_widget = self.plot_manager.get_main_widget()
        
        # Информационная панель
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.StyledPanel)
        info_layout = QHBoxLayout(info_frame)
        
        self.connected_registers_label = QLabel("Активных регистров: 0")
        self.total_points_label = QLabel("Всего точек: 0")
        self.connection_status_label = QLabel("Статус: Не подключен")
        
        info_layout.addWidget(self.connected_registers_label)
        info_layout.addWidget(self.connection_status_label)
        info_layout.addStretch()
        info_layout.addWidget(self.total_points_label)
        
        right_layout.addWidget(plot_widget)
        right_layout.addWidget(info_frame)
        
        return right_widget
    
    def setup_connections(self):
        """Настройка сигналов и слотов"""
        # Подключаем сигналы логгера
        self.logger.data_received.connect(self.plot_manager.update_plot)
        self.logger.data_received.connect(self.update_statistics)
        
        # Подключаем сигналы изменения конфигурации регистров
        self.register_widget.registers_changed.connect(self.on_registers_changed)
    
    def toggle_connection(self):
        """Переключает состояние подключения"""
        if not self.is_connected:
            self.add_status("Попытка подключения...")
            
            # Получаем конфигурацию подключения
            config = self.connection_widget.get_connection_config()
            
            # Пытаемся подключиться
            if self.modbus_manager.connect(config):
                self.logger.set_client(self.modbus_manager.get_client())
                self.is_connected = True
                
                self.connect_btn.setText("Отключить")
                self.start_btn.setEnabled(True)
                self.connection_status_label.setText(f"Статус: Подключен ({config})")
                self.add_status(f"Подключение установлено: {config}")
            else:
                self.add_status("Ошибка подключения")
                QMessageBox.critical(self, "Ошибка", "Не удалось установить подключение к Modbus устройству")
        else:
            self.disconnect_modbus()
    
    def disconnect_modbus(self):
        """Отключается от Modbus устройства"""
        if self.is_logging:
            self.toggle_logging()
        
        self.modbus_manager.disconnect()
        self.logger.set_client(None)
        self.is_connected = False
        
        self.connect_btn.setText("Подключить")
        self.start_btn.setEnabled(False)
        self.connection_status_label.setText("Статус: Не подключен")
        self.add_status("Отключено от Modbus устройства")
    
    def toggle_logging(self):
        """Переключает состояние логирования"""
        if not self.is_logging:
            # Проверяем наличие активных регистров
            if not self.register_widget.get_enabled_registers():
                QMessageBox.warning(self, "Предупреждение", "Нет активных регистров для логирования")
                return
            
            # Начинаем логирование
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"modbus_multi_data_{timestamp}.csv"
            
            if self.logger.start_logging(csv_filename):
                interval = self.connection_widget.get_read_interval()
                self.read_timer.start(interval)
                
                self.is_logging = True
                self.start_btn.setText("Остановить логирование")
                self.add_status(f"Логирование начато. Файл: {csv_filename}, интервал: {interval}мс")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось начать логирование")
        else:
            # Останавливаем логирование
            self.read_timer.stop()
            self.logger.stop_logging()
            
            self.is_logging = False
            self.start_btn.setText("Начать логирование")
            self.add_status("Логирование остановлено")
    
    def read_all_data(self):
        """Читает данные со всех регистров"""
        self.logger.read_all_registers()
    
    def clear_plots(self):
        """Очищает все графики"""
        self.logger.clear_all_data()
        self.plot_manager.clear_all_plots()
        self.total_points_label.setText("Всего точек: 0")
        self.add_status("Графики очищены")
    
    def on_registers_changed(self):
        """Обработчик изменения конфигурации регистров"""
        # Обновляем регистры в логгере
        registers = self.register_widget.get_all_registers()
        self.logger.register_manager._registers = {reg.name: reg for reg in registers}
        
        # Обновляем графики
        enabled_registers = self.register_widget.get_enabled_registers()
        plot_mode = self.register_widget.get_plot_mode()
        self.plot_manager.create_plots(enabled_registers, plot_mode)
        
        # Обновляем информацию
        self.connected_registers_label.setText(f"Активных регистров: {len(enabled_registers)}")
    
    def update_statistics(self, register_name: str, value: float, timestamp: str):
        """Обновляет статистику"""
        total_points = self.logger.register_manager.get_total_data_points()
        self.total_points_label.setText(f"Всего точек: {total_points}")
    
    def open_write_window(self):
        """Открывает окно записи в регистры"""
        if not self.write_window:
            self.write_window = WriteRegistersWindow(self.logger, self)
        
        self.write_window.show()
        self.write_window.raise_()
        self.write_window.activateWindow()
    
    def add_status(self, message: str):
        """Добавляет сообщение в статус"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")
        
        # Прокручиваем к последнему сообщению
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        if self.is_logging:
            reply = QMessageBox.question(
                self, 'Закрытие приложения',
                'Логирование активно. Вы уверены, что хотите закрыть приложение?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.toggle_logging()
                self.disconnect_modbus()
                event.accept()
            else:
                event.ignore()
        else:
            self.disconnect_modbus()
            event.accept()


def main():
    """Точка входа в приложение"""
    app = QApplication(sys.argv)
    
    # Настройка стиля приложения
    app.setStyle('Fusion')
    
    # Создание и показ главного окна
    window = MainWindow()
    window.show()
    
    # Запуск приложения
    sys.exit(app.exec_())