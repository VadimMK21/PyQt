"""
Модуль для логирования данных Modbus
"""
import csv
import time
from datetime import datetime
from typing import Optional, Dict, Any

from PyQt5.QtCore import QObject, pyqtSignal
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.client.mixin import ModbusClientMixin

from config.register_config import RegisterConfig, WriteRegisterConfig, RegisterManager


class ModbusReader:
    """Класс для чтения данных из Modbus регистров"""
    
    def __init__(self, client):
        self.client = client
    
    def read_register(self, reg_config: RegisterConfig) -> Optional[float]:
        """Читает значение из регистра"""
        if not self.client or not reg_config.enabled:
            return None
        
        try:
            # Определяем тип данных и функцию чтения
            if reg_config.reg_type == "H_Float":
                data_type = ModbusClientMixin.DATATYPE.FLOAT32
                result = self.client.read_holding_registers(
                    reg_config.address, count=reg_config.count, device_id=reg_config.slave_id
                )
            elif reg_config.reg_type == "H_Int":
                data_type = ModbusClientMixin.DATATYPE.INT32
                result = self.client.read_holding_registers(
                    reg_config.address, count=reg_config.count, device_id=reg_config.slave_id
                )
            elif reg_config.reg_type == "I_Float":
                data_type = ModbusClientMixin.DATATYPE.FLOAT32
                result = self.client.read_input_registers(
                    reg_config.address, count=reg_config.count, device_id=reg_config.slave_id
                )
            elif reg_config.reg_type == "I_Int":
                data_type = ModbusClientMixin.DATATYPE.INT32
                result = self.client.read_input_registers(
                    reg_config.address, count=reg_config.count, device_id=reg_config.slave_id
                )
            elif reg_config.reg_type == "Coils":
                result = self.client.read_coils(
                    reg_config.address, count=reg_config.count, device_id=reg_config.slave_id
                )
            else:  # Discrete
                result = self.client.read_discrete_inputs(
                    reg_config.address, count=reg_config.count, device_id=reg_config.slave_id
                )
            
            if result.isError():
                return None
            
            # Обработка результата
            if reg_config.reg_type in ["Coils", "Discrete"]:
                return float(result.bits[0])
            else:
                if reg_config.count == 1:
                    return float(result.registers[0])
                else:
                    registers_float = ModbusSerialClient.convert_from_registers(
                        registers=result.registers,
                        data_type=data_type,
                        word_order="big"
                    )
                    return registers_float
                    
        except Exception as e:
            print(f"Ошибка чтения регистра {reg_config.name}: {e}")
            return None


class ModbusWriter:
    """Класс для записи данных в Modbus регистры"""
    
    def __init__(self, client):
        self.client = client
    
    def write_register(self, write_config: WriteRegisterConfig) -> tuple[bool, str]:
        """Записывает значение в регистр"""
        if not self.client:
            return False, "Нет подключения к Modbus"
        
        try:
            success = False
            message = ""
            
            if write_config.reg_type == "I_Float":
                registers_float = ModbusSerialClient.convert_to_registers(
                    value=write_config.value,
                    data_type=ModbusClientMixin.DATATYPE.FLOAT32,
                    word_order="big"
                )
                result = self.client.write_registers(
                    write_config.address, values=registers_float, device_id=write_config.slave_id
                )
                if not result.isError():
                    success = True
                    message = f"Успешно записано {write_config.value} в Holding_Float регистр {write_config.address}"
                else:
                    message = f"Ошибка записи в Holding_Float регистр: {result}"
                    
            elif write_config.reg_type == "I_Int":
                registers_int = ModbusSerialClient.convert_to_registers(
                    value=int(write_config.value),
                    data_type=ModbusClientMixin.DATATYPE.INT32,
                    word_order="big"
                )
                result = self.client.write_registers(
                    write_config.address, values=registers_int, device_id=write_config.slave_id
                )
                if not result.isError():
                    success = True
                    message = f"Успешно записано {write_config.value} в Holding_Int регистр {write_config.address}"
                else:
                    message = f"Ошибка записи в Holding_Int регистр: {result}"
                    
            elif write_config.reg_type == "Coils":
                result = self.client.write_coil(
                    write_config.address, bool(write_config.value), slave=write_config.slave_id
                )
                if not result.isError():
                    success = True
                    message = f"Успешно записано {bool(write_config.value)} в Coil {write_config.address}"
                else:
                    message = f"Ошибка записи в Coil: {result}"
            else:
                message = f"Тип регистра {write_config.reg_type} не поддерживает запись"
            
            return success, message
            
        except Exception as e:
            error_message = f"Исключение при записи в {write_config.name}: {e}"
            return False, error_message


