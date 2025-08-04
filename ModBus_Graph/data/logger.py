"""
Модуль для логирования данных Modbus
Содержит классы для чтения/записи Modbus регистров и сохранения данных в CSV
"""

# Импорт стандартных библиотек для работы с CSV файлами
import csv
# Импорт модуля времени для создания задержек и временных меток
import time
# Импорт модуля для работы с датой и временем
from datetime import datetime
# Импорт типов для аннотации типов (улучшение читаемости кода)
from typing import Optional, Dict, Any

# Импорт базового класса для Qt объектов и сигналов для межпоточного взаимодействия
from PyQt5.QtCore import QObject, pyqtSignal
# Импорт клиентов Modbus для TCP и Serial подключений
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
# Импорт миксина с дополнительными методами для работы с типами данных
from pymodbus.client.mixin import ModbusClientMixin

# Импорт конфигурационных классов для работы с регистрами
from config.register_config import RegisterConfig, WriteRegisterConfig, RegisterManager


class ModbusReader:
    """Класс для чтения данных из Modbus регистров"""
    
    def __init__(self, client):
        # Сохраняем ссылку на Modbus клиент для выполнения запросов
        self.client = client
    
    def read_register(self, reg_config: RegisterConfig) -> Optional[float]:
        """Читает значение из регистра согласно его конфигурации"""
        # Проверяем наличие клиента и что регистр включен для чтения
        if not self.client or not reg_config.enabled:
            return None  # Возвращаем None если условия не выполнены
        
        try:
            # Блок обработки различных типов регистров
            # Определяем тип данных и функцию чтения в зависимости от типа регистра
            
            if reg_config.reg_type == "H_Float":
                # Устанавливаем тип данных как 32-битное число с плавающей точкой
                data_type = ModbusClientMixin.DATATYPE.FLOAT32
                # Читаем Holding регистры (регистры хранения) для float значений
                result = self.client.read_holding_registers(
                    reg_config.address,      # Адрес начального регистра
                    count=reg_config.count,  # Количество регистров для чтения
                    device_id=reg_config.slave_id  # ID устройства в сети Modbus
                )
            elif reg_config.reg_type == "H_Int":
                # Устанавливаем тип данных как 32-битное целое число
                data_type = ModbusClientMixin.DATATYPE.INT32
                # Читаем Holding регистры для integer значений
                result = self.client.read_holding_registers(
                    reg_config.address, count=reg_config.count, device_id=reg_config.slave_id
                )
            elif reg_config.reg_type == "I_Float":
                # Устанавливаем тип данных как 32-битное число с плавающей точкой
                data_type = ModbusClientMixin.DATATYPE.FLOAT32
                # Читаем Input регистры (регистры ввода) для float значений
                result = self.client.read_input_registers(
                    reg_config.address, count=reg_config.count, device_id=reg_config.slave_id
                )
            elif reg_config.reg_type == "I_Int":
                # Устанавливаем тип данных как 32-битное целое число
                data_type = ModbusClientMixin.DATATYPE.INT32
                # Читаем Input регистры для integer значений
                result = self.client.read_input_registers(
                    reg_config.address, count=reg_config.count, device_id=reg_config.slave_id
                )
            elif reg_config.reg_type == "Coils":
                # Читаем катушки (coils) - дискретные выходы (биты)
                result = self.client.read_coils(
                    reg_config.address, count=reg_config.count, device_id=reg_config.slave_id
                )
            else:  # Discrete
                # Читаем дискретные входы (discrete inputs) - биты только для чтения
                result = self.client.read_discrete_inputs(
                    reg_config.address, count=reg_config.count, device_id=reg_config.slave_id
                )
            
            # Проверяем, произошла ли ошибка при чтении
            if result.isError():
                return None  # Возвращаем None при ошибке
            
            # Обработка полученного результата в зависимости от типа регистра
            if reg_config.reg_type in ["Coils", "Discrete"]:
                # Для битовых регистров берем первый бит и преобразуем в float
                return float(result.bits[0])
            else:
                # Для числовых регистров
                if reg_config.count == 1:
                    # Если читаем один регистр, просто преобразуем в float
                    return float(result.registers[0])
                else:
                    # Если читаем несколько регистров, конвертируем в соответствующий тип данных
                    registers_float = ModbusSerialClient.convert_from_registers(
                        registers=result.registers,  # Массив прочитанных регистров
                        data_type=data_type,        # Тип данных для конвертации
                        word_order="big"            # Порядок байтов (big-endian)
                    )
                    return registers_float
                    
        except Exception as e:
            # Обработка любых исключений при чтении
            print(f"Ошибка чтения регистра {reg_config.name}: {e}")
            return None  # Возвращаем None при исключении


