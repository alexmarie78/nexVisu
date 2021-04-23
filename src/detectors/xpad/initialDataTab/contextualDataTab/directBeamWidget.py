from PyQt5.QtGui import QFont, QValidator
from PyQt5.QtWidgets import QLabel, QPushButton, QLineEdit, QWidget, QGridLayout, QVBoxLayout
from PyQt5.QtCore import pyqtSignal


class DirectBeamWidget(QWidget):
    labelFilled = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent=parent)

        self.layout = QGridLayout(self)

        self.direct_beam_label = QLabel("Direct Beam :")

        self.x_label = QLabel('X coordinate(s) in pixel :')
        self.x_inputs = [QLineEdit()]
        self.x_inputs_list = QWidget()
        
        self.y_label = QLabel('Y coordinate(s) in pixel :')
        self.y_inputs = [QLineEdit()]
        self.y_inputs_list = QWidget()
        
        self.delta_label = QLabel('Delta angle(s) in degree :')
        self.delta_inputs = [QLineEdit()]
        self.delta_inputs_list = QWidget()
        
        self.gamma_label = QLabel('Gamma angle(s) in degree :')
        self.gamma_inputs = [QLineEdit()]
        self.gamma_inputs_list = QWidget()

        # En faire des dictionnaires au lieu de listes !!!
        self.input_lists = {
            '0': self.x_inputs,
            '1': self.y_inputs,
            '2': self.delta_inputs,
            '3': self.gamma_inputs
        }
        self.input_widgets = [self.x_inputs_list, self.y_inputs_list, self.delta_inputs_list, self.gamma_inputs_list]

        self.add_button = QPushButton("+")
        self.remove_button = QPushButton("-")

        self.add_button.clicked.connect(self.add_row)
        self.remove_button.clicked.connect(self.remove_row)
        
        self.init_ui()

    def init_ui(self):

        font_title = QFont()
        font_title.setPointSize(14)
        font_title.setUnderline(True)
        font_title.setBold(True)

        font_subtitle = QFont()
        font_subtitle.setPointSize(10)

        self.direct_beam_label.setFont(font_title)

        self.layout.addWidget(self.direct_beam_label, 0, 0, 1, 4)

        self.x_label.setFont(font_subtitle), self.y_label.setFont(font_subtitle)

        self.layout.addWidget(self.x_label, 1, 0, 1, 2), self.layout.addWidget(self.y_label, 1, 2, 1, 2)

        self.x_inputs_list.setLayout(QVBoxLayout())
        [self.x_inputs_list.layout().addWidget(widget) for widget in self.x_inputs]

        self.y_inputs_list.setLayout(QVBoxLayout())
        [self.y_inputs_list.layout().addWidget(widget) for widget in self.y_inputs]

        self.layout.addWidget(self.x_inputs_list, 2, 0, 2, 2), self.layout.addWidget(self.y_inputs_list, 2, 2, 2, 2)
        self.layout.addWidget(self.add_button, 3, 4, 1, 1)

        self.delta_label.setFont(font_subtitle), self.gamma_label.setFont(font_subtitle)

        self.layout.addWidget(self.delta_label, 4, 0, 1, 2), self.layout.addWidget(self.gamma_label, 4, 2, 1, 2)
        self.layout.addWidget(self.remove_button, 4, 4, 1, 1)

        self.delta_inputs_list.setLayout(QVBoxLayout())
        [self.delta_inputs_list.layout().addWidget(widget) for widget in self.delta_inputs]

        self.gamma_inputs_list.setLayout(QVBoxLayout())
        [self.gamma_inputs_list.layout().addWidget(widget) for widget in self.gamma_inputs]

        self.layout.addWidget(self.delta_inputs_list, 5, 0, 2, 2), self.layout.addWidget(self.gamma_inputs_list, 5, 2, 2, 2)

        # self.force_numeric()
        self.connect_labels()

    def add_row(self):
        if self.input_widgets[0].layout().count() < 5:
            for input_list in self.input_lists.values():
                input_list.append(QLineEdit())
            for index, widget in enumerate(self.input_widgets):
                [widget.layout().addWidget(line) for line in self.input_lists[f'{index}']]
            # self.force_numeric()
            self.connect_labels()

    def force_numeric(self):
        for input_list in self.input_lists.values():
            for line in input_list:
                line.setValidator(NumericValidator(self))

    def connect_labels(self):
        for input_list in self.input_lists.values():
            for line in input_list:
                line.editingFinished.connect(self.label_filled)

    def remove_row(self):
        if self.input_widgets[0].layout().count() > 1:
            for input_list in self.input_lists.values():
                del input_list[-1]
            for index, widget in enumerate(self.input_widgets):
                delete = widget.layout().takeAt(widget.layout().count() - 1).widget()
                delete.deleteLater()

    def label_filled(self):
        for input_list in self.input_lists.values():
            for line in input_list:
                if line.text() == '':
                    return
        self.labelFilled.emit()

    def input_number(self):
        return self.x_inputs_list.layout().count()

    def get_label_at(self, index: int):
        return self.inner_widget.layout().itemAt(index).widget().text()

    def get_contextual_data(self):
        return {
            'x': [float(line.text()) for line in self.x_inputs if line.text().isnumeric()],
            'y': [float(line.text()) for line in self.y_inputs if line.text().isnumeric()],
            'delta': [float(line.text()) for line in self.delta_inputs if line.text().isnumeric()],
            'gamma': [float(line.text()) for line in self.gamma_inputs if line.text().isnumeric()]
        }

    # NE PAS OUBLIER DE METTRE LE CALCUL DE LA DISTANCE ET SON AFFICHAGE DANS CE WIDGET
    # S'OCCUPER DES FONCTIONS QUI VONT SAUVEGARDER OU ECRIRE LES PARAMETRES
    # GERER L'ENVOI DES DONNEES


class NumericValidator(QValidator):
    def __init__(self, parent):
        super().__init__(parent)

    def validate(self, s, pos):
        print(s)
        if s.isnumeric():
            print('hello')
            return QValidator.Acceptable, pos
        else:
            self.fixup(s)
            #return QValidator.Invalid, pos

    def fixup(self, s):
        print(s.count())
        s.replace(0, s.count(), '')
