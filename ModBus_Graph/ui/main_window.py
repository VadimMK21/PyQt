"""
Главное окно приложения Modbus Logger
"""
# Импорт системного модуля для работы с аргументами командной строки
import sys
# Импорт класса для работы с датой и временем
from datetime import datetime
# Импорт типа Optional для указания необязательных параметров
from typing import Optional

# Импорт основных виджетов PyQt5 для создания оконного приложения
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                             QPushButton, QLabel, QTextEdit, QSplitter, QFrame,
                             QMessageBox, QApplication)
# Импорт таймера и константы выравнивания из PyQt5
from PyQt5.QtCore import QTimer, Qt
# Импорт класса шрифта из PyQt5
from PyQt5.QtGui import QFont

# Импорт собственных модулей приложения
from data.logger import DataLogger  # Логгер для записи данных
from data.modbus_client import ModbusClientManager, ConnectionConfig  # Менеджер Modbus подключений
from ui.connection_widget import ConnectionWidget  # Виджет настройки подключения
from ui.register_widget import RegisterWidget  # Виджет настройки регистров
from ui.plot_widget import PlotManager  # Менеджер графиков
from ui.write_window import WriteRegistersWindow  # Окно записи в регистры
from utils.file_operations import ConfigFileManager  # Менеджер файловых операций


