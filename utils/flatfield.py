from typing import NamedTuple, Optional, Text, Union
from functools import partial
from h5py import Dataset, File
from PyQt5.QtWidgets import QMessageBox, QProgressBar, QApplication, QWidget

import numpy
import os

# Generic hdf5 access types.
DatasetPathContains = NamedTuple("DatasetPathContains", [("path", Text)])
DatasetPathContainsDefault = NamedTuple("DatasetPathContains", [("path", Text),
                                                                ("default", float)])

DatasetPathWithAttribute = NamedTuple("DatasetPathWithAttribute",
                                      [('attribute', Text),
                                       ('value', bytes)])

DatasetPath = Union[DatasetPathContains,
                    DatasetPathWithAttribute]

def get_dataset(h5file: File, path: DatasetPath) -> Optional[Dataset]:
    res = None
    if isinstance(path, DatasetPathContains):
        res = h5file.visititems(partial(_v_item, path.path))
    elif isinstance(path, DatasetPathContainsDefault):
        res = h5file.visititems(partial(_v_item, path.path))
    elif isinstance(path, DatasetPathWithAttribute):
        res = h5file.visititems(partial(_v_attrs,  path.attribute, path.value))
    return res

def _v_attrs(attribute: Text, value: Text, _name: Text, obj) -> Dataset:
    """extract all the images and accumulate them in the acc variable"""
    if isinstance(obj, Dataset):
        if attribute in obj.attrs and obj.attrs[attribute] == value:
            return obj

def _v_item(key: Text, name: Text, obj: Dataset) -> Dataset:
    if key in name:
        return obj

def genFlatfield(first_scan: int, last_scan: int, path: str, progress: QProgressBar, application: QApplication):
    flatfield = numpy.zeros((240, 560), dtype=numpy.int64)
    if os.path.basename(path).split('_')[-1].split('.')[-2] == "0001":
        extension = "_0001.nxs"
    else:
        extension = ".nxs"
    scan_name = os.path.basename(path).replace(extension, '').replace(str(first_scan), '').replace(str(last_scan), '')
    directory_path = os.path.dirname(path)
    try:
        completed = 0
        for i in range(last_scan - first_scan + 1):
            filename = scan_name +  f"{i + first_scan}" + extension
            with File(os.path.join(directory_path, filename), mode='r') as h5file:
                for data in get_dataset(h5file, DatasetPathWithAttribute("interpretation",b"image")):
                    flatfield += data
            # Segment the progress bar according to number of scan
            completed += 100/(last_scan - first_scan + 1)
            # Update the progress bar value
            progress.setValue(completed)
            # Update the gui and the progress bar
            application.processEvents()
        return flatfield
    except ValueError:
        QMessageBox(QMessageBox.Icon.Critical, "Failed", "You are running a flatfield on a different detector shape").exec()
    except OSError:
        QMessageBox(QMessageBox.Icon.Critical, "Failed", f"You selected {filename} file wich does not exist in the location").exec()
