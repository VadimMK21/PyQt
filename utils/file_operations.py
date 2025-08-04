"""
Модуль для работы с файлами конфигурации и данными
"""
import configparser
from typing import List, Optional, Tuple

from config.register_config import RegisterConfig, WriteRegisterConfig


class ConfigFileManager:
    """Менеджер для работы с INI файлами конфигурации"""
    
    @staticmethod
    def save_registers_config(filename: str, registers: List[RegisterConfig], 
                            plot_mode: str = "separate") -> bool:
        """Сохраняет конфигурацию регистров в INI файл"""
        config = configparser.ConfigParser()
        
        try:
            # Сохраняем режим отображения
            config['Display'] = {
                'mode': plot_mode
            }
            
            # Сохраняем каждый регистр
            for i, reg in enumerate(registers):
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
                'register_count': str(len(registers))
            }
            
            with open(filename, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            return True
            
        except Exception as e:
            print(f"Ошибка сохранения конфигурации регистров: {e}")
            return False
    
    @staticmethod
    def load_registers_config(filename: str) -> Tuple[Optional[List[RegisterConfig]], Optional[str]]:
        """Загружает конфигурацию регистров из INI файла"""
        config = configparser.ConfigParser()
        
        try:
            config.read(filename, encoding='utf-8')
            
            registers = []
            plot_mode = "separate"
            
            # Загружаем режим отображения
            if 'Display' in config:
                plot_mode = config['Display'].get('mode', 'separate')
            
            # Загружаем регистры
            if 'General' in config:
                register_count = int(config['General'].get('register_count', 0))
                
                for i in range(register_count):
                    section_name = f'Register_{i}'
                    if section_name in config:
                        section = config[section_name]
                        
                        # Безопасное получение значений с значениями по умолчанию
                        reg = RegisterConfig(
                            name=section.get('name', f'Register_{i+1}'),
                            slave_id=int(section.get('slave_id', 1)),
                            address=int(section.get('address', 0)),
                            count=int(section.get('count', 1)),
                            reg_type=section.get('reg_type', 'Holding'),
                            enabled=section.getboolean('enabled', True),
                            color=ConfigFileManager._parse_color(section.get('color', 'r')),
                            plot_group=section.get('plot_group', 'Group1')
                        )
                        
                        registers.append(reg)
            
            return registers, plot_mode
            
        except Exception as e:
            print(f"Ошибка загрузки конфигурации регистров: {e}")
            return None, None
    
    @staticmethod
    def save_write_registers_config(filename: str, write_registers: List[WriteRegisterConfig]) -> bool:
        """Сохраняет конфигурацию регистров для записи в INI файл"""
        config = configparser.ConfigParser()
        
        try:
            # Сохраняем каждый регистр для записи
            for i, write_reg in enumerate(write_registers):
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
                'write_register_count': str(len(write_registers))
            }
            
            with open(filename, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            return True
            
        except Exception as e:
            print(f"Ошибка сохранения конфигурации записи: {e}")
            return False
    
    @staticmethod
    def load_write_registers_config(filename: str) -> Optional[List[WriteRegisterConfig]]:
        """Загружает конфигурацию регистров для записи из INI файла"""
        config = configparser.ConfigParser()
        
        try:
            config.read(filename, encoding='utf-8')
            
            write_registers = []
            
            # Загружаем регистры для записи
            if 'General' in config:
                register_count = int(config['General'].get('write_register_count', 0))
                
                for i in range(register_count):
                    section_name = f'WriteRegister_{i}'
                    if section_name in config:
                        section = config[section_name]
                        
                        write_reg = WriteRegisterConfig(
                            name=section.get('name', f'WriteReg_{i+1}'),
                            slave_id=int(section.get('slave_id', 1)),
                            address=int(section.get('address', 0)),
                            reg_type=section.get('reg_type', 'Holding'),
                            value=float(section.get('value', 0))
                        )
                        
                        write_registers.append(write_reg)
            
            return write_registers
            
        except Exception as e:
            print(f"Ошибка загрузки конфигурации записи: {e}")
            return None
    
    @staticmethod
    def _parse_color(color_str: str):
        """Парсит строку цвета в соответствующий объект"""
        try:
            # Пытаемся преобразовать в кортеж RGB если это строка вида "(r, g, b)"
            if color_str.startswith('(') and color_str.endswith(')'):
                rgb_values = color_str.strip('()').split(',')
                if len(rgb_values) == 3:
                    return tuple(int(val.strip()) for val in rgb_values)
            # Иначе возвращаем как есть (символьное обозначение цвета)
            return color_str
        except:
            return 'r'  # Цвет по умолчанию
    
    @staticmethod
    def save_connection_config(filename: str, conn_type: str, host: str, port: int,
                             baudrate: int, parity: str, stopbits: int, bytesize: int) -> bool:
        """Сохраняет конфигурацию подключения"""
        config = configparser.ConfigParser()
        
        try:
            config['Connection'] = {
                'type': conn_type,
                'host': host,
                'port': str(port),
                'baudrate': str(baudrate),
                'parity': parity,
                'stopbits': str(stopbits),
                'bytesize': str(bytesize)
            }
            
            with open(filename, 'w', encoding='utf-8') as configfile:
                config.write(configfile)
            return True
            
        except Exception as e:
            print(f"Ошибка сохранения конфигурации подключения: {e}")
            return False
    
    @staticmethod
    def load_connection_config(filename: str) -> Optional[dict]:
        """Загружает конфигурацию подключения"""
        config = configparser.ConfigParser()
        
        try:
            config.read(filename, encoding='utf-8')
            
            if 'Connection' in config:
                section = config['Connection']
                return {
                    'type': section.get('type', 'TCP'),
                    'host': section.get('host', '127.0.0.1'),
                    'port': int(section.get('port', 502)),
                    'baudrate': int(section.get('baudrate', 38400)),
                    'parity': section.get('parity', 'N'),
                    'stopbits': int(section.get('stopbits', 1)),
                    'bytesize': int(section.get('bytesize', 8))
                }
            
            return None
            
        except Exception as e:
            print(f"Ошибка загрузки конфигурации подключения: {e}")
            return None


class CSVExporter:
    """Класс для экспорта данных в различные форматы"""
    
    @staticmethod
    def export_register_data(filename: str, registers: List[RegisterConfig], 
                           format_type: str = "csv") -> bool:
        """Экспортирует данные регистров в файл"""
        try:
            if format_type.lower() == "csv":
                return CSVExporter._export_to_csv(filename, registers)
            else:
                print(f"Неподдерживаемый формат: {format_type}")
                return False
                
        except Exception as e:
            print(f"Ошибка экспорта данных: {e}")
            return False
    
    @staticmethod
    def _export_to_csv(filename: str, registers: List[RegisterConfig]) -> bool:
        """Экспортирует данные в CSV файл"""
        import csv
        from datetime import datetime
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Заголовки
                headers = ['Timestamp'] + [reg.name for reg in registers if reg.data]
                writer.writerow(headers)
                
                # Находим максимальную длину данных
                max_length = max(len(reg.data) for reg in registers if reg.data) if registers else 0
                
                # Записываем данные
                for i in range(max_length):
                    row = []
                    
                    # Время (используем время первого регистра с данными или текущее)
                    timestamp = None
                    for reg in registers:
                        if reg.time_data and i < len(reg.time_data):
                            timestamp = datetime.fromtimestamp(reg.time_data[i]).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                            break
                    
                    if not timestamp:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    
                    row.append(timestamp)
                    
                    # Данные регистров
                    for reg in registers:
                        if reg.data and i < len(reg.data):
                            row.append(reg.data[i])
                        else:
                            row.append('')
                    
                    writer.writerow(row)
            
            return True
            
        except Exception as e:
            print(f"Ошибка записи CSV файла: {e}")
            return False