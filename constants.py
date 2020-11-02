from enum import Enum
from utils.nexusNavigation import DatasetPathWithAttribute, DatasetPathContains


class Detectors(Enum):
    XPAD = "XPAD"
    CIRPAD = "CIRPAD"


class ScanTypes(Enum):
    ASCAN = "ascan"
    TSCAN = "tscan"
    FSCAN = "fscan"


class FittingCurves(Enum):
    GAUSSIAN = "GAUSSIAN"
    GAUSSIANb = "GAUSSIANb"
    LORENTZ = "LORENTZ"


class MetadataPath(Enum):
    # To use with DatasetPathContains
    DELTA = DatasetPathContains("d13-1-cx1__ex__diff.1-delta/raw_value")
    OLD_DELTA = DatasetPathContains("d13-1-cx1__EX__DIF.1-DELTA__#1/raw_value")
    OLD_CAPS_DELTA = DatasetPathContains("D13-1-CX1__EX__DIF.1-DELTA__#1/raw_value")
    OLD_GAMMA = DatasetPathContains("d13-1-cx1__EX__DIF.1-GAMMA__#1/raw_value")
    OLD_CAPS_GAMMA = DatasetPathContains("D13-1-CX1__EX__DIF.1-GAMMA__#1/raw_value")


class DataPath(Enum):
    # To use with DatasetPathWithAttribute
    IMAGE_INTERPRETATION = DatasetPathWithAttribute("interpretation", b"image")
    DELTA_INTERPRETATION = DatasetPathWithAttribute("interpretation", b"Delta")
    DELTA_LONG_NAME = DatasetPathWithAttribute("long_name", b"d13-1-cx1/ex/diff.1-delta/position")
    GAMMA_INTERPRETATION = DatasetPathWithAttribute("interpretation", b"Gamma")
    GAMMA_LONG_NAME = DatasetPathWithAttribute("long_name", b"d13-1-cx1/ex/diff.1-gamma/position")
