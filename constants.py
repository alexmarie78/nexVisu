from enum import Enum

class detectors(Enum):
      XPAD = "XPAD"
      CIRPAD = "CIRPAD"

class fitting_curves(Enum):
      GAUSSIAN = "GAUSSIAN"
      GAUSSIANb = "GAUSSIANb"
      LORENTZ = "LORENTZ"
