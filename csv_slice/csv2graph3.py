import sys
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QFileDialog, QComboBox, QListWidget,
                            QAbstractItemView, QLabel, QSpinBox, QGroupBox, QGridLayout,
                            QMessageBox, QCheckBox, QSlider, QDoubleSpinBox, QDateTimeEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime
import pyqtgraph as pg
from pyqtgraph import PlotWidget, LinearRegionItem, InfiniteLine
import os
from datetime import datetime

class CSVGraphAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.df = None
        self.current_slice = None
        self.datetime_columns = []
        self.numeric_columns = []
        self.linear_region = None
        self.region_active = False
        self.init_ui()
        
    def init_ui(self):
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
        control_widget = QWidget()
        control_widget.setMaximumWidth(400)
        layout = QVBoxLayout(control_widget)
        
        # Группа загрузки файла
        file_group = QGroupBox("Файл")
        file_layout = QVBoxLayout(file_group)
        
        self.load_btn = QPushButton("Загрузить CSV")
        self.load_btn.clicked.connect(self.load_csv)
        file_layout.addWidget(self.load_btn)
        
        self.file_label = QLabel("Файл не выбран")
        file_layout.addWidget(self.file_label)
        
        layout.addWidget(file_group)
        
        # Группа выбора параметров
        params_group = QGroupBox("Параметры для отображения")
        params_layout = QVBoxLayout(params_group)
        
        # X-ось
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("X-ось:"))
        self.x_combo = QComboBox()
        self.x_combo.currentTextChanged.connect(self.on_x_changed)
        x_layout.addWidget(self.x_combo)
        params_layout.addLayout(x_layout)
        
        # Y-параметры (множественный выбор)
        params_layout.addWidget(QLabel("Y-параметры:"))
        self.y_list = QListWidget()
        self.y_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.y_list.itemSelectionChanged.connect(self.update_plot)
        params_layout.addWidget(self.y_list)
        
        # Автомасштабирование
        self.autoscale_cb = QCheckBox("Автомасштабирование")
        self.autoscale_cb.setChecked(True)
        self.autoscale_cb.stateChanged.connect(self.update_plot)
        params_layout.addWidget(self.autoscale_cb)
        
        layout.addWidget(params_group)
        
        # Группа интерактивного среза
        interactive_group = QGroupBox("Интерактивный срез")
        interactive_layout = QVBoxLayout(interactive_group)
        
        self.toggle_region_btn = QPushButton("Включить выделение области")
        self.toggle_region_btn.clicked.connect(self.toggle_linear_region)
        self.toggle_region_btn.setEnabled(False)
        interactive_layout.addWidget(self.toggle_region_btn)
        
        self.create_slice_from_region_btn = QPushButton("Создать срез из выделенной области")
        self.create_slice_from_region_btn.clicked.connect(self.create_slice_from_region)
        self.create_slice_from_region_btn.setEnabled(False)
        interactive_layout.addWidget(self.create_slice_from_region_btn)
        
        # Информация о выделенной области
        self.region_info_label = QLabel("Область не выделена")
        interactive_layout.addWidget(self.region_info_label)
        
        layout.addWidget(interactive_group)
        
        # Группа создания среза (ручной ввод)
        slice_group = QGroupBox("Ручное создание среза")
        slice_layout = QGridLayout(slice_group)
        
        # Диапазон по X
        slice_layout.addWidget(QLabel("Диапазон X:"), 0, 0, 1, 2)
        
        # Для числовых данных
        self.numeric_range_widget = QWidget()
        numeric_layout = QGridLayout(self.numeric_range_widget)
        numeric_layout.setContentsMargins(0, 0, 0, 0)
        
        numeric_layout.addWidget(QLabel("От:"), 0, 0)
        self.x_min_spin = QDoubleSpinBox()
        self.x_min_spin.setRange(-999999, 999999)
        self.x_min_spin.setDecimals(3)
        self.x_min_spin.valueChanged.connect(self.sync_manual_to_region)
        numeric_layout.addWidget(self.x_min_spin, 0, 1)
        
        numeric_layout.addWidget(QLabel("До:"), 1, 0)
        self.x_max_spin = QDoubleSpinBox()
        self.x_max_spin.setRange(-999999, 999999)
        self.x_max_spin.setDecimals(3)
        self.x_max_spin.valueChanged.connect(self.sync_manual_to_region)
        numeric_layout.addWidget(self.x_max_spin, 1, 1)
        
        slice_layout.addWidget(self.numeric_range_widget, 1, 0, 1, 2)
        
        # Для временных данных
        self.datetime_range_widget = QWidget()
        datetime_layout = QGridLayout(self.datetime_range_widget)
        datetime_layout.setContentsMargins(0, 0, 0, 0)
        
        datetime_layout.addWidget(QLabel("От:"), 0, 0)
        self.x_min_datetime = QDateTimeEdit()
        self.x_min_datetime.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        self.x_min_datetime.setCalendarPopup(True)
        self.x_min_datetime.dateTimeChanged.connect(self.sync_manual_to_region)
        datetime_layout.addWidget(self.x_min_datetime, 0, 1)
        
        datetime_layout.addWidget(QLabel("До:"), 1, 0)
        self.x_max_datetime = QDateTimeEdit()
        self.x_max_datetime.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        self.x_max_datetime.setCalendarPopup(True)
        self.x_max_datetime.dateTimeChanged.connect(self.sync_manual_to_region)
        datetime_layout.addWidget(self.x_max_datetime, 1, 1)
        
        slice_layout.addWidget(self.datetime_range_widget, 1, 0, 1, 2)
        self.datetime_range_widget.setVisible(False)
        
        # Кнопки для работы со срезом
        self.create_slice_btn = QPushButton("Создать срез")
        self.create_slice_btn.clicked.connect(self.create_slice)
        slice_layout.addWidget(self.create_slice_btn, 2, 0, 1, 2)
        
        self.show_slice_btn = QPushButton("Показать срез")
        self.show_slice_btn.clicked.connect(self.show_slice)
        self.show_slice_btn.setEnabled(False)
        slice_layout.addWidget(self.show_slice_btn, 3, 0, 1, 2)
        
        self.save_slice_btn = QPushButton("Сохранить срез")
        self.save_slice_btn.clicked.connect(self.save_slice)
        self.save_slice_btn.setEnabled(False)
        slice_layout.addWidget(self.save_slice_btn, 4, 0, 1, 2)
        
        self.show_full_btn = QPushButton("Показать все данные")
        self.show_full_btn.clicked.connect(self.show_full_data)
        slice_layout.addWidget(self.show_full_btn, 5, 0, 1, 2)
        
        layout.addWidget(slice_group)
        
        # Информация о данных
        info_group = QGroupBox("Информация")
        info_layout = QVBoxLayout(info_group)
        
        self.info_label = QLabel("Данные не загружены")
        info_layout.addWidget(self.info_label)
        
        layout.addWidget(info_group)
        
        layout.addStretch()
        return control_widget
        
    def create_graph_panel(self):
        graph_widget = QWidget()
        layout = QVBoxLayout(graph_widget)
        
        # График
        self.plot_widget = PlotWidget()
        self.plot_widget.setLabel('left', 'Y')
        self.plot_widget.setLabel('bottom', 'X')
        self.plot_widget.showGrid(True, True)
        self.plot_widget.addLegend()
        
        # Настройка временной оси
        self.date_axis = pg.DateAxisItem(orientation='bottom')
        
        layout.addWidget(self.plot_widget)
        
        return graph_widget
    
    def toggle_linear_region(self):
        """Включает/выключает LinearRegionItem"""
        if not self.region_active:
            # Включаем выделение области
            self.enable_linear_region()
        else:
            # Выключаем выделение области
            self.disable_linear_region()
    
    def enable_linear_region(self):
        """Включает LinearRegionItem на графике"""
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
            x_min = x_data.min().timestamp()
            x_max = x_data.max().timestamp()
            # Начальная область - средние 50% данных
            region_min = x_min + (x_max - x_min) * 0.25
            region_max = x_min + (x_max - x_min) * 0.75
        else:
            # Для числовых данных
            x_data = current_df[x_col].dropna()
            if len(x_data) == 0:
                return
            x_min = float(x_data.min())
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
        self.linear_region.sigRegionChanged.connect(self.on_region_changed)

        self.infinite_line = InfiniteLine(angle=90, movable=True)
        self.plot_widget.addItem(self.infinite_line)
        
        # Добавляем регион на график
        self.plot_widget.addItem(self.linear_region)

        
        self.region_active = True
        self.toggle_region_btn.setText("Выключить выделение области")
        self.create_slice_from_region_btn.setEnabled(True)
        
        # Обновляем информацию о регионе
        self.update_region_info()
    
    def disable_linear_region(self):
        """Выключает LinearRegionItem"""
        if self.linear_region is not None:
            self.plot_widget.removeItem(self.linear_region)
            self.linear_region = None
        
        self.region_active = False
        self.toggle_region_btn.setText("Включить выделение области")
        self.create_slice_from_region_btn.setEnabled(False)
        self.region_info_label.setText("Область не выделена")
    
    def on_region_changed(self):
        """Вызывается при изменении LinearRegionItem"""
        self.update_region_info()
    
    def update_region_info(self):
        """Обновляет информацию о выделенной области и синхронизирует с полями ручного среза"""
        if self.linear_region is None or not self.region_active:
            self.region_info_label.setText("Область не выделена")
            return
        
        x_col = self.x_combo.currentText()
        if not x_col:
            return
        
        # Получаем границы региона
        region_min, region_max = self.linear_region.getRegion()
        
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
        self.region_info_label.setText(info_text)
    
    def sync_manual_to_region(self):
        """Синхронизирует поля ручного задания среза с LinearRegionItem"""
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
        """Обновляет только информацию о выделенной области без синхронизации"""
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
        self.region_info_label.setText(info_text)
    
    def sync_region_to_manual_controls(self, region_min, region_max, x_col):
        """Синхронизирует границы LinearRegionItem с полями ручного задания среза"""
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
        """Создает срез данных из выделенной области LinearRegionItem"""
        if self.linear_region is None or not self.region_active or self.df is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала выделите область на графике")
            return
        
        x_col = self.x_combo.currentText()
        if not x_col:
            QMessageBox.warning(self, "Предупреждение", "Выберите параметр для X-оси")
            return
        
        # Получаем границы региона
        region_min, region_max = self.linear_region.getRegion()
        
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
        mask = (self.df[x_col] >= x_min) & (self.df[x_col] <= x_max)
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
        self.disable_linear_region()
    
    def on_x_changed(self):
        """Вызывается при изменении X-параметра"""
        # Выключаем LinearRegionItem при смене X-параметра
        if self.region_active:
            self.disable_linear_region()
        
        self.update_slice_controls()
        self.update_plot()
        
        # Включаем кнопку LinearRegionItem только если есть данные
        self.toggle_region_btn.setEnabled(self.df is not None and self.x_combo.currentText() != "")
        
    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите CSV файл", "", "CSV files (*.csv)")
        
        if file_path:
            try:
                # Пытаемся загрузить с разными разделителями
                separators = [',', ';', '\t']
                for sep in separators:
                    try:
                        df = pd.read_csv(file_path, sep=sep, encoding='utf-8')
                        if len(df.columns) > 1:
                            self.df = df
                            break
                    except:
                        try:
                            df = pd.read_csv(file_path, sep=sep, encoding='cp1251')
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
                
                for col in self.df.columns:
                    if self.df[col].dtype == 'object':
                        # Пытаемся преобразовать в число
                        try:
                            self.df[col] = pd.to_numeric(self.df[col].str.replace(',', '.'))
                            self.numeric_columns.append(col)
                        except:
                            # Пытаемся преобразовать в datetime
                            try:
                                # Пробуем различные форматы времени
                                datetime_formats = [
                                    '%Y-%m-%d %H:%M:%S.%f',
                                    '%Y-%m-%d %H:%M:%S',
                                    '%d.%m.%Y %H:%M:%S',
                                    '%d/%m/%Y %H:%M:%S',
                                    '%Y-%m-%d',
                                    '%d.%m.%Y',
                                    '%d/%m/%Y'
                                ]
                                
                                parsed = False
                                for fmt in datetime_formats:
                                    try:
                                        self.df[col] = pd.to_datetime(self.df[col], format=fmt)
                                        self.datetime_columns.append(col)
                                        parsed = True
                                        break
                                    except:
                                        continue
                                
                                if not parsed:
                                    # Пытаемся автоматическое определение
                                    self.df[col] = pd.to_datetime(self.df[col], infer_datetime_format=True)
                                    self.datetime_columns.append(col)
                                    
                            except:
                                pass
                    else:
                        # Уже числовой столбец
                        self.numeric_columns.append(col)
                
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
        if self.df is None:
            return
            
        # Очищаем предыдущие значения
        self.x_combo.clear()
        self.y_list.clear()
        
        # Для X-оси можем использовать и числовые, и временные столбцы
        x_columns = self.numeric_columns + self.datetime_columns
        
        # Заполняем комбобоксы
        self.x_combo.addItems(x_columns)
        
        # Для Y-оси используем только числовые столбцы
        for col in self.numeric_columns:
            self.y_list.addItem(col)
        
        # Устанавливаем диапазоны для среза
        if len(x_columns) > 0:
            self.update_slice_controls()
    
    def update_slice_controls(self):
        """Обновляет элементы управления срезом в зависимости от типа выбранной X-колонки"""
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
            
        elif x_col in self.numeric_columns:
            # Показываем numeric контролы
            self.datetime_range_widget.setVisible(False)
            self.numeric_range_widget.setVisible(True)
            
            # Устанавливаем диапазон чисел
            min_val = float(self.df[x_col].min())
            max_val = float(self.df[x_col].max())
            
            self.x_min_spin.setRange(min_val, max_val)
            self.x_max_spin.setRange(min_val, max_val)
            self.x_min_spin.setValue(min_val)
            self.x_max_spin.setValue(max_val)
    
    def update_info(self):
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
        if self.df is None:
            return
            
        current_df = self.current_slice if self.current_slice is not None else self.df
        
        # Получаем выбранные параметры
        x_col = self.x_combo.currentText()
        selected_items = self.y_list.selectedItems()
        
        if not x_col or not selected_items:
            return
        
        # Определяем тип X-оси и пересоздаем график при необходимости
        is_datetime_x = x_col in self.datetime_columns
        
        # Сохраняем LinearRegionItem перед очисткой
        region_to_restore = None
        if self.linear_region is not None and self.region_active:
            region_to_restore = self.linear_region.getRegion()
        
        # Очищаем график
        self.plot_widget.clear()
        
        # Если X-ось временная, используем DateAxisItem
        if is_datetime_x:
            if not isinstance(self.plot_widget.getAxis('bottom'), pg.DateAxisItem):
                # Пересоздаем график с временной осью
                layout = self.plot_widget.parent().layout()
                layout.removeWidget(self.plot_widget)
                self.plot_widget.close()
                
                self.plot_widget = PlotWidget(axisItems={'bottom': pg.DateAxisItem()})
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
                
                self.plot_widget = PlotWidget()
                self.plot_widget.setLabel('left', 'Y')
                self.plot_widget.setLabel('bottom', x_col)
                self.plot_widget.showGrid(True, True)
                self.plot_widget.addLegend()
                layout.addWidget(self.plot_widget)
        
        # Цвета для графиков
        colors = ['r', 'g', 'b', 'c', 'm', 'y', 'w']
        
        try:
            # Строим графики для каждого выбранного Y-параметра
            for i, item in enumerate(selected_items):
                y_col = item.text()
                if x_col in current_df.columns and y_col in current_df.columns:
                    # Находим общие индексы (без NaN)
                    common_idx = current_df[[x_col, y_col]].dropna().index
                    x_data = current_df.loc[common_idx, x_col]
                    y_data = current_df.loc[common_idx, y_col]
                    
                    # Преобразуем datetime в timestamp для pyqtgraph
                    if is_datetime_x:
                        x_data = x_data.apply(lambda x: x.timestamp())
                    
                    color = colors[i % len(colors)]
                    self.plot_widget.plot(x_data, y_data, pen=color, name=y_col, symbol=None, symbolSize=4)
            
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
            if self.autoscale_cb.isChecked():
                self.plot_widget.autoRange()
                
        except Exception as e:
            QMessageBox.warning(self, "Предупреждение", f"Ошибка при построении графика:\n{str(e)}")
    
    def create_slice(self):
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
        mask = (self.df[x_col] >= x_min) & (self.df[x_col] <= x_max)
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
        if self.current_slice is not None:
            self.update_plot()
            self.update_info()
    
    def show_full_data(self):
        self.current_slice = None
        self.update_plot()
        self.update_info()
    
    def save_slice(self):
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

def main():
    app = QApplication(sys.argv)
    window = CSVGraphAnalyzer()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()