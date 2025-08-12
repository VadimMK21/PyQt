"""Приложение на PyQt5 для анализа CSV:
- загрузка файла, автоматическое определение типов столбцов (число/время);
- выбор X и нескольких Y для отрисовки графиков в pyqtgraph (включая лог-шкалу Y);
- интерактивное выделение диапазона (LinearRegionItem) с подсчетом статистик;
- создание/показ/сохранение срезов данных по диапазону X;
- сохранение изображения графика.

Интерфейс состоит из панели управления (слева) и области графика (справа).
"""

# Импортируем системный модуль для работы с аргументами командной строки и завершения приложения
import sys
# Импортируем pandas для работы с табличными данными (CSV)
import pandas as pd
# Импортируем numpy для численных вычислений
import numpy as np
# Импортируем все необходимые виджеты PyQt5 для создания интерфейса
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QFileDialog, QComboBox, QListWidget,
                            QAbstractItemView, QLabel, QSpinBox, QGroupBox, QGridLayout,
                            QMessageBox, QCheckBox, QSlider, QDoubleSpinBox, QDateTimeEdit)
# Импортируем базовые классы Qt и сигналы для обработки событий
from PyQt5.QtCore import Qt, pyqtSignal, QDateTime
# Импортируем pyqtgraph для создания быстрых интерактивных графиков
import pyqtgraph as pg
# Импортируем конкретные классы pyqtgraph для графика и выделения области
from pyqtgraph import PlotWidget, LinearRegionItem
# Импортируем модуль для работы с путями файлов
import os
# Импортируем datetime для работы со временем
from datetime import datetime
# Включаем сглаживание линий в pyqtgraph для лучшего качества отображения
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
        # Вызываем конструктор родительского класса QMainWindow
        super().__init__()
        # Инициализируем переменную для хранения основного DataFrame с загруженными данными
        self.df = None
        # Инициализируем переменную для хранения отфильтрованного среза данных
        self.current_slice = None
        # Создаем список для хранения названий столбцов с датами/временем
        self.datetime_columns = []
        # Создаем список для хранения названий столбцов с числовыми данными
        self.numeric_columns = []
        # Инициализируем переменную для хранения объекта LinearRegionItem (область выделения на графике)
        self.linear_region = None
        # Флаг, показывающий активен ли в данный момент режим выделения области
        self.region_active = False
        # Вызываем метод для создания пользовательского интерфейса
        self.init_ui()
        
    def init_ui(self):
        """Создаёт и раскладывает элементы интерфейса окна."""
        # Устанавливаем заголовок главного окна приложения
        self.setWindowTitle('CSV Graph Analyzer')
        # Устанавливаем позицию и размер окна (x=100, y=100, ширина=1400, высота=800)
        self.setGeometry(100, 100, 1400, 800)
        
        # Создаем центральный виджет - основной контейнер для всех элементов интерфейса
        central_widget = QWidget()
        # Устанавливаем созданный виджет как центральный элемент главного окна
        self.setCentralWidget(central_widget)
        # Создаем горизонтальный layout для размещения панели управления и графика рядом
        main_layout = QHBoxLayout(central_widget)
        
        # Создаем левую панель управления с кнопками и настройками
        control_panel = self.create_control_panel()
        # Добавляем панель управления в layout с весом 1 (займет 1 часть доступного пространства)
        main_layout.addWidget(control_panel, 1)
        
        # Создаем правую панель с графиком
        graph_panel = self.create_graph_panel()
        # Добавляем панель графика в layout с весом 3 (займет 3 части, т.е. будет в 3 раза шире)
        main_layout.addWidget(graph_panel, 3)
        
    def create_control_panel(self):
        """Создаёт левую панель управления: загрузка, выбор осей, срезы, информация."""
        # Создаем виджет-контейнер для всех элементов управления
        control_widget = QWidget()
        # Ограничиваем максимальную ширину панели управления для удобства
        control_widget.setMaximumWidth(400)
        # Создаем вертикальный layout для размещения групп элементов сверху вниз
        layout = QVBoxLayout(control_widget)
        
        # ==================== ГРУППА ЗАГРУЗКИ ФАЙЛА ====================
        # Создаем группу (рамку) для элементов работы с файлами
        file_group = QGroupBox("Файл")
        # Создаем вертикальный layout внутри группы файлов
        file_layout = QVBoxLayout(file_group)
        
        # Создаем кнопку для открытия диалога выбора и загрузки CSV файла
        self.load_btn = QPushButton("Загрузить CSV")
        # Подключаем обработчик события нажатия кнопки к методу загрузки файла
        self.load_btn.clicked.connect(self.load_csv)
        # Добавляем кнопку в layout группы файлов
        file_layout.addWidget(self.load_btn)
        
        # Создаем текстовую метку для отображения имени загруженного файла
        self.file_label = QLabel("Файл не выбран")
        # Добавляем метку в layout группы файлов
        file_layout.addWidget(self.file_label)

        # Создаем кнопку для сохранения текущего графика как изображения
        self.save_plot_btn = QPushButton("Сохранить график")
        # Подключаем обработчик для экспорта изображения графика
        self.save_plot_btn.clicked.connect(self.save_plot_image)
        # Добавляем кнопку в layout группы файлов
        file_layout.addWidget(self.save_plot_btn)
        
        # Добавляем всю группу файлов в основной layout панели управления
        layout.addWidget(file_group)
        
        # ==================== ГРУППА ВЫБОРА ПАРАМЕТРОВ ====================
        # Создаем группу для настройки параметров отображения графика
        params_group = QGroupBox("Параметры для отображения")
        # Создаем вертикальный layout для элементов этой группы
        params_layout = QVBoxLayout(params_group)
        
        # --- Выбор оси X ---
        # Создаем горизонтальный layout для размещения подписи и комбобокса рядом
        x_layout = QHBoxLayout()
        # Добавляем текстовую подпись для выбора оси X
        x_layout.addWidget(QLabel("X-ось:"))
        # Создаем выпадающий список для выбора столбца, который будет использоваться как ось X
        self.x_combo = QComboBox()
        # Подключаем обработчик изменения выбора X-оси для перестроения графика
        self.x_combo.currentTextChanged.connect(self.on_x_changed)
        # Добавляем комбобокс в горизонтальный layout
        x_layout.addWidget(self.x_combo)
        # Добавляем весь горизонтальный layout в вертикальный layout группы
        params_layout.addLayout(x_layout)
        
        # --- Выбор параметров Y (множественный) ---
        # Добавляем текстовую подпись для списка Y-параметров
        params_layout.addWidget(QLabel("Y-параметры:"))
        # Создаем список для выбора множественных столбцов как осей Y
        self.y_list = QListWidget()
        # Устанавливаем режим множественного выбора (можно выбрать несколько элементов)
        self.y_list.setSelectionMode(QAbstractItemView.MultiSelection)
        # Подключаем обработчик изменения выбора для перестроения графика при смене Y-параметров
        self.y_list.itemSelectionChanged.connect(self.update_plot)
        # Добавляем список в layout группы
        params_layout.addWidget(self.y_list)
        
        # --- Чекбокс автомасштабирования ---
        # Создаем чекбокс для включения/выключения автоматического масштабирования графика
        self.autoscale_cb = QCheckBox("Автомасштабирование")
        # По умолчанию включаем автомасштабирование
        self.autoscale_cb.setChecked(True)
        # Подключаем обработчик изменения состояния чекбокса
        self.autoscale_cb.stateChanged.connect(self.update_plot)
        # Добавляем чекбокс в layout группы
        params_layout.addWidget(self.autoscale_cb)

        # --- Чекбокс логарифмической шкалы ---
        # Создаем чекбокс для переключения Y-оси в логарифмический режим
        self.log_y_cb = QCheckBox("Логарифмическая шкала Y")
        # Подключаем специальный обработчик для логарифмической шкалы
        self.log_y_cb.stateChanged.connect(self.on_log_y_changed)
        # Добавляем чекбокс в layout группы
        params_layout.addWidget(self.log_y_cb)

        # --- Кнопка сброса масштаба ---
        # Создаем кнопку для возврата к автоматическому подбору видимого диапазона
        self.reset_zoom_btn = QPushButton("Сбросить масштаб")
        # Подключаем обработчик для автоподбора масштаба
        self.reset_zoom_btn.clicked.connect(self.on_reset_zoom)
        # Добавляем кнопку в layout группы
        params_layout.addWidget(self.reset_zoom_btn)
        
        # Добавляем всю группу параметров в основной layout панели управления
        layout.addWidget(params_group)
        
        # ==================== ГРУППА ИНТЕРАКТИВНОГО СРЕЗА ====================
        # Создаем группу для инструментов интерактивного выделения области на графике
        interactive_group = QGroupBox("Интерактивный срез")
        # Создаем вертикальный layout для элементов этой группы
        interactive_layout = QVBoxLayout(interactive_group)
        
        # Создаем кнопку для включения/выключения инструмента выделения области (LinearRegionItem)
        self.toggle_region_btn = QPushButton("Включить выделение области")
        # Подключаем обработчик переключения режима выделения
        self.toggle_region_btn.clicked.connect(self.toggle_linear_region)
        # По умолчанию кнопка неактивна, активируется только когда есть данные и выбрана ось X
        self.toggle_region_btn.setEnabled(False)
        # Добавляем кнопку в layout группы
        interactive_layout.addWidget(self.toggle_region_btn)
        
        # Создаем кнопку для создания среза данных на основе выделенной на графике области
        self.create_slice_from_region_btn = QPushButton("Создать срез из выделенной области")
        # Подключаем обработчик создания среза по выделению
        self.create_slice_from_region_btn.clicked.connect(self.create_slice_from_region)
        # По умолчанию кнопка неактивна, активируется только когда область выделена
        self.create_slice_from_region_btn.setEnabled(False)
        # Добавляем кнопку в layout группы
        interactive_layout.addWidget(self.create_slice_from_region_btn)
        
        # Создаем текстовую метку для отображения информации о выделенной области и статистик
        self.region_info_label = QLabel("Область не выделена")
        # Добавляем метку в layout группы
        interactive_layout.addWidget(self.region_info_label)
        
        # Добавляем всю группу интерактивного среза в основной layout панели управления
        layout.addWidget(interactive_group)
        
        # ==================== ГРУППА РУЧНОГО СОЗДАНИЯ СРЕЗА ====================
        # Создаем группу для ручного задания диапазона среза через поля ввода
        slice_group = QGroupBox("Ручное создание среза")
        # Создаем сеточный layout для аккуратного размещения элементов в строках и столбцах
        slice_layout = QGridLayout(slice_group)
        
        # --- Заголовок для диапазона X ---
        # Добавляем подпись в первую строку, занимающую 2 столбца
        slice_layout.addWidget(QLabel("Диапазон X:"), 0, 0, 1, 2)
        
        # --- Контролы для числового диапазона ---
        # Создаем контейнер для элементов ввода числового диапазона
        self.numeric_range_widget = QWidget()
        # Создаем сеточный layout внутри контейнера
        numeric_layout = QGridLayout(self.numeric_range_widget)
        # Убираем отступы для компактности
        numeric_layout.setContentsMargins(0, 0, 0, 0)
        
        # Добавляем подпись "От:" в первую строку, первый столбец
        numeric_layout.addWidget(QLabel("От:"), 0, 0)
        # Создаем поле ввода для нижней границы числового диапазона
        self.x_min_spin = QDoubleSpinBox()
        # Устанавливаем широкий диапазон допустимых значений
        self.x_min_spin.setRange(-999999, 999999)
        # Устанавливаем точность до 3 знаков после запятой
        self.x_min_spin.setDecimals(3)
        # Подключаем обработчик изменения значения для синхронизации с LinearRegionItem
        self.x_min_spin.valueChanged.connect(self.sync_manual_to_region)
        # Добавляем поле в первую строку, второй столбец
        numeric_layout.addWidget(self.x_min_spin, 0, 1)
        
        # Добавляем подпись "До:" во вторую строку, первый столбец
        numeric_layout.addWidget(QLabel("До:"), 1, 0)
        # Создаем поле ввода для верхней границы числового диапазона
        self.x_max_spin = QDoubleSpinBox()
        # Устанавливаем тот же диапазон значений
        self.x_max_spin.setRange(-999999, 999999)
        # Устанавливаем ту же точность
        self.x_max_spin.setDecimals(3)
        # Подключаем тот же обработчик для синхронизации
        self.x_max_spin.valueChanged.connect(self.sync_manual_to_region)
        # Добавляем поле во вторую строку, второй столбец
        numeric_layout.addWidget(self.x_max_spin, 1, 1)
        
        # Добавляем весь контейнер числовых контролов в основной layout группы
        slice_layout.addWidget(self.numeric_range_widget, 1, 0, 1, 2)
        
        # --- Контролы для временного диапазона ---
        # Создаем контейнер для элементов ввода временного диапазона
        self.datetime_range_widget = QWidget()
        # Создаем сеточный layout внутри контейнера
        datetime_layout = QGridLayout(self.datetime_range_widget)
        # Убираем отступы для компактности
        datetime_layout.setContentsMargins(0, 0, 0, 0)
        
        # Добавляем подпись "От:" в первую строку
        datetime_layout.addWidget(QLabel("От:"), 0, 0)
        # Создаем поле выбора даты и времени для нижней границы
        self.x_min_datetime = QDateTimeEdit()
        # Устанавливаем формат отображения даты и времени
        self.x_min_datetime.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        # Включаем всплывающий календарь для удобства выбора даты
        self.x_min_datetime.setCalendarPopup(True)
        # Подключаем обработчик изменения даты/времени для синхронизации
        self.x_min_datetime.dateTimeChanged.connect(self.sync_manual_to_region)
        # Добавляем поле в первую строку, второй столбец
        datetime_layout.addWidget(self.x_min_datetime, 0, 1)
        
        # Добавляем подпись "До:" во вторую строку
        datetime_layout.addWidget(QLabel("До:"), 1, 0)
        # Создаем поле выбора даты и времени для верхней границы
        self.x_max_datetime = QDateTimeEdit()
        # Устанавливаем тот же формат отображения
        self.x_max_datetime.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        # Включаем календарь
        self.x_max_datetime.setCalendarPopup(True)
        # Подключаем тот же обработчик
        self.x_max_datetime.dateTimeChanged.connect(self.sync_manual_to_region)
        # Добавляем поле во вторую строку, второй столбец
        datetime_layout.addWidget(self.x_max_datetime, 1, 1)
        
        # Добавляем контейнер временных контролов в основной layout (изначально скрыт)
        slice_layout.addWidget(self.datetime_range_widget, 1, 0, 1, 2)
        # По умолчанию скрываем временные контролы (показываются только для временных данных)
        self.datetime_range_widget.setVisible(False)
        
        # --- Кнопки для работы со срезом ---
        # Создаем кнопку для создания среза данных по введенному вручную диапазону
        self.create_slice_btn = QPushButton("Создать срез")
        # Подключаем обработчик создания среза
        self.create_slice_btn.clicked.connect(self.create_slice)
        # Добавляем кнопку в третью строку, занимающую 2 столбца
        slice_layout.addWidget(self.create_slice_btn, 2, 0, 1, 2)
        
        # Создаем кнопку для переключения отображения на созданный срез
        self.show_slice_btn = QPushButton("Показать срез")
        # Подключаем обработчик показа среза
        self.show_slice_btn.clicked.connect(self.show_slice)
        # По умолчанию кнопка неактивна (активируется после создания среза)
        self.show_slice_btn.setEnabled(False)
        # Добавляем кнопку в четвертую строку
        slice_layout.addWidget(self.show_slice_btn, 3, 0, 1, 2)
        
        # Создаем кнопку для экспорта созданного среза в CSV файл
        self.save_slice_btn = QPushButton("Сохранить срез")
        # Подключаем обработчик сохранения среза
        self.save_slice_btn.clicked.connect(self.save_slice)
        # По умолчанию кнопка неактивна
        self.save_slice_btn.setEnabled(False)
        # Добавляем кнопку в пятую строку
        slice_layout.addWidget(self.save_slice_btn, 4, 0, 1, 2)
        
        # Создаем кнопку для возврата к отображению всех данных (отмены среза)
        self.show_full_btn = QPushButton("Показать все данные")
        # Подключаем обработчик отмены среза
        self.show_full_btn.clicked.connect(self.show_full_data)
        # Добавляем кнопку в шестую строку
        slice_layout.addWidget(self.show_full_btn, 5, 0, 1, 2)
        
        # Добавляем всю группу среза в основной layout панели управления
        layout.addWidget(slice_group)
        
        # ==================== ГРУППА ИНФОРМАЦИИ О ДАННЫХ ====================
        # Создаем группу для отображения краткой информации о загруженных данных
        info_group = QGroupBox("Информация")
        # Создаем вертикальный layout для элементов группы
        info_layout = QVBoxLayout(info_group)
        
        # Создаем текстовую метку для отображения сводки по текущему DataFrame
        self.info_label = QLabel("Данные не загружены")
        # Добавляем метку в layout группы
        info_layout.addWidget(self.info_label)
        
        # Добавляем группу информации в основной layout панели управления
        layout.addWidget(info_group)
        
        # Добавляем растягивающийся элемент в конец layout для прижатия всех групп к верху
        layout.addStretch()
        # Возвращаем готовый виджет панели управления
        return control_widget
        
    def create_graph_panel(self):
        """Создаёт правую панель с графиком pyqtgraph."""
        # Создаем виджет-контейнер для графической части
        graph_widget = QWidget()
        # Создаем вертикальный layout для размещения графика
        layout = QVBoxLayout(graph_widget)
        
        # Создаем основной виджет для отрисовки графиков с использованием pyqtgraph
        self.plot_widget = PlotWidget()
        # Устанавливаем подпись левой оси (Y-ось)
        self.plot_widget.setLabel('left', 'Y')
        # Устанавливаем подпись нижней оси (X-ось)
        self.plot_widget.setLabel('bottom', 'X')
        # Включаем отображение сетки по обеим осям для удобства чтения графика
        self.plot_widget.showGrid(True, True)
        # Добавляем легенду для различения множественных кривых на графике
        self.plot_widget.addLegend()
        
        # Создаем специальную ось времени для случаев, когда X-параметр является датой/временем
        self.date_axis = pg.DateAxisItem(orientation='bottom')
        
        # Добавляем виджет графика в layout панели
        layout.addWidget(self.plot_widget)
        
        # Возвращаем готовый виджет графической панели
        return graph_widget
    
    def toggle_linear_region(self):
        """Включает/выключает LinearRegionItem на графике для выделения диапазона X."""
        # Проверяем текущее состояние режима выделения области
        if not self.region_active:
            # Если выделение выключено, включаем его
            self.enable_linear_region()
        else:
            # Если выделение включено, выключаем его
            self.disable_linear_region()
    
    def enable_linear_region(self):
        """Добавляет вертикальный LinearRegionItem с начальным диапазоном (средние 50% данных)."""
        # Проверяем, что данные загружены и выбрана ось X
        if self.df is None or self.x_combo.currentText() == "":
            return
        
        # Получаем название столбца, выбранного для оси X
        x_col = self.x_combo.currentText()
        # Определяем источник данных: текущий срез или полный набор данных
        current_df = self.current_slice if self.current_slice is not None else self.df
        
        # Обрабатываем случай временных данных
        if x_col in self.datetime_columns:
            # Получаем колонку с временными данными, исключая пустые значения
            x_data = current_df[x_col].dropna()
            # Если нет данных, выходим из метода
            if len(x_data) == 0:
                return
            # Находим минимальное время и конвертируем в секунды (timestamp)
            x_min = x_data.min().timestamp()
            # Находим максимальное время и конвертируем в секунды
            x_max = x_data.max().timestamp()
            # Вычисляем начальную позицию области выделения (25% от начала диапазона)
            region_min = x_min + (x_max - x_min) * 0.25
            # Вычисляем конечную позицию области выделения (75% от начала диапазона)
            region_max = x_min + (x_max - x_min) * 0.75
        else:
            # Обрабатываем случай числовых данных
            # Получаем колонку с числовыми данными, исключая пустые значения
            x_data = current_df[x_col].dropna()
            # Если нет данных, выходим из метода
            if len(x_data) == 0:
                return
            # Находим минимальное числовое значение
            x_min = float(x_data.min())
            # Находим максимальное числовое значение
            x_max = float(x_data.max())
            # Вычисляем границы начальной области выделения (средние 50% диапазона)
            region_min = x_min + (x_max - x_min) * 0.25
            region_max = x_min + (x_max - x_min) * 0.75
        
        # Создаем объект LinearRegionItem для интерактивного выделения области на графике
        self.linear_region = LinearRegionItem(
            values=[region_min, region_max],  # Начальные границы области
            orientation='vertical',  # Вертикальная ориентация (выделение по оси X)
            brush=pg.mkBrush(color=(100, 100, 255, 50)),  # Полупрозрачная синяя заливка
            pen=pg.mkPen(color='blue', width=2)  # Синяя обводка толщиной 2 пикселя
        )
        
        # Подключаем сигнал изменения области к обработчику для обновления информации
        self.linear_region.sigRegionChanged.connect(self.on_region_changed)
        
        # Добавляем область выделения на график
        self.plot_widget.addItem(self.linear_region)

        # Устанавливаем флаг активности области выделения
        self.region_active = True
        # Изменяем текст кнопки для отражения нового состояния
        self.toggle_region_btn.setText("Выключить выделение области")
        # Активируем кнопку создания среза из области
        self.create_slice_from_region_btn.setEnabled(True)
        
        # Обновляем информацию о выделенной области
        self.update_region_info()
    
    def disable_linear_region(self):
        """Удаляет LinearRegionItem и сбрасывает связанное состояние."""
        # Проверяем, что область выделения существует
        if self.linear_region is not None:
            # Удаляем область выделения с графика
            self.plot_widget.removeItem(self.linear_region)
            # Обнуляем ссылку на объект области
            self.linear_region = None
        
        # Сбрасываем флаг активности области выделения
        self.region_active = False
        # Возвращаем исходный текст кнопки
        self.toggle_region_btn.setText("Включить выделение области")
        # Деактивируем кнопку создания среза из области
        self.create_slice_from_region_btn.setEnabled(False)
        # Сбрасываем информационный текст
        self.region_info_label.setText("Область не выделена")
    
    def on_region_changed(self):
        """Слот: обновляет текстовую информацию при перемещении границ региона."""
        # Вызываем метод обновления информации о регионе
        self.update_region_info()
    
    def update_region_info(self):
        """Показывает границы выделения, число точек и базовую статистику по выбранным Y.

        Также синхронизирует значения с ручными контролами диапазона.
        """
        # Проверяем, что область выделения активна
        if self.linear_region is None or not self.region_active:
            # Если область не активна, показываем соответствующее сообщение
            self.region_info_label.setText("Область не выделена")
            return
        
        # Получаем название столбца для оси X
        x_col = self.x_combo.currentText()
        # Если столбец не выбран, выходим из метода
        if not x_col:
            return
        
        # Получаем текущие границы выделенной области
        region_min, region_max = self.linear_region.getRegion()
        
        # Синхронизируем значения области с полями ручного ввода
        self.sync_region_to_manual_controls(region_min, region_max, x_col)
        
        # Форматируем отображение границ в зависимости от типа данных
        if x_col in self.datetime_columns:
            # Для временных данных: преобразуем timestamp обратно в datetime
            min_dt = pd.to_datetime(region_min, unit='s')
            max_dt = pd.to_datetime(region_max, unit='s')
            # Форматируем текст с датами
            info_text = f"Выделено:\nОт: {min_dt.strftime('%Y-%m-%d %H:%M:%S')}\nДо: {max_dt.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            # Для числовых данных: форматируем с 3 знаками после запятой
            info_text = f"Выделено:\nОт: {region_min:.3f}\nДо: {region_max:.3f}"
        
        # Определяем источник данных для подсчета статистик
        current_df = self.current_slice if self.current_slice is not None else self.df
        # Преобразуем границы области в формат, подходящий для фильтрации данных
        if x_col in self.datetime_columns:
            # Для временных данных: преобразуем из timestamp в datetime
            min_val = pd.to_datetime(region_min, unit='s')
            max_val = pd.to_datetime(region_max, unit='s')
        else:
            # Для числовых данных: используем значения как есть
            min_val = region_min
            max_val = region_max
        
        # Создаем булеву маску для фильтрации строк, попадающих в выделенный диапазон
        mask = (current_df[x_col] >= min_val) & (current_df[x_col] <= max_val)
        # Подсчитываем количество точек в выделенной области
        points_in_region = mask.sum()

        # Добавляем информацию о количестве точек
        info_text += f"\nТочек: {points_in_region}"

        # Добавляем базовую статистику по выбранным Y-параметрам (ограничиваемся первыми 3)
        selected_y = [item.text() for item in self.y_list.selectedItems()][:3]
        # Проходим по каждому выбранному Y-параметру
        for y_col in selected_y:
            # Проверяем, что столбец существует в данных
            if y_col in current_df.columns:
                # Получаем подмножество данных Y-параметра в выделенной области, исключая пустые значения
                subset = current_df.loc[mask, y_col].dropna()
                # Если есть данные для анализа
                if len(subset) > 0:
                    # Вычисляем минимальное значение
                    y_min = float(subset.min())
                    # Вычисляем среднее значение
                    y_mean = float(subset.mean())
                    # Вычисляем максимальное значение
                    y_max = float(subset.max())
                    # Добавляем статистику к информационному тексту
                    info_text += f"\n{y_col}: min={y_min:.3f}, mean={y_mean:.3f}, max={y_max:.3f}"
        # Обновляем текст информационной метки
        self.region_info_label.setText(info_text)
    
    def sync_manual_to_region(self):
        """Обновляет LinearRegionItem при изменении ручных контролов диапазона X."""
        # Проверяем, что режим выделения активен и область существует
        if not self.region_active or self.linear_region is None:
            return
        
        # Получаем название столбца для оси X
        x_col = self.x_combo.currentText()
        # Если столбец не выбран, выходим
        if not x_col:
            return
        
        try:
            # Обрабатываем временные данные
            if x_col in self.datetime_columns:
                # Получаем выбранные даты из виджетов выбора времени
                min_qt = self.x_min_datetime.dateTime()
                max_qt = self.x_max_datetime.dateTime()
                
                # Преобразуем QDateTime в pandas datetime
                min_dt = pd.to_datetime(min_qt.toString('yyyy-MM-dd hh:mm:ss'))
                max_dt = pd.to_datetime(max_qt.toString('yyyy-MM-dd hh:mm:ss'))
                
                # Преобразуем datetime в timestamp для LinearRegionItem
                region_min = min_dt.timestamp()
                region_max = max_dt.timestamp()
                
            elif x_col in self.numeric_columns:
                # Обрабатываем числовые данные: просто получаем значения из полей ввода
                region_min = self.x_min_spin.value()
                region_max = self.x_max_spin.value()
            else:
                # Если тип данных неподдерживаемый, выходим
                return
            
            # Временно отключаем сигнал изменения области, чтобы избежать рекурсивных вызовов
            self.linear_region.sigRegionChanged.disconnect()
            
            # Обновляем границы LinearRegionItem новыми значениями
            self.linear_region.setRegion([region_min, region_max])
            
            # Восстанавливаем подключение сигнала
            self.linear_region.sigRegionChanged.connect(self.on_region_changed)
            
            # Обновляем отображаемую информацию без повторной синхронизации контролов
            self.update_region_info_only()
            
        except Exception as e:
            # В случае ошибки восстанавливаем подключение сигнала
            if self.linear_region is not None:
                try:
                    # Пытаемся переподключить сигнал
                    self.linear_region.sigRegionChanged.connect(self.on_region_changed)
                except:
                    # Игнорируем ошибки переподключения
                    pass
    
    def update_region_info_only(self):
        """Обновляет только текстовую информацию о текущем выделении (без изменения контролов)."""
        # Проверяем, что область выделения активна
        if self.linear_region is None or not self.region_active:
            # Если область не активна, показываем соответствующее сообщение
            self.region_info_label.setText("Область не выделена")
            return
        
        # Получаем название столбца для оси X
        x_col = self.x_combo.currentText()
        # Если столбец не выбран, выходим
        if not x_col:
            return
        
        # Получаем текущие границы выделенной области
        region_min, region_max = self.linear_region.getRegion()
        
        # Форматируем отображение границ в зависимости от типа данных
        if x_col in self.datetime_columns:
            # Для временных данных: преобразуем timestamp в datetime и форматируем
            min_dt = pd.to_datetime(region_min, unit='s')
            max_dt = pd.to_datetime(region_max, unit='s')
            info_text = f"Выделено:\nОт: {min_dt.strftime('%Y-%m-%d %H:%M:%S')}\nДо: {max_dt.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            # Для числовых данных: форматируем с заданной точностью
            info_text = f"Выделено:\nОт: {region_min:.3f}\nДо: {region_max:.3f}"
        
        # Определяем источник данных для анализа
        current_df = self.current_slice if self.current_slice is not None else self.df
        # Преобразуем границы в подходящий формат для фильтрации
        if x_col in self.datetime_columns:
            min_val = pd.to_datetime(region_min, unit='s')
            max_val = pd.to_datetime(region_max, unit='s')
        else:
            min_val = region_min
            max_val = region_max
        
        # Создаем маску для фильтрации данных в выделенном диапазоне
        mask = (current_df[x_col] >= min_val) & (current_df[x_col] <= max_val)
        # Подсчитываем количество точек в области
        points_in_region = mask.sum()
        
        # Добавляем информацию о количестве точек
        info_text += f"\nТочек: {points_in_region}"

        # Добавляем статистику по выбранным Y-параметрам
        selected_y = [item.text() for item in self.y_list.selectedItems()][:3]
        for y_col in selected_y:
            if y_col in current_df.columns:
                # Получаем данные Y-параметра в выделенной области
                subset = current_df.loc[mask, y_col].dropna()
                if len(subset) > 0:
                    # Вычисляем и добавляем статистики
                    y_min = float(subset.min())
                    y_mean = float(subset.mean())
                    y_max = float(subset.max())
                    info_text += f"\n{y_col}: min={y_min:.3f}, mean={y_mean:.3f}, max={y_max:.3f}"
        # Обновляем отображаемый текст
        self.region_info_label.setText(info_text)
    
    def sync_region_to_manual_controls(self, region_min, region_max, x_col):
        """Подставляет значения текущего выделения в ручные контролы диапазона X."""
        # Обрабатываем временные данные
        if x_col in self.datetime_columns:
            # Преобразуем timestamp в datetime объекты pandas
            min_dt = pd.to_datetime(region_min, unit='s')
            max_dt = pd.to_datetime(region_max, unit='s')
            
            # Преобразуем pandas datetime в QDateTime для виджетов Qt
            min_qt = QDateTime.fromString(min_dt.strftime('%Y-%m-%d %H:%M:%S'), 'yyyy-MM-dd hh:mm:ss')
            max_qt = QDateTime.fromString(max_dt.strftime('%Y-%m-%d %H:%M:%S'), 'yyyy-MM-dd hh:mm:ss')
            
            # Устанавливаем значения в виджеты выбора даты/времени
            self.x_min_datetime.setDateTime(min_qt)
            self.x_max_datetime.setDateTime(max_qt)
            
        elif x_col in self.numeric_columns:
            # Для числовых данных: напрямую устанавливаем значения в поля ввода
            self.x_min_spin.setValue(region_min)
            self.x_max_spin.setValue(region_max)
    
    def create_slice_from_region(self):
        """Создаёт DataFrame-срез по текущему выделению LinearRegionItem и включает кнопки показа/сохранения."""
        # Проверяем, что все необходимые условия выполнены
        if self.linear_region is None or not self.region_active or self.df is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала выделите область на графике")
            return
        
        # Получаем название столбца для оси X
        x_col = self.x_combo.currentText()
        if not x_col:
            QMessageBox.warning(self, "Предупреждение", "Выберите параметр для X-оси")
            return
        
        # Получаем текущие границы выделенной области
        region_min, region_max = self.linear_region.getRegion()
        
        # Преобразуем границы в нужный формат в зависимости от типа данных
        if x_col in self.datetime_columns:
            # Для временных данных: преобразуем timestamp обратно в datetime
            x_min = pd.to_datetime(region_min, unit='s')
            x_max = pd.to_datetime(region_max, unit='s')
        else:
            # Для числовых данных: используем значения напрямую
            x_min = region_min
            x_max = region_max
        
        # Проверяем корректность диапазона
        if x_min >= x_max:
            QMessageBox.warning(self, "Предупреждение", "Некорректный диапазон выделения")
            return
        
        # Создаем булеву маску для фильтрации строк по диапазону X
        mask = (self.df[x_col] >= x_min) & (self.df[x_col] <= x_max)
        # Создаем копию отфильтрованных данных
        self.current_slice = self.df[mask].copy()
        
        # Проверяем, что в срезе есть данные
        if len(self.current_slice) == 0:
            QMessageBox.warning(self, "Предупреждение", "В выделенной области нет данных")
            # Сбрасываем срез при отсутствии данных
            self.current_slice = None
            return
        
        # Активируем кнопки для работы со срезом
        self.show_slice_btn.setEnabled(True)
        self.save_slice_btn.setEnabled(True)
        
        # Форматируем текст сообщения в зависимости от типа данных
        if x_col in self.datetime_columns:
            range_text = f"с {x_min.strftime('%Y-%m-%d %H:%M:%S')} по {x_max.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            range_text = f"с {x_min:.3f} по {x_max:.3f}"
            
        # Показываем информационное сообщение о созданном срезе
        QMessageBox.information(self, "Информация", 
                              f"Срез создан из выделенной области ({range_text}): {len(self.current_slice)} строк из {len(self.df)}")
        
        # Автоматически отключаем инструмент выделения области после создания среза
        self.disable_linear_region()
    
    def on_x_changed(self):
        """Перестраивает контролы, график и доступность инструментов при смене столбца X."""
        # Отключаем инструмент выделения области при смене X-параметра
        if self.region_active:
            self.disable_linear_region()
        
        # Обновляем контролы ручного задания диапазона под новый тип данных
        self.update_slice_controls()
        # Перестраиваем график с новым X-параметром
        self.update_plot()
        
        # Активируем кнопку выделения области только если есть данные и выбрана ось X
        self.toggle_region_btn.setEnabled(self.df is not None and self.x_combo.currentText() != "")
        
    def load_csv(self):
        """Открывает диалог выбора файла и загружает CSV с попыткой автоопределения разделителя и кодировки.

        Формирует списки столбцов по типам: числовые и временные, приводит значения.
        """
        # Открываем диалог выбора файла с фильтром для CSV файлов
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите CSV файл", "", "CSV files (*.csv)")
        
        # Если файл был выбран
        if file_path:
            try:
                # Пробуем различные разделители для автоматического определения формата CSV
                separators = [',', ';', '\t']
                # Инициализируем переменную для данных
                self.df = None
                
                # Перебираем возможные разделители
                for sep in separators:
                    try:
                        # Пытаемся загрузить файл с текущим разделителем в кодировке UTF-8
                        df = pd.read_csv(file_path, sep=sep, encoding='utf-8')
                        # Если получили больше одного столбца, считаем формат правильным
                        if len(df.columns) > 1:
                            self.df = df
                            break
                    except:
                        try:
                            # Если UTF-8 не подошла, пробуем Windows-1251
                            df = pd.read_csv(file_path, sep=sep, encoding='cp1251')
                            if len(df.columns) > 1:
                                self.df = df
                                break
                        except:
                            # Если и это не сработало, переходим к следующему разделителю
                            continue
                
                # Если не удалось загрузить ни с одним из разделителей
                if self.df is None:
                    raise Exception("Не удалось определить формат файла")
                
                # Инициализируем списки для хранения типов столбцов
                self.datetime_columns = []
                self.numeric_columns = []
                
                # Проходим по всем столбцам для определения их типов
                for col in self.df.columns:
                    # Получаем данные столбца
                    series = self.df[col]
                    
                    # Проверяем, не является ли столбец уже datetime64
                    if pd.api.types.is_datetime64_any_dtype(series):
                        self.datetime_columns.append(col)
                        continue
                        
                    # Пытаемся преобразовать в числовой формат
                    # Заменяем запятые на точки для европейского формата десятичных чисел
                    s_num = pd.to_numeric(series.astype(str).str.replace(',', '.'), errors='coerce')
                    # Если удалось преобразовать хотя бы часть значений и это не дата
                    if s_num.notna().sum() > 0 and not pd.api.types.is_datetime64_any_dtype(s_num):
                        # Сохраняем преобразованные числовые данные
                        self.df[col] = s_num
                        # Добавляем столбец в список числовых
                        self.numeric_columns.append(col)
                        continue
                        
                    # Пытаемся преобразовать в формат даты/времени
                    s_dt = pd.to_datetime(series, errors='coerce')
                    # Если удалось преобразовать хотя бы часть значений
                    if s_dt.notna().sum() > 0:
                        # Сохраняем преобразованные временные данные
                        self.df[col] = s_dt
                        # Добавляем столбец в список временных
                        self.datetime_columns.append(col)
                        continue
                    
                    # Если столбец не удалось классифицировать, оставляем как есть
                
                # Обновляем отображение имени загруженного файла
                self.file_label.setText(f"Загружен: {os.path.basename(file_path)}")
                # Заполняем списки выбора X и Y параметров
                self.populate_combos()
                # Обновляем информацию о загруженных данных
                self.update_info()
                # Сбрасываем текущий срез
                self.current_slice = None
                
                # Отключаем инструмент выделения области при загрузке нового файла
                if self.region_active:
                    self.disable_linear_region()
                
            except Exception as e:
                # Показываем сообщение об ошибке при неудачной загрузке
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл:\n{str(e)}")
    
    def populate_combos(self):
        """Заполняет списки X и Y после успешной загрузки данных."""
        # Проверяем, что данные загружены
        if self.df is None:
            return
            
        # Очищаем предыдущие значения в элементах управления
        self.x_combo.clear()
        self.y_list.clear()
        
        # Для оси X разрешаем использовать и числовые, и временные столбцы
        x_columns = self.numeric_columns + self.datetime_columns
        
        # Заполняем комбобокс выбора X-параметра
        self.x_combo.addItems(x_columns)
        
        # Для осей Y используем только числовые столбцы
        for col in self.numeric_columns:
            # Добавляем каждый числовой столбец как элемент списка Y-параметров
            self.y_list.addItem(col)
        
        # Если есть доступные столбцы для X, настраиваем контролы среза
        if len(x_columns) > 0:
            self.update_slice_controls()
    
    def update_slice_controls(self):
        """Переключает набор контролов (числовые/временные) и подставляет допустимые диапазоны."""
        # Получаем текущий выбранный столбец для оси X
        x_col = self.x_combo.currentText()
        # Если столбец не выбран или данные не загружены, выходим
        if not x_col or self.df is None:
            return
            
        # Обрабатываем случай временных данных
        if x_col in self.datetime_columns:
            # Скрываем контролы для числовых данных
            self.numeric_range_widget.setVisible(False)
            # Показываем контролы для временных данных
            self.datetime_range_widget.setVisible(True)
            
            # Находим минимальную и максимальную даты в столбце
            min_date = self.df[x_col].min()
            max_date = self.df[x_col].max()
            
            # Устанавливаем начальные значения в виджеты выбора времени
            self.x_min_datetime.setDateTime(QDateTime.fromString(min_date.strftime('%Y-%m-%d %H:%M:%S'), 'yyyy-MM-dd hh:mm:ss'))
            self.x_max_datetime.setDateTime(QDateTime.fromString(max_date.strftime('%Y-%m-%d %H:%M:%S'), 'yyyy-MM-dd hh:mm:ss'))
            
            # Пытаемся ограничить диапазон выбора дат границами данных
            try:
                # Устанавливаем минимальные и максимальные допустимые даты для виджетов
                self.x_min_datetime.setMinimumDateTime(QDateTime.fromString(min_date.strftime('%Y-%m-%d %H:%M:%S'), 'yyyy-MM-dd hh:mm:ss'))
                self.x_min_datetime.setMaximumDateTime(QDateTime.fromString(max_date.strftime('%Y-%m-%d %H:%M:%S'), 'yyyy-MM-dd hh:mm:ss'))
                self.x_max_datetime.setMinimumDateTime(QDateTime.fromString(min_date.strftime('%Y-%m-%d %H:%M:%S'), 'yyyy-MM-dd hh:mm:ss'))
                self.x_max_datetime.setMaximumDateTime(QDateTime.fromString(max_date.strftime('%Y-%m-%d %H:%M:%S'), 'yyyy-MM-dd hh:mm:ss'))
            except Exception:
                # Игнорируем ошибки установки ограничений
                pass
            
        elif x_col in self.numeric_columns:
            # Обрабатываем случай числовых данных
            # Скрываем контролы для временных данных
            self.datetime_range_widget.setVisible(False)
            # Показываем контролы для числовых данных
            self.numeric_range_widget.setVisible(True)
            
            # Находим минимальное и максимальное значения в числовом столбце
            min_val = float(self.df[x_col].min())
            max_val = float(self.df[x_col].max())
            
            # Устанавливаем диапазоны для полей ввода числовых значений
            self.x_min_spin.setRange(min_val, max_val)
            self.x_max_spin.setRange(min_val, max_val)
            # Устанавливаем начальные значения равными границам данных
            self.x_min_spin.setValue(min_val)
            self.x_max_spin.setValue(max_val)
    
    def update_info(self):
        """Обновляет краткую сводку по текущему набору данных (полный или срез)."""
        # Проверяем, что данные загружены
        if self.df is None:
            self.info_label.setText("Данные не загружены")
            return
            
        # Определяем источник данных: срез или полный набор
        current_df = self.current_slice if self.current_slice is not None else self.df
        
        # Формируем информационный текст
        info_text = f"Строк: {len(current_df)}\n"
        info_text += f"Столбцов: {len(current_df.columns)}\n"
        # Указываем, отображается ли срез или все данные
        if self.current_slice is not None:
            info_text += "Показан срез данных"
        else:
            info_text += "Показаны все данные"
            
        # Обновляем информационную метку
        self.info_label.setText(info_text)
    
    def update_plot(self):
        """Перестраивает график с учётом выбранного X и множества Y.

        При необходимости пересоздаёт PlotWidget с временной осью, восстанавливает выделение,
        применяет авто-масштаб и логарифмическую шкалу Y.
        """
        # Проверяем, что данные загружены
        if self.df is None:
            return
            
        # Определяем источник данных для построения графика
        current_df = self.current_slice if self.current_slice is not None else self.df
        
        # Получаем выбранные параметры
        x_col = self.x_combo.currentText()
        selected_items = self.y_list.selectedItems()
        
        # Если не выбраны X или Y параметры, не строим график
        if not x_col or not selected_items:
            return
        
        # Определяем, нужна ли временная ось для X-параметра
        is_datetime_x = x_col in self.datetime_columns
        
        # Сохраняем параметры LinearRegionItem перед очисткой графика
        region_to_restore = None
        # Если область выделения активна, сохраняем её границы для восстановления после перестроения
        if self.linear_region is not None and self.region_active:
            region_to_restore = self.linear_region.getRegion()
        
        # Очищаем график от всех кривых и элементов
        self.plot_widget.clear()
        
        # Проверяем, нужно ли пересоздать график с другим типом оси
        if is_datetime_x:
            # Если X-параметр временной, но текущая нижняя ось не DateAxisItem
            if not isinstance(self.plot_widget.getAxis('bottom'), pg.DateAxisItem):
                # Получаем родительский layout для замены виджета
                layout = self.plot_widget.parent().layout()
                # Удаляем старый виджет из layout
                layout.removeWidget(self.plot_widget)
                # Закрываем старый виджет
                self.plot_widget.close()
                
                # Создаем новый график с временной осью
                self.plot_widget = PlotWidget(axisItems={'bottom': pg.DateAxisItem()})
                # Устанавливаем подписи осей
                self.plot_widget.setLabel('left', 'Y')
                self.plot_widget.setLabel('bottom', 'Время')
                # Включаем сетку
                self.plot_widget.showGrid(True, True)
                # Добавляем легенду
                self.plot_widget.addLegend()
                # Добавляем новый виджет в layout
                layout.addWidget(self.plot_widget)
        else:
            # Если X-параметр числовой, но текущая ось временная
            if isinstance(self.plot_widget.getAxis('bottom'), pg.DateAxisItem):
                # Аналогично пересоздаем график с обычной осью
                layout = self.plot_widget.parent().layout()
                layout.removeWidget(self.plot_widget)
                self.plot_widget.close()
                
                # Создаем обычный график без специальной оси
                self.plot_widget = PlotWidget()
                self.plot_widget.setLabel('left', 'Y')
                self.plot_widget.setLabel('bottom', x_col)
                self.plot_widget.showGrid(True, True)
                self.plot_widget.addLegend()
                layout.addWidget(self.plot_widget)
        
        try:
            # Строим графики для каждого выбранного Y-параметра
            for i, item in enumerate(selected_items):
                # Получаем название Y-параметра
                y_col = item.text()
                # Проверяем, что оба столбца существуют в данных
                if x_col in current_df.columns and y_col in current_df.columns:
                    # Находим индексы строк, где оба значения (X и Y) не являются NaN
                    common_idx = current_df[[x_col, y_col]].dropna().index
                    # Получаем данные X и Y только для этих строк
                    x_data = current_df.loc[common_idx, x_col]
                    y_data = current_df.loc[common_idx, y_col]
                    
                    # Если X-параметр временной, преобразуем datetime в timestamp для pyqtgraph
                    if is_datetime_x:
                        x_data = x_data.apply(lambda x: x.timestamp())
                    
                    # Создаем уникальный цвет для каждой кривой и перо для рисования
                    pen = pg.mkPen(pg.intColor(i), width=2)
                    # Добавляем кривую на график
                    item_plot = self.plot_widget.plot(x_data.to_numpy(), y_data.to_numpy(), 
                                                    pen=pen, name=y_col, symbol=None, symbolSize=4)
                    try:
                        # Пытаемся включить оптимизации отображения для больших наборов данных
                        item_plot.setClipToView(True)  # Обрезка невидимых частей
                        item_plot.setDownsampling(auto=True, method='peak')  # Автоматическое прореживание
                    except Exception:
                        # Игнорируем ошибки оптимизации, если они не поддерживаются
                        pass
            
            # Восстанавливаем LinearRegionItem если он был активен до перестроения
            if region_to_restore is not None and self.region_active:
                # Создаем новый LinearRegionItem с сохраненными границами
                self.linear_region = LinearRegionItem(
                    values=region_to_restore,
                    orientation='vertical',
                    brush=pg.mkBrush(color=(100, 100, 255, 50)),
                    pen=pg.mkPen(color='blue', width=2)
                )
                # Подключаем обработчик изменения области
                self.linear_region.sigRegionChanged.connect(self.on_region_changed)
                # Добавляем область на новый график
                self.plot_widget.addItem(self.linear_region)
                # Обновляем информацию о восстановленной области
                self.update_region_info()
            
            # Обновляем подпись нижней оси для числовых данных
            if not is_datetime_x:
                self.plot_widget.setLabel('bottom', x_col)
                
            # Применяем автомасштабирование если включено
            if self.autoscale_cb.isChecked():
                self.plot_widget.autoRange()

            # Применяем логарифмическую шкалу Y, если она включена
            try:
                self.plot_widget.setLogMode(y=self.log_y_cb.isChecked())
            except Exception:
                # Игнорируем ошибки применения логарифмического режима
                pass
                
        except Exception as e:
            # Показываем предупреждение при ошибке построения графика
            QMessageBox.warning(self, "Предупреждение", f"Ошибка при построении графика:\n{str(e)}")
    
    def create_slice(self):
        """Создаёт срез по введённому вручную диапазону (числовому/временному) и показывает результат."""
        # Проверяем, что данные загружены
        if self.df is None:
            return
            
        # Получаем выбранный X-параметр
        x_col = self.x_combo.currentText()
        if not x_col:
            QMessageBox.warning(self, "Предупреждение", "Выберите параметр для X-оси")
            return
        
        # Определяем тип среза в зависимости от типа X-столбца
        if x_col in self.datetime_columns:
            # Обрабатываем временной срез
            # Получаем выбранные даты из виджетов
            x_min_qt = self.x_min_datetime.dateTime()
            x_max_qt = self.x_max_datetime.dateTime()
            
            # Преобразуем QDateTime в pandas datetime
            x_min = pd.to_datetime(x_min_qt.toString('yyyy-MM-dd hh:mm:ss'))
            x_max = pd.to_datetime(x_max_qt.toString('yyyy-MM-dd hh:mm:ss'))
            
        elif x_col in self.numeric_columns:
            # Обрабатываем числовой срез
            # Получаем значения из полей ввода
            x_min = self.x_min_spin.value()
            x_max = self.x_max_spin.value()
        else:
            # Неподдерживаемый тип данных
            QMessageBox.warning(self, "Предупреждение", "Неподдерживаемый тип данных для создания среза")
            return
        
        # Проверяем корректность диапазона
        if x_min >= x_max:
            QMessageBox.warning(self, "Предупреждение", "Минимальное значение должно быть меньше максимального")
            return
        
        # Создаем булеву маску для фильтрации строк по заданному диапазону X
        mask = (self.df[x_col] >= x_min) & (self.df[x_col] <= x_max)
        # Создаем копию отфильтрованных данных
        self.current_slice = self.df[mask].copy()
        
        # Проверяем, что в срезе есть данные
        if len(self.current_slice) == 0:
            QMessageBox.warning(self, "Предупреждение", "В указанном диапазоне нет данных")
            # Сбрасываем срез если данных нет
            self.current_slice = None
            return
        
        # Активируем кнопки работы со срезом
        self.show_slice_btn.setEnabled(True)
        self.save_slice_btn.setEnabled(True)
        
        # Форматируем сообщение в зависимости от типа данных
        if x_col in self.datetime_columns:
            range_text = f"с {x_min.strftime('%Y-%m-%d %H:%M:%S')} по {x_max.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            range_text = f"с {x_min} по {x_max}"
            
        # Показываем информационное сообщение о созданном срезе
        QMessageBox.information(self, "Информация", 
                              f"Срез создан ({range_text}): {len(self.current_slice)} строк из {len(self.df)}")
    
    def show_slice(self):
        """Переключает отображение на текущий срез (если создан)."""
        # Если срез существует, обновляем график и информацию
        if self.current_slice is not None:
            self.update_plot()  # Перестраиваем график с данными среза
            self.update_info()  # Обновляем информационную панель
    
    def show_full_data(self):
        """Отменяет срез и отображает полный набор данных."""
        # Сбрасываем текущий срез
        self.current_slice = None
        # Перестраиваем график с полными данными
        self.update_plot()
        # Обновляем информационную панель
        self.update_info()
    
    def save_slice(self):
        """Сохраняет текущий срез в CSV через диалог выбора пути."""
        # Проверяем, что срез существует
        if self.current_slice is None:
            QMessageBox.warning(self, "Предупреждение", "Сначала создайте срез")
            return
        
        # Открываем диалог сохранения файла
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить срез", "slice.csv", "CSV files (*.csv)")
        
        # Если путь выбран, сохраняем файл
        if file_path:
            try:
                # Сохраняем срез в CSV без индексов строк в кодировке UTF-8
                self.current_slice.to_csv(file_path, index=False, encoding='utf-8')
                # Показываем сообщение об успехе
                QMessageBox.information(self, "Успех", f"Срез сохранен в {file_path}")
            except Exception as e:
                # Показываем сообщение об ошибке
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")

    def on_log_y_changed(self):
        """Слот: включает/выключает логарифмическую шкалу Y."""
        try:
            # Переключаем логарифмический режим для Y-оси
            self.plot_widget.setLogMode(y=self.log_y_cb.isChecked())
        except Exception:
            # Игнорируем ошибки переключения режима
            pass

    def on_reset_zoom(self):
        """Слот: сбрасывает масштаб графика (autoRange)."""
        try:
            # Автоматически подбираем масштаб для отображения всех данных
            self.plot_widget.autoRange()
        except Exception:
            # Игнорируем ошибки автомасштабирования
            pass

    def save_plot_image(self):
        """Сохраняет видимую область графика как изображение (PNG/JPEG)."""
        # Открываем диалог сохранения изображения с поддержкой разных форматов
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить график", "plot.png", "PNG (*.png);;JPEG (*.jpg *.jpeg)")
        # Если путь не выбран, выходим
        if not file_path:
            return
        try:
            # Создаем снимок (скриншот) виджета графика
            pixmap = self.plot_widget.grab()
            # Пытаемся сохранить изображение
            if not pixmap.save(file_path):
                raise Exception("Не удалось сохранить изображение")
            # Показываем сообщение об успешном сохранении
            QMessageBox.information(self, "Успех", f"График сохранен в {file_path}")
        except Exception as e:
            # Показываем сообщение об ошибке сохранения
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить график:\n{str(e)}")

def main():
    """Точка входа: создаёт QApplication, окно и запускает цикл событий."""
    # Создаем объект приложения Qt, передавая аргументы командной строки
    app = QApplication(sys.argv)
    # Создаем экземпляр главного окна приложения
    window = CSVGraphAnalyzer()
    # Показываем окно на экране
    window.show()
    # Запускаем главный цикл обработки событий Qt и завершаем программу с его кодом возврата
    sys.exit(app.exec_())

# Проверяем, что скрипт запущен напрямую (не импортирован как модуль)
if __name__ == '__main__':
    # Вызываем главную функцию
    main()