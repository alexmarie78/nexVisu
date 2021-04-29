from scipy import ndimage

from constants import DataPath, MetadataPath
from h5py import File
from PyQt5.QtWidgets import QMessageBox, QProgressBar, QApplication
from utils.nexusNavigation import get_dataset

import numpy
import os


def gen_flatfield(first_scan: int, last_scan: int, path: str, progress: QProgressBar, application: QApplication):
    flatfield = numpy.zeros((240, 560), dtype=numpy.int64)
    if os.path.basename(path).split('_')[-1].split('.')[-2] == "0001":
        extension = "_0001.nxs"
    else:
        extension = ".nxs"
    scan_name = os.path.basename(path).replace(extension, '').replace(str(first_scan), '').replace(str(last_scan), '')
    directory_path = os.path.dirname(path)
    completed = 0
    progress.setVisible(True)
    for i in range(last_scan - first_scan + 1):
        try:
            filename = scan_name + f"{i + first_scan}" + extension
            with File(os.path.join(directory_path, filename), mode='r') as h5file:
                for data in get_dataset(h5file, DataPath.IMAGE_INTERPRETATION.value):
                    flatfield += data
            # Segment the progress bar according to number of scan
            completed += 100/(last_scan - first_scan + 1)
            # Update the progress bar value
            progress.setValue(completed)
            # Update the gui and the progress bar
            application.processEvents()
        except ValueError:
            QMessageBox(QMessageBox.Icon.Critical, "Failed",
                        "You are running a flatfield on a different detector shape").exec()
        except OSError:
            if i > first_scan:
                # We need to update the progress bar even if we skip a scan
                completed += 100 / (last_scan - first_scan + 1)
                progress.setValue(completed)
                application.processEvents()
                print(f"{filename} scan seems to not exist. It has been skipped in the flatfield computation")
            else:
                QMessageBox(QMessageBox.Icon.Critical, "Failed", f"You selected {filename} file which does not "
                                                                 f"exist in the {directory_path} location").exec()
    if 99.0 < completed < 100:
        completed = 100.0
        progress.setValue(completed)
        application.processEvents()
    return flatfield


