from enum import Enum
from src.utils.nexusNavigation import DatasetPathWithAttribute, DatasetPathContains
from PyQt5.QtWidgets import QFileDialog

import sys
import distro


class Detectors(Enum):
    XPAD = "XPAD"


class ScanTypes(Enum):
    ASCAN = "ascan"
    TSCAN = "timescan"
    FSCAN = "fscan"


class FittingCurves(Enum):
    GAUSSIAN = "GAUSSIAN"
    GAUSSIANb = "GAUSSIANb"
    LORENTZ = "LORENTZ"


class MetadataPath(Enum):
    class Delta(Enum):
        DELTA = DatasetPathContains("d13-1-cx1__ex__dif.1-delta/raw_value")
        DELTA_BAD = DatasetPathContains("d13-1-cx1__ex__diff.1-delta/raw_value")
        OLD_DELTA = DatasetPathContains("d13-1-cx1__EX__DIF.1-DELTA__#1/raw_value")
        OLD_CAPS_DELTA = DatasetPathContains("D13-1-CX1__EX__DIF.1-DELTA__#1/raw_value")

    class Gamma(Enum):
        GAMMA = DatasetPathContains("d13-1-cx1__ex__dif.1-gamma/raw_value")
        GAMMA_BAD = DatasetPathContains("d13-1-cx1__ex__diff.1-gamma/raw_value")
        OLD_GAMMA = DatasetPathContains("d13-1-cx1__EX__DIF.1-GAMMA__#1/raw_value")
        OLD_CAPS_GAMMA = DatasetPathContains("D13-1-CX1__EX__DIF.1-GAMMA__#1/raw_value")


class DataPath(Enum):
    IMAGE_INTERPRETATION = DatasetPathWithAttribute("interpretation", b"image")

    class Delta(Enum):
        DELTA_INTERPRETATION = DatasetPathWithAttribute("interpretation", b"Delta")
        DELTA_LONG_NAME = DatasetPathWithAttribute("long_name", b"d13-1-cx1/ex/dif.1-delta/position")
        DELTA_LONG_NAME_BAD = DatasetPathWithAttribute("long_name", b"d13-1-cx1/ex/diff.1-delta/position")

    class Gamma(Enum):
        GAMMA_INTERPRETATION = DatasetPathWithAttribute("interpretation", b"Gamma")
        GAMMA_LONG_NAME = DatasetPathWithAttribute("long_name", b"d13-1-cx1/ex/dif.1-gamma/position")
        GAMMA_LONG_NAME_BAD = DatasetPathWithAttribute("long_name", b"d13-1-cx1/ex/diff.1-gamma/position")


def get_dialog_options() -> QFileDialog.Options:
    options = QFileDialog.Options()
    options |= QFileDialog.DontResolveSymlinks
    if sys.platform.startswith('linux'):
        if distro.linux_distribution()[0] == 'Ubuntu':
            options |= QFileDialog.DontUseNativeDialog
    return options
