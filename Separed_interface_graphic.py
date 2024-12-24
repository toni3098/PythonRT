import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QFileDialog, QLabel, QMessageBox, QGroupBox, QComboBox, QCheckBox, QAction
)
from PyQt5.QtCore import Qt


def plot_line_graph(data_file, start_time, end_time, start_altitude, end_altitude):
    """
    Строит график зависимости температуры от времени
    для разных высот с фильтрацией по временному интервалу и высоте.
    """
    df = pd.read_csv(data_file, sep="\t", skiprows=26, header=None)
    df.columns = ['Time'] + [f'Temperature_{i}' for i in range(1, df.shape[1])]

    # Traitement des données
    df['Time'] = pd.to_datetime(df['Time'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    df = df.dropna(subset=['Time'])
    df = df[(df['Time'].dt.hour >= start_time) & (df['Time'].dt.hour <= end_time)]

    time = df['Time']
    temperatures = df.iloc[:, 1:].replace(',', '.', regex=True).astype(float)

    altitudes = np.arange(start_altitude, end_altitude + 50, 50)  # Intervalle d'altitudes
    plt.figure(figsize=(12, 6))
    for i in range(min(len(altitudes), temperatures.shape[1])):
        plt.plot(time, temperatures.iloc[:, i], label=f"{altitudes[i]} m")

    plt.xlabel('Время (чч:мм:сс)')
    plt.ylabel('Температура (°C)')
    plt.title('Зависимость температуры от времени на разных высотах')
    plt.legend(title='Высоты')
    plt.grid()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gcf().autofmt_xdate()
    plt.show()


def plot_contour_graph(data_file, start_time, end_time, start_altitude, end_altitude):
    """
    Рисует контурный график, показывающий зависимость температуры от высоты и времени
    с фильтрацией по временному интервалу и высоте.
    """
    df = pd.read_csv(data_file, sep="\t", skiprows=26, header=None)
    df.columns = ['Time'] + [f'Temperature_{i}' for i in range(1, df.shape[1])]

    # Обработка данных
    df['Time'] = pd.to_datetime(df['Time'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
    df = df.dropna(subset=['Time'])

    # Фильтрация по временному интервалу
    df = df[(df['Time'].dt.hour >= start_time) & (df['Time'].dt.hour <= end_time)]

    time = df['Time']
    temperatures = df.iloc[:, 1:].replace(',', '.', regex=True).astype(float)

    # Создание диапазона высот
    altitudes = np.arange(start_altitude, end_altitude + 50, 50)

    # Проверка соответствия высот и температурных данных
    if len(altitudes) > temperatures.shape[1]:
        raise ValueError("Диапазон высот больше, чем количество столбцов с температурами.")

    time_numeric = mdates.date2num(time)  # Преобразование времени в числовой формат
    time_grid, altitude_grid = np.meshgrid(time_numeric, altitudes)

    # Настройка размеров температур для согласования с высотами
    temperatures_resized = temperatures.iloc[:, :len(altitudes)].T

    # Построение контурного графика
    plt.figure(figsize=(12, 6))
    contour_filled = plt.contourf(time_grid, altitude_grid, temperatures_resized, cmap='coolwarm', levels=100)
    plt.colorbar(contour_filled, label='Температура (°C)')

    # Добавление черных линий для разделения областей
    contour_lines = plt.contour(time_grid, altitude_grid, temperatures_resized, colors='black', linewidths=0.5, levels=10)
    plt.clabel(contour_lines, inline=True, fontsize=8, fmt='%1.1f')  # Подписываем линии контуров

    plt.xlabel('Время (чч:мм:сс)')
    plt.ylabel('Высота (м)')
    plt.title('Температура как функция высоты и времени')
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gcf().autofmt_xdate()
    plt.grid()
    plt.show()


class TemperaturePlotApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Визуализация температуры")

        # Fixe la taille de la fenêtre
        self.setFixedSize(800, 600)  # Taille fixe pour la fenêtre (largeur 800px, hauteur 600px)

        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('Файл')
        help_menu = menubar.addMenu('Спарвка')

        open_action = QAction('Открыть', self)
        open_action.triggered.connect(self.load_folder)
        file_menu.addAction(open_action)

        quit_action = QAction('Выйти', self)
        quit_action.triggered.connect(self.quit_app)
        file_menu.addAction(quit_action)

        info_action = QAction('Информация', self)
        info_action.triggered.connect(self.show_info)
        help_menu.addAction(info_action)

        # Layout principal
        layout = QVBoxLayout()

        # Label de titre (avec taille et en gras)
        self.title_label = QLabel("Программный радиотехнический продукт на Python\nдля построения высотно-временного распределения\nградиента температуры воздуха\nпо данным MTP-5 (июнь 2019 года)", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 19px; font-weight: bold;")  # Taille et gras
        layout.addWidget(self.title_label)

        # GroupBox pour importer les données
        import_group = QGroupBox("Импортировать данные")
        import_layout = QVBoxLayout()

        self.add_folder_button = QPushButton("Добавить папку данных", self)
        self.add_folder_button.clicked.connect(self.load_folder)
        import_layout.addWidget(self.add_folder_button)

        # Label pour afficher le dossier chargé
        self.folder_label = QLabel("Папка не выбрана", self)
        self.folder_label.setAlignment(Qt.AlignCenter)
        import_layout.addWidget(self.folder_label)

        import_group.setLayout(import_layout)
        layout.addWidget(import_group)

        # GroupBox pour le choix du fichier
        file_group = QGroupBox("Выберите файл")
        file_layout = QVBoxLayout()

        self.file_combo = QComboBox(self)
        self.file_combo.currentIndexChanged.connect(self.update_file_label)
        file_layout.addWidget(self.file_combo)

        self.file_label = QLabel("Файлы не выбраны", self)
        self.file_label.setAlignment(Qt.AlignCenter)
        file_layout.addWidget(self.file_label)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # GroupBox pour le choix de l'intervalle de temps
        time_group = QGroupBox("Выберите временной интервал")
        time_layout = QHBoxLayout()

        self.time_checkbox = QCheckBox("Включить временной интервал-->", self)
        self.time_checkbox.setChecked(False)  # Case désactivée par défaut
        self.time_checkbox.toggled.connect(self.toggle_time_interval)
        time_layout.addWidget(self.time_checkbox)

        self.start_time_combo = QComboBox(self)
        self.start_time_combo.addItems([f"{i:02d}:00" for i in range(24)])
        self.start_time_combo.setCurrentIndex(0)  # Définir l'heure de début par défaut à 00:00
        self.start_time_combo.setEnabled(False)  # Désactivé initialement
        time_layout.addWidget(QLabel("Время начала:"))
        time_layout.addWidget(self.start_time_combo)

        self.end_time_combo = QComboBox(self)
        self.end_time_combo.addItems([f"{i:02d}:00" for i in range(1, 25)])
        self.end_time_combo.setCurrentIndex(0)  # Définir l'heure de fin par défaut à 01:00
        self.end_time_combo.setEnabled(False)  # Désactivé initialement
        time_layout.addWidget(QLabel("Время конца:"))
        time_layout.addWidget(self.end_time_combo)

        time_group.setLayout(time_layout)
        layout.addWidget(time_group)

        # GroupBox pour le choix de l'intervalle d'altitude
        altitude_group = QGroupBox("Выберите интервал высоты")
        altitude_layout = QHBoxLayout()

        self.altitude_checkbox = QCheckBox("Включить диапазон высот-->", self)
        self.altitude_checkbox.setChecked(False)  # Case désactivée par défaut
        self.altitude_checkbox.toggled.connect(self.toggle_altitude_interval)
        altitude_layout.addWidget(self.altitude_checkbox)

        self.start_altitude_combo = QComboBox(self)
        self.start_altitude_combo.addItems([str(i) for i in range(0, 1001, 50)])
        self.start_altitude_combo.setCurrentIndex(0)  # Altitude de départ à 0m
        self.start_altitude_combo.setEnabled(False)  # Désactivé initialement
        altitude_layout.addWidget(QLabel("Начальная высота (м):"))
        altitude_layout.addWidget(self.start_altitude_combo)

        self.end_altitude_combo = QComboBox(self)
        self.end_altitude_combo.addItems([str(i) for i in range(50, 1001, 50)])
        self.end_altitude_combo.setCurrentIndex(len(self.end_altitude_combo) - 1)  # Altitude de fin à 1000m
        self.end_altitude_combo.setEnabled(False)  # Désactivé initialement
        altitude_layout.addWidget(QLabel("Конечная высота (м):"))
        altitude_layout.addWidget(self.end_altitude_combo)

        altitude_group.setLayout(altitude_layout)
        layout.addWidget(altitude_group)

        # GroupBox pour afficher les graphiques
        graph_group = QGroupBox("Просмотр графиков")
        graph_layout = QVBoxLayout()

        self.line_graph_button = QPushButton("Показать линейный график", self)
        self.line_graph_button.clicked.connect(self.show_line_graph)
        graph_layout.addWidget(self.line_graph_button)

        self.contour_graph_button = QPushButton("Показать контурный график", self)
        self.contour_graph_button.clicked.connect(self.show_contour_graph)
        graph_layout.addWidget(self.contour_graph_button)


        graph_group.setLayout(graph_layout)
        layout.addWidget(graph_group)

        # Widget central
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Variables pour stocker le chemin du fichier ou du dossier
        self.data_file = None
        self.data_folder = None
        self.files_in_folder = []

        # Bouton "Quitter"
        self.quit_button = QPushButton("Выйти из приложения", self)
        self.quit_button.clicked.connect(self.quit_app)
        layout.addWidget(self.quit_button)

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

                # Extraire et formater les dates des noms de fichiers
                dates = [f[4:12] for f in txt_files]  # Extraire AAAAMMJJ
                formatted_dates = [f"{date[:4]}-{date[4:6]}-{date[6:]}" for date in dates]  # Formater en AAAA-MM-JJ

                self.file_combo.addItems(formatted_dates)
            else:
                self.folder_label.setText(f"В папке не найдены текстовые файлы.")
        else:
            self.folder_label.setText("Папка не выбрана")
            self.file_combo.clear()
            self.file_label.setText("Файл не выбран")

    def update_file_label(self):
        if self.file_combo.currentIndex() >= 0 and self.files_in_folder:
            selected_date = self.file_combo.currentText()
            # Trouver le fichier correspondant à la date sélectionnée
            for file in self.files_in_folder:
                if f"{selected_date.replace('-', '')}" in file:
                    self.data_file = os.path.join(self.data_folder, file)
                    self.file_label.setText(f"Файл загружен : {file}")
                    QMessageBox.information(self, "Файл загружен", f"Выбранный файл : {file}")
                    break
        else:
            self.file_label.setText("Файлы не выбраны.")

    def toggle_time_interval(self):
        if self.time_checkbox.isChecked():
            self.start_time_combo.setEnabled(True)
            self.end_time_combo.setEnabled(True)
        else:
            self.start_time_combo.setEnabled(False)
            self.end_time_combo.setEnabled(False)

    def toggle_altitude_interval(self):
        if self.altitude_checkbox.isChecked():
            self.start_altitude_combo.setEnabled(True)
            self.end_altitude_combo.setEnabled(True)
        else:
            self.start_altitude_combo.setEnabled(False)
            self.end_altitude_combo.setEnabled(False)

    def show_line_graph(self):
        if not self.data_file:
            QMessageBox.warning(self, "Нет файла",
                                "Пожалуйста, выберите файл перед просмотром диаграммы.")
            return

        start_time = int(self.start_time_combo.currentText().split(":")[0]) if self.time_checkbox.isChecked() else 0
        end_time = int(self.end_time_combo.currentText().split(":")[0]) if self.time_checkbox.isChecked() else 24
        start_altitude = int(self.start_altitude_combo.currentText()) if self.altitude_checkbox.isChecked() else 0
        end_altitude = int(self.end_altitude_combo.currentText()) if self.altitude_checkbox.isChecked() else 1000

        if start_time >= end_time:
            QMessageBox.warning(self, "Ошибка времени", "Время начала должно быть меньше времени окончания.")
            return

        plot_line_graph(self.data_file, start_time, end_time, start_altitude, end_altitude)

    def show_contour_graph(self):
        if not self.data_file:
            QMessageBox.warning(self, "Нет файла",
                                "Пожалуйста, выберите файл перед просмотром диаграммы.")
            return

        start_time = int(self.start_time_combo.currentText().split(":")[0]) if self.time_checkbox.isChecked() else 0
        end_time = int(self.end_time_combo.currentText().split(":")[0]) if self.time_checkbox.isChecked() else 24
        start_altitude = int(self.start_altitude_combo.currentText()) if self.altitude_checkbox.isChecked() else 0
        end_altitude = int(self.end_altitude_combo.currentText()) if self.altitude_checkbox.isChecked() else 1000

        if start_time >= end_time:
            QMessageBox.warning(self, "Ошибка времени", "Время начала должно быть меньше времени окончания.")
            return

        plot_contour_graph(self.data_file, start_time, end_time, start_altitude, end_altitude)

    def show_info(self):
        QMessageBox.information(self, "Информация", "Copyright 2024, Zafitombo Antonio")

    def quit_app(self):
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TemperaturePlotApp()
    window.show()
    sys.exit(app.exec_())
