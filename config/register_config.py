"""
Модуль для работы с конфигурациями регистров Modbus
"""
import random
from collections import deque
from typing import Optional, Any


class RegisterConfig:
    """Конфигурация регистра для чтения"""
    
    def __init__(self, name: str = "Register", slave_id: int = 1, address: int = 0, 
                 count: int = 1, reg_type: str = "Holding", enabled: bool = True, 
                 color: Optional[Any] = None, plot_group: str = "Group1"):
        self.name = name
        self.slave_id = slave_id
        self.address = address
        self.count = count
        self.reg_type = reg_type
        self.enabled = enabled
        self.color = color or self.generate_random_color()
        self.plot_group = plot_group
        self.data = deque(maxlen=10000)
        self.time_data = deque(maxlen=10000)
   
    def generate_random_color(self) -> Any:
        """Генерирует случайный цвет для графика"""
        colors = ['r', 'g', 'b', 'c', 'm', 'y', 'w', (255, 165, 0), (255, 20, 147), (50, 205, 50)]
        return random.choice(colors)
    
    def clear_data(self) -> None:
        """Очищает данные регистра"""
        self.data.clear()
        self.time_data.clear()


class WriteRegisterConfig:
    """Конфигурация регистра для записи"""
    
    def __init__(self, name: str = "WriteReg", slave_id: int = 1, address: int = 0, 
                 reg_type: str = "Holding", value: float = 0):
        self.name = name
        self.slave_id = slave_id
        self.address = address
        self.reg_type = reg_type
        self.value = value
    
    def __str__(self) -> str:
        return (f"WriteRegisterConfig(name='{self.name}', slave_id={self.slave_id}, "
                f"address={self.address}, reg_type='{self.reg_type}', value={self.value})")


class RegisterManager:
    """Менеджер для управления коллекцией регистров"""
    
    def __init__(self):
        self._registers = {}
    
    def add_register(self, reg_config: RegisterConfig) -> None:
        """Добавляет регистр"""
        self._registers[reg_config.name] = reg_config
    
    def remove_register(self, name: str) -> bool:
        """Удаляет регистр по имени"""
        if name in self._registers:
            del self._registers[name]
            return True
        return False
    
    def update_register(self, old_name: str, reg_config: RegisterConfig) -> None:
        """Обновляет регистр"""
        if old_name in self._registers:
            del self._registers[old_name]
        self._registers[reg_config.name] = reg_config
    
    def get_register(self, name: str) -> Optional[RegisterConfig]:
        """Получает регистр по имени"""
        return self._registers.get(name)
    
    def get_all_registers(self) -> dict:
        """Возвращает все регистры"""
        return self._registers.copy()
    
    def get_enabled_registers(self) -> list:
        """Возвращает только включенные регистры"""
        return [reg for reg in self._registers.values() if reg.enabled]
    
    def clear_all_data(self) -> None:
        """Очищает данные всех регистров"""
        for reg in self._registers.values():
            reg.clear_data()
    
    def get_plot_groups(self) -> dict:
        """Возвращает словарь групп с их регистрами"""
        groups = {}
        for reg in self.get_enabled_registers():
            if reg.plot_group not in groups:
                groups[reg.plot_group] = []
            groups[reg.plot_group].append(reg)
        return groups
    
    def get_total_data_points(self) -> int:
        """Возвращает общее количество точек данных"""
        return sum(len(reg.data) for reg in self._registers.values())
    
    @property
    def count(self) -> int:
        """Количество регистров"""
        return len(self._registers)
    
    @property
    def enabled_count(self) -> int:
        """Количество включенных регистров"""
        return len(self.get_enabled_registers())


def create_default_registers() -> list:
    """Создает набор регистров по умолчанию"""
    return [
        RegisterConfig("output", 10, 3335, 2, "Holding", True, 'r', "Sensors"),
        RegisterConfig("pv", 10, 1284, 2, "Holding", True, 'g', "Sensors"),
        RegisterConfig("setpoint", 10, 1539, 2, "Holding", True, 'b', "Flow")
    ]


def create_default_write_registers() -> list:
    """Создает набор регистров для записи по умолчанию"""
    return [
        WriteRegisterConfig("setpoint_write", 10, 1539, "Holding", 25.0),
        WriteRegisterConfig("enable_output", 10, 2000, "Coils", 1),
        WriteRegisterConfig("manual_output", 10, 3000, "Holding", 50.0)
    ]