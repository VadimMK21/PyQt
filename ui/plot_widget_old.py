"""
Модуль для управления графиками
"""
import time
from typing import Dict, List, Optional

import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt

from config.register_config import RegisterConfig


class PlotManager:
    """Менеджер графиков"""
    
    def __init__(self, scroll_window_size: int = 600):
        self.plot_curves = {}  # Словарь кривых: {register_name: plot_info}
        self.scroll_window_size = scroll_window_size
        self.plots_layout = None
        self.scroll_widget = None
        self.main_widget = None
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        self.main_widget = QWidget()
        main_layout = QVBoxLayout(self.main_widget)
        
        # Кнопки управления графиками
        controls_layout = QHBoxLayout()
        
        self.reset_zoom_btn = QPushButton("Сбросить масштаб")
        self.reset_zoom_btn.clicked.connect(self.reset_all_zoom)
        
        self.auto_scroll_btn = QPushButton("Авто-прокрутка: ВКЛ")
        self.auto_scroll_btn.setCheckable(True)
        self.auto_scroll_btn.setChecked(True)
        self.auto_scroll_btn.clicked.connect(self.toggle_auto_scroll)
        
        controls_layout.addWidget(self.reset_zoom_btn)
        controls_layout.addWidget(self.auto_scroll_btn)
        controls_layout.addStretch()
        
        # Скролл для графиков
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.plots_layout = QVBoxLayout(scroll_widget)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.scroll_widget = scroll_widget
        
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(scroll_area)
    
    def get_main_widget(self) -> QWidget:
        """Возвращает главный виджет"""
        return self.main_widget
    
    def create_plots(self, registers: List[RegisterConfig], plot_mode: str = "separate"):
        """Создает графики для регистров"""
        # Очищаем старые графики
        self.clear_all_plots()
        
        if plot_mode == "separate":
            self._create_separate_plots(registers)
        else:
            self._create_grouped_plots(registers)
    
    def _create_separate_plots(self, registers: List[RegisterConfig]):
        """Создает отдельный график для каждого регистра"""
        for reg in registers:
            if reg.enabled:
                # Создаем график
                plot_widget = pg.PlotWidget(
                    title=f"{reg.name} (Slave:{reg.slave_id}, Addr:{reg.address})"
                )
                plot_widget.setLabel('left', 'Значение')
                plot_widget.setLabel('bottom', 'Время (сек)')
                plot_widget.showGrid(x=True, y=True)
                plot_widget.setMinimumHeight(200)
                
                # Настраиваем автоматическое масштабирование
                plot_widget.setAutoVisible(y=True)
                plot_widget.enableAutoRange(axis='y')
                plot_widget.disableAutoRange(axis='x')
                
                # Создаем кривую
                curve = plot_widget.plot(pen=pg.mkPen(color=reg.color, width=2))
                
                # Сохраняем информацию о графике
                self.plot_curves[reg.name] = {
                    'curve': curve,
                    'widget': plot_widget,
                    'config': reg,
                    'type': 'separate'
                }
                
                # Добавляем в layout
                self.plots_layout.addWidget(plot_widget)
    
    def _create_grouped_plots(self, registers: List[RegisterConfig]):
        """Создает график для каждой группы с несколькими кривыми"""
        # Группируем регистры
        groups = {}
        for reg in registers:
            if reg.enabled:
                if reg.plot_group not in groups:
                    groups[reg.plot_group] = []
                groups[reg.plot_group].append(reg)
        
        # Создаем график для каждой группы
        for group_name, group_registers in groups.items():
            if not group_registers:
                continue
            
            # Создаем график группы
            plot_widget = pg.PlotWidget(title=f"Группа: {group_name}")
            plot_widget.setLabel('left', 'Значение')
            plot_widget.setLabel('bottom', 'Время (сек)')
            plot_widget.showGrid(x=True, y=True)
            plot_widget.setMinimumHeight(250)
            
            # Настраиваем автоматическое масштабирование
            plot_widget.setAutoVisible(y=True)
            plot_widget.enableAutoRange(axis='y')
            plot_widget.disableAutoRange(axis='x')
            
            # Добавляем легенду
            plot_widget.addLegend()
            
            # Создаем кривую для каждого регистра в группе
            for reg in group_registers:
                curve = plot_widget.plot(
                    pen=pg.mkPen(color=reg.color, width=2),
                    name=reg.name
                )
                
                # Сохраняем информацию о кривой
                self.plot_curves[reg.name] = {
                    'curve': curve,
                    'widget': plot_widget,
                    'config': reg,
                    'group': group_name,
                    'type': 'grouped'
                }
            
            # Добавляем график в layout
            self.plots_layout.addWidget(plot_widget)
    
    def update_plot(self, register_name: str, value: float, timestamp: str):
        """Обновляет график для регистра"""
        if register_name not in self.plot_curves:
            return
        
        plot_info = self.plot_curves[register_name]
        reg_config = plot_info['config']
        plot_widget = plot_info['widget']
        curve = plot_info['curve']
        
        # Добавляем данные в регистр
        current_time = time.time()
        reg_config.time_data.append(current_time)
        reg_config.data.append(value)
        
        # Обновляем график
        if len(reg_config.time_data) > 1:
            time_array = np.array(reg_config.time_data)
            time_relative = time_array - time_array[0]  # Относительное время от начала
            
            # Обновляем кривую
            curve.setData(time_relative, list(reg_config.data))
            
            # Автоматическая прокрутка (если включена)
            if self.auto_scroll_btn.isChecked() and len(reg_config.time_data) > 100:
                window_size = min(self.scroll_window_size, time_relative[-1])
                plot_widget.setXRange(time_relative[-1] - window_size, time_relative[-1])
    
    def clear_all_plots(self):
        """Очищает все графики"""
        # Удаляем все виджеты из layout
        for i in reversed(range(self.plots_layout.count())):
            child = self.plots_layout.takeAt(i).widget()
            if child:
                child.setParent(None)
        
        # Очищаем словарь кривых
        self.plot_curves.clear()
    
    def reset_all_zoom(self):
        """Сбрасывает масштаб всех графиков"""
        processed_widgets = set()  # Чтобы не обрабатывать один виджет несколько раз
        
        for plot_info in self.plot_curves.values():
            plot_widget = plot_info['widget']
            reg_config = plot_info['config']
            
            # Пропускаем уже обработанные виджеты (для группированных графиков)
            if id(plot_widget) in processed_widgets:
                continue
            processed_widgets.add(id(plot_widget))
            
            if len(reg_config.time_data) > 1:
                time_array = np.array(reg_config.time_data)
                time_relative = time_array - time_array[0]
                
                # Устанавливаем полный диапазон данных
                plot_widget.setXRange(time_relative[0], time_relative[-1])
                plot_widget.enableAutoRange(axis='y')
                plot_widget.disableAutoRange(axis='x')
            else:
                # Если данных нет, устанавливаем стандартный диапазон
                plot_widget.setXRange(0, 1)
                plot_widget.setYRange(0, 1)
    
    def toggle_auto_scroll(self):
        """Переключает режим автоматической прокрутки"""
        if self.auto_scroll_btn.isChecked():
            self.auto_scroll_btn.setText("Авто-прокрутка: ВКЛ")
        else:
            self.auto_scroll_btn.setText("Авто-прокрутка: ВЫКЛ")
    
    def set_scroll_window_size(self, size: int):
        """Устанавливает размер окна прокрутки"""
        self.scroll_window_size = size
    
    def get_plot_count(self) -> int:
        """Возвращает количество графиков"""
        return self.plots_layout.count()
    
    def get_curves_count(self) -> int:
        """Возвращает количество кривых"""
        return len(self.plot_curves)
    
    def export_plot_image(self, register_name: str, filename: str) -> bool:
        """Экспортирует график в изображение"""
        if register_name not in self.plot_curves:
            return False
        
        try:
            plot_widget = self.plot_curves[register_name]['widget']
            exporter = pg.exporters.ImageExporter(plot_widget.plotItem)
            exporter.export(filename)
            return True
        except Exception as e:
            print(f"Ошибка экспорта графика: {e}")
            return False
    
    def get_plot_statistics(self) -> Dict[str, Dict]:
        """Возвращает статистику по графикам"""
        stats = {}
        
        for reg_name, plot_info in self.plot_curves.items():
            reg_config = plot_info['config']
            
            if len(reg_config.data) > 0:
                data_array = np.array(reg_config.data)
                stats[reg_name] = {
                    'count': len(reg_config.data),
                    'min': float(np.min(data_array)),
                    'max': float(np.max(data_array)),
                    'mean': float(np.mean(data_array)),
                    'std': float(np.std(data_array)),
                    'last_value': reg_config.data[-1]
                }
            else:
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
    """Виджет управления графиками"""
    
    def __init__(self, plot_manager: PlotManager, parent=None):
        super().__init__(parent)
        self.plot_manager = plot_manager
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        
        # Рамка с настройками
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        frame_layout = QHBoxLayout(frame)
        
        # Кнопки управления
        self.clear_btn = QPushButton("Очистить данные")
        self.clear_btn.clicked.connect(self.clear_data)
        
        self.export_btn = QPushButton("Экспорт графиков")
        self.export_btn.clicked.connect(self.export_plots)
        
        self.stats_btn = QPushButton("Показать статистику")
        self.stats_btn.clicked.connect(self.show_statistics)
        
        frame_layout.addWidget(self.clear_btn)
        frame_layout.addWidget(self.export_btn)
        frame_layout.addWidget(self.stats_btn)
        frame_layout.addStretch()
        
        layout.addWidget(frame)
    
    def clear_data(self):
        """Очищает данные графиков"""
        # Здесь нужно очистить данные в регистрах
        # Это должно делаться через основное приложение
        pass
    
    def export_plots(self):
        """Экспортирует графики"""
        # Реализация экспорта
        pass
    
    def show_statistics(self):
        """Показывает статистику"""
        stats = self.plot_manager.get_plot_statistics()
        print("Статистика графиков:", stats)  # Временная реализация