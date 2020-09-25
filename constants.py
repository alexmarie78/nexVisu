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
