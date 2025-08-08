 # Описание модуля ниже — многострочная строка документации для виджета
"""
Виджет для настройки подключения к Modbus устройству
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,  # Импорт основных виджетов и компоновщиков PyQt5
                             QGridLayout, QLabel, QComboBox, QLineEdit,  # Импорт дополнительных элементов интерфейса
                             QSpinBox, QPushButton, QFileDialog, QMessageBox)  # Импорт спинбоксов, кнопок и диалогов
from PyQt5.QtCore import pyqtSignal  # Импорт механизма сигналов PyQt

from data.modbus_client import ConnectionConfig, create_tcp_config, create_rtu_config  # Импорты типов/фабрик конфигураций подключения
from utils.file_operations import ConfigFileManager  # Менеджер сохранения/загрузки конфигурации в файл


class ConnectionWidget(QWidget):  # Класс виджета конфигурации подключения, наследуется от QWidget
    """Виджет настройки подключения"""  # Документация класса
    
    connection_changed = pyqtSignal()  # Сигнал, испускаемый при смене типа/параметров подключения
    
    def __init__(self, parent=None):  # Конструктор виджета, parent — родительский виджет
        super().__init__(parent)  # Инициализация базового класса QWidget
        self.setup_ui()  # Создание и размещение элементов интерфейса
        
    def setup_ui(self):  # Метод сборки интерфейса
        """Настройка интерфейса"""  # Описание метода
        layout = QVBoxLayout(self)  # Главный вертикальный компоновщик для виджета
        
        # Группа настроек подключения
        conn_group = QGroupBox("Настройки подключения Modbus")  # Группа UI для параметров Modbus
        conn_layout = QGridLayout(conn_group)  # Сеточный компоновщик внутри группы подключения
        
        # Тип подключения
        self.conn_type = QComboBox()  # Выпадающий список выбора типа подключения
        self.conn_type.addItems(["TCP", "RTU"])  # Добавляем варианты: TCP (сеть) и RTU (COM-порт)
        self.conn_type.currentTextChanged.connect(self.on_connection_type_changed)  # Реакция на смену типа
        
        # TCP настройки
        self.host_edit = QLineEdit("127.0.0.1")  # Поле ввода IP адреса/имени хоста или имени COM-порта
        self.port_spin = QSpinBox()  # Спинбокс для TCP-порта
        self.port_spin.setRange(1, 65535)  # Допустимый диапазон TCP-портов
        self.port_spin.setValue(502)  # Значение по умолчанию для Modbus TCP
        
        # RTU настройки
        self.baudrate_combo = QComboBox()  # Список скоростей порта для RTU
        self.baudrate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])  # Популярные скорости
        self.baudrate_combo.setCurrentText("38400")  # Значение по умолчанию
        
        self.parity_combo = QComboBox()  # Выбор чётности (parity)
        self.parity_combo.addItems(["N", "E", "O"])  # None, Even, Odd
        
        self.stopbits_combo = QComboBox()  # Выбор числа стоп-битов
        self.stopbits_combo.addItems(["1", "2"])  # Возможные значения стоп-битов
        
        self.bytesize_combo = QComboBox()  # Выбор размера байта данных
        self.bytesize_combo.addItems(["7", "8"])  # 7 или 8 бит данных
        self.bytesize_combo.setCurrentText("8")  # Значение по умолчанию
        
        # Размещение элементов
        conn_layout.addWidget(QLabel("Тип:"), 0, 0)  # Метка для поля выбора типа подключения
        conn_layout.addWidget(self.conn_type, 0, 1)  # Сам комбобокс типа подключения
        conn_layout.addWidget(QLabel("Хост/COM:"), 1, 0)  # Метка для ввода хоста или COM-порта
        conn_layout.addWidget(self.host_edit, 1, 1)  # Поле ввода хоста/COM
        conn_layout.addWidget(QLabel("Порт:"), 2, 0)  # Метка для TCP-порта
        conn_layout.addWidget(self.port_spin, 2, 1)  # Спинбокс порта TCP
        conn_layout.addWidget(QLabel("Скорость:"), 3, 0)  # Метка для скорости порта (RTU)
        conn_layout.addWidget(self.baudrate_combo, 3, 1)  # Комбобокс скоростей (RTU)
        conn_layout.addWidget(QLabel("Четность:"), 4, 0)  # Метка для чётности (RTU)
        conn_layout.addWidget(self.parity_combo, 4, 1)  # Комбобокс чётности (RTU)
        conn_layout.addWidget(QLabel("Стоп-биты:"), 5, 0)  # Метка для числа стоп-битов (RTU)
        conn_layout.addWidget(self.stopbits_combo, 5, 1)  # Комбобокс числа стоп-битов (RTU)
        conn_layout.addWidget(QLabel("Размер:"), 6, 0)  # Метка для размера байта (RTU)
        conn_layout.addWidget(self.bytesize_combo, 6, 1)  # Комбобокс размера байта (RTU)
        
        # Группа настроек чтения
        read_group = QGroupBox("Настройки чтения")  # Группа UI для параметров чтения данных
        read_layout = QGridLayout(read_group)  # Сеточный компоновщик для группы чтения
        
        # Должен отвечать за диапазон показываемых значений на графике
        self.interval_spin = QSpinBox()  # Частота опроса/обновления данных в мс
        self.interval_spin.setRange(20, 10000)  # Допустимый диапазон интервала чтения
        self.interval_spin.setValue(1000)  # Интервал по умолчанию (1 секунда)
        self.interval_spin.setSuffix(" мс")  # Отображаем суффикс единиц измерения
        
        self.timeout_spin = QSpinBox()  # Таймаут операций Modbus в мс
        self.timeout_spin.setRange(500, 5000)  # Допустимый диапазон таймаута
        self.timeout_spin.setValue(1000)  # Таймаут по умолчанию
        self.timeout_spin.setSuffix(" мс")  # Суффикс единиц
        
        read_layout.addWidget(QLabel("Интервал чтения:"), 0, 0)  # Метка для интервала чтения
        read_layout.addWidget(self.interval_spin, 0, 1)  # Поле установки интервала чтения
        read_layout.addWidget(QLabel("Таймаут:"), 1, 0)  # Метка для таймаута
        read_layout.addWidget(self.timeout_spin, 1, 1)  # Поле установки таймаута
        
        # Кнопки сохранения/загрузки конфигурации
        buttons_layout = QHBoxLayout()  # Горизонтальный компоновщик для кнопок
        
        self.save_config_btn = QPushButton("Сохранить настройки")  # Кнопка сохранения конфигурации в файл
        self.save_config_btn.clicked.connect(self.save_connection_config)  # Обработчик клика: сохранить
        
        self.load_config_btn = QPushButton("Загрузить настройки")  # Кнопка загрузки конфигурации из файла
        self.load_config_btn.clicked.connect(self.load_connection_config)  # Обработчик клика: загрузить
        
        buttons_layout.addWidget(self.save_config_btn)  # Добавляем кнопку «Сохранить» на панель
        buttons_layout.addWidget(self.load_config_btn)  # Добавляем кнопку «Загрузить» на панель
        
        # Сборка виджета
        layout.addWidget(conn_group)  # Добавляем группу подключения в основной лейаут
        layout.addWidget(read_group)  # Добавляем группу чтения в основной лейаут
        layout.addLayout(buttons_layout)  # Добавляем панель кнопок
        
        # Инициализация состояния
        self.on_connection_type_changed("TCP")  # Устанавливаем начальное состояние как TCP
    
    def on_connection_type_changed(self, conn_type: str):  # Слот: вызывается при смене типа подключения
        """Обработчик изменения типа подключения"""  # Докстринг обработчика
        is_tcp = conn_type == "TCP"  # Флаг: выбран ли режим TCP
        
        # Включаем/выключаем соответствующие поля
        self.port_spin.setEnabled(is_tcp)  # Порт TCP активен только для TCP
        self.baudrate_combo.setEnabled(not is_tcp)  # Скорость — только для RTU
        self.parity_combo.setEnabled(not is_tcp)  # Чётность — только для RTU
        self.stopbits_combo.setEnabled(not is_tcp)  # Стоп-биты — только для RTU
        self.bytesize_combo.setEnabled(not is_tcp)  # Размер байта — только для RTU
        
        # Меняем подсказку для поля хост/com
        if is_tcp:  # Если TCP, готовим поле как IP/хост
            self.host_edit.setText("127.0.0.1")  # Значение по умолчанию для TCP
        else:  # Если RTU, готовим поле как имя COM-порта
            self.host_edit.setText("COM1")  # Значение по умолчанию для RTU
        
        self.connection_changed.emit()  # Излучаем сигнал о смене настроек
    
    def get_connection_config(self) -> ConnectionConfig:  # Получить объект конфигурации подключения
        """Возвращает текущую конфигурацию подключения"""  # Докстринг метода
        if self.conn_type.currentText() == "TCP":  # Если выбран TCP
            return create_tcp_config(  # Создаём конфигурацию TCP
                host=self.host_edit.text(),  # IP/хост
                port=self.port_spin.value(),  # TCP-порт
                timeout=self.timeout_spin.value() / 1000.0  # Конвертируем таймаут из мс в секунды
            )
        else:  # Иначе RTU
            return create_rtu_config(  # Создаём конфигурацию RTU
                port=self.host_edit.text(),  # Имя COM-порта
                baudrate=int(self.baudrate_combo.currentText()),  # Скорость порта
                parity=self.parity_combo.currentText(),  # Чётность
                stopbits=int(self.stopbits_combo.currentText()),  # Стоп-биты
                bytesize=int(self.bytesize_combo.currentText()),  # Размер байта
                timeout=self.timeout_spin.value() / 1000.0  # Конвертируем таймаут из мс в секунды
            )
    
    def set_connection_config(self, config: ConnectionConfig):  # Применить конфигурацию подключения к UI
        """Устанавливает конфигурацию подключения"""  # Докстринг метода
        # Устанавливаем тип подключения
        self.conn_type.setCurrentText(config.connection_type)  # Применяем тип: TCP или RTU
        
        # Общие настройки
        self.host_edit.setText(config.host)  # Применяем хост/порт
        self.timeout_spin.setValue(int(config.timeout * 1000))  # Применяем таймаут (в мс)
        
        if config.connection_type == "TCP":  # Специфические настройки TCP
            self.port_spin.setValue(config.port)  # Применяем TCP-порт
        else:  # Специфические настройки RTU
            self.baudrate_combo.setCurrentText(str(config.baudrate))  # Применяем скорость
            self.parity_combo.setCurrentText(config.parity)  # Применяем чётность
            self.stopbits_combo.setCurrentText(str(config.stopbits))  # Применяем стоп-биты
            self.bytesize_combo.setCurrentText(str(config.bytesize))  # Применяем размер байта
    
    def get_read_interval(self) -> int:  # Получить интервал чтения (мс)
        """Возвращает интервал чтения в миллисекундах"""  # Должен отвечать за диапазон показываемых значений на графике
        return self.interval_spin.value()  # Текущее значение спинбокса интервала
    
    def set_read_interval(self, interval: int):  # Задать интервал чтения (мс)
        """Устанавливает интервал чтения"""  # Докстринг
        self.interval_spin.setValue(interval)  # Установка значения в спинбокс
    
    def save_connection_config(self):  # Сохранить текущие настройки подключения в INI-файл
        """Сохраняет конфигурацию подключения в файл"""  # Докстринг
        filename, _ = QFileDialog.getSaveFileName(  # Диалог сохранения файла
            self,  # Родительский виджет
            "Сохранить настройки подключения",  # Заголовок диалога
            "connection_config.ini",  # Имя файла по умолчанию
            "INI файлы (*.ini);;Все файлы (*)"  # Фильтр типов файлов
        )
        
        if filename:  # Если пользователь выбрал путь
            success = ConfigFileManager.save_connection_config(  # Пишем файл конфигурации
                filename,  # Путь к файлу
                self.conn_type.currentText(),  # Тип подключения
                self.host_edit.text(),  # Хост/COM
                self.port_spin.value(),  # Порт TCP
                int(self.baudrate_combo.currentText()),  # Скорость RTU
                self.parity_combo.currentText(),  # Чётность RTU
                int(self.stopbits_combo.currentText()),  # Стоп-биты RTU
                int(self.bytesize_combo.currentText())  # Размер байта RTU
            )
            
            if success:  # Успех записи файла
                QMessageBox.information(  # Показываем информационное сообщение
                    self, "Успех",  # Заголовок
                    f"Настройки подключения сохранены в файл:\n{filename}"  # Текст
                )
            else:  # Ошибка записи файла
                QMessageBox.critical(  # Показываем сообщение об ошибке
                    self, "Ошибка",  # Заголовок
                    "Не удалось сохранить настройки подключения"  # Текст
                )
    
    def load_connection_config(self):  # Загрузить настройки подключения из INI-файла
        """Загружает конфигурацию подключения из файла"""  # Докстринг
        filename, _ = QFileDialog.getOpenFileName(  # Диалог открытия файла
            self,  # Родительский виджет
            "Загрузить настройки подключения",  # Заголовок диалога
            "",  # Стартовая директория
            "INI файлы (*.ini);;Все файлы (*)"  # Фильтр типов файлов
        )
        
        if filename:  # Если файл выбран
            config_data = ConfigFileManager.load_connection_config(filename)  # Читаем конфиг из файла
            
            if config_data:  # Если данные успешно загружены
                # Применяем загруженные настройки
                self.conn_type.setCurrentText(config_data['type'])  # Тип подключения
                self.host_edit.setText(config_data['host'])  # Хост/COM
                self.port_spin.setValue(config_data['port'])  # TCP-порт
                self.baudrate_combo.setCurrentText(str(config_data['baudrate']))  # Скорость RTU
                self.parity_combo.setCurrentText(config_data['parity'])  # Чётность RTU
                self.stopbits_combo.setCurrentText(str(config_data['stopbits']))  # Стоп-биты RTU
                self.bytesize_combo.setCurrentText(str(config_data['bytesize']))  # Размер байта RTU
                
                QMessageBox.information(  # Сообщение об успешной загрузке
                    self, "Успех",  # Заголовок
                    f"Настройки подключения загружены из файла:\n{filename}"  # Текст
                )
            else:  # Ошибка чтения/формата
                QMessageBox.critical(  # Сообщение об ошибке
                    self, "Ошибка",  # Заголовок
                    "Не удалось загрузить настройки подключения"  # Текст
                )
    
    def validate_settings(self) -> tuple[bool, str]:  # Проверка корректности введённых настроек
        """Проверяет корректность настроек"""  # Докстринг
        if self.conn_type.currentText() == "TCP":  # Для TCP проверяем IP
            host = self.host_edit.text().strip()  # Получаем хост без пробелов
            if not host:  # Пустое значение — ошибка
                return False, "Не указан IP адрес"  # Возвращаем статус и сообщение
            
            # Простая проверка IP адреса
            if not self._is_valid_ip(host):  # Валидация формата IPv4
                return False, "Некорректный IP адрес"  # Ошибка формата IP
        else:  # Для RTU проверяем имя COM-порта
            port = self.host_edit.text().strip()  # Получаем имя порта
            if not port:  # Пустое значение — ошибка
                return False, "Не указан COM порт"  # Статус и сообщение
            
            # Простая проверка COM порта
            if not port.upper().startswith('COM'):  # Имя должно начинаться с COM
                return False, "COM порт должен начинаться с 'COM'"  # Сообщение об ошибке
        
        return True, "Настройки корректны"  # Успешная проверка
    
    def _is_valid_ip(self, ip: str) -> bool:  # Примитивная проверка IPv4 адреса
        """Простая проверка IP адреса"""  # Докстринг
        try:  # Обрабатываем возможные ошибки преобразования типов
            parts = ip.split('.')  # Делим IP по точкам
            if len(parts) != 4:  # Должно быть ровно 4 октета
                return False  # Неверный формат
            
            for part in parts:  # Проверяем каждый октет
                num = int(part)  # Преобразуем в число
                if num < 0 or num > 255:  # Диапазон октета 0..255
                    return False  # Неверное значение
            
            return True  # Формат корректный
        except:  # Любая ошибка парсинга
            return False  # IP некорректен
    
    def get_settings_summary(self) -> str:  # Краткая строка-резюме текущих настроек
        """Возвращает краткое описание текущих настроек"""  # Докстринг
        if self.conn_type.currentText() == "TCP":  # Для TCP форматим «IP:порт»
            return f"TCP {self.host_edit.text()}:{self.port_spin.value()}"  # Возвращаем строку TCP
        else:  # Для RTU форматим «COM скорость чётность-стопбиты-размер»
            return (f"RTU {self.host_edit.text()} "  # Имя порта
                   f"{self.baudrate_combo.currentText()}bps "  # Скорость
                   f"{self.parity_combo.currentText()}-"  # Чётность
                   f"{self.stopbits_combo.currentText()}-"  # Стоп-биты
                   f"{self.bytesize_combo.currentText()}")  # Размер байта