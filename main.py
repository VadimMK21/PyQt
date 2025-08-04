#!/usr/bin/env python3
"""
Modbus Multi-Register Logger v2.0 - Модульная версия
Главный файл для запуска приложения
"""

import sys
import os

# Добавляем текущую директорию в путь для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtCore import Qt
    import pyqtgraph as pg
except ImportError as e:
    print(f"Ошибка импорта PyQt5 или pyqtgraph: {e}")
    print("Убедитесь, что установлены все необходимые зависимости:")
    print("pip install PyQt5 pyqtgraph pymodbus numpy")
    sys.exit(1)

try:
    from ui.main_window import MainWindow
except ImportError as e:
    print(f"Ошибка импорта модулей приложения: {e}")
    print("Убедитесь, что все файлы модулей находятся в правильных директориях")
    sys.exit(1)


QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

def setup_application():
    """Настройка приложения"""
    app = QApplication(sys.argv)
    
    # Настройка стиля
    app.setStyle('Fusion')
    
    # Настройка pyqtgraph
    pg.setConfigOptions(
        antialias=True,
        useOpenGL=False,  # Отключаем OpenGL для совместимости
        enableExperimental=False
    )
    
    # Настройка высокого DPI
    #app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    return app


def check_dependencies():
    """Проверка зависимостей"""
    try:
        import pymodbus
        import numpy
        import configparser
        import csv
        return True
    except ImportError as e:
        QMessageBox.critical(
            None,
            "Ошибка зависимостей",
            f"Отсутствует необходимая библиотека: {e}\n\n"
            "Установите все зависимости:\n"
            "pip install PyQt5 pyqtgraph pymodbus numpy"
        )
        return False


def main():
    """Главная функция"""
    print("=" * 60)
    print("Modbus Multi-Register Logger v2.0 (Модульная версия)")
    print("=" * 60)
    
    # Создаем приложение
    app = setup_application()
    
    # Проверяем зависимости
    if not check_dependencies():
        return 1
    
    try:
        # Создаем и показываем главное окно
        main_window = MainWindow()
        main_window.show()
        
        print("Приложение запущено успешно!")
        print("Для выхода закройте окно приложения или нажмите Ctrl+C")
        
        # Запускаем цикл событий
        return app.exec_()
        
    except Exception as e:
        print(f"Критическая ошибка при запуске приложения: {e}")
        QMessageBox.critical(
            None,
            "Критическая ошибка",
            f"Не удалось запустить приложение:\n{e}"
        )
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nПриложение остановлено пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        sys.exit(1)