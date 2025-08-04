# Modbus Multi-Register Logger v2.0 (Модульная версия)

Приложение для мониторинга и логирования данных с Modbus устройств в реальном времени с графическим интерфейсом.

## Особенности

- **Модульная архитектура** - код разбит на логические модули для лучшей поддержки
- **Поддержка TCP и RTU** - подключение через Ethernet и Serial порт
- **Множественные регистры** - одновременное чтение нескольких регистров
- **Реальное время графики** - отображение данных в реальном времени с автопрокруткой
- **Запись в регистры** - возможность записи значений в Modbus регистры
- **Экспорт данных** - сохранение в CSV файлы
- **Конфигурации** - сохранение и загрузка настроек

## Структура проекта

```
modbus_logger/
├── main.py                    # Точка входа
├── config/                    # Конфигурации
│   ├── __init__.py
│   └── register_config.py     # Конфигурации регистров
├── data/                      # Логика данных
│   ├── __init__.py
│   ├── logger.py             # Логирование данных
│   └── modbus_client.py      # Modbus клиент
├── ui/                        # Пользовательский интерфейс
│   ├── __init__.py
│   ├── main_window.py        # Главное окно
│   ├── connection_widget.py  # Виджет подключения
│   ├── register_widget.py    # Настройка регистров
│   ├── plot_widget.py        # Графики
│   └── write_window.py       # Окно записи
├── utils/                     # Утилиты
│   ├── __init__.py
│   └── file_operations.py    # Работа с файлами
├── requirements.txt
└── README.md
```

## Установка

### Требования

- Python 3.7+
- PyQt5
- pyqtgraph
- pymodbus
- numpy

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Запуск

```bash
python main.py
```

## Использование

### 1. Настройка подключения

- Выберите тип подключения (TCP или RTU)
- Укажите параметры подключения
- Нажмите "Подключить"

### 2. Конфигурация регистров

- Добавьте регистры для мониторинга
- Настройте адреса, типы данных и группы
- Включите/выключите нужные регистры

### 3. Логирование

- Нажмите "Начать логирование"
- Данные будут отображаться на графиках
- CSV файл создается автоматически

### 4. Запись в регистры

- Откройте окно записи
- Настройте регистры для записи
- Укажите значения и выполните запись

## Типы регистров

- **H_Float/H_Int** - Holding регистры (Float32/Int32)
- **I_Float/I_Int** - Input регистры (Float32/Int32)  
- **Coils** - Дискретные выходы
- **Discrete** - Дискретные входы

## Конфигурационные файлы

Приложение поддерживает сохранение/загрузку:
- Настроек подключения (*.ini)
- Конфигурации регистров чтения (*.ini)
- Конфигурации регистров записи (*.ini)

## Преимущества модульной архитектуры

### Исходная версия (монолитная)
- 1000+ строк в одном файле
- Сложно поддерживать и расширять
- Трудно тестировать отдельные компоненты

### Новая версия (модульная)
- Разделение ответственности
- Легкость тестирования
- Возможность повторного использования
- Лучшая читаемость кода
- Упрощенная отладка

## Архитектурные решения

### Разделение логики
- **config/** - конфигурации и модели данных
- **data/** - логика работы с данными
- **ui/** - пользовательский интерфейс
- **utils/** - вспомогательные функции

### Паттерны проектирования
- **MVC** - разделение модели, представления и контроллера
- **Observer** - использование Qt сигналов/слотов
- **Factory** - фабричные методы для создания конфигураций
- **Manager** - менеджеры для управления коллекциями

## API

### Основные классы

```python
# Конфигурация регистра
from config.register_config import RegisterConfig

reg = RegisterConfig(
    name="temperature",
    slave_id=1,
    address=100,
    reg_type="H_Float"
)

# Подключение к Modbus
from data.modbus_client import ModbusClientManager, create_tcp_config

manager = ModbusClientManager()
config = create_tcp_config("192.168.1.100", 502)
manager.connect(config)

# Логирование данных
from data.logger import DataLogger

logger = DataLogger()
logger.set_client(manager.get_client())
logger.add_register(reg)
```

## Расширение функциональности

### Добавление нового типа регистра

1. Обновите `RegisterConfig` в `config/register_config.py`
2. Добавьте логику чтения в `ModbusReader`
3. Обновите UI в `RegisterWidget`

### Добавление нового формата экспорта

1. Расширьте `CSVExporter` в `utils/file_operations.py`
2. Добавьте UI элементы для выбора формата

### Интеграция с базами данных

1. Создайте новый модуль `data/database.py`
2. Реализуйте интерфейс для записи в БД
3. Интегрируйте с `DataLogger`

## Тестирование

Для каждого модуля можно создать отдельные тесты:

```python
# tests/test_register_config.py
import unittest
from config.register_config import RegisterConfig

class TestRegisterConfig(unittest.TestCase):
    def test_register_creation(self):
        reg = RegisterConfig("test", 1, 100)
        self.assertEqual(reg.name, "test")
        self.assertEqual(reg.slave_id, 1)
        self.assertEqual(reg.address, 100)
```

## Отладка

Каждый модуль можно отлаживать независимо:

```python
# Отладка логгера
from data.logger import DataLogger
logger = DataLogger()
# ... отладочный код

# Отладка UI
from ui.register_widget import RegisterWidget
widget = RegisterWidget()
# ... отладочный код
```

## Лицензия

MIT License

## Автор

Разработано для демонстрации принципов модульного программирования на Python