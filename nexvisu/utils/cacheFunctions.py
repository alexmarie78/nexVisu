
def memoisation(calibration: dict, use_flatfield: bool = None):
    index = []
    for value in calibration.values():
        index += value
    if use_flatfield is not None:
        index.append(use_flatfield)
    return tuple(index)