class ModbusWriter:
    """Класс для записи данных в Modbus регистры"""
    
    def __init__(self, client):
        # Сохраняем ссылку на Modbus клиент для выполнения операций записи
        self.client = client
    
    def write_register(self, write_config: WriteRegisterConfig) -> tuple[bool, str]:
        """Записывает значение в регистр согласно конфигурации записи"""
        # Проверяем наличие подключения к Modbus
        if not self.client:
            return False, "Нет подключения к Modbus"
        
        try:
            # Инициализируем переменные для результата операции
            success = False
            message = ""
            
            # Обработка записи в зависимости от типа регистра
            if write_config.reg_type == "I_Float":
                # Конвертируем float значение в формат регистров Modbus
                registers_float = ModbusSerialClient.convert_to_registers(
                    value=write_config.value,           # Значение для записи
                    data_type=ModbusClientMixin.DATATYPE.FLOAT32,  # Тип данных
                    word_order="big"                    # Порядок байтов
                )
                # Записываем массив регистров в устройство
                result = self.client.write_registers(
                    write_config.address,      # Адрес начального регистра
                    values=registers_float,    # Массив значений для записи
                    device_id=write_config.slave_id  # ID устройства
                )
                # Проверяем результат записи
                if not result.isError():
                    success = True
                    message = f"Успешно записано {write_config.value} в Holding_Float регистр {write_config.address}"
                else:
                    message = f"Ошибка записи в Holding_Float регистр: {result}"
                    
            elif write_config.reg_type == "I_Int":
                # Конвертируем integer значение в формат регистров Modbus
                registers_int = ModbusSerialClient.convert_to_registers(
                    value=int(write_config.value),      # Преобразуем в целое число
                    data_type=ModbusClientMixin.DATATYPE.INT32,  # Тип данных
                    word_order="big"                    # Порядок байтов
                )
                # Записываем массив регистров в устройство
                result = self.client.write_registers(
                    write_config.address, values=registers_int, device_id=write_config.slave_id
                )
                # Проверяем результат записи
                if not result.isError():
                    success = True
                    message = f"Успешно записано {write_config.value} в Holding_Int регистр {write_config.address}"
                else:
                    message = f"Ошибка записи в Holding_Int регистр: {result}"
                    
            elif write_config.reg_type == "Coils":
                # Записываем значение в катушку (coil) - дискретный выход
                result = self.client.write_coil(
                    write_config.address,              # Адрес катушки
                    bool(write_config.value),          # Преобразуем значение в булев тип
                    slave=write_config.slave_id        # ID устройства
                )
                # Проверяем результат записи
                if not result.isError():
                    success = True
                    message = f"Успешно записано {bool(write_config.value)} в Coil {write_config.address}"
                else:
                    message = f"Ошибка записи в Coil: {result}"
            else:
                # Обработка неподдерживаемых типов регистров для записи
                message = f"Тип регистра {write_config.reg_type} не поддерживает запись"
            
            # Возвращаем результат операции и сообщение
            return success, message
            
        except Exception as e:
            # Обработка исключений при записи
            error_message = f"Исключение при записи в {write_config.name}: {e}"
            return False, error_message


class CSVLogger:
    """Класс для записи данных в CSV файл"""
    
    def __init__(self):
        # Инициализируем переменные для работы с CSV файлом
        self.csv_file = None        # Объект файла
        self.csv_writer = None      # Объект для записи в CSV
        self.is_active = False      # Флаг активности логирования
    
    def start_logging(self, filename: str, register_names: list) -> bool:
        """Начинает логирование в CSV файл с заданными заголовками"""
        try:
            # Открываем файл для записи с UTF-8 кодировкой
            self.csv_file = open(filename, 'w', newline='', encoding='utf-8')
            # Создаем объект для записи CSV данных
            self.csv_writer = csv.writer(self.csv_file)
            
            # Формируем заголовки: временная метка + названия регистров
            headers = ['Timestamp'] + register_names
            # Записываем строку заголовков в файл
            self.csv_writer.writerow(headers)
            # Принудительно сохраняем данные на диск
            self.csv_file.flush()
            # Устанавливаем флаг активности логирования
            self.is_active = True
            return True  # Возвращаем успех
        except Exception as e:
            # Обработка ошибок при создании файла
            print(f"Ошибка создания CSV файла: {e}")
            return False  # Возвращаем неудачу
    
    def log_data(self, timestamp: str, data: Dict[str, Any]) -> None:
        """Записывает строку данных с временной меткой в CSV"""
        # Проверяем активность логирования и наличие writer
        if not self.is_active or not self.csv_writer:
            return  # Выходим если логирование неактивно
        
        try:
            # Формируем строку данных: временная метка + значения регистров
            row = [timestamp] + [data.get(name, '') for name in data.keys()]
            # Записываем строку в CSV файл
            self.csv_writer.writerow(row)
            # Принудительно сохраняем данные на диск
            self.csv_file.flush()
        except Exception as e:
            # Обработка ошибок при записи данных
            print(f"Ошибка записи в CSV: {e}")
    
    def stop_logging(self) -> None:
        """Останавливает логирование и закрывает файл"""
        # Деактивируем логирование
        self.is_active = False
        # Закрываем файл если он открыт
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None      # Очищаем ссылку на файл
            self.csv_writer = None    # Очищаем ссылку на writer


