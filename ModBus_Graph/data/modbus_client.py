"""
Модуль для работы с Modbus клиентом
"""
from typing import Optional, Union
from pymodbus.client import ModbusTcpClient, ModbusSerialClient


class ConnectionConfig:
    """Конфигурация подключения"""
    
    def __init__(self, connection_type: str = "TCP", host: str = "127.0.0.1", 
                 port: int = 502, baudrate: int = 38400, parity: str = "N", 
                 stopbits: int = 1, bytesize: int = 8, timeout: float = 1.0):
        self.connection_type = connection_type
        self.host = host
        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.timeout = timeout
    
    def __str__(self) -> str:
        if self.connection_type == "TCP":
            return f"TCP {self.host}:{self.port}"
        else:
            return f"RTU {self.host} {self.baudrate}bps"


class ModbusClientManager:
    """Менеджер для управления Modbus подключением"""
    
    def __init__(self):
        self.client: Optional[Union[ModbusTcpClient, ModbusSerialClient]] = None
        self.config: Optional[ConnectionConfig] = None
        self.is_connected = False
    
    def connect(self, config: ConnectionConfig) -> bool:
        """Устанавливает подключение к Modbus устройству"""
        try:
            # Закрываем предыдущее подключение если есть
            self.disconnect()
            
            # Создаем новый клиент
            if config.connection_type == "TCP":
                self.client = ModbusTcpClient(
                    host=config.host,
                    port=config.port,
                    timeout=config.timeout
                )
            else:  # RTU
                self.client = ModbusSerialClient(
                    port=config.host,  # COM порт
                    baudrate=config.baudrate,
                    parity=config.parity,
                    stopbits=config.stopbits,
                    bytesize=config.bytesize,
                    timeout=config.timeout
                )
            
            # Пытаемся подключиться
            connection_result = self.client.connect()
            
            if connection_result:
                self.config = config
                self.is_connected = True
                return True
            else:
                self.client = None
                return False
                
        except Exception as e:
            print(f"Ошибка подключения к Modbus: {e}")
            self.client = None
            return False
    
    def disconnect(self) -> None:
        """Закрывает подключение"""
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                print(f"Ошибка при закрытии подключения: {e}")
            finally:
                self.client = None
                self.is_connected = False
                self.config = None
    
    def test_connection(self) -> bool:
        """Тестирует подключение простым запросом"""
        if not self.client or not self.is_connected:
            return False
        
        try:
            # Пытаемся прочитать один регистр для теста
            result = self.client.read_holding_registers(0, 1, device_id=1)
            # Даже если регистр не существует, подключение работает если нет ошибки связи
            return not result.isError() or "Connection" not in str(result)
        except Exception:
            return False
    
    def get_client(self) -> Optional[Union[ModbusTcpClient, ModbusSerialClient]]:
        """Возвращает клиент если подключен"""
        return self.client if self.is_connected else None
    
    def get_connection_info(self) -> str:
        """Возвращает информацию о подключении"""
        if not self.is_connected or not self.config:
            return "Не подключен"
        return str(self.config)
    
    def __enter__(self):
        """Контекстный менеджер - вход"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход"""
        self.disconnect()


def create_tcp_config(host: str = "127.0.0.1", port: int = 502, timeout: float = 1.0) -> ConnectionConfig:
    """Создает конфигурацию TCP подключения"""
    return ConnectionConfig(
        connection_type="TCP",
        host=host,
        port=port,
        timeout=timeout
    )


def create_rtu_config(port: str = "COM1", baudrate: int = 38400, parity: str = "N", 
                     stopbits: int = 1, bytesize: int = 8, timeout: float = 1.0) -> ConnectionConfig:
    """Создает конфигурацию RTU подключения"""
    return ConnectionConfig(
        connection_type="RTU",
        host=port,
        baudrate=baudrate,
        parity=parity,
        stopbits=stopbits,
        bytesize=bytesize,
        timeout=timeout
    )