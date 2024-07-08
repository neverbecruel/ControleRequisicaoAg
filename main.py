import os
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QWidget,
    QComboBox, QDateEdit, QHeaderView, QMessageBox, QTabWidget, QDialog, QLabel, QDialogButtonBox, QTableWidget,
    QTableWidgetItem
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import sys
import sqlite3
from collections import defaultdict

home_dir = os.path.expanduser("~")
data_dir = os.path.join(home_dir, "data")
os.makedirs(data_dir, exist_ok=True)
database = os.path.join(data_dir, "database.db")


# database = "database1.db"


class PasswordDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Senha Necessária")
        self.setFixedSize(300, 100)

        self.layout = QVBoxLayout()
        self.label = QLabel("Digite a senha para continuar:", self)
        self.layout.addWidget(self.label)

        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.layout.addWidget(self.password_input)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                                        self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        self.setLayout(self.layout)

    def get_password(self):
        return self.password_input.text()


class DeleteEntryDialog(QDialog):
    def __init__(self, databasepath):
        super().__init__()
        self.databasePath = databasepath
        self.setWindowTitle("Excluir Inserção")
        self.setFixedSize(445, 400)

        self.layout = QVBoxLayout()
        self.table = QTableWidget(self)
        self.layout.addWidget(self.table)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
                                        self)
        self.buttons.accepted.connect(self.close)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        self.setLayout(self.layout)
        self.load_entries()

    def load_entries(self):
        try:
            conn = sqlite3.connect(self.databasePath)
            cursor = conn.cursor()
            cursor.execute("SELECT id, quantidade, tipo, talao, date(data) FROM requisicoes ORDER BY id DESC LIMIT 10")
            rows = cursor.fetchall()
            conn.close()

            self.table.setRowCount(len(rows))
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["ID", "Quantidade", "Tipo", "Talão", "Data"])

            header = self.table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(4, 130)

            for row_idx, row in enumerate(rows):
                for col_idx, col in enumerate(row):
                    item = QTableWidgetItem(str(col))
                    if col_idx == 4:  # Coluna de data
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # Alinhar o texto ao centro
                    self.table.setItem(row_idx, col_idx, item)
        except sqlite3.Error as e:
            QMessageBox.critical(self, "ERRO", f"Erro ao carregar as entradas: {e}")

    def delete_entry(self):
        selected_items = self.table.selectedItems()
        if selected_items:
            entry_id = selected_items[0].text()
            try:
                conn = sqlite3.connect(self.databasePath)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM requisicoes WHERE id = ?", (entry_id,))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "Sucesso", "Entrada excluída com sucesso")
                self.load_entries()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "ERRO", f"Erro ao excluir a entrada: {e}")
        else:
            QMessageBox.warning(self, "Aviso", "Nenhuma entrada selecionada para exclusão.")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.databasePath = database
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
        if os.path.exists(self.databasePath):
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

        # Delete last entry button
        self.delLastReq_bt = QPushButton("DELETAR", self)
        self.delLastReq_bt.setFixedSize(100, 30)
        self.delLastReq_bt.clicked.connect(self.confirm_delete_entry)
        self.input_form_layout.addWidget(self.delLastReq_bt)

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
        quantity: str = self.numAg_input.text()
        type = self.tipoAg_input.currentText()
        talao = self.talaoAg_input.currentText()
        data = self.data_input.date().toString("yyyy-MM-dd")

        if not quantity or not type or not talao:
            QMessageBox.warning(self, "Aviso", "Preencha todos os campos.")
            return
        else:
            try:
                conn = sqlite3.connect(self.databasePath)
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE IF NOT EXISTS requisicoes ("
                               "id INTEGER PRIMARY KEY,"
                               " quantidade INTEGER,"
                               " tipo TEXT,"
                               " data DATE,"
                               " talao TEXT)")
                cursor.execute("INSERT INTO requisicoes (quantidade, tipo, talao, data) VALUES (?,?,?,?)",
                               (quantity, type, talao, data))
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

    @staticmethod
    def update_plot(plot_widget, filter_combo_box):
        interval = filter_combo_box.currentIndex()
        if interval == 0:
            interval = 'yearly'
        elif interval == 1:
            interval = 'monthly'
        else:
            return
        plot_widget.plot(interval=interval)

    def confirm_delete_entry(self):
        password_dialog = PasswordDialog()
        if password_dialog.exec() == QDialog.DialogCode.Accepted:
            if password_dialog.get_password() == "1220":
                delete_dialog = DeleteEntryDialog(self.databasePath)
                if delete_dialog.exec() == QDialog.DialogCode.Accepted:
                    self.neetex_plot_widget.plot()
                    self.grozbeckert_plot_widget.plot()
            else:
                QMessageBox.warning(self, "Aviso", "Senha incorreta.")


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100, tipo_agulha=None):
        self.databasePath = database
        self.tipo_agulha = tipo_agulha
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.plot()

    def plot(self, interval='yearly'):
        if not os.path.exists(self.databasePath):
            return

        conn = sqlite3.connect(self.databasePath)
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

        # Limitar a largura máxima das barras
        max_width = 0.35  # Largura máxima desejada para as barras (proporcional ao número de barras)
        if len(labels) == 1:
            width = min(max_width, max_width / len(labels))  # Ajuste o valor conforme necessário
        else:
            width = max_width

        self.axes.clear()
        self.axes.bar(x, datas, width, label=self.tipo_agulha,
                      color='steelblue' if self.tipo_agulha == 'Groz-Beckert' else 'orange')

        self.axes.set_xticks(x)
        self.axes.set_xticklabels(labels)
        self.axes.set_xlabel('Período')
        self.axes.set_ylabel('Quantidade')
        self.axes.set_title(f'Quantidade de Requisições ao Longo do Tempo - {self.tipo_agulha}', fontsize=14)

        self.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
