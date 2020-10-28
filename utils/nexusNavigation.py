from functools import partial
from h5py import Dataset, File
from typing import NamedTuple, Optional, Text, Union
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
