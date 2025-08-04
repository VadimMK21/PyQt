import sys
import pandas as pd
import pyqtgraph as pg
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                           QWidget, QPushButton, QFileDialog, QListWidget, 
                           QListWidgetItem, QLabel, QDateTimeEdit, QMessageBox,
                           QCheckBox, QSplitter, QGroupBox, QScrollArea)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont
import numpy as np
from datetime import datetime
import os

# Настройка pyqtgraph для работы с PyQt5
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

class CSVGraphAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.df = None
        self.time_column = None
        self.numeric_columns = []
        self.plot_items = {}
        self.colors = ['r', 'g', 'b', 'c', 'm', 'y', 'w', 'orange', 'purple', 'brown']
        
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('CSV График Анализатор')
        self.setGeometry(100, 100, 1400, 800)
        
        # Главный виджет
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Основной layout
        main_layout = QHBoxLayout(main_widget)
        
        # Создаем сплиттер для разделения панели управления и графика
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Левая панель управления
        control_panel = self.create_control_panel()
        splitter.addWidget(control_panel)
        
        # Правая панель с графиком
        plot_panel = self.create_plot_panel()
        splitter.addWidget(plot_panel)
        
        # Устанавливаем пропорции
        splitter.setSizes([300, 1100])
        
    def create_control_panel(self):
        """Создает панель управления"""
        panel = QWidget()
        panel.setMaximumWidth(350)
        panel.setMinimumWidth(300)
        
        layout = QVBoxLayout(panel)
        
        # Кнопка загрузки файла
        self.load_btn = QPushButton('Загрузить CSV файл')
        self.load_btn.clicked.connect(self.load_csv)
        self.load_btn.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.load_btn)
        
        # Информация о файле
        self.file_info = QLabel('Файл не загружен')
        self.file_info.setWordWrap(True)
        layout.addWidget(self.file_info)
        
        # Группа выбора параметров
        params_group = QGroupBox("Параметры для отображения")
        params_layout = QVBoxLayout(params_group)
        
        # Скроллируемая область для чекбоксов
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(200)
        
        self.params_widget = QWidget()
        self.params_layout = QVBoxLayout(self.params_widget)
        scroll.setWidget(self.params_widget)
        
        params_layout.addWidget(scroll)
        layout.addWidget(params_group)
        
        # Группа выбора временного среза
        slice_group = QGroupBox("Выбор временного среза")
        slice_layout = QVBoxLayout(slice_group)
        
        slice_layout.addWidget(QLabel("Начало среза:"))
        self.start_datetime = QDateTimeEdit()
        self.start_datetime.setCalendarPopup(True)
        self.start_datetime.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        slice_layout.addWidget(self.start_datetime)
        
        slice_layout.addWidget(QLabel("Конец среза:"))
        self.end_datetime = QDateTimeEdit()
        self.end_datetime.setCalendarPopup(True)
        self.end_datetime.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        slice_layout.addWidget(self.end_datetime)
        
        # Кнопки для среза
        self.apply_slice_btn = QPushButton('Применить срез к графику')
        self.apply_slice_btn.clicked.connect(self.apply_time_slice)
        self.apply_slice_btn.setEnabled(False)
        slice_layout.addWidget(self.apply_slice_btn)
        
        self.save_slice_btn = QPushButton('Сохранить срез в CSV')
        self.save_slice_btn.clicked.connect(self.save_slice_to_csv)
        self.save_slice_btn.setEnabled(False)
        slice_layout.addWidget(self.save_slice_btn)
        
        layout.addWidget(slice_group)
        
        # Кнопки управления
        self.clear_btn = QPushButton('Очистить график')
        self.clear_btn.clicked.connect(self.clear_plot)
        self.clear_btn.setEnabled(False)
        layout.addWidget(self.clear_btn)
        
        self.reset_zoom_btn = QPushButton('Сбросить масштаб')
        self.reset_zoom_btn.clicked.connect(self.reset_zoom)
        self.reset_zoom_btn.setEnabled(False)
        layout.addWidget(self.reset_zoom_btn)
        
        layout.addStretch()
        
        return panel
        
    def create_plot_panel(self):
        """Создает панель с графиком"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # График
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('left', 'Значение')
        self.plot_widget.setLabel('bottom', 'Время')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.addLegend()
        
        # Включаем возможность выбора области
        self.plot_widget.setMouseEnabled(x=True, y=True)
        
        layout.addWidget(self.plot_widget)
        
        return panel
        
    def load_csv(self):
        """Загрузка CSV файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Выберите CSV файл', '', 'CSV files (*.csv)'
        )
        
        if file_path:
            try:
                # Читаем CSV файл
                self.df = pd.read_csv(file_path)
                
                # Ищем столбец времени
                self.find_time_column()
                
                if self.time_column is None:
                    QMessageBox.warning(self, 'Предупреждение', 
                                      'Не найден столбец времени в нужном формате!')
                    return
                
                # Конвертируем время
                self.df[self.time_column] = pd.to_datetime(self.df[self.time_column])
                
                # Находим числовые столбцы
                self.numeric_columns = []
                for col in self.df.columns:
                    if col != self.time_column and pd.api.types.is_numeric_dtype(self.df[col]):
                        self.numeric_columns.append(col)
                
                # Обновляем интерфейс
                self.update_file_info(file_path)
                self.create_parameter_checkboxes()
                self.setup_datetime_range()
                self.enable_controls()
                
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Ошибка при загрузке файла:\n{str(e)}')
                
    def find_time_column(self):
        """Поиск столбца времени"""
        for col in self.df.columns:
            if self.df[col].dtype == 'object':
                try:
                    # Пробуем распарсить несколько первых значений
                    sample = self.df[col].dropna().head(5)
                    for value in sample:
                        pd.to_datetime(value, format='%Y-%m-%d %H:%M:%S.%f')
                    self.time_column = col
                    return
                except:
                    continue
        
        # Если не найден точный формат, пробуем автоматическое определение
        for col in self.df.columns:
            if self.df[col].dtype == 'object':
                try:
                    pd.to_datetime(self.df[col].dropna().head(5))
                    self.time_column = col
                    return
                except:
                    continue
                    
    def update_file_info(self, file_path):
        """Обновление информации о файле"""
        filename = os.path.basename(file_path)
        rows, cols = self.df.shape
        info_text = f"Файл: {filename}\n"
        info_text += f"Строк: {rows}, Столбцов: {cols}\n"
        info_text += f"Столбец времени: {self.time_column}\n"
        info_text += f"Числовых параметров: {len(self.numeric_columns)}"
        self.file_info.setText(info_text)
        
    def create_parameter_checkboxes(self):
        """Создание чекбоксов для выбора параметров"""
        # Очищаем предыдущие чекбоксы
        for i in reversed(range(self.params_layout.count())):
            self.params_layout.itemAt(i).widget().setParent(None)
            
        # Создаем новые чекбоксы
        for i, param in enumerate(self.numeric_columns):
            checkbox = QCheckBox(param)
            checkbox.stateChanged.connect(self.update_plot)
            self.params_layout.addWidget(checkbox)
            
    def setup_datetime_range(self):
        """Настройка диапазона дат"""
        if self.time_column and not self.df.empty:
            min_time = self.df[self.time_column].min()
            max_time = self.df[self.time_column].max()
            
            self.start_datetime.setDateTime(QDateTime.fromString(
                min_time.strftime('%Y-%m-%d %H:%M:%S'), 'yyyy-MM-dd hh:mm:ss'
            ))
            self.end_datetime.setDateTime(QDateTime.fromString(
                max_time.strftime('%Y-%m-%d %H:%M:%S'), 'yyyy-MM-dd hh:mm:ss'
            ))
            
    def enable_controls(self):
        """Включение элементов управления"""
        self.apply_slice_btn.setEnabled(True)
        self.save_slice_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.reset_zoom_btn.setEnabled(True)
        
    def update_plot(self):
        """Обновление графика"""
        if self.df is None:
            return
            
        self.plot_widget.clear()
        self.plot_items = {}
        
        # Получаем выбранные параметры
        selected_params = []
        for i in range(self.params_layout.count()):
            checkbox = self.params_layout.itemAt(i).widget()
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                selected_params.append(checkbox.text())
                
        # Строим графики для выбранных параметров
        for i, param in enumerate(selected_params):
            if param in self.df.columns:
                # Конвертируем время в timestamp для pyqtgraph
                x_data = self.df[self.time_column].astype(np.int64) // 10**9
                y_data = self.df[param].values
                
                # Удаляем NaN значения
                mask = ~np.isnan(y_data)
                x_data = x_data[mask]
                y_data = y_data[mask]
                
                if len(x_data) > 0:
                    color = self.colors[i % len(self.colors)]
                    plot_item = self.plot_widget.plot(
                        x_data, y_data, 
                        pen=color, 
                        name=param
                    )
                    self.plot_items[param] = plot_item
                    
        # Настраиваем ось времени
        if selected_params:
            axis = self.plot_widget.getAxis('bottom')
            axis.setTicks([[(timestamp, datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')) 
                          for timestamp in np.linspace(x_data.min(), x_data.max(), 6)]])
                          
    def apply_time_slice(self):
        """Применение временного среза к графику"""
        if self.df is None:
            return
            
        # Получаем выбранный диапазон времени
        start_time = self.start_datetime.dateTime().toPyDateTime()
        end_time = self.end_datetime.dateTime().toPyDateTime()
        
        # Фильтруем данные
        mask = (self.df[self.time_column] >= start_time) & (self.df[self.time_column] <= end_time)
        filtered_df = self.df[mask]
        
        if filtered_df.empty:
            QMessageBox.warning(self, 'Предупреждение', 'В выбранном диапазоне нет данных!')
            return
            
        # Временно сохраняем оригинальные данные
        original_df = self.df.copy()
        self.df = filtered_df
        
        # Обновляем график
        self.update_plot()
        
        # Восстанавливаем оригинальные данные
        self.df = original_df
        
    def save_slice_to_csv(self):
        """Сохранение среза данных в CSV"""
        if self.df is None:
            return
            
        # Получаем выбранный диапазон времени
        start_time = self.start_datetime.dateTime().toPyDateTime()
        end_time = self.end_datetime.dateTime().toPyDateTime()
        
        # Фильтруем данные
        mask = (self.df[self.time_column] >= start_time) & (self.df[self.time_column] <= end_time)
        filtered_df = self.df[mask]
        
        if filtered_df.empty:
            QMessageBox.warning(self, 'Предупреждение', 'В выбранном диапазоне нет данных!')
            return
            
        # Выбираем файл для сохранения
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Сохранить срез данных', 
            f'slice_{start_time.strftime("%Y%m%d_%H%M%S")}_to_{end_time.strftime("%Y%m%d_%H%M%S")}.csv',
            'CSV files (*.csv)'
        )
        
        if file_path:
            try:
                filtered_df.to_csv(file_path, index=False)
                QMessageBox.information(self, 'Успех', f'Срез данных сохранен в:\n{file_path}')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Ошибка при сохранении файла:\n{str(e)}')
                
    def clear_plot(self):
        """Очистка графика"""
        self.plot_widget.clear()
        self.plot_items = {}
        
    def reset_zoom(self):
        """Сброс масштаба"""
        self.plot_widget.autoRange()


def run_app():
    """Функция для запуска приложения"""
    # Создаем QApplication если его еще нет
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
    window = CSVGraphAnalyzer()
    window.show()
    
    # Запускаем event loop
    app.exec_()
    
    return window


def main():
    # Создаем QApplication в самом начале
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
    
    # Создаем и показываем главное окно
    window = CSVGraphAnalyzer()
    window.show()
    
    # Запускаем событийный цикл
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()