def compute_geometry(contextual_data: dict, flat_image: numpy.ndarray, images: numpy.ndarray):
    deg2rad = numpy.pi / 180
    inv_deg2rad = 1 / (numpy.pi / 180)
    calib = contextual_data["distance"][0]  # pixels in 1 deg.76.78
    chip_size_x = 80
    chip_size_y = 120  # chip dimension, in pixels (X = horiz, Y = vertical)
    # Corrected positions (add 3 pixels whenever cross 80 * i in X)
    x_center_detector = contextual_data["x"][0] + 3 * (contextual_data["x"][0] // chip_size_x)
    # position of direct beam on xpad at (delltaOffset, gamOffset).
    # Use the 'corrected' positions (add 3 pixels whenever cross 120 in Y)
    y_center_detector = contextual_data["y"][0] + 3 * (contextual_data["y"][0] // chip_size_y)
    delta_position = contextual_data["delta_position"][0] * -1.0 # Let the user input the real (negative value) of the delta position of the detector with direct beam
    # positions in diffracto angles for which the above values XcenDetector, YcenDetectors are reported
    gamma_position = contextual_data["gamma_position"][0] * -1.0
    number_of_modules = images.shape[1] // chip_size_y
    number_of_chips = images.shape[2] // chip_size_x  # detector dimension, XPAD S-140
    distance = contextual_data["distance"][0] / numpy.tan(1.0 * deg2rad)
    lines_to_remove_array = [0, -3]
    between_chips = [i * 80 + 3 * (i - 1) + 1 for i in range(1, 7)]

    if flat_image is not None:
        factor_intensity_double_pixel = 1.0
        flat_image = 1.0 * flat_image / flat_image.mean()
        flat_image_inv = 1.0 / flat_image
        flat_image_inv[numpy.isnan(flat_image_inv)] = -10000000
        flat_image_inv[numpy.isinf(flat_image_inv)] = -10000000
        print("hello from flatimageinv computing")
    else:
        flat_image_inv = numpy.ones_like(images[0], dtype=numpy.float32)
        factor_intensity_double_pixel = 2.3

    lines_to_remove = -3

    # size of the resulting (corrected) image
    image_corr1_size_y = number_of_modules * chip_size_y - lines_to_remove
    image_corr1_size_x = (number_of_chips - 1) * 3 + number_of_chips * chip_size_x

    new_x_array = numpy.zeros(image_corr1_size_x)
    new_x_ifactor_array = numpy.zeros(image_corr1_size_x)
    for x in range(0, 79):  # this is the 1st chip (image_index chip = 0)
        new_x_array[x] = x
        new_x_ifactor_array[x] = 1  # no change in intensity

    # Last two columns + doube pixel of first chip
    new_x_array[79:82] = [79] * 3
    new_x_ifactor_array[79:81] = [-1.0 / factor_intensity_double_pixel] * 2
    new_x_ifactor_array[81] = -10

    for indexChip in range(1, 6):
        temp_index0 = indexChip * 83
        for x in range(1, 79):  # this are the regular size (130 um) pixels
            temp_index = temp_index0 + x
            new_x_array[temp_index] = x + 80 * indexChip
            new_x_ifactor_array[temp_index] = 1  # no change in intensity

        # First two columns of chip i
        new_x_array[temp_index0 - 1 : temp_index0 + 1] = [80 * indexChip] * 2
        new_x_ifactor_array[temp_index0 - 1 : temp_index0 + 1] = [-1.0 / factor_intensity_double_pixel] * 2

        # Last two columns of chip i and double pixel
        new_x_array[temp_index0 + 79: temp_index0 + 82] = [80 * indexChip + 79] * 3
        new_x_ifactor_array[temp_index0 + 79: temp_index0 + 81] = [-1.0 / factor_intensity_double_pixel] * 2
        new_x_ifactor_array[temp_index0 + 81] = -10

    for x in range(6 * 80 + 1, 560):  # this is the last chip (image_index chip = 6)
        temp_index = 18 + x
        new_x_array[temp_index] = x
        new_x_ifactor_array[temp_index] = 1  # no change in intensity

    # First two columns of last chip
    new_x_array[497:499] = [480] * 2
    new_x_ifactor_array[497:499] = [-1.0 / factor_intensity_double_pixel] * 2

    new_y_array = numpy.zeros(image_corr1_size_y)  # correspondence oldY - newY
    new_y_array_module_id = numpy.zeros(image_corr1_size_y)  # will keep trace of module image_index

    new_y_index = 0
    for moduleIndex in range(0, number_of_modules):
        for chipY in range(0, chip_size_y):
            y = chipY + chip_size_y * moduleIndex
            new_y_index = y - lines_to_remove_array[moduleIndex] * moduleIndex
            new_y_array[new_y_index] = y
            new_y_array_module_id[new_y_index] = moduleIndex

    geometry = {
        "deg2rad": deg2rad,
        "inv_deg2rad": inv_deg2rad,
        "distance": distance,
        "calib": calib,
        "x_center_detector": x_center_detector,
        "y_center_detector": y_center_detector,
        "chip_size_y": chip_size_y,
        "delta_position": delta_position,
        "gamma_position": gamma_position,
        "image_corr1_size_x": image_corr1_size_x,
        "image_corr1_size_y": image_corr1_size_y,
        "factor_intensity_double_pixel": factor_intensity_double_pixel,
        "new_y_array": new_y_array,
        "new_x_array": new_x_array,
        "new_x_ifactor_array": new_x_ifactor_array,
        "flat_image_inv": flat_image_inv,
        "between_chips": between_chips
    }

    return geometry


def correct_and_unfold_data(geometry: dict, image: numpy.ndarray, delta: float, gamma: float, median_filter_flag=False):
    # extracting the XY coordinates for the rest of the scan transformation
    # ========psiAve = 1, deltaPsi = 1=============================================

    diffracto_delta_rad = (delta + geometry["delta_position"]) * geometry["deg2rad"]
    sindelta = numpy.sin(diffracto_delta_rad)
    cosdelta = numpy.cos(diffracto_delta_rad)
    diffracto_gam_rad = (gamma + geometry["gamma_position"]) * geometry["deg2rad"]
    singamma = numpy.sin(diffracto_gam_rad)
    cosgamma = numpy.cos(diffracto_gam_rad)

    # the array this_corrected_image contains the corrected image (double pixels corrections)
    # two_th_array = numpy.zeros((image_corr1_size_y, image_corr1_size_x))
    # psi_array = numpy.zeros((image_corr1_size_y, image_corr1_size_x))

    x_line = numpy.linspace(0, geometry["image_corr1_size_x"] - 1, geometry["image_corr1_size_x"])
    x_matrix = numpy.zeros((geometry["image_corr1_size_x"],  geometry["image_corr1_size_y"]))
    for a in range(geometry["image_corr1_size_y"]):
        x_matrix[:, a] = x_line[:]

    y_line = numpy.linspace(0, geometry["image_corr1_size_y"] - 1, geometry["image_corr1_size_y"])
    y_matrix = numpy.zeros((geometry["image_corr1_size_x"],  geometry["image_corr1_size_y"]))
    for a in range(geometry["image_corr1_size_x"]):
        y_matrix[a, :] = y_line[:]

    corr_array_x = geometry["distance"]  # for xpad3.2 like
    corr_array_z = geometry["y_center_detector"] - y_matrix  # for xpad3.2 like
    corr_array_y = geometry["x_center_detector"] - x_matrix  # sign is reversed
    temp_x = corr_array_x
    temp_y = corr_array_z * (-1.0)
    temp_z = corr_array_y

    x1 = temp_x * cosdelta - temp_z * sindelta
    y1 = temp_y
    z1 = temp_x * sindelta + temp_z * cosdelta
    # apply Rz(-gamma); due to geo consideration on the image, the gamma rotation should be negative for gam>0
    # apply the same considerations as for the delta, and keep gam values positive
    corr_array_x = x1 * cosgamma + y1 * singamma
    corr_array_y = -x1 * singamma + y1 * cosgamma
    corr_array_z = z1
    # calculate the square values and normalization
    corr_array_x2 = corr_array_x * corr_array_x
    corr_array_y2 = corr_array_y * corr_array_y
    corr_array_z2 = corr_array_z * corr_array_z
    norm = numpy.sqrt(corr_array_x2 + corr_array_y2 + corr_array_z2)
    # calculate the corresponding angles
    # delta = angle between vector(corr_array_x, corr_array_y, corr_array_z) and the vector(1,0,0)
    this_delta = numpy.arccos(corr_array_x / norm) * geometry["inv_deg2rad"]

    # psi = angle between vector(0, corr_array_y, corr_array_z) and the vector(0,1,0)
    sign = numpy.sign(corr_array_z)
    cos_psi_rad = corr_array_y / numpy.sqrt(corr_array_y2 + corr_array_z2)
    psi = numpy.arccos(cos_psi_rad) * geometry["inv_deg2rad"] * sign

    psi[psi < 0] += 360
    psi -= 90
    psi_array = psi.T
    two_th_array = this_delta.T

    # ======================end geometry====================================

    # dealing now with the intensitiespointIndex
    this_image = geometry["flat_image_inv"] * image
    if median_filter_flag:
        this_image = ndimage.median_filter(this_image, size=3)

    this_corrected_image = numpy.zeros((geometry["image_corr1_size_y"], geometry["image_corr1_size_x"]))
    intensity_factor = geometry["new_x_ifactor_array"]  # x
    new_y_array = geometry["new_y_array"].astype('int')
    new_x_array = geometry["new_x_array"].astype('int')

    for x in range(0, geometry["image_corr1_size_x"]):
        this_corrected_image[:, x] = this_image[new_y_array[:], new_x_array[x]]
        if -1 <= intensity_factor[x] < 0:
             this_corrected_image[:, x] = this_image[new_y_array[:], new_x_array[x]] / geometry["factor_intensity_double_pixel"]
    for x in geometry["between_chips"]:
        if intensity_factor[x] == -10:
            # correct the double lines (last and 1st line of the modules, at their junction)
            this_corrected_image[:, x] = (this_corrected_image[:, x-1]
                                          + this_corrected_image[:, x+1]) / 2.0

    # last line of module1 = 119, is the 1st line to correct
    line_index1 = geometry["chip_size_y"] - 1

    # Last two lines of the first module
    this_corrected_image[line_index1 : line_index1 + 2, :] =  [this_corrected_image[line_index1, :] / geometry["factor_intensity_double_pixel"]] * 2
    # Two first lines of the second module
    this_corrected_image[line_index1 + 3 : line_index1 + 5, :] =  [this_corrected_image[line_index1 + 4, :] / geometry["factor_intensity_double_pixel"]] * 2
    # Line between the two modules (0.5 + 0.5 pixels)
    this_corrected_image[line_index1 + 2, :] = (this_corrected_image[line_index1, :] + this_corrected_image[line_index1 + 4, :]) / 2.0

    # this is the corrected intensity of each pixel, on the image having the new size
    """
    tth = []
    psi = []
    corrected = []
    for x in range(0, geometry["image_corr1_size_x"]):
        for y in range(0, geometry["image_corr1_size_y"]):
            tth.append(two_th_array[y, x])
            psi.append(psi_array[y, x])
            corrected.append(this_corrected_image[y, x])
    """
    intensity_array = this_corrected_image.T.reshape(geometry["image_corr1_size_x"] * geometry["image_corr1_size_y"])
    psi_array = psi_array.T.reshape(geometry["image_corr1_size_x"] * geometry["image_corr1_size_y"])
    two_th_array = two_th_array.T.reshape(geometry["image_corr1_size_x"] * geometry["image_corr1_size_y"])
    return two_th_array, psi_array, intensity_array


def extract_diffraction_diagram(two_th_array, psi_array, intensity_array, step_two_th, psi1, psi2, patch_data_flag=True):
    mask_psi = numpy.ones(psi_array.shape)
    mask_psi[psi_array < psi1] = 0.0
    mask_psi[psi_array > psi2] = 0.0

    two_th_min = two_th_array.min()
    two_th_max = two_th_array.max()

    nb_of_bins = int((0.0 + two_th_max - two_th_min) / step_two_th) + 1

    two_th_result = numpy.zeros(nb_of_bins + 1)  # generate the tables for radial integration, this is delta

    for ii in range(0, nb_of_bins):
        two_th_temp1 = two_th_min + ii * step_two_th
        two_th_temp2 = two_th_temp1 + step_two_th
        two_th_result[ii] = 0.5 * (two_th_temp1 + two_th_temp2)

    this_bin_array = numpy.floor((two_th_array * mask_psi - two_th_min) / step_two_th)
    this_bin_array = this_bin_array.astype('int')

    intensity_result = numpy.zeros(nb_of_bins + 1) # this will be the summed intensity
    intensity_array = intensity_array * mask_psi

    indexes_ = numpy.nonzero(intensity_array > 0)[0]
    my_bin = this_bin_array[indexes_]

    my_intensity = intensity_array[indexes_]
    aggregated = numpy.zeros(nb_of_bins + 1)
    for i in range(my_bin.max() + 1):
        selected_intensities = my_intensity[my_bin == i]
        intensity_result[i] = selected_intensities.mean()

    intensity_result[numpy.isnan(intensity_result)] = -1

    if patch_data_flag:
        two_th_result, intensity_result = patch_data(two_th_result, intensity_result)

    return two_th_result[1: -1], intensity_result[1: -1]


def patch_data(tth_data_array, intensity_data_array):
    nb_points2throw_begin = 15
    nb_points2throw_end = 15
    tth1 = 0.
    tth2 = 150.
    tth_step = 0.0105
    npoints = int(round((tth2 - tth1) / tth_step)) + 1
    tth_array = numpy.linspace(tth1, tth2, npoints)
    intensity_array = numpy.zeros(npoints)
    n_intensity_array = numpy.zeros(npoints)
    for uu in range(nb_points2throw_begin, tth_data_array.shape[0] - nb_points2throw_end):
        tth_index = int(round((tth_data_array[uu] - tth1) / tth_step))
        if intensity_data_array[uu] > 0:
            intensity_array[tth_index] += intensity_data_array[uu]
            n_intensity_array[tth_index] += 1.
    intensity_array = intensity_array / n_intensity_array
    return tth_array, intensity_array


def get_angles(path: str) -> (numpy.ndarray, numpy.ndarray):
    with File(path, mode='r') as h5file:
        # Collecting delta and gamma arrays
        delta_array = None
        gamma_array = None
        for delta_path, gamma_path in zip(DataPath.Delta.value, DataPath.Gamma.value):
            try:
                if delta_array is None:
                    # We copy the data because we will use them after closing the file
                    delta_array = get_dataset(h5file, delta_path.value)[:]
                if gamma_array is None:
                    gamma_array = get_dataset(h5file, gamma_path.value)[:]
            # This exception let the loop continue if one path is incorrect, and let the loop try unpacking data
            except (AttributeError, TypeError):
                pass

        # If the delta array is empty, it means that delta is in static mode, so we search delta in metadata
        if delta_array is None:
            for delta_path in MetadataPath.Delta.value:
                try:
                    if delta_array is None:
                        delta_array = get_dataset(h5file, delta_path.value)[:]
                except (AttributeError, TypeError):
                    pass

        # If the gamma array is empty, it means that gamma is in static mode, so we search gamma in the metadata
        if gamma_array is None:
            for gamma_path in MetadataPath.Gamma.value:
                try:
                    if gamma_array is None:
                        gamma_array = get_dataset(h5file, gamma_path.value)[:]
                except (AttributeError, TypeError):
                    pass
    return delta_array, gamma_array
