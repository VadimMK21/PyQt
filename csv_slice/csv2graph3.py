"""Приложение на PyQt5 для анализа CSV:
- загрузка файла, автоматическое определение типов столбцов (число/время);
- выбор X и нескольких Y для отрисовки графиков в pyqtgraph (включая лог-шкалу Y);
- интерактивное выделение диапазона (LinearRegionItem) с подсчетом статистик;
- создание/показ/сохранение срезов данных по диапазону X;
- сохранение изображения графика.

Интерфейс состоит из панели управления (слева) и области графика (справа).
"""

import sys  # Модуль системных вызовов (запуск QApplication, завершение)
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QFileDialog, QComboBox, QListWidget,
                            QAbstractItemView, QLabel, QSpinBox, QGroupBox, QGridLayout,
                            QMessageBox, QCheckBox, QSlider, QDoubleSpinBox, QDateTimeEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime
import pyqtgraph as pg
from pyqtgraph import PlotWidget, LinearRegionItem
import os
from datetime import datetime
pg.setConfigOptions(antialias=True)

class CSVGraphAnalyzer(QMainWindow):
    """Главное окно приложения анализа CSV.

    Содержит:
    - загрузку файла и отображение информации о данных;
    - выбор столбца X и нескольких столбцов Y;
    - построение графиков (линейные, с временной осью при необходимости);
    - инструменты среза: ручной (числовой/временной) и интерактивный (LinearRegionItem);
    - сохранение среза в CSV и сохранение картинки графика.
    """
    def __init__(self):
        super().__init__()  # Инициализация базового класса QMainWindow
        self.df = None
        self.current_slice = None
        self.datetime_columns = []
        self.numeric_columns = []
        self.linear_region = None
        self.region_active = False
        self.init_ui()  # Построение интерфейса
        
    def init_ui(self):
        """Создаёт и раскладывает элементы интерфейса окна."""
        self.setWindowTitle('CSV Graph Analyzer')
        self.setGeometry(100, 100, 1400, 800)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Левая панель управления
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel, 1)
        
        # Правая панель с графиками
        graph_panel = self.create_graph_panel()
        main_layout.addWidget(graph_panel, 3)
        
    def create_control_panel(self):
        """Создаёт левую панель управления: загрузка, выбор осей, срезы, информация."""
        control_widget = QWidget()
        control_widget.setMaximumWidth(400)
        layout = QVBoxLayout(control_widget)
        
        # Группа загрузки файла
        file_group = QGroupBox("Файл")
        file_layout = QVBoxLayout(file_group)
        
        self.load_btn = QPushButton("Загрузить CSV")  # Кнопка выбора и загрузки файла
        self.load_btn.clicked.connect(self.load_csv)  # Обработчик загрузки
        file_layout.addWidget(self.load_btn)
        
        self.file_label = QLabel("Файл не выбран")
        file_layout.addWidget(self.file_label)

        self.save_plot_btn = QPushButton("Сохранить график")  # Экспорт изображения графика
        self.save_plot_btn.clicked.connect(self.save_plot_image)
        file_layout.addWidget(self.save_plot_btn)
        
        layout.addWidget(file_group)
        
        # Группа выбора параметров
        params_group = QGroupBox("Параметры для отображения")
        params_layout = QVBoxLayout(params_group)
        
        # X-ось
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("X-ось:"))
        self.x_combo = QComboBox()  # Список столбцов для X (числовые и временные)
        self.x_combo.currentTextChanged.connect(self.on_x_changed)  # Перестроение при смене X
        x_layout.addWidget(self.x_combo)
        params_layout.addLayout(x_layout)
        
        # Y-параметры (множественный выбор)
        params_layout.addWidget(QLabel("Y-параметры:"))
        self.y_list = QListWidget()  # Список доступных числовых столбцов для Y
        self.y_list.setSelectionMode(QAbstractItemView.MultiSelection)  # Множественный выбор
        self.y_list.itemSelectionChanged.connect(self.update_plot)  # Перестроение при смене выбора
        params_layout.addWidget(self.y_list)
        
        # Автомасштабирование
        self.autoscale_cb = QCheckBox("Автомасштабирование")  # Включить автоRange графика
        self.autoscale_cb.setChecked(True)
        self.autoscale_cb.stateChanged.connect(self.update_plot)
        params_layout.addWidget(self.autoscale_cb)

        self.log_y_cb = QCheckBox("Логарифмическая шкала Y")  # Логарифм по оси Y
        self.log_y_cb.stateChanged.connect(self.on_log_y_changed)
        params_layout.addWidget(self.log_y_cb)

        self.reset_zoom_btn = QPushButton("Сбросить масштаб")  # Автоподбор видимого диапазона
        self.reset_zoom_btn.clicked.connect(self.on_reset_zoom)
        params_layout.addWidget(self.reset_zoom_btn)
        
        layout.addWidget(params_group)
        
        # Группа интерактивного среза
        interactive_group = QGroupBox("Интерактивный срез")
        interactive_layout = QVBoxLayout(interactive_group)
        
        self.toggle_region_btn = QPushButton("Включить выделение области")  # Переключение LinearRegionItem
        self.toggle_region_btn.clicked.connect(self.toggle_linear_region)
        self.toggle_region_btn.setEnabled(False)  # Активна только когда есть данные и X
        interactive_layout.addWidget(self.toggle_region_btn)
        
        self.create_slice_from_region_btn = QPushButton("Создать срез из выделенной области")  # Маска по выделению
        self.create_slice_from_region_btn.clicked.connect(self.create_slice_from_region)
        self.create_slice_from_region_btn.setEnabled(False)
        interactive_layout.addWidget(self.create_slice_from_region_btn)
        
        # Информация о выделенной области
        self.region_info_label = QLabel("Область не выделена")  # Текст о текущем выделении и статистиках
        interactive_layout.addWidget(self.region_info_label)
        
        layout.addWidget(interactive_group)
        
        # Группа создания среза (ручной ввод)
        slice_group = QGroupBox("Ручное создание среза")
        slice_layout = QGridLayout(slice_group)
        
        # Диапазон по X
        slice_layout.addWidget(QLabel("Диапазон X:"), 0, 0, 1, 2)
        
        # Для числовых данных
        self.numeric_range_widget = QWidget()  # Контролы для числового диапазона X
        numeric_layout = QGridLayout(self.numeric_range_widget)
        numeric_layout.setContentsMargins(0, 0, 0, 0)
        
        numeric_layout.addWidget(QLabel("От:"), 0, 0)
        self.x_min_spin = QDoubleSpinBox()  # Нижняя граница числового диапазона
        self.x_min_spin.setRange(-999999, 999999)
        self.x_min_spin.setDecimals(3)
        self.x_min_spin.valueChanged.connect(self.sync_manual_to_region)
        numeric_layout.addWidget(self.x_min_spin, 0, 1)
        
        numeric_layout.addWidget(QLabel("До:"), 1, 0)
        self.x_max_spin = QDoubleSpinBox()  # Верхняя граница числового диапазона
        self.x_max_spin.setRange(-999999, 999999)
        self.x_max_spin.setDecimals(3)
        self.x_max_spin.valueChanged.connect(self.sync_manual_to_region)
        numeric_layout.addWidget(self.x_max_spin, 1, 1)
        
        slice_layout.addWidget(self.numeric_range_widget, 1, 0, 1, 2)
        
        # Для временных данных
        self.datetime_range_widget = QWidget()  # Контролы для временного диапазона X
        datetime_layout = QGridLayout(self.datetime_range_widget)
        datetime_layout.setContentsMargins(0, 0, 0, 0)
        
        datetime_layout.addWidget(QLabel("От:"), 0, 0)
        self.x_min_datetime = QDateTimeEdit()  # Нижняя граница времени
        self.x_min_datetime.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        self.x_min_datetime.setCalendarPopup(True)
        self.x_min_datetime.dateTimeChanged.connect(self.sync_manual_to_region)
        datetime_layout.addWidget(self.x_min_datetime, 0, 1)
        
        datetime_layout.addWidget(QLabel("До:"), 1, 0)
        self.x_max_datetime = QDateTimeEdit()  # Верхняя граница времени
        self.x_max_datetime.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        self.x_max_datetime.setCalendarPopup(True)
        self.x_max_datetime.dateTimeChanged.connect(self.sync_manual_to_region)
        datetime_layout.addWidget(self.x_max_datetime, 1, 1)
        
        slice_layout.addWidget(self.datetime_range_widget, 1, 0, 1, 2)
        self.datetime_range_widget.setVisible(False)
        
        # Кнопки для работы со срезом
        self.create_slice_btn = QPushButton("Создать срез")  # Создать срез по ручному диапазону
        self.create_slice_btn.clicked.connect(self.create_slice)
        slice_layout.addWidget(self.create_slice_btn, 2, 0, 1, 2)
        
        self.show_slice_btn = QPushButton("Показать срез")  # Перейти к отображению среза
        self.show_slice_btn.clicked.connect(self.show_slice)
        self.show_slice_btn.setEnabled(False)
        slice_layout.addWidget(self.show_slice_btn, 3, 0, 1, 2)
        
        self.save_slice_btn = QPushButton("Сохранить срез")  # Экспорт выделенного среза в CSV
        self.save_slice_btn.clicked.connect(self.save_slice)
        self.save_slice_btn.setEnabled(False)
        slice_layout.addWidget(self.save_slice_btn, 4, 0, 1, 2)
        
        self.show_full_btn = QPushButton("Показать все данные")  # Отменить срез
        self.show_full_btn.clicked.connect(self.show_full_data)
        slice_layout.addWidget(self.show_full_btn, 5, 0, 1, 2)
        
        layout.addWidget(slice_group)
        
        # Информация о данных
        info_group = QGroupBox("Информация")
        info_layout = QVBoxLayout(info_group)
        
        self.info_label = QLabel("Данные не загружены")  # Краткая сводка по текущему DataFrame
        info_layout.addWidget(self.info_label)
        
        layout.addWidget(info_group)
        
        layout.addStretch()
        return control_widget
        
    def create_graph_panel(self):
        """Создаёт правую панель с графиком pyqtgraph."""
        graph_widget = QWidget()
        layout = QVBoxLayout(graph_widget)
        
        # График
        self.plot_widget = PlotWidget()  # Виджет графика (пересоздаётся при временной оси)
        self.plot_widget.setLabel('left', 'Y')
        self.plot_widget.setLabel('bottom', 'X')
        self.plot_widget.showGrid(True, True)
        self.plot_widget.addLegend()
        
        # Настройка временной оси
        self.date_axis = pg.DateAxisItem(orientation='bottom')  # Готовая ось времени (для пересоздания графика)
        
        layout.addWidget(self.plot_widget)
        
        return graph_widget
    
    def toggle_linear_region(self):
        """Включает/выключает LinearRegionItem на графике для выделения диапазона X."""
        if not self.region_active:
            # Включаем выделение области
            self.enable_linear_region()
        else:
            # Выключаем выделение области
            self.disable_linear_region()
    
    def enable_linear_region(self):
        """Добавляет вертикальный LinearRegionItem с начальным диапазоном (средние 50% данных)."""
        if self.df is None or self.x_combo.currentText() == "":
            return
        
        # Получаем диапазон данных для начальной позиции региона
        x_col = self.x_combo.currentText()
        current_df = self.current_slice if self.current_slice is not None else self.df
        
        if x_col in self.datetime_columns:
            # Для временных данных
            x_data = current_df[x_col].dropna()
            if len(x_data) == 0:
                return
            x_min = x_data.min().timestamp()  # В секундах для pyqtgraph
            x_max = x_data.max().timestamp()
            # Начальная область - средние 50% данных
            region_min = x_min + (x_max - x_min) * 0.25
            region_max = x_min + (x_max - x_min) * 0.75
        else:
            # Для числовых данных
            x_data = current_df[x_col].dropna()
            if len(x_data) == 0:
                return
            x_min = float(x_data.min())  # Числовые границы
            x_max = float(x_data.max())
            # Начальная область - средние 50% данных
            region_min = x_min + (x_max - x_min) * 0.25
            region_max = x_min + (x_max - x_min) * 0.75
        
        # Создаем LinearRegionItem
        self.linear_region = LinearRegionItem(
            values=[region_min, region_max],
            orientation='vertical',
            brush=pg.mkBrush(color=(100, 100, 255, 50)),  # Полупрозрачный синий
            pen=pg.mkPen(color='blue', width=2)
        )
        
        # Подключаем сигнал изменения региона
        self.linear_region.sigRegionChanged.connect(self.on_region_changed)  # Обновление инфо при движении ручек
        
        # Добавляем регион на график
        self.plot_widget.addItem(self.linear_region)  # Размещаем на сцене графика

        
        self.region_active = True
        self.toggle_region_btn.setText("Выключить выделение области")
        self.create_slice_from_region_btn.setEnabled(True)
        
        # Обновляем информацию о регионе
        self.update_region_info()
    
    def disable_linear_region(self):
        """Удаляет LinearRegionItem и сбрасывает связанное состояние."""
        if self.linear_region is not None:
            self.plot_widget.removeItem(self.linear_region)
            self.linear_region = None
        
        self.region_active = False
        self.toggle_region_btn.setText("Включить выделение области")
        self.create_slice_from_region_btn.setEnabled(False)
        self.region_info_label.setText("Область не выделена")
    
    def on_region_changed(self):
        """Слот: обновляет текстовую информацию при перемещении границ региона."""
        self.update_region_info()
    
    def update_region_info(self):
        """Показывает границы выделения, число точек и базовую статистику по выбранным Y.

        Также синхронизирует значения с ручными контролами диапазона.
        """
        if self.linear_region is None or not self.region_active:
            self.region_info_label.setText("Область не выделена")
            return
        
        x_col = self.x_combo.currentText()
        if not x_col:
            return
        
        # Получаем границы региона
        region_min, region_max = self.linear_region.getRegion()  # Текущие значения границ
        
        # Синхронизируем с полями ручного задания среза
        self.sync_region_to_manual_controls(region_min, region_max, x_col)
        
        # Форматируем в зависимости от типа данных
        if x_col in self.datetime_columns:
            # Преобразуем timestamp обратно в datetime
            min_dt = pd.to_datetime(region_min, unit='s')
            max_dt = pd.to_datetime(region_max, unit='s')
            info_text = f"Выделено:\nОт: {min_dt.strftime('%Y-%m-%d %H:%M:%S')}\nДо: {max_dt.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            info_text = f"Выделено:\nОт: {region_min:.3f}\nДо: {region_max:.3f}"
        
        # Подсчитываем количество точек в регионе
        current_df = self.current_slice if self.current_slice is not None else self.df  # Источник данных
        if x_col in self.datetime_columns:
            min_val = pd.to_datetime(region_min, unit='s')
            max_val = pd.to_datetime(region_max, unit='s')
        else:
            min_val = region_min
            max_val = region_max
        
        mask = (current_df[x_col] >= min_val) & (current_df[x_col] <= max_val)  # Булева маска диапазона
        points_in_region = mask.sum()

        info_text += f"\nТочек: {points_in_region}"

        # Базовая статистика по выбранным Y (первые 3)
        selected_y = [item.text() for item in self.y_list.selectedItems()][:3]
        for y_col in selected_y:
            if y_col in current_df.columns:
                subset = current_df.loc[mask, y_col].dropna()
                if len(subset) > 0:
                    y_min = float(subset.min())
                    y_mean = float(subset.mean())
                    y_max = float(subset.max())
                    info_text += f"\n{y_col}: min={y_min:.3f}, mean={y_mean:.3f}, max={y_max:.3f}"
        self.region_info_label.setText(info_text)
    
    def sync_manual_to_region(self):
        """Обновляет LinearRegionItem при изменении ручных контролов диапазона X."""
        if not self.region_active or self.linear_region is None:
            return
        
        x_col = self.x_combo.currentText()
        if not x_col:
            return
        
        try:
            if x_col in self.datetime_columns:
                # Для временных данных
                min_qt = self.x_min_datetime.dateTime()
                max_qt = self.x_max_datetime.dateTime()
                
                min_dt = pd.to_datetime(min_qt.toString('yyyy-MM-dd hh:mm:ss'))
                max_dt = pd.to_datetime(max_qt.toString('yyyy-MM-dd hh:mm:ss'))
                
                # Преобразуем в timestamp для LinearRegionItem
                region_min = min_dt.timestamp()
                region_max = max_dt.timestamp()
                
            elif x_col in self.numeric_columns:
                # Для числовых данных
                region_min = self.x_min_spin.value()
                region_max = self.x_max_spin.value()
            else:
                return
            
            # Временно отключаем сигнал, чтобы избежать рекурсии
            self.linear_region.sigRegionChanged.disconnect()
            
            # Обновляем LinearRegionItem
            self.linear_region.setRegion([region_min, region_max])
            
            # Восстанавливаем сигнал
            self.linear_region.sigRegionChanged.connect(self.on_region_changed)
            
            # Обновляем информацию о регионе (без синхронизации обратно)
            self.update_region_info_only()
            
        except Exception as e:
            # В случае ошибки восстанавливаем сигнал
            if self.linear_region is not None:
                try:
                    self.linear_region.sigRegionChanged.connect(self.on_region_changed)
                except:
                    pass
    
    def update_region_info_only(self):
        """Обновляет только текстовую информацию о текущем выделении (без изменения контролов)."""
        if self.linear_region is None or not self.region_active:
            self.region_info_label.setText("Область не выделена")
            return
        
        x_col = self.x_combo.currentText()
        if not x_col:
            return
        
        # Получаем границы региона
        region_min, region_max = self.linear_region.getRegion()
        
        # Форматируем в зависимости от типа данных
        if x_col in self.datetime_columns:
            # Преобразуем timestamp обратно в datetime
            min_dt = pd.to_datetime(region_min, unit='s')
            max_dt = pd.to_datetime(region_max, unit='s')
            info_text = f"Выделено:\nОт: {min_dt.strftime('%Y-%m-%d %H:%M:%S')}\nДо: {max_dt.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            info_text = f"Выделено:\nОт: {region_min:.3f}\nДо: {region_max:.3f}"
        
        # Подсчитываем количество точек в регионе
        current_df = self.current_slice if self.current_slice is not None else self.df
        if x_col in self.datetime_columns:
            min_val = pd.to_datetime(region_min, unit='s')
            max_val = pd.to_datetime(region_max, unit='s')
        else:
            min_val = region_min
            max_val = region_max
        
        mask = (current_df[x_col] >= min_val) & (current_df[x_col] <= max_val)
        points_in_region = mask.sum()
        
        info_text += f"\nТочек: {points_in_region}"

        # Базовая статистика по выбранным Y (первые 3)
        selected_y = [item.text() for item in self.y_list.selectedItems()][:3]
        for y_col in selected_y:
            if y_col in current_df.columns:
                subset = current_df.loc[mask, y_col].dropna()
                if len(subset) > 0:
                    y_min = float(subset.min())
                    y_mean = float(subset.mean())
                    y_max = float(subset.max())
                    info_text += f"\n{y_col}: min={y_min:.3f}, mean={y_mean:.3f}, max={y_max:.3f}"
        self.region_info_label.setText(info_text)
    
    def sync_region_to_manual_controls(self, region_min, region_max, x_col):
        """Подставляет значения текущего выделения в ручные контролы диапазона X."""
        if x_col in self.datetime_columns:
            # Для временных данных
            min_dt = pd.to_datetime(region_min, unit='s')
            max_dt = pd.to_datetime(region_max, unit='s')
            
            # Обновляем QDateTimeEdit виджеты
            min_qt = QDateTime.fromString(min_dt.strftime('%Y-%m-%d %H:%M:%S'), 'yyyy-MM-dd hh:mm:ss')
            max_qt = QDateTime.fromString(max_dt.strftime('%Y-%m-%d %H:%M:%S'), 'yyyy-MM-dd hh:mm:ss')
            
            self.x_min_datetime.setDateTime(min_qt)
            self.x_max_datetime.setDateTime(max_qt)
            
        elif x_col in self.numeric_columns:
            # Для числовых данных
            self.x_min_spin.setValue(region_min)
            self.x_max_spin.setValue(region_max)
    
    def create_slice_from_region(self):
        """Создаёт DataFrame-срез по текущему выделению LinearRegionItem и включает кнопки показа/сохранения."""
        if self.linear_region is None or not self.region_active or self.df is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала выделите область на графике")
            return
        
        x_col = self.x_combo.currentText()
        if not x_col:
            QMessageBox.warning(self, "Предупреждение", "Выберите параметр для X-оси")
            return
        
        # Получаем границы региона
        region_min, region_max = self.linear_region.getRegion()  # Значения в секундах или числах
        
        # Преобразуем границы в нужный формат
        if x_col in self.datetime_columns:
            # Для временных данных преобразуем timestamp обратно в datetime
            x_min = pd.to_datetime(region_min, unit='s')
            x_max = pd.to_datetime(region_max, unit='s')
        else:
            # Для числовых данных используем как есть
            x_min = region_min
            x_max = region_max
        
        if x_min >= x_max:
            QMessageBox.warning(self, "Предупреждение", "Некорректный диапазон выделения")
            return
        
        # Создаем срез
        mask = (self.df[x_col] >= x_min) & (self.df[x_col] <= x_max)  # Фильтрация строк по диапазону
        self.current_slice = self.df[mask].copy()
        
        if len(self.current_slice) == 0:
            QMessageBox.warning(self, "Предупреждение", "В выделенной области нет данных")
            self.current_slice = None
            return
        
        self.show_slice_btn.setEnabled(True)
        self.save_slice_btn.setEnabled(True)
        
        # Форматируем сообщение в зависимости от типа данных
        if x_col in self.datetime_columns:
            range_text = f"с {x_min.strftime('%Y-%m-%d %H:%M:%S')} по {x_max.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            range_text = f"с {x_min:.3f} по {x_max:.3f}"
            
        QMessageBox.information(self, "Информация", 
                              f"Срез создан из выделенной области ({range_text}): {len(self.current_slice)} строк из {len(self.df)}")
        
        # Выключаем выделение области после создания среза
        self.disable_linear_region()  # После создания среза отключаем инструмент выделения
    
    def on_x_changed(self):
        """Перестраивает контролы, график и доступность инструментов при смене столбца X."""
        # Выключаем LinearRegionItem при смене X-параметра
        if self.region_active:
            self.disable_linear_region()
        
        self.update_slice_controls()
        self.update_plot()
        
        # Включаем кнопку LinearRegionItem только если есть данные
        self.toggle_region_btn.setEnabled(self.df is not None and self.x_combo.currentText() != "")
        
    def load_csv(self):
        """Открывает диалог выбора файла и загружает CSV с попыткой автоопределения разделителя и кодировки.

        Формирует списки столбцов по типам: числовые и временные, приводит значения.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите CSV файл", "", "CSV files (*.csv)")
        
        if file_path:
            try:
                # Пытаемся загрузить с разными разделителями
                separators = [',', ';', '\t']
                for sep in separators:  # Пробуем несколько разделителей
                    try:
                        df = pd.read_csv(file_path, sep=sep, encoding='utf-8')  # UTF-8
                        if len(df.columns) > 1:
                            self.df = df
                            break
                    except:
                        try:
                            df = pd.read_csv(file_path, sep=sep, encoding='cp1251')  # Windows-1251
                            if len(df.columns) > 1:
                                self.df = df
                                break
                        except:
                            continue
                
                if self.df is None:
                    raise Exception("Не удалось определить формат файла")
                
                # Преобразуем числовые колонки и ищем временные
                self.datetime_columns = []
                self.numeric_columns = []
                
                for col in self.df.columns:  # Определяем типы столбцов
                    series = self.df[col]
                    # Если уже datetime64
                    if pd.api.types.is_datetime64_any_dtype(series):
                        self.datetime_columns.append(col)
                        continue
                    # Попытка привести к числу
                    s_num = pd.to_numeric(series.astype(str).str.replace(',', '.'), errors='coerce')  # 1,23 -> 1.23
                    if s_num.notna().sum() > 0 and not pd.api.types.is_datetime64_any_dtype(s_num):
                        self.df[col] = s_num
                        self.numeric_columns.append(col)
                        continue
                    # Попытка привести к дате
                    s_dt = pd.to_datetime(series, errors='coerce')
                    if s_dt.notna().sum() > 0:
                        self.df[col] = s_dt
                        self.datetime_columns.append(col)
                        continue
                    # Иначе оставляем как есть
                
                self.file_label.setText(f"Загружен: {os.path.basename(file_path)}")
                self.populate_combos()
                self.update_info()
                self.current_slice = None
                
                # Выключаем LinearRegionItem при загрузке нового файла
                if self.region_active:
                    self.disable_linear_region()
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл:\n{str(e)}")
    
    def populate_combos(self):
        """Заполняет списки X и Y после успешной загрузки данных."""
        if self.df is None:
            return
            
        # Очищаем предыдущие значения
        self.x_combo.clear()
        self.y_list.clear()
        
        # Для X-оси можем использовать и числовые, и временные столбцы
        x_columns = self.numeric_columns + self.datetime_columns  # Разрешаем и числа, и время для X
        
        # Заполняем комбобоксы
        self.x_combo.addItems(x_columns)
        
        # Для Y-оси используем только числовые столбцы
        for col in self.numeric_columns:
            self.y_list.addItem(col)
        
        # Устанавливаем диапазоны для среза
        if len(x_columns) > 0:
            self.update_slice_controls()
    
    def update_slice_controls(self):
        """Переключает набор контролов (числовые/временные) и подставляет допустимые диапазоны."""
        x_col = self.x_combo.currentText()
        if not x_col or self.df is None:
            return
            
        if x_col in self.datetime_columns:
            # Показываем datetime контролы
            self.numeric_range_widget.setVisible(False)
            self.datetime_range_widget.setVisible(True)
            
            # Устанавливаем диапазон дат
            min_date = self.df[x_col].min()
            max_date = self.df[x_col].max()
            
            self.x_min_datetime.setDateTime(QDateTime.fromString(min_date.strftime('%Y-%m-%d %H:%M:%S'), 'yyyy-MM-dd hh:mm:ss'))
            self.x_max_datetime.setDateTime(QDateTime.fromString(max_date.strftime('%Y-%m-%d %H:%M:%S'), 'yyyy-MM-dd hh:mm:ss'))
            # Ограничиваем выбор дат диапазоном
            try:
                self.x_min_datetime.setMinimumDateTime(QDateTime.fromString(min_date.strftime('%Y-%m-%d %H:%M:%S'), 'yyyy-MM-dd hh:mm:ss'))
                self.x_min_datetime.setMaximumDateTime(QDateTime.fromString(max_date.strftime('%Y-%m-%d %H:%M:%S'), 'yyyy-MM-dd hh:mm:ss'))
                self.x_max_datetime.setMinimumDateTime(QDateTime.fromString(min_date.strftime('%Y-%m-%d %H:%M:%S'), 'yyyy-MM-dd hh:mm:ss'))
                self.x_max_datetime.setMaximumDateTime(QDateTime.fromString(max_date.strftime('%Y-%m-%d %H:%M:%S'), 'yyyy-MM-dd hh:mm:ss'))
            except Exception:
                pass
            
        elif x_col in self.numeric_columns:
            # Показываем numeric контролы
            self.datetime_range_widget.setVisible(False)
            self.numeric_range_widget.setVisible(True)
            
            # Устанавливаем диапазон чисел
            min_val = float(self.df[x_col].min())  # Границы для спинбоксов
            max_val = float(self.df[x_col].max())
            
            self.x_min_spin.setRange(min_val, max_val)
            self.x_max_spin.setRange(min_val, max_val)
            self.x_min_spin.setValue(min_val)
            self.x_max_spin.setValue(max_val)
    
    def update_info(self):
        """Обновляет краткую сводку по текущему набору данных (полный или срез)."""
        if self.df is None:
            self.info_label.setText("Данные не загружены")
            return
            
        current_df = self.current_slice if self.current_slice is not None else self.df
        
        info_text = f"Строк: {len(current_df)}\n"
        info_text += f"Столбцов: {len(current_df.columns)}\n"
        if self.current_slice is not None:
            info_text += "Показан срез данных"
        else:
            info_text += "Показаны все данные"
            
        self.info_label.setText(info_text)
    
    def update_plot(self):
        """Перестраивает график с учётом выбранного X и множества Y.

        При необходимости пересоздаёт PlotWidget с временной осью, восстанавливает выделение,
        применяет авто-масштаб и логарифмическую шкалу Y.
        """
        if self.df is None:
            return
            
        current_df = self.current_slice if self.current_slice is not None else self.df
        
        # Получаем выбранные параметры
        x_col = self.x_combo.currentText()
        selected_items = self.y_list.selectedItems()
        
        if not x_col or not selected_items:
            return
        
        # Определяем тип X-оси и пересоздаем график при необходимости
        is_datetime_x = x_col in self.datetime_columns  # Нужна ли ось времени
        
        # Сохраняем LinearRegionItem перед очисткой
        region_to_restore = None
        if self.linear_region is not None and self.region_active:  # Сохраняем диапазон, если активен
            region_to_restore = self.linear_region.getRegion()
        
        # Очищаем график
        self.plot_widget.clear()  # Удаляем кривые/элементы
        
        # Если X-ось временная, используем DateAxisItem
        if is_datetime_x:
            if not isinstance(self.plot_widget.getAxis('bottom'), pg.DateAxisItem):
                # Пересоздаем график с временной осью
                layout = self.plot_widget.parent().layout()  # Контейнер QVBoxLayout
                layout.removeWidget(self.plot_widget)
                self.plot_widget.close()
                
                self.plot_widget = PlotWidget(axisItems={'bottom': pg.DateAxisItem()})  # Новый виджет с осью времени
                self.plot_widget.setLabel('left', 'Y')
                self.plot_widget.setLabel('bottom', 'Время')
                self.plot_widget.showGrid(True, True)
                self.plot_widget.addLegend()
                layout.addWidget(self.plot_widget)
        else:
            if isinstance(self.plot_widget.getAxis('bottom'), pg.DateAxisItem):
                # Пересоздаем график с обычной осью
                layout = self.plot_widget.parent().layout()
                layout.removeWidget(self.plot_widget)
                self.plot_widget.close()
                
                self.plot_widget = PlotWidget()  # Обычный виджет без оси времени
                self.plot_widget.setLabel('left', 'Y')
                self.plot_widget.setLabel('bottom', x_col)
                self.plot_widget.showGrid(True, True)
                self.plot_widget.addLegend()
                layout.addWidget(self.plot_widget)
        
        # Цвета для графиков
        
        try:
            # Строим графики для каждого выбранного Y-параметра
            for i, item in enumerate(selected_items):
                y_col = item.text()
                if x_col in current_df.columns and y_col in current_df.columns:
                    # Находим общие индексы (без NaN)
                    common_idx = current_df[[x_col, y_col]].dropna().index  # Исключаем NaN пары
                    x_data = current_df.loc[common_idx, x_col]
                    y_data = current_df.loc[common_idx, y_col]
                    
                    # Преобразуем datetime в timestamp для pyqtgraph
                    if is_datetime_x:
                        x_data = x_data.apply(lambda x: x.timestamp())  # Перевод в секунды float
                    
                    pen = pg.mkPen(pg.intColor(i), width=2)
                    item_plot = self.plot_widget.plot(x_data.to_numpy(), y_data.to_numpy(), pen=pen, name=y_col, symbol=None, symbolSize=4)
                    try:
                        item_plot.setClipToView(True)
                        item_plot.setDownsampling(auto=True, method='peak')
                    except Exception:
                        pass
            
            # Восстанавливаем LinearRegionItem если он был активен
            if region_to_restore is not None and self.region_active:
                self.linear_region = LinearRegionItem(
                    values=region_to_restore,
                    orientation='vertical',
                    brush=pg.mkBrush(color=(100, 100, 255, 50)),
                    pen=pg.mkPen(color='blue', width=2)
                )
                self.linear_region.sigRegionChanged.connect(self.on_region_changed)
                self.plot_widget.addItem(self.linear_region)
                self.update_region_info()
            
            # Обновляем подписи осей
            if not is_datetime_x:
                self.plot_widget.setLabel('bottom', x_col)
                
            # Автомасштабирование
            if self.autoscale_cb.isChecked():  # Автомасштаб по текущим кривым
                self.plot_widget.autoRange()

            # Применяем логарифмическую шкалу Y, если включена
            try:
                self.plot_widget.setLogMode(y=self.log_y_cb.isChecked())  # Логарифмическая шкала по Y
            except Exception:
                pass
                
        except Exception as e:
            QMessageBox.warning(self, "Предупреждение", f"Ошибка при построении графика:\n{str(e)}")
    
    def create_slice(self):
        """Создаёт срез по введённому вручную диапазону (числовому/временному) и показывает результат."""
        if self.df is None:
            return
            
        x_col = self.x_combo.currentText()
        if not x_col:
            QMessageBox.warning(self, "Предупреждение", "Выберите параметр для X-оси")
            return
        
        # Определяем тип среза по типу X-колонки
        if x_col in self.datetime_columns:
            # Временной срез
            x_min_qt = self.x_min_datetime.dateTime()
            x_max_qt = self.x_max_datetime.dateTime()
            
            x_min = pd.to_datetime(x_min_qt.toString('yyyy-MM-dd hh:mm:ss'))
            x_max = pd.to_datetime(x_max_qt.toString('yyyy-MM-dd hh:mm:ss'))
            
        elif x_col in self.numeric_columns:
            # Числовой срез
            x_min = self.x_min_spin.value()
            x_max = self.x_max_spin.value()
        else:
            QMessageBox.warning(self, "Предупреждение", "Неподдерживаемый тип данных для создания среза")
            return
        
        if x_min >= x_max:
            QMessageBox.warning(self, "Предупреждение", "Минимальное значение должно быть меньше максимального")
            return
        
        # Создаем срез
        mask = (self.df[x_col] >= x_min) & (self.df[x_col] <= x_max)  # Фильтр строк по X
        self.current_slice = self.df[mask].copy()
        
        if len(self.current_slice) == 0:
            QMessageBox.warning(self, "Предупреждение", "В указанном диапазоне нет данных")
            self.current_slice = None
            return
        
        self.show_slice_btn.setEnabled(True)
        self.save_slice_btn.setEnabled(True)
        
        # Форматируем сообщение в зависимости от типа данных
        if x_col in self.datetime_columns:
            range_text = f"с {x_min.strftime('%Y-%m-%d %H:%M:%S')} по {x_max.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            range_text = f"с {x_min} по {x_max}"
            
        QMessageBox.information(self, "Информация", 
                              f"Срез создан ({range_text}): {len(self.current_slice)} строк из {len(self.df)}")
    
    def show_slice(self):
        """Переключает отображение на текущий срез (если создан)."""
        if self.current_slice is not None:
            self.update_plot()
            self.update_info()
    
    def show_full_data(self):
        """Отменяет срез и отображает полный набор данных."""
        self.current_slice = None
        self.update_plot()
        self.update_info()
    
    def save_slice(self):
        """Сохраняет текущий срез в CSV через диалог выбора пути."""
        if self.current_slice is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала создайте срез")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить срез", "slice.csv", "CSV files (*.csv)")
        
        if file_path:
            try:
                self.current_slice.to_csv(file_path, index=False, encoding='utf-8')
                QMessageBox.information(self, "Успех", f"Срез сохранен в {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")

    def on_log_y_changed(self):
        """Слот: включает/выключает логарифмическую шкалу Y."""
        try:
            self.plot_widget.setLogMode(y=self.log_y_cb.isChecked())
        except Exception:
            pass

    def on_reset_zoom(self):
        """Слот: сбрасывает масштаб графика (autoRange)."""
        try:
            self.plot_widget.autoRange()
        except Exception:
            pass

    def save_plot_image(self):
        """Сохраняет видимую область графика как изображение (PNG/JPEG)."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить график", "plot.png", "PNG (*.png);;JPEG (*.jpg *.jpeg)")
        if not file_path:
            return
        try:
            pixmap = self.plot_widget.grab()  # Снимок текущего виджета
            if not pixmap.save(file_path):
                raise Exception("Не удалось сохранить изображение")
            QMessageBox.information(self, "Успех", f"График сохранен в {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить график:\n{str(e)}")

def main():
    """Точка входа: создаёт QApplication, окно и запускает цикл событий."""
    app = QApplication(sys.argv)
    window = CSVGraphAnalyzer()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()