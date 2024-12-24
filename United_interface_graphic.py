import sys
import os
import pandas as pd
import numpy as np
import matplotlib.dates as mdates
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QFileDialog, QLabel, QMessageBox, QGroupBox, QComboBox, QCheckBox, QAction, QSplitter
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT


class TemperaturePlotApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Визуализация температуры")
        self.setFixedSize(1920, 900)

        # меню
        menubar = self.menuBar()
        file_menu = menubar.addMenu('Файл')
        help_menu = menubar.addMenu('Справка')

        open_action = QAction('Открыть', self)
        open_action.triggered.connect(self.load_folder)
        file_menu.addAction(open_action)

        quit_action = QAction('Выйти', self)
        quit_action.triggered.connect(self.quit_app)
        file_menu.addAction(quit_action)

        info_action = QAction('Информация', self)
        info_action.triggered.connect(self.show_info)
        help_menu.addAction(info_action)

        # Основной макет
        main_layout = QHBoxLayout()

        # Левая часть: существующие виджеты
        left_layout = QVBoxLayout()

        # Название
        self.title_label = QLabel("Программный радиотехнический продукт на Python\n"
                                  "для построения высотно-временного распределения\n"
                                  "градиента температуры воздуха\nпо данным MTP-5 (июнь 2019 года)", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 19px; font-weight: bold;")
        left_layout.addWidget(self.title_label)

        # GroupBox импортировать данные
        import_group = QGroupBox("Импортировать данные")
        import_layout = QVBoxLayout()

        self.add_folder_button = QPushButton("Добавить папку данных", self)
        self.add_folder_button.clicked.connect(self.load_folder)
        import_layout.addWidget(self.add_folder_button)

        self.folder_label = QLabel("Папка не выбрана", self)
        self.folder_label.setAlignment(Qt.AlignCenter)
        import_layout.addWidget(self.folder_label)

        import_group.setLayout(import_layout)
        left_layout.addWidget(import_group)

        # GroupBox для выбора файла
        file_group = QGroupBox("Выберите файл")
        file_layout = QVBoxLayout()

        self.file_combo = QComboBox(self)
        self.file_combo.currentIndexChanged.connect(self.update_file_label)
        file_layout.addWidget(self.file_combo)

        self.file_label = QLabel("Файлы не выбраны", self)
        self.file_label.setAlignment(Qt.AlignCenter)
        file_layout.addWidget(self.file_label)

        file_group.setLayout(file_layout)
        left_layout.addWidget(file_group)

        # GroupBox для выбора интервалов
        interval_group = QGroupBox("Настройки интервалов")
        interval_layout = QVBoxLayout()

        # Временной интервал
        time_layout = QVBoxLayout()
        self.time_checkbox = QCheckBox("Включить временной интервал", self)
        self.time_checkbox.setChecked(False)
        self.time_checkbox.toggled.connect(self.toggle_time_interval)
        time_layout.addWidget(self.time_checkbox)

        self.start_time_combo = QComboBox(self)
        self.start_time_combo.addItems([f"{i:02d}:00" for i in range(24)])
        self.start_time_combo.setEnabled(False)
        time_layout.addWidget(QLabel("Время начала:"))
        time_layout.addWidget(self.start_time_combo)

        self.end_time_combo = QComboBox(self)
        self.end_time_combo.addItems([f"{i:02d}:00" for i in range(1, 25)])
        self.end_time_combo.setEnabled(False)
        time_layout.addWidget(QLabel("Время конца:"))
        time_layout.addWidget(self.end_time_combo)

        interval_layout.addLayout(time_layout)

        # Интервал высот
        altitude_layout = QVBoxLayout()
        self.altitude_checkbox = QCheckBox("Включить диапазон высот", self)
        self.altitude_checkbox.setChecked(False)
        self.altitude_checkbox.toggled.connect(self.toggle_altitude_interval)
        altitude_layout.addWidget(self.altitude_checkbox)

        self.start_altitude_combo = QComboBox(self)
        self.start_altitude_combo.addItems([str(i) for i in range(0, 1001, 50)])
        self.start_altitude_combo.setEnabled(False)
        altitude_layout.addWidget(QLabel("Начальная высота (м):"))
        altitude_layout.addWidget(self.start_altitude_combo)

        self.end_altitude_combo = QComboBox(self)
        self.end_altitude_combo.addItems([str(i) for i in range(50, 1001, 50)])
        self.end_altitude_combo.setEnabled(False)
        altitude_layout.addWidget(QLabel("Конечная высота (м):"))
        altitude_layout.addWidget(self.end_altitude_combo)

        interval_layout.addLayout(altitude_layout)

        interval_group.setLayout(interval_layout)
        left_layout.addWidget(interval_group)

        # Кнопки для отображения графиков
        graph_buttons_group = QGroupBox("Просмотр графиков")
        graph_buttons_layout = QVBoxLayout()

        self.contour_graph_button = QPushButton("Показать контурный график", self)
        self.contour_graph_button.clicked.connect(self.show_contour_graph)
        graph_buttons_layout.addWidget(self.contour_graph_button)

        self.line_graph_button = QPushButton("Показать линейный график", self)
        self.line_graph_button.clicked.connect(self.show_line_graph)
        graph_buttons_layout.addWidget(self.line_graph_button)

        graph_buttons_group.setLayout(graph_buttons_layout)
        left_layout.addWidget(graph_buttons_group)

        # Кнопка выхода
        self.quit_button = QPushButton("Выйти из приложения", self)
        self.quit_button.clicked.connect(self.quit_app)
        left_layout.addWidget(self.quit_button)

        # Правая часть: место для графика
        self.canvas = FigureCanvas(Figure(figsize=(30, 20)))
        self.ax = self.canvas.figure.add_subplot(111)

        # Добавлена панель инструментов для манипуляций с графиками.
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        # GroupBox графической части
        graph_group = QGroupBox("График")
        graph_layout = QVBoxLayout()
        graph_layout.addWidget(self.toolbar)
        graph_layout.addWidget(self.canvas)
        graph_group.setLayout(graph_layout)

        # Добавлен разделитель для разделения левого и правого.
        splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)
        splitter.addWidget(graph_group)
        splitter.setSizes([400, 1200])  # Изначальный размер

        # principal layout
        main_layout.addWidget(splitter)

        # центральный виджет
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Переменные для хранения данных
        self.data_file = None
        self.data_folder = None
        self.files_in_folder = []

    def load_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку с данными")
        if folder_path:
            self.data_folder = folder_path
            files = os.listdir(folder_path)
            txt_files = [f for f in files if f.endswith('.txt')]
            if txt_files:
                self.files_in_folder = txt_files
                self.folder_label.setText(f"Папка загружена : {os.path.basename(folder_path)}")
                self.file_combo.clear()
                # Извлечение и форматирование дат из имен файлов
                dates = [f[4:12] for f in txt_files]  # Извлечь ГГГГММДД
                formatted_dates = [f"{date[:4]}-{date[4:6]}-{date[6:]}" for date in dates]  # Formater en AAAA-MM-JJ

                self.file_combo.addItems(formatted_dates)
            else:
                self.folder_label.setText("Текстовые файлы не найдены.")
        else:
            self.folder_label.setText("Папка не выбрана")
            self.file_combo.clear()
            self.file_label.setText("Файл не выбран")

    def update_file_label(self):
        if self.file_combo.currentIndex() >= 0 and self.files_in_folder:
            selected_date = self.file_combo.currentText()
            # Найдите файл, соответствующий выбранной дате
            for file in self.files_in_folder:
                if f"{selected_date.replace('-', '')}" in file:
                    self.data_file = os.path.join(self.data_folder, file)
                    self.file_label.setText(f"Файл загружен : {file}")
                    QMessageBox.information(self, "Файл загружен", f"Выбранный файл : {file}")
                    break
        else:
            self.file_label.setText("Файлы не выбраны.")

    def toggle_time_interval(self):
        is_checked = self.time_checkbox.isChecked()
        self.start_time_combo.setEnabled(is_checked)
        self.end_time_combo.setEnabled(is_checked)

    def toggle_altitude_interval(self):
        is_checked = self.altitude_checkbox.isChecked()
        self.start_altitude_combo.setEnabled(is_checked)
        self.end_altitude_combo.setEnabled(is_checked)

    def plot_graph(self, plot_function, start_time, end_time, start_altitude, end_altitude):
        self.ax.clear()  # Очистить старую диаграмму
        plot_function(self.ax, self.data_file, start_time, end_time, start_altitude, end_altitude)
        self.canvas.draw()

    def show_line_graph(self):
        if not self.data_file:
            QMessageBox.warning(self, "Нет файла", "Выберите файл перед просмотром графика.")
            return

        # Récupérer les valeurs des heures et altitudes
        start_time = int(self.start_time_combo.currentText().split(":")[0]) if self.time_checkbox.isChecked() else 0
        end_time = int(self.end_time_combo.currentText().split(":")[0]) if self.time_checkbox.isChecked() else 24
        start_altitude = int(self.start_altitude_combo.currentText()) if self.altitude_checkbox.isChecked() else 0
        end_altitude = int(self.end_altitude_combo.currentText()) if self.altitude_checkbox.isChecked() else 1000

        # Проверка временных интервалов
        if start_time >= end_time:
            QMessageBox.warning(self, "Ошибка во временном интервале",
                                "Время начала не может быть больше или равно времени конца.")
            return

        # Проверка интервалов высот
        if start_altitude >= end_altitude:
            QMessageBox.warning(self, "Ошибка в интервале высот",
                                "Начальная высота не может быть больше или равна конечной высоте.")
            return

        self.plot_graph(self.plot_line_graph_internal, start_time, end_time, start_altitude, end_altitude)

    def show_contour_graph(self):
        if not self.data_file:
            QMessageBox.warning(self, "Нет файла", "Выберите файл перед просмотром графика.")
            return

        # Получить значения часов и высот
        start_time = int(self.start_time_combo.currentText().split(":")[0]) if self.time_checkbox.isChecked() else 0
        end_time = int(self.end_time_combo.currentText().split(":")[0]) if self.time_checkbox.isChecked() else 24
        start_altitude = int(self.start_altitude_combo.currentText()) if self.altitude_checkbox.isChecked() else 0
        end_altitude = int(self.end_altitude_combo.currentText()) if self.altitude_checkbox.isChecked() else 1000

        # Проверка временных интервалов
        if start_time >= end_time:
            QMessageBox.warning(self, "Ошибка во временном интервале",
                                "Время начала не может быть больше или равно времени конца.")
            return

        # Проверка интервалов высот
        if start_altitude >= end_altitude:
            QMessageBox.warning(self, "Ошибка в интервале высот",
                                "Начальная высота не может быть больше или равна конечной высоте.")
            return

        # Очистить старый график, прежде чем рисовать новый.
        self.ax.clear()
        self.plot_graph(self.plot_contour_graph_internal, start_time, end_time, start_altitude, end_altitude)

    def plot_line_graph_internal(self, ax, data_file, start_time, end_time, start_altitude, end_altitude):
        # Чтение данных из файла в формате CSV.
        # Файл разделен табуляцией (\t), пропускаются первые 26 строк (skiprows=26),
        df = pd.read_csv(data_file, sep="\t", skiprows=26, header=None)
        df.columns = ['Time'] + [f'Temperature_{i}' for i in range(1, df.shape[1])]
        df['Time'] = pd.to_datetime(df['Time'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        df = df.dropna(subset=['Time'])
        df = df[(df['Time'].dt.hour >= start_time) & (df['Time'].dt.hour <= end_time)]
        time = df['Time']
        temperatures = df.iloc[:, 1:].replace(',', '.', regex=True).astype(float)
        altitudes = np.arange(start_altitude, end_altitude + 50, 50)
        for i in range(min(len(altitudes), temperatures.shape[1])):
            ax.plot(time, temperatures.iloc[:, i], label=f"{altitudes[i]} m")
        ax.set_xlabel('Время (чч:мм:сс)')
        ax.set_ylabel('Температура (°C)')
        ax.set_title('Зависимость температуры от времени на разных высотах')
        ax.legend(title='Высоты')
        ax.grid()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

    def plot_contour_graph_internal(self, ax, data_file, start_time, end_time, start_altitude, end_altitude):
        # Чтение данных из файла в формате CSV.
        # Файл разделен табуляцией (\t), пропускаются первые 26 строк (skiprows=26),
        df = pd.read_csv(data_file, sep="\t", skiprows=26, header=None)
        df.columns = ['Time'] + [f'Temperature_{i}' for i in range(1, df.shape[1])]
        df['Time'] = pd.to_datetime(df['Time'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        df = df.dropna(subset=['Time'])
        df = df[(df['Time'].dt.hour >= start_time) & (df['Time'].dt.hour <= end_time)]
        time = df['Time']
        temperatures = df.iloc[:, 1:].replace(',', '.', regex=True).astype(float)
        altitudes = np.arange(start_altitude, end_altitude + 50, 50)
        time_numeric = mdates.date2num(time)
        time_grid, altitude_grid = np.meshgrid(time_numeric, altitudes)
        temperatures_resized = temperatures.iloc[:, :len(altitudes)].T

        # Проверить и удалите предыдущую цветовую панель, если она существует.
        if hasattr(self, 'colorbar') and self.colorbar:
            self.colorbar.remove()

        contour_filled = ax.contourf(time_grid, altitude_grid, temperatures_resized, cmap='coolwarm', levels=100)
        self.colorbar = ax.figure.colorbar(contour_filled, ax=ax, label='Температура (°C)')
        contour_lines = ax.contour(time_grid, altitude_grid, temperatures_resized, colors='black', linewidths=0.5,
                                   levels=10)
        ax.clabel(contour_lines, inline=True, fontsize=8, fmt='%1.1f')
        ax.set_xlabel('Время (чч:мм:сс)')
        ax.set_ylabel('Высота (м)')
        ax.set_title('Температура как функция высоты и времени')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

    def show_info(self):
        QMessageBox.information(self, "Информация",
                                "Программа для анализа температурных данных по высоте и времени.\n"
                                "Выберите папку с данными, затем выберите файл и настройте интервалы.")

    def quit_app(self):
        QApplication.quit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TemperaturePlotApp()
    window.show()
    sys.exit(app.exec_())
