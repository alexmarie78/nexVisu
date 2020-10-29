from enum import Enum

class detectors(Enum):
      XPAD = "XPAD"
      CIRPAD = "CIRPAD"

class scan_types(Enum):
      ASCAN = "ascan"
      TSCAN = "tscan"
      FSCAN = "fscan"

class fitting_curves(Enum):
      GAUSSIAN = "GAUSSIAN"
      GAUSSIANb = "GAUSSIANb"
      LORENTZ = "LORENTZ"

class metadata_path(Enum):
      # To use with DatasetPathContains
      DELTA =
      OLD_DELTA = "d13-1-cx1__EX__DIF.1-DELTA__#1/raw_value"
      OLD_DELTA = "D13-1-CX1__EX__DIF.1-DELTA__#1/raw_value"
      OLD_GAMMA = "d13-1-cx1__EX__DIF.1-GAMMA__#1/raw_value"
      OLD_GAMMA = "D13-1-CX1__EX__DIF.1-GAMMA__#1/raw_value"

class data_path(Enum):
      # To use with DatasetPathWithAttribute
      DELTA_LONG_NAME = "d13-1-cx1/ex/diff.1-delta/position"
      GAMMA_LONG_NAME = "d13-1-cx1/ex/diff.1-gamma/position"
