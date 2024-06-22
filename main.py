import os

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QWidget, QGridLayout,
    QComboBox, QDateEdit, QMessageBox, QTabWidget
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import sys
import sqlite3
from collections import defaultdict


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Controle de requisição de agulhas")
        self.setFixedSize(1000, 500)
        self.center_window()
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowMaximizeButtonHint)

        # Main widget
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        # Layouts
        self.main_layout = QVBoxLayout(self.main_widget)

        # Layout for data input
        self.input_layout = QVBoxLayout()
        self.create_input_form()
        self.main_layout.addLayout(self.input_layout)

        # Tab widget
        self.tabs = QTabWidget(self)
        self.main_layout.addWidget(self.tabs)

        # Tabs for plotting
        self.neetex_tab = QWidget()
        self.neetex_layout = QVBoxLayout(self.neetex_tab)
        self.create_plot_tab(self.neetex_layout, "Neetex")
        self.tabs.addTab(self.neetex_tab, "Visualização do Gráfico - Neetex")

        self.grozbeckert_tab = QWidget()
        self.grozbeckert_layout = QVBoxLayout(self.grozbeckert_tab)
        self.create_plot_tab(self.grozbeckert_layout, "Groz-Beckert")
        self.tabs.addTab(self.grozbeckert_tab, "Visualização do Gráfico - Groz-Beckert")

        # Plot the initial data if the database exists
        if os.path.exists("database.db"):
            self.neetex_plot_widget.plot()
            self.grozbeckert_plot_widget.plot()

    def center_window(self):
        screen_geometry = QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def create_input_form(self):
        self.input_form_layout = QHBoxLayout()

        # Input fields
        self.numAg_input = QLineEdit(self)
        self.numAg_input.setPlaceholderText("Quantidade")
        self.numAg_input.setFixedSize(100, 30)
        self.input_form_layout.addWidget(self.numAg_input)

        self.tipoAg_input = QComboBox(self)
        self.tipoAg_input.setPlaceholderText("Tipo")
        self.tipoAg_input.addItem("Groz-Beckert")
        self.tipoAg_input.addItem("Neetex")
        self.tipoAg_input.setFixedSize(100, 30)
        self.input_form_layout.addWidget(self.tipoAg_input)

        self.talaoAg_input = QComboBox(self)
        self.talaoAg_input.setPlaceholderText("Talão")
        self.talaoAg_input.addItem("Alto")
        self.talaoAg_input.addItem("Baixo")
        self.talaoAg_input.setFixedSize(100, 30)
        self.input_form_layout.addWidget(self.talaoAg_input)

        self.data_input = QDateEdit(self)
        self.data_input.setDate(QDate.currentDate())
        self.data_input.setCalendarPopup(True)
        self.data_input.setFixedSize(100, 30)
        self.input_form_layout.addWidget(self.data_input)

        # Confirm button
        self.novaReq_bt = QPushButton("Confirmar", self)
        self.novaReq_bt.setFixedSize(100, 30)
        self.novaReq_bt.clicked.connect(self.insert_data)
        self.input_form_layout.addWidget(self.novaReq_bt)

        self.input_layout.addLayout(self.input_form_layout)

    def create_plot_tab(self, layout, tipo_agulha):
        # Filter combo box
        filter_combo_box = QComboBox(self)
        filter_combo_box.addItems(["Ano", "Mês"])
        layout.addWidget(filter_combo_box)

        # Plotting area
        plot_widget = PlotCanvas(self, width=8, height=4, tipo_agulha=tipo_agulha)
        layout.addWidget(plot_widget)

        # Connect filter combo box to the plot widget's plot function
        filter_combo_box.currentIndexChanged.connect(lambda: self.update_plot(tipo_agulha, plot_widget, filter_combo_box))

        if tipo_agulha == "Neetex":
            self.neetex_plot_widget = plot_widget
        else:
            self.grozbeckert_plot_widget = plot_widget

    def insert_data(self):
        quantity = self.numAg_input.text()
        type = self.tipoAg_input.currentText()
        talao = self.talaoAg_input.currentText()
        data = self.data_input.date().toString("yyyy-MM-dd")

        if not quantity or not type or not talao:
            QMessageBox.warning(self, "Aviso", "Preencha todos os campos.")
            return
        else:
            try:
                conn = sqlite3.connect("database.db")
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE IF NOT EXISTS requisicoes (id INTEGER PRIMARY KEY, quantidade INTEGER, tipo TEXT, data DATE, talao TEXT)")
                cursor.execute("INSERT INTO requisicoes (quantidade, tipo, talao, data) VALUES (?,?,?,?)", (quantity, type, talao, data))
                conn.commit()
                QMessageBox.information(self, "Sucesso", "Dados inseridos no banco de dados")
                self.numAg_input.clear()
                self.tipoAg_input.setCurrentIndex(0)
                self.talaoAg_input.setCurrentIndex(0)
                self.neetex_plot_widget.plot()
                self.grozbeckert_plot_widget.plot()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "ERRO", f"Erro ao inserir os dados no banco de dados: {e}")
            finally:
                conn.close()

    def update_plot(self, tipo_agulha, plot_widget, filter_combo_box):
        interval = filter_combo_box.currentIndex()
        if interval == 0:
            interval = 'yearly'
        elif interval == 1:
            interval = 'monthly'
        else:
            return
        plot_widget.plot(interval=interval)


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100, tipo_agulha=None):
        self.tipo_agulha = tipo_agulha
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.plot()

    def plot(self, interval='yearly'):
        if not os.path.exists("database.db"):
            return

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Seleciona os dados do banco de dados
        if interval == 'yearly':
            query = '''SELECT strftime('%Y', data) AS periodo, tipo, SUM(quantidade) 
                       FROM requisicoes 
                       WHERE tipo = ?
                       GROUP BY periodo, tipo'''
        elif interval == 'monthly':
            query = '''SELECT strftime('%Y-%m', data) AS periodo, tipo, SUM(quantidade) 
                       FROM requisicoes 
                       WHERE tipo = ?
                       GROUP BY periodo, tipo'''
        else:
            return

        cursor.execute(query, (self.tipo_agulha,))
        rows = cursor.fetchall()

        conn.close()

        data_dict = defaultdict(list)
        all_periods = set()
        for row in rows:
            periodo, tipo, quantidade = row
            if periodo is not None:
                all_periods.add(periodo)
                data_dict[tipo].append((periodo, quantidade))

        sorted_periods = sorted(all_periods)
        if len(sorted_periods) > 10:
            sorted_periods = sorted_periods[-10:]

        labels = sorted_periods
        datas = []
        for periodo, quantidade in data_dict.get(self.tipo_agulha, []):
            if periodo in sorted_periods:
                datas.append(quantidade)

        x = range(len(labels))
        width = 0.35

        self.axes.clear()
        self.axes.bar(x, datas, width, label=self.tipo_agulha, color='steelblue' if self.tipo_agulha == 'Groz-Beckert' else 'orange')

        self.axes.set_xticks(x)
        self.axes.set_xticklabels(labels)
        self.axes.set_xlabel('Período')
        self.axes.set_ylabel('Quantidade')
        self.axes.set_title(f'Quantidade de Requisições ao Longo do Tempo - {self.tipo_agulha}', fontsize=14)

        self.axes.legend(fontsize=10, loc='upper right', facecolor='lightgray', title='Tipo',
                         title_fontsize='medium', shadow=True, fancybox=True, edgecolor='black', handletextpad=1,
                         labelspacing=1, handlelength=2, handleheight=0.5, ncol=1, borderaxespad=0.5, columnspacing=0.5)
        self.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