class CSVLogger:
    """Класс для записи данных в CSV файл"""
    
    def __init__(self):
        self.csv_file = None
        self.csv_writer = None
        self.is_active = False
    
    def start_logging(self, filename: str, register_names: list) -> bool:
        """Начинает логирование в CSV файл"""
        try:
            self.csv_file = open(filename, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.csv_file)
            
            # Записываем заголовки
            headers = ['Timestamp'] + register_names
            self.csv_writer.writerow(headers)
            self.csv_file.flush()
            self.is_active = True
            return True
        except Exception as e:
            print(f"Ошибка создания CSV файла: {e}")
            return False
    
    def log_data(self, timestamp: str, data: Dict[str, Any]) -> None:
        """Записывает строку данных в CSV"""
        if not self.is_active or not self.csv_writer:
            return
        
        try:
            row = [timestamp] + [data.get(name, '') for name in data.keys()]
            self.csv_writer.writerow(row)
            self.csv_file.flush()
        except Exception as e:
            print(f"Ошибка записи в CSV: {e}")
    
    def stop_logging(self) -> None:
        """Останавливает логирование"""
        self.is_active = False
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None


class DataLogger(QObject):
    """Основной класс логгера данных"""
    
    data_received = pyqtSignal(str, float, str)  # register_name, value, timestamp
    write_completed = pyqtSignal(str, bool, str)  # register_name, success, message
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.register_manager = RegisterManager()
        self.reader = None
        self.writer = None
        self.csv_logger = CSVLogger()
        self.is_running = False
    
    def set_client(self, client) -> None:
        """Устанавливает Modbus клиент"""
        self.client = client
        self.reader = ModbusReader(client) if client else None
        self.writer = ModbusWriter(client) if client else None
    
    def start_logging(self, csv_filename: str) -> bool:
        """Начинает логирование данных"""
        enabled_registers = self.register_manager.get_enabled_registers()
        register_names = [reg.name for reg in enabled_registers]
        
        if self.csv_logger.start_logging(csv_filename, register_names):
            self.is_running = True
            return True
        return False
    
    def stop_logging(self) -> None:
        """Останавливает логирование"""
        self.is_running = False
        self.csv_logger.stop_logging()
    
    def read_all_registers(self) -> None:
        """Читает все активные регистры"""
        if not self.reader or not self.is_running:
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        values = {}
        
        for reg_name, reg_config in self.register_manager.get_all_registers().items():
            if reg_config.enabled:
                value = self.reader.read_register(reg_config)
                if value is not None:
                    values[reg_name] = value
                    # Добавляем данные в регистр
                    current_time = time.time()
                    reg_config.time_data.append(current_time)
                    reg_config.data.append(value)
                    # Отправляем сигнал
                    self.data_received.emit(reg_name, value, timestamp)
        
        # Записываем в CSV
        if values:
            self.csv_logger.log_data(timestamp, values)
    
    def write_register(self, write_config: WriteRegisterConfig) -> None:
        """Записывает значение в регистр"""
        if not self.writer:
            self.write_completed.emit(write_config.name, False, "Нет подключения к Modbus")
            return
        
        success, message = self.writer.write_register(write_config)
        self.write_completed.emit(write_config.name, success, message)
    
    def add_register(self, reg_config: RegisterConfig) -> None:
        """Добавляет регистр"""
        self.register_manager.add_register(reg_config)
    
    def remove_register(self, name: str) -> bool:
        """Удаляет регистр"""
        return self.register_manager.remove_register(name)
    
    def update_register(self, old_name: str, reg_config: RegisterConfig) -> None:
        """Обновляет регистр"""
        self.register_manager.update_register(old_name, reg_config)
    
    def clear_all_data(self) -> None:
        """Очищает все данные"""
        self.register_manager.clear_all_data()
    
    @property
    def registers(self) -> dict:
        """Возвращает все регистры"""
        return self.register_manager.get_all_registers()
    
    @registers.setter
    def registers(self, value: dict) -> None:
        """Устанавливает регистры (для обратной совместимости)"""
        self.register_manager._registers = value