class DataLogger(QObject):
    """Основной класс логгера данных - координирует все операции"""
    
    # Определяем сигналы Qt для межпоточного взаимодействия
    data_received = pyqtSignal(str, float, str)  # Сигнал получения данных: имя_регистра, значение, время
    write_completed = pyqtSignal(str, bool, str)  # Сигнал завершения записи: имя_регистра, успех, сообщение
    
    def __init__(self):
        # Вызываем конструктор родительского класса QObject
        super().__init__()
        # Инициализируем основные компоненты
        self.client = None                          # Modbus клиент
        self.register_manager = RegisterManager()   # Менеджер регистров
        self.reader = None                          # Объект для чтения регистров
        self.writer = None                          # Объект для записи регистров
        self.csv_logger = CSVLogger()               # Логгер CSV файлов
        self.is_running = False                     # Флаг активности логирования
    
    def set_client(self, client) -> None:
        """Устанавливает Modbus клиент и создает reader/writer"""
        # Сохраняем ссылку на клиент
        self.client = client
        # Создаем reader только если есть клиент
        self.reader = ModbusReader(client) if client else None
        # Создаем writer только если есть клиент
        self.writer = ModbusWriter(client) if client else None
    
    def start_logging(self, csv_filename: str) -> bool:
        """Начинает процесс логирования данных в CSV файл"""
        # Получаем список активных регистров
        enabled_registers = self.register_manager.get_enabled_registers()
        # Извлекаем имена регистров для заголовков CSV
        register_names = [reg.name for reg in enabled_registers]
        
        # Пытаемся начать логирование в CSV
        if self.csv_logger.start_logging(csv_filename, register_names):
            self.is_running = True  # Устанавливаем флаг активности
            return True
        return False  # Возвращаем неудачу если не удалось начать логирование
    
    def stop_logging(self) -> None:
        """Останавливает процесс логирования"""
        self.is_running = False      # Деактивируем логирование
        self.csv_logger.stop_logging()  # Останавливаем CSV логгер
    
    def read_all_registers(self) -> None:
        """Читает все активные регистры и записывает данные"""
        # Проверяем наличие reader и активность логирования
        if not self.reader or not self.is_running:
            return  # Выходим если условия не выполнены
        
        # Создаем временную метку для текущего чтения (с миллисекундами)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        # Словарь для хранения прочитанных значений
        values = {}
        
        # Проходим по всем зарегистрированным регистрам
        for reg_name, reg_config in self.register_manager.get_all_registers().items():
            if reg_config.enabled:  # Проверяем, что регистр активен
                # Читаем значение из регистра
                value = self.reader.read_register(reg_config)
                if value is not None:  # Если чтение успешно
                    values[reg_name] = value  # Сохраняем значение
                    # Добавляем данные во внутренний буфер регистра для построения графиков
                    current_time = time.time()           # Текущее время в секундах
                    reg_config.time_data.append(current_time)  # Добавляем время
                    reg_config.data.append(value)        # Добавляем значение
                    # Отправляем сигнал о получении новых данных
                    self.data_received.emit(reg_name, value, timestamp)
        
        # Записываем собранные данные в CSV файл
        if values:  # Только если есть данные для записи
            self.csv_logger.log_data(timestamp, values)
    
    def write_register(self, write_config: WriteRegisterConfig) -> None:
        """Записывает значение в указанный регистр"""
        # Проверяем наличие writer
        if not self.writer:
            # Отправляем сигнал об ошибке
            self.write_completed.emit(write_config.name, False, "Нет подключения к Modbus")
            return
        
        # Выполняем запись в регистр
        success, message = self.writer.write_register(write_config)
        # Отправляем сигнал о завершении операции записи
        self.write_completed.emit(write_config.name, success, message)
    
    def add_register(self, reg_config: RegisterConfig) -> None:
        """Добавляет новый регистр в менеджер"""
        self.register_manager.add_register(reg_config)
    
    def remove_register(self, name: str) -> bool:
        """Удаляет регистр из менеджера по имени"""
        return self.register_manager.remove_register(name)
    
    def update_register(self, old_name: str, reg_config: RegisterConfig) -> None:
        """Обновляет существующий регистр"""
        self.register_manager.update_register(old_name, reg_config)
    
    def clear_all_data(self) -> None:
        """Очищает все накопленные данные в регистрах"""
        self.register_manager.clear_all_data()
    
    @property
    def registers(self) -> dict:
        """Свойство для получения всех регистров"""
        return self.register_manager.get_all_registers()
    
    @registers.setter
    def registers(self, value: dict) -> None:
        """Сеттер для установки регистров (для обратной совместимости)"""
        self.register_manager._registers = value