class MainWindow(QMainWindow):
    """Главное окно приложения - основной класс, управляющий всем приложением"""
    
    def __init__(self):
        # Вызываем конструктор родительского класса QMainWindow
        super().__init__()
        # Устанавливаем заголовок окна
        self.setWindowTitle("Multi-Register Modbus Real-Time Logger v2.0")
        # Устанавливаем размер и положение окна (x, y, ширина, высота)
        self.setGeometry(100, 100, 1400, 900)
        
        # Основные компоненты приложения
        # Менеджер для управления Modbus подключениями
        self.modbus_manager = ModbusClientManager()
        # Логгер для записи данных в файлы и управления регистрами
        self.logger = DataLogger()
        # Менеджер графиков для отображения данных в реальном времени
        self.plot_manager = PlotManager()
        
        # Таймер для периодического чтения данных с устройств
        self.read_timer = QTimer()
        # Подключаем сигнал таймера к методу чтения данных
        self.read_timer.timeout.connect(self.read_all_data)
        
        # UI компоненты (инициализируются как None, создаются позже)
        self.connection_widget: Optional[ConnectionWidget] = None  # Виджет настройки подключения
        self.register_widget: Optional[RegisterWidget] = None  # Виджет настройки регистров
        self.write_window: Optional[WriteRegistersWindow] = None  # Окно записи регистров
        
        # Состояние приложения
        self.is_logging = False  # Флаг активности логирования
        self.is_connected = False  # Флаг состояния подключения к Modbus
        
        # Вызываем методы инициализации
        self.setup_ui()  # Настройка пользовательского интерфейса
        self.setup_connections()  # Настройка сигналов и слотов
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса - создание всех элементов окна"""
        # Создаем центральный виджет (главный виджет окна)
        central_widget = QWidget()
        # Устанавливаем его как центральный виджет главного окна
        self.setCentralWidget(central_widget)
        
        # Основной splitter для разделения окна на две части
        main_splitter = QSplitter(Qt.Horizontal)  # Горизонтальное разделение
        # Создаем макет для центрального виджета
        central_widget_layout = QVBoxLayout(central_widget)
        # Добавляем splitter в макет
        central_widget_layout.addWidget(main_splitter)
        
        # Левая панель настроек
        left_widget = self.create_left_panel()  # Создаем левую панель
        left_widget.setMaximumWidth(450)  # Ограничиваем максимальную ширину
        
        # Правая панель с графиками
        right_widget = self.create_right_panel()  # Создаем правую панель
        
        # Добавляем панели в splitter
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(right_widget)
        # Устанавливаем начальные размеры частей splitter'а
        main_splitter.setSizes([450, 950])  # Левая - 450px, правая - 950px
    
    def create_left_panel(self) -> QWidget:
        """Создает левую панель с настройками подключения и регистров"""
        # Создаем виджет для левой панели
        left_widget = QWidget()
        # Создаем вертикальный макет для элементов левой панели
        left_layout = QVBoxLayout(left_widget)
        
        # Виджет подключения для настройки параметров связи с Modbus устройством
        self.connection_widget = ConnectionWidget()
        
        # Виджет конфигурации регистров для настройки списка отслеживаемых регистров
        self.register_widget = RegisterWidget()
        
        # Кнопки управления приложением
        # Создаем горизонтальный макет для кнопок
        control_layout = QHBoxLayout()
        
        # Кнопка подключения/отключения к Modbus устройству
        self.connect_btn = QPushButton("Подключить")
        # Подключаем обработчик нажатия к методу переключения подключения
        self.connect_btn.clicked.connect(self.toggle_connection)
        
        # Кнопка начала/остановки логирования данных
        self.start_btn = QPushButton("Начать логирование")
        # Подключаем обработчик к методу переключения логирования
        self.start_btn.clicked.connect(self.toggle_logging)
        # По умолчанию кнопка неактивна (активируется только после подключения)
        self.start_btn.setEnabled(False)
        
        # Кнопка очистки всех графиков
        self.clear_btn = QPushButton("Очистить графики")
        # Подключаем обработчик к методу очистки графиков
        self.clear_btn.clicked.connect(self.clear_plots)
        
        # Добавляем кнопки управления в горизонтальный макет
        control_layout.addWidget(self.connect_btn)
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.clear_btn)
        
        # Кнопка открытия окна записи в регистры
        self.write_btn = QPushButton("Открыть окно записи")
        # Подключаем обработчик к методу открытия окна записи
        self.write_btn.clicked.connect(self.open_write_window)
        
        # Поле для отображения статуса работы приложения
        self.status_text = QTextEdit()
        # Ограничиваем высоту поля статуса
        self.status_text.setMaximumHeight(150)
        # Делаем поле только для чтения
        self.status_text.setReadOnly(True)
        # Устанавливаем моноширинный шрифт для лучшего отображения логов
        self.status_text.setFont(QFont("Consolas", 9))
        
        # Сборка левой панели - добавляем все элементы в вертикальный макет
        left_layout.addWidget(self.connection_widget)  # Виджет настройки подключения
        left_layout.addWidget(self.register_widget)  # Виджет настройки регистров
        left_layout.addLayout(control_layout)  # Кнопки управления
        left_layout.addWidget(self.write_btn)  # Кнопка окна записи
        left_layout.addWidget(QLabel("Статус:"))  # Заголовок для поля статуса
        left_layout.addWidget(self.status_text)  # Поле статуса
        
        # Возвращаем готовый виджет левой панели
        return left_widget
    
    def create_right_panel(self) -> QWidget:
        """Создает правую панель с графиками и информационной панелью"""
        # Создаем виджет для правой панели
        right_widget = QWidget()
        # Создаем вертикальный макет для правой панели
        right_layout = QVBoxLayout(right_widget)
        
        # Получаем главный виджет менеджера графиков
        plot_widget = self.plot_manager.get_main_widget()
        
        # Информационная панель снизу для отображения статистики
        # Создаем рамку для визуального выделения информационной панели
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.StyledPanel)  # Стиль рамки
        # Создаем горизонтальный макет для элементов информационной панели
        info_layout = QHBoxLayout(info_frame)
        
        # Метки для отображения текущей информации о состоянии
        # Метка количества активных регистров
        self.connected_registers_label = QLabel("Активных регистров: 0")
        # Метка общего количества собранных точек данных
        self.total_points_label = QLabel("Всего точек: 0")
        # Метка статуса подключения
        self.connection_status_label = QLabel("Статус: Не подключен")
        
        # Размещаем метки в горизонтальном макете
        info_layout.addWidget(self.connected_registers_label)
        info_layout.addWidget(self.connection_status_label)
        # Добавляем растягивающийся элемент для разделения меток
        info_layout.addStretch()
        info_layout.addWidget(self.total_points_label)
        
        # Добавляем элементы в макет правой панели
        right_layout.addWidget(plot_widget)  # Область с графиками (основная часть)
        right_layout.addWidget(info_frame)  # Информационная панель (внизу)
        
        # Возвращаем готовый виджет правой панели
        return right_widget
    
    def setup_connections(self):
        """Настройка сигналов и слотов - связывание событий с обработчиками"""
        # Подключаем сигналы логгера для автоматического обновления интерфейса
        # При получении новых данных обновляем соответствующий график
        self.logger.data_received.connect(self.plot_manager.update_plot)
        # При получении новых данных обновляем статистику
        self.logger.data_received.connect(self.update_statistics)
        
        # Подключаем сигнал изменения конфигурации регистров к обработчику
        self.register_widget.registers_changed.connect(self.on_registers_changed)
    
    def toggle_connection(self):
        """Переключает состояние подключения к Modbus устройству"""
        # Если не подключены, пытаемся подключиться
        if not self.is_connected:
            # Добавляем сообщение в статус о попытке подключения
            self.add_status("Попытка подключения...")
            
            # Получаем конфигурацию подключения из виджета настроек
            config = self.connection_widget.get_connection_config()
            
            # Пытаемся установить подключение через менеджер Modbus
            if self.modbus_manager.connect(config):
                # Если подключение успешно, передаем клиента в логгер
                self.logger.set_client(self.modbus_manager.get_client())
                # Обновляем флаг состояния подключения
                self.is_connected = True
                
                # Обновляем интерфейс для состояния "подключено"
                self.connect_btn.setText("Отключить")  # Меняем текст кнопки
                self.start_btn.setEnabled(True)  # Активируем кнопку логирования
                # Обновляем метку статуса подключения
                self.connection_status_label.setText(f"Статус: Подключен ({config})")
                # Добавляем сообщение об успешном подключении в статус
                self.add_status(f"Подключение установлено: {config}")
            else:
                # Если подключение не удалось
                self.add_status("Ошибка подключения")
                # Показываем диалог с ошибкой
                QMessageBox.critical(self, "Ошибка", "Не удалось установить подключение к Modbus устройству")
        else:
            # Если уже подключены, отключаемся
            self.disconnect_modbus()
    
    def disconnect_modbus(self):
        """Отключается от Modbus устройства и обновляет интерфейс"""
        # Если логирование активно, сначала останавливаем его
        if self.is_logging:
            self.toggle_logging()
        
        # Отключаемся от Modbus устройства
        self.modbus_manager.disconnect()
        # Убираем клиента из логгера
        self.logger.set_client(None)
        # Обновляем флаг состояния
        self.is_connected = False
        
        # Обновляем интерфейс для состояния "отключено"
        self.connect_btn.setText("Подключить")  # Возвращаем исходный текст кнопки
        self.start_btn.setEnabled(False)  # Деактивируем кнопку логирования
        # Обновляем метку статуса
        self.connection_status_label.setText("Статус: Не подключен")
        # Добавляем сообщение об отключении в статус
        self.add_status("Отключено от Modbus устройства")
    
    def toggle_logging(self):
        """Переключает состояние логирования данных"""
        # Если логирование не активно, запускаем его
        if not self.is_logging:
            # Проверяем наличие активных регистров для логирования
            if not self.register_widget.get_enabled_registers():
                # Если нет активных регистров, показываем предупреждение
                QMessageBox.warning(self, "Предупреждение", "Нет активных регистров для логирования")
                return  # Выходим без запуска логирования
            
            # Создаем имя файла с текущей датой и временем
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"modbus_multi_data_{timestamp}.csv"
            
            # Пытаемся запустить логирование с созданным именем файла
            if self.logger.start_logging(csv_filename):
                # Получаем интервал чтения из настроек подключения
                interval = self.connection_widget.get_read_interval()
                # Запускаем таймер с заданным интервалом
                self.read_timer.start(interval)
                
                # Обновляем состояние и интерфейс
                self.is_logging = True
                self.start_btn.setText("Остановить логирование")
                # Добавляем сообщение о начале логирования
                self.add_status(f"Логирование начато. Файл: {csv_filename}, интервал: {interval}мс")
            else:
                # Если не удалось запустить логирование, показываем ошибку
                QMessageBox.critical(self, "Ошибка", "Не удалось начать логирование")
        else:
            # Если логирование активно, останавливаем его
            self.read_timer.stop()  # Останавливаем таймер чтения
            self.logger.stop_logging()  # Останавливаем логгер
            
            # Обновляем состояние и интерфейс
            self.is_logging = False
            self.start_btn.setText("Начать логирование")
            # Добавляем сообщение об остановке логирования
            self.add_status("Логирование остановлено")
    
    def read_all_data(self):
        """Читает данные со всех активных регистров (вызывается по таймеру)"""
        # Делегируем чтение данных логгеру
        self.logger.read_all_registers()
    
    def clear_plots(self):
        """Очищает все графики и накопленные данные"""
        # Очищаем все данные в логгере
        self.logger.clear_all_data()
        # Очищаем все графики в менеджере графиков
        self.plot_manager.clear_all_plots()
        # Сбрасываем счетчик точек данных
        self.total_points_label.setText("Всего точек: 0")
        # Добавляем сообщение об очистке в статус
        self.add_status("Графики очищены")
    
    def on_registers_changed(self):
        """Обработчик изменения конфигурации регистров"""
        # Получаем обновленный список всех регистров
        registers = self.register_widget.get_all_registers()
        # Обновляем регистры в логгере (заменяем весь словарь регистров)
        self.logger.register_manager._registers = {reg.name: reg for reg in registers}
        
        # Получаем только активные (включенные) регистры и режим отображения
        enabled_registers = self.register_widget.get_enabled_registers()
        plot_mode = self.register_widget.get_plot_mode()
        # Пересоздаем графики с новой конфигурацией
        self.plot_manager.create_plots(enabled_registers, plot_mode)
        
        # Обновляем информационную панель с количеством активных регистров
        self.connected_registers_label.setText(f"Активных регистров: {len(enabled_registers)}")
    
    def update_statistics(self, register_name: str, value: float, timestamp: str):
        """Обновляет статистику приложения при получении новых данных"""
        # Получаем общее количество точек данных от менеджера регистров
        total_points = self.logger.register_manager.get_total_data_points()
        # Обновляем метку с общим количеством точек
        self.total_points_label.setText(f"Всего точек: {total_points}")
    
    def open_write_window(self):
        """Открывает окно записи данных в регистры Modbus устройства"""
        # Создаем окно записи только если оно еще не создано
        if not self.write_window:
            self.write_window = WriteRegistersWindow(self.logger, self)
        
        # Показываем окно и выводим его на передний план
        self.write_window.show()
        self.write_window.raise_()  # Поднимаем окно над другими
        self.write_window.activateWindow()  # Активируем окно (фокус)
    
    def add_status(self, message: str):
        """Добавляет сообщение с временной меткой в поле статуса"""
        # Получаем текущее время в формате часы:минуты:секунды
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Добавляем сообщение с временной меткой в текстовое поле
        self.status_text.append(f"[{timestamp}] {message}")
        
        # Автоматически прокручиваем к последнему сообщению
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())  # Устанавливаем максимальную позицию скролла
    
    def closeEvent(self, event):
        """Обработчик закрытия окна приложения"""
        # Если логирование активно, спрашиваем подтверждение у пользователя
        if self.is_logging:
            reply = QMessageBox.question(
                self, 'Закрытие приложения',
                'Логирование активно. Вы уверены, что хотите закрыть приложение?',
                QMessageBox.Yes | QMessageBox.No,  # Кнопки диалога
                QMessageBox.No  # Кнопка по умолчанию
            )
            
            # Если пользователь подтвердил закрытие
            if reply == QMessageBox.Yes:
                self.toggle_logging()  # Останавливаем логирование
                self.disconnect_modbus()  # Отключаемся от устройства
                event.accept()  # Разрешаем закрытие окна
            else:
                event.ignore()  # Отменяем закрытие окна
        else:
            # Если логирование не активно, просто отключаемся и закрываемся
            self.disconnect_modbus()
            event.accept()


def main():
    """Точка входа в приложение - функция запуска программы"""
    # Создаем объект приложения PyQt
    app = QApplication(sys.argv)
    
    # Настройка стиля приложения для лучшего внешнего вида
    app.setStyle('Fusion')  # Современный стиль интерфейса
    
    # Создание и отображение главного окна
    window = MainWindow()  # Создаем экземпляр главного окна
    window.show()  # Показываем окно на экране
    
    # Запуск главного цикла приложения
    # Программа будет работать до закрытия всех окон
    sys.exit(app.exec_())