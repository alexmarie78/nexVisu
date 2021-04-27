from PyQt5.QtGui import QFont, QValidator
from PyQt5.QtWidgets import QLabel, QPushButton, QLineEdit, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout
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

        self.distance_label = QLabel("number of pixel/° : ")
        self.distance_output = QLineEdit()
        self.distance_output.setReadOnly(True)
        self.distance_widget = QWidget()

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
        self.labelFilled.connect(self.compute_pixels_per_degree)
        
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

        self.distance_widget.layout = QHBoxLayout(self.distance_widget)
        self.distance_widget.layout.addWidget(self.distance_label)
        self.distance_widget.layout.addWidget(self.distance_output)

        self.layout.addWidget(self.distance_widget, 7, 0, 1, 4)

        # self.force_numeric()
        self.connect_labels()

        self.setStyleSheet("""
        QWidget {
        background-color: lightgrey;
        border-style: outset;
        border-width: 2px;
        border-radius: 10px;
        border-color: beige;
        font: bold 14px;
        min-width: 10em;
        padding: 6px;
        }
        
        QLineEdit {
        border: 2px solid gray; 
        border-radius: 10px; 
        padding: 0 8px; 
        background: lightblue; 
        selection-background-color: darkgray;
        }
        """)

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
        print(self.delta_inputs[0].text())
        return {
            'x': [float(line.text()) for line in self.x_inputs if is_number(line.text())],
            'y': [float(line.text()) for line in self.y_inputs if is_number(line.text())],
            'delta': [float(line.text()) for line in self.delta_inputs if is_number(line.text())],
            'gamma': [float(line.text()) for line in self.gamma_inputs if is_number(line.text())],
            'distance': float(self.distance_output.text()) if is_number(self.distance_output.text()) else None
        }

    def compute_pixels_per_degree(self):
        pix_per_deg = 0
        inputs = self.get_contextual_data()
        number_of_inputs = len(inputs['x'])
        print(inputs)
        print(number_of_inputs)
        try:
            for index in range(1, number_of_inputs):
                pix_per_deg += inputs['x'][index - 1] - inputs['x'][index]
        except IndexError:
            print('There is not enough data to compute pixels per degree')
        try:
            pix_per_deg /= (number_of_inputs - 1) * abs((inputs['delta'][0] - inputs['delta'][1]))
        except IndexError:
            print('Not enough delta data')
            try:
                pix_per_deg /= (number_of_inputs - 1) * abs((inputs['gamma'][0] - inputs['gamma'][1]))
            except IndexError:
                print('Not enough gamma data')
        self.distance_output.setText(str(pix_per_deg))


    # S'OCCUPER DES FONCTIONS QUI VONT SAUVEGARDER OU ECRIRE LES PARAMETRES
    # GERER L'ENVOI DES DONNEES

def is_number(string):
    print(string)
    try:
        float(string)
        return True
    except ValueError:
        return False


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
