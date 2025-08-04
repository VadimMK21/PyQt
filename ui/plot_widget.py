"""
Модуль для управления графиками
"""
# Импорт модуля времени для работы с временными метками
import time
# Импорт типов для аннотации типов переменных и возвращаемых значений
from typing import Dict, List, Optional

# Импорт библиотеки для численных вычислений с массивами
import numpy as np
# Импорт библиотеки для создания графиков в PyQt
import pyqtgraph as pg
# Импорт основных виджетов PyQt5 для создания интерфейса
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QPushButton, QHBoxLayout, QSpinBox
# Импорт константы выравнивания из PyQt5
from PyQt5.QtCore import Qt

# Импорт конфигурации регистров из собственного модуля
from config.register_config import RegisterConfig


class PlotManager:
    """Менеджер графиков - основной класс для управления всеми графиками в приложении"""
    
    def __init__(self, scroll_window_size: int = 60):
        # Словарь для хранения информации о каждой кривой графика
        # Ключ - имя регистра, значение - словарь с информацией о графике
        self.plot_curves = {}  # Словарь кривых: {register_name: plot_info}
        
        # Размер окна прокрутки в секундах (сколько секунд данных показывать)
        self.scroll_window_size = scroll_window_size
        
        # Ссылки на элементы интерфейса (инициализируются позже)
        self.plots_layout = None  # Макет для размещения графиков
        self.scroll_widget = None  # Виджет с прокруткой
        self.main_widget = None  # Главный виджет менеджера
        
        # Вызываем метод настройки интерфейса
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка интерфейса - создание всех элементов UI"""
        # Создаем главный виджет, который будет содержать все элементы
        self.main_widget = QWidget()
        # Создаем вертикальный макет для главного виджета
        main_layout = QVBoxLayout(self.main_widget)
        
        # Кнопки управления графиками
        # Создаем горизонтальный макет для кнопок
        controls_layout = QHBoxLayout()
        
        # Кнопка для сброса масштаба всех графиков
        self.reset_zoom_btn = QPushButton("Сбросить масштаб")
        # Подключаем обработчик нажатия кнопки к методу сброса масштаба
        self.reset_zoom_btn.clicked.connect(self.reset_all_zoom)
        
        # Кнопка переключения автоматической прокрутки
        self.auto_scroll_btn = QPushButton("Авто-прокрутка: ВКЛ")
        # Делаем кнопку переключаемой (может быть нажата/отжата)
        self.auto_scroll_btn.setCheckable(True)
        # По умолчанию кнопка нажата (автопрокрутка включена)
        self.auto_scroll_btn.setChecked(True)
        # Подключаем обработчик переключения к методу переключения автопрокрутки
        self.auto_scroll_btn.clicked.connect(self.toggle_auto_scroll)

        self.interval_auto_scroll = QSpinBox()
        self.interval_auto_scroll.setRange(1, 600)
        self.interval_auto_scroll.setValue(60)
        self.interval_auto_scroll.setSuffix(" сек")
        self.interval_auto_scroll.setToolTip("Интервал автоматической прокрутки в секундах")
        
        # Добавляем кнопки в горизонтальный макет
        controls_layout.addWidget(self.reset_zoom_btn)
        controls_layout.addWidget(self.auto_scroll_btn)
        controls_layout.addWidget(self.interval_auto_scroll)
        # Добавляем растягивающийся элемент для выравнивания кнопок по левому краю
        controls_layout.addStretch()
        
        # Скролл для графиков
        # Создаем область прокрутки для размещения графиков
        scroll_area = QScrollArea()
        # Создаем виджет, который будет прокручиваться
        scroll_widget = QWidget()
        # Создаем вертикальный макет для размещения графиков в прокручиваемом виджете
        self.plots_layout = QVBoxLayout(scroll_widget)
        
        # Устанавливаем прокручиваемый виджет в область прокрутки
        scroll_area.setWidget(scroll_widget)
        # Разрешаем автоматическое изменение размера виджета при изменении содержимого
        scroll_area.setWidgetResizable(True)
        # Настраиваем политику отображения полос прокрутки
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # Вертикальная - по необходимости
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # Горизонтальная - по необходимости
        
        # Сохраняем ссылку на прокручиваемый виджет для дальнейшего использования
        self.scroll_widget = scroll_widget
        
        # Добавляем элементы в главный макет
        main_layout.addLayout(controls_layout)  # Кнопки управления
        main_layout.addWidget(scroll_area)  # Область с графиками
    
    def get_main_widget(self) -> QWidget:
        """Возвращает главный виджет для встраивания в другие окна"""
        return self.main_widget
    
    def create_plots(self, registers: List[RegisterConfig], plot_mode: str = "separate"):
        """Создает графики для регистров в зависимости от выбранного режима"""
        # Очищаем все существующие графики перед созданием новых
        self.clear_all_plots()
        
        # Выбираем способ создания графиков в зависимости от режима
        if plot_mode == "separate":
            # Отдельный график для каждого регистра
            self._create_separate_plots(registers)
        else:
            # Группировка регистров по группам на одном графике
            self._create_grouped_plots(registers)
    
    def _create_separate_plots(self, registers: List[RegisterConfig]):
        """Создает отдельный график для каждого активного регистра"""
        # Проходим по всем регистрам
        for reg in registers:
            # Проверяем, что регистр включен для отображения
            if reg.enabled:
                # Создаем виджет графика с заголовком, содержащим информацию о регистре
                plot_widget = pg.PlotWidget(
                    title=f"{reg.name} (Slave:{reg.slave_id}, Addr:{reg.address})"
                )
                # Устанавливаем подписи осей
                plot_widget.setLabel('left', 'Значение')  # Левая ось - значения
                plot_widget.setLabel('bottom', 'Время (сек)')  # Нижняя ось - время
                # Включаем сетку для лучшего восприятия данных
                plot_widget.showGrid(x=True, y=True)
                # Устанавливаем минимальную высоту графика
                plot_widget.setMinimumHeight(200)
                
                # Настраиваем автоматическое масштабирование
                plot_widget.setAutoVisible(y=True)  # Автоматическое масштабирование по Y
                plot_widget.enableAutoRange(axis='y')  # Включаем авто-диапазон по Y
                plot_widget.disableAutoRange(axis='x')  # Отключаем авто-диапазон по X (управляем вручную)
                
                # Создаем кривую (линию) на графике с цветом из конфигурации регистра
                curve = plot_widget.plot(pen=pg.mkPen(color=reg.color, width=2))
                
                # Сохраняем всю информацию о графике в словаре
                self.plot_curves[reg.name] = {
                    'curve': curve,  # Объект кривой для обновления данных
                    'widget': plot_widget,  # Виджет графика
                    'config': reg,  # Конфигурация регистра
                    'type': 'separate'  # Тип графика - отдельный
                }
                
                # Добавляем график в макет (отображаем на экране)
                self.plots_layout.addWidget(plot_widget)
    
    def _create_grouped_plots(self, registers: List[RegisterConfig]):
        """Создает график для каждой группы с несколькими кривыми на одном графике"""
        # Группируем регистры по группам
        groups = {}
        # Проходим по всем регистрам
        for reg in registers:
            # Проверяем, что регистр включен
            if reg.enabled:
                # Если группа еще не существует, создаем для нее пустой список
                if reg.plot_group not in groups:
                    groups[reg.plot_group] = []
                # Добавляем регистр в соответствующую группу
                groups[reg.plot_group].append(reg)
        
        # Создаем график для каждой группы
        for group_name, group_registers in groups.items():
            # Пропускаем пустые группы
            if not group_registers:
                continue
            
            # Создаем график для группы с заголовком группы
            plot_widget = pg.PlotWidget(title=f"Группа: {group_name}")
            # Устанавливаем подписи осей
            plot_widget.setLabel('left', 'Значение')
            plot_widget.setLabel('bottom', 'Время (сек)')
            # Включаем сетку
            plot_widget.showGrid(x=True, y=True)
            # Устанавливаем минимальную высоту (больше для группового графика)
            plot_widget.setMinimumHeight(250)
            
            # Настраиваем автоматическое масштабирование
            plot_widget.setAutoVisible(y=True)
            plot_widget.enableAutoRange(axis='y')
            plot_widget.disableAutoRange(axis='x')
            
            # Добавляем легенду для различения кривых
            plot_widget.addLegend()
            
            # Создаем кривую для каждого регистра в группе
            for reg in group_registers:
                # Создаем кривую с цветом регистра и его именем для легенды
                curve = plot_widget.plot(
                    pen=pg.mkPen(color=reg.color, width=2),
                    name=reg.name  # Имя для отображения в легенде
                )
                
                # Сохраняем информацию о кривой
                self.plot_curves[reg.name] = {
                    'curve': curve,
                    'widget': plot_widget,  # Один виджет может содержать несколько кривых
                    'config': reg,
                    'group': group_name,  # Имя группы
                    'type': 'grouped'  # Тип - групповой график
                }
            
            # Добавляем график группы в макет
            self.plots_layout.addWidget(plot_widget)
    
    def update_plot(self, register_name: str, value: float, timestamp: str):
        """Обновляет график для конкретного регистра новыми данными"""
        # Проверяем, существует ли график для этого регистра
        if register_name not in self.plot_curves:
            return  # Если нет, выходим из функции
        
        # Получаем информацию о графике
        plot_info = self.plot_curves[register_name]
        reg_config = plot_info['config']  # Конфигурация регистра
        plot_widget = plot_info['widget']  # Виджет графика
        curve = plot_info['curve']  # Кривая для обновления
        
        # Добавляем новые данные в регистр
        current_time = time.time()  # Получаем текущее время в секундах
        reg_config.time_data.append(current_time)  # Добавляем время в список
        reg_config.data.append(value)  # Добавляем значение в список
        
        # Обновляем график только если есть хотя бы 2 точки данных
        if len(reg_config.time_data) > 1:
            # Преобразуем список времени в numpy массив для вычислений
            time_array = np.array(reg_config.time_data)
            # Вычисляем относительное время от начала измерений
            time_relative = time_array - time_array[0]  # Относительное время от начала
            
            # Обновляем данные кривой на графике
            curve.setData(time_relative, list(reg_config.data))
            
            # Автоматическая прокрутка (если включена и накопилось достаточно данных)
            if self.auto_scroll_btn.isChecked() and len(reg_config.time_data) > 100:
                # Вычисляем размер окна прокрутки
                window_size = min(self.scroll_window_size, time_relative[-1])
                # Устанавливаем диапазон отображения по X (показываем последние данные)
                plot_widget.setXRange(time_relative[-1] - window_size, time_relative[-1])
    
    def clear_all_plots(self):
        """Очищает все графики и удаляет их из интерфейса"""
        # Удаляем все виджеты из макета (проходим в обратном порядке)
        for i in reversed(range(self.plots_layout.count())):
            # Получаем элемент макета
            child = self.plots_layout.takeAt(i).widget()
            # Если это виджет, удаляем его
            if child:
                child.setParent(None)  # Убираем родителя (удаляем из интерфейса)
        
        # Очищаем словарь кривых
        self.plot_curves.clear()
    
    def reset_all_zoom(self):
        """Сбрасывает масштаб всех графиков к полному диапазону данных"""
        # Множество для отслеживания уже обработанных виджетов
        processed_widgets = set()  # Чтобы не обрабатывать один виджет несколько раз
        
        # Проходим по всем кривым
        for plot_info in self.plot_curves.values():
            plot_widget = plot_info['widget']
            reg_config = plot_info['config']
            
            # Пропускаем уже обработанные виджеты (важно для групповых графиков)
            if id(plot_widget) in processed_widgets:
                continue
            # Добавляем виджет в множество обработанных
            processed_widgets.add(id(plot_widget))
            
            # Если есть данные для отображения
            if len(reg_config.time_data) > 1:
                # Вычисляем относительное время
                time_array = np.array(reg_config.time_data)
                time_relative = time_array - time_array[0]

                plot_widget.autoRange()
                
                # Устанавливаем диапазон отображения на весь период данных
                ##plot_widget.setXRange(time_relative[0], time_relative[-1])
                # Включаем автоматическое масштабирование по Y
                ##plot_widget.enableAutoRange(axis='y')
                # Отключаем автоматическое масштабирование по X (управляем вручную)
                ##plot_widget.disableAutoRange(axis='x')
            else:
                # Если данных нет, устанавливаем стандартный диапазон
                plot_widget.setXRange(0, 1)
                plot_widget.setYRange(0, 1)
    
    def toggle_auto_scroll(self):
        """Переключает режим автоматической прокрутки графиков"""
        # Проверяем состояние кнопки и обновляем текст
        if self.auto_scroll_btn.isChecked():
            self.auto_scroll_btn.setText("Авто-прокрутка: ВКЛ")
            self.set_scroll_window_size(int(self.interval_auto_scroll.value()))
            #self.scroll_window_size = int(self.interval_auto_scroll.value())
        else:
            self.auto_scroll_btn.setText("Авто-прокрутка: ВЫКЛ")
                
    def set_scroll_window_size(self, size: int):
        """Устанавливает размер окна прокрутки в секундах"""
        self.scroll_window_size = size
    
    def get_plot_count(self) -> int:
        """Возвращает количество отдельных графиков (виджетов)"""
        return self.plots_layout.count()
    
    def get_curves_count(self) -> int:
        """Возвращает количество кривых (может быть больше графиков при группировке)"""
        return len(self.plot_curves)
    
    def export_plot_image(self, register_name: str, filename: str) -> bool:
        """Экспортирует график конкретного регистра в файл изображения"""
        # Проверяем существование графика
        if register_name not in self.plot_curves:
            return False
        
        try:
            # Получаем виджет графика
            plot_widget = self.plot_curves[register_name]['widget']
            # Создаем экспортер изображений для данного графика
            exporter = pg.exporters.ImageExporter(plot_widget.plotItem)
            # Экспортируем в файл
            exporter.export(filename)
            return True  # Успешный экспорт
        except Exception as e:
            # В случае ошибки выводим сообщение и возвращаем False
            print(f"Ошибка экспорта графика: {e}")
            return False
    
    def get_plot_statistics(self) -> Dict[str, Dict]:
        """Возвращает статистику по всем графикам (мин, макс, среднее и т.д.)"""
        stats = {}
        
        # Проходим по всем кривым
        for reg_name, plot_info in self.plot_curves.items():
            reg_config = plot_info['config']
            
            # Если есть данные для анализа
            if len(reg_config.data) > 0:
                # Преобразуем данные в numpy массив для статистических вычислений
                data_array = np.array(reg_config.data)
                # Вычисляем статистики
                stats[reg_name] = {
                    'count': len(reg_config.data),  # Количество точек
                    'min': float(np.min(data_array)),  # Минимальное значение
                    'max': float(np.max(data_array)),  # Максимальное значение
                    'mean': float(np.mean(data_array)),  # Среднее значение
                    'std': float(np.std(data_array)),  # Стандартное отклонение
                    'last_value': reg_config.data[-1]  # Последнее значение
                }
            else:
                # Если данных нет, заполняем нулями
                stats[reg_name] = {
                    'count': 0,
                    'min': 0,
                    'max': 0,
                    'mean': 0,
                    'std': 0,
                    'last_value': 0
                }
        
        return stats


class PlotControlWidget(QWidget):
    """Виджет управления графиками - дополнительные элементы управления"""
    
    def __init__(self, plot_manager: PlotManager, parent=None):
        # Вызываем конструктор родительского класса
        super().__init__(parent)
        # Сохраняем ссылку на менеджер графиков
        self.plot_manager = plot_manager
        # Настраиваем интерфейс
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка интерфейса виджета управления"""
        # Создаем основной макет
        layout = QVBoxLayout(self)
        
        # Рамка с настройками для визуального выделения
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)  # Стиль рамки
        frame_layout = QHBoxLayout(frame)  # Горизонтальный макет внутри рамки
        
        # Кнопки управления
        # Кнопка очистки данных
        self.clear_btn = QPushButton("Очистить данные")
        self.clear_btn.clicked.connect(self.clear_data)
        
        # Кнопка экспорта графиков
        self.export_btn = QPushButton("Экспорт графиков")
        self.export_btn.clicked.connect(self.export_plots)
        
        # Кнопка показа статистики
        self.stats_btn = QPushButton("Показать статистику")
        self.stats_btn.clicked.connect(self.show_statistics)
        
        # Добавляем кнопки в макет рамки
        frame_layout.addWidget(self.clear_btn)
        frame_layout.addWidget(self.export_btn)
        frame_layout.addWidget(self.stats_btn)
        # Добавляем растягивающийся элемент для выравнивания кнопок
        frame_layout.addStretch()
        
        # Добавляем рамку в основной макет
        layout.addWidget(frame)
    
    def clear_data(self):
        """Очищает данные графиков"""
        # Здесь нужно очистить данные в регистрах
        # Это должно делаться через основное приложение
        # TODO: Реализация очистки данных
        pass
    
    def export_plots(self):
        """Экспортирует графики в файлы"""
        # TODO: Реализация экспорта графиков
        pass
    
    def show_statistics(self):
        """Показывает статистику по графикам"""
        # Получаем статистику от менеджера графиков
        stats = self.plot_manager.get_plot_statistics()
        # Временная реализация - вывод в консоль
        print("Статистика графиков:", stats)  # Временная реализация