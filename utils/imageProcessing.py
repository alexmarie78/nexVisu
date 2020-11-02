from constants import DataPath, MetadataPath
from h5py import File
from PyQt5.QtWidgets import QMessageBox, QProgressBar, QApplication
from scipy import ndimage
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
    try:
        completed = 0
        progress.setVisible(True)
        for i in range(last_scan - first_scan + 1):
            filename = scan_name + f"{i + first_scan}" + extension
            with File(os.path.join(directory_path, filename), mode='r') as h5file:
                for data in get_dataset(h5file, DataPath.IMAGE_INTERPRETATION):
                    flatfield += data
            # Segment the progress bar according to number of scan
            completed += 100/(last_scan - first_scan + 1)
            # Update the progress bar value
            progress.setValue(completed)
            # Update the gui and the progress bar
            application.processEvents()
        return flatfield
    except ValueError:
        QMessageBox(QMessageBox.Icon.Critical, "Failed",
                    "You are running a flatfield on a different detector shape").exec()
    except OSError:
        QMessageBox(QMessageBox.Icon.Critical, "Failed",
                    f"You selected {filename} file wich does not exist in the location").exec()


def correct_and_unfold_data(flat_image: numpy.ndarray, images: numpy.ndarray, path: str, contextual_data: dict) \
        -> [set]:
    # Result
    unfolded_data = []

    # Constant that will help us during the computation
    deg2rad = numpy.pi / 180
    inv_deg2rad = 1 / (numpy.pi/180)

    # We assign
    calib = contextual_data["distance"]  # pixels in 1 deg.76.78
    chip_size_x = 80
    chip_size_y = 120  # chip dimension, in pixels (X = horiz, Y = vertical)
    # Corrected positions (add 3 pixels whenever cross 80 * i in X)
    x_center_detector = contextual_data["x"] + 3 * (contextual_data["x"] // chip_size_x)
    # position of direct beam on xpad at (delltaOffset, gamOffset).
    # Use the 'corrected' positions (add 3 pixels whenever cross 120 in Y)
    y_center_detector = contextual_data["y"] + 3 * (contextual_data["y"] // chip_size_y)
    delta_offset = contextual_data["delta_offset"]
    # positions in diffracto angles for which the above values XcenDetector, YcenDetectors are reported
    gamma_offset = contextual_data["gamma_offset"]
    number_of_modules = images.shape[1] // chip_size_y
    number_of_chips = images.shape[2] // chip_size_x  # detector dimension, XPAD S-140
    distance = contextual_data["distance"] / numpy.tan(1.0 * deg2rad)
    lines_to_remove_array = [0, -3]

    if flat_image is not None:
        factor_intensity_double_pixel = 1.0
        flat_image = 1.0 * flat_image / flat_image.mean()
        flat_image_inv = 1.0 / flat_image
        flat_image_inv[numpy.isnan(flat_image_inv)] = -10000000
        flat_image_inv[numpy.isinf(flat_image_inv)] = -10000000
    else:
        flat_image_inv = numpy.ones_like(images[0])
        factor_intensity_double_pixel = 2.5

    lines_to_remove = -3

    # size of the resulting (corrected) image
    image_corr1_size_y = number_of_modules * chip_size_y - lines_to_remove
    image_corr1_size_x = (number_of_chips - 1) * 3 + number_of_chips * chip_size_x

    new_x_array = numpy.zeros(image_corr1_size_x); new_x_ifactor_array = numpy.zeros(image_corr1_size_x)
    for x in range(0, 79): # this is the 1st chip (index chip = 0)
        new_x_array[x] = x
        new_x_ifactor_array[x] = 1 # no change in intensity

    new_x_array[79] = 79; new_x_ifactor_array[79] = 1/factor_intensity_double_pixel
    new_x_array[80] = 79; new_x_ifactor_array[80] = 1/factor_intensity_double_pixel
    new_x_array[81] = 79; new_x_ifactor_array[81] = -1

    for indexChip in range (1, 6):
        temp_index0 = indexChip * 83
        for x in range(1, 79): # this are the regular size (130 um) pixels
            temp_index = temp_index0 + x
            new_x_array[temp_index] = x + 80 * indexChip
            new_x_ifactor_array[temp_index] = 1  # no change in intensity
        new_x_array[temp_index0] = 80 * indexChip
        new_x_ifactor_array[temp_index0] = 1 / factor_intensity_double_pixel  # 1st double column
        new_x_array[temp_index0 - 1] = 80 * indexChip
        new_x_ifactor_array[temp_index0 - 1] = 1 / factor_intensity_double_pixel
        new_x_array[temp_index0 + 79] = 80 * indexChip + 79
        new_x_ifactor_array[temp_index0 + 79] = 1 / factor_intensity_double_pixel  # last double column
        new_x_array[temp_index0 + 80] = 80 * indexChip + 79
        new_x_ifactor_array[temp_index0 + 80] = 1 / factor_intensity_double_pixel
        new_x_array[temp_index0 + 81] = 80 * indexChip + 79
        new_x_ifactor_array[temp_index0 + 81] = -1

    for x in range(6 * 80 + 1, 560):  # this is the last chip (index chip = 6)
        temp_index = 18 + x
        new_x_array[temp_index] = x
        new_x_ifactor_array[temp_index] = 1 # no change in intensity

    new_x_array[497] = 480; new_x_ifactor_array[497] = 1/factor_intensity_double_pixel
    new_x_array[498] = 480; new_x_ifactor_array[498] = 1/factor_intensity_double_pixel

    new_y_array = numpy.zeros(image_corr1_size_y)  # correspondance oldY - newY
    new_y_array_module_id = numpy.zeros(image_corr1_size_y)  # will keep trace of module index

    new_y_index = 0
    for moduleIndex in range(0, number_of_modules):
        for chipY in range(0, chip_size_y):
            y = chipY + chip_size_y * moduleIndex
            new_y_index = y - lines_to_remove_array[moduleIndex] * moduleIndex
            new_y_array[new_y_index] = y
            new_y_array_module_id[new_y_index] = moduleIndex

    # Collect deltas and gammas.
    deltas, gammas = get_angles(path)
    # for idx, data in enumerate(images):
    index = 2
    if index == 2:
        data = images[2]
        for pointIndex in range(deltas.shape[0]):
            delta = deltas[pointIndex]
            print(delta)

            # extracting the XY coordinates for the rest of the scan transformation
            # ========psiAve = 1, deltaPsi = 1=============================================

            diffracto_delta_rad = (delta + delta_offset) * deg2rad
            sindelta = numpy.sin(diffracto_delta_rad)
            cosdelta = numpy.cos(diffracto_delta_rad)
            diffracto_gam_rad = (gammas[0] + gamma_offset) * deg2rad
            singamma = numpy.sin(diffracto_gam_rad)
            cosgamma = numpy.cos(diffracto_gam_rad)

            # the array this_corrected_image contains the corrected image (double pixels corrections)
            two_th_array = numpy.zeros((image_corr1_size_y, image_corr1_size_x))
            psi_array = numpy.zeros((image_corr1_size_y, image_corr1_size_x))

            x_line = numpy.linspace(0, image_corr1_size_x - 1, image_corr1_size_x)
            x_matrix = numpy.zeros((image_corr1_size_x,  image_corr1_size_y))
            for a in range (image_corr1_size_y):
                x_matrix[:, a] = x_line[:]

            y_line = numpy.linspace(0, image_corr1_size_y - 1, image_corr1_size_y)
            y_matrix = numpy.zeros((image_corr1_size_x,  image_corr1_size_y))
            for a in range (image_corr1_size_x):
                y_matrix[a, :] = y_line[:]

            corr_array_x = distance  # for xpad3.2 like
            corr_array_z = y_center_detector - y_matrix  # for xpad3.2 like
            corr_array_y = x_center_detector - x_matrix  # sign is reversed
            temp_x = corr_array_x; temp_y = corr_array_z * (-1.0); temp_z = corr_array_y

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
            this_delta = numpy.arccos(corr_array_x / norm) * inv_deg2rad

            # psi = angle between vector(0, corr_array_y, corr_array_z) and the vector(0,1,0)
            sign = numpy.sign(corr_array_z)
            cos_psi_rad = corr_array_y / numpy.sqrt(corr_array_y2 + corr_array_z2)
            psi = numpy.arccos(cos_psi_rad) * inv_deg2rad * sign

            psi[psi < 0] += 360
            psi -= 90
            psi_array = psi.T
            two_th_array = this_delta.T

            # ======================end geometry====================================

            # dealing now with the intensitiespointIndex
            this_image = data[pointIndex]
            this_image = flat_image_inv * this_image
            this_image = ndimage.median_filter(this_image, 3)

            this_corrected_image = numpy.zeros((image_corr1_size_y, image_corr1_size_x))
            intensity_factor = new_x_ifactor_array  # x
            new_y_array = new_y_array.astype('int')
            new_x_array = new_x_array.astype('int')

            for x in range(0, image_corr1_size_x):
                this_corrected_image[:, x] = this_image[new_y_array[:], new_x_array[x]]
                if intensity_factor[x] < 0:
                    this_corrected_image[:, x] = (this_image[new_y_array[:], new_x_array[x] - 1]
                                                  + this_image[new_y_array[:], new_x_array[x] + 1]) \
                                                 / factor_intensity_double_pixel
                    this_corrected_image[numpy.isnan(this_corrected_image)] = -100000

            # correct the double lines (last and 1st line of the modules, at their junction)

            # last line of module1 = 119, is the 1st line to correct
            line_index1 = chip_size_y - 1

            # 1st line of module2 (after adding the 3 empty lines), becomes the 5th line to correct
            line_index5 = line_index1 + 3 + 1
            line_index2 = line_index1 + 1
            line_index3 = line_index1 + 2
            line_index4 = line_index1 + 3

            i1 = this_corrected_image[line_index1, :], i1new = i1 / factor_intensity_double_pixel
            i5 = this_corrected_image[line_index5, :], i5new = i5 / factor_intensity_double_pixel
            i3 = (i1new + i5new) / 2.0
            this_corrected_image[line_index1, :] = i1new
            this_corrected_image[line_index2, :] = i1new
            this_corrected_image[line_index3, :] = i3
            this_corrected_image[line_index5, :] = i5new
            this_corrected_image[line_index4, :] = i5new

            # IntensityArray = this_corrected_image.T.reshape(image_corr1_size_x * image_corr1_size_y)
            # this is the corrected intensity of each pixel, on the image having the new size
            tth = [], psi = [], corrected = []
            for x in range (0, image_corr1_size_x):
                for y in range (0, image_corr1_size_y):
                    tth.append(two_th_array[y, x])
                    psi.append(psi_array[y, x])
                    corrected.append(this_corrected_image[y, x])
            unfolded_data.append((pointIndex, tth, psi, corrected))
    return unfolded_data


def get_angles(path: str) -> (numpy.ndarray, numpy.ndarray):
    with File(path, mode='r') as h5file:
        for path in
        try:
            delta_array = numpy.zeros(get_dataset(h5file,
                                                  DatasetPathWithAttribute("label", b"Delta")).shape)
            for idx, delta in enumerate(get_dataset(h5file,
                                                    DatasetPathWithAttribute("label", b"Delta"))):
                delta_array[idx] = delta
        except AttributeError:
            try:
                delta_array = numpy.zeros(get_dataset(h5file,
                                                      DatasetPathContains("d13-1-cx1__EX__DIF.1-DELTA__#1/raw_value")).shape)
                for idx, delta in enumerate(get_dataset(h5file,
                                                        DatasetPathContains("d13-1-cx1__EX__DIF.1-DELTA__#1/raw_value"))):
                    delta_array[idx] = delta
            except AttributeError:
                try:
                    delta_array = numpy.zeros(get_dataset(h5file,
                                                          DatasetPathContains("D13-1-CX1__EX__DIF.1-DELTA__#1/raw_value")).shape)
                    for idx, delta in enumerate(get_dataset(h5file,
                                                            DatasetPathContains("D13-1-CX1__EX__DIF.1-DELTA__#1/raw_value"))):
                        delta_array[idx] = delta
                except AttributeError:
                    delta_array = 0
        try:
            gamma_array = numpy.zeros(get_dataset(h5file,
                                                  DatasetPathWithAttribute("label", b"Gamma")).shape)
            for idx, gamma in enumerate(get_dataset(h5file,
                                                    DatasetPathWithAttribute("label", b"Gamma"))):
                gamma_array[idx] = gamma
        except AttributeError:
            try:
                gamma_array = numpy.zeros(get_dataset(h5file,
                                                      DatasetPathContains("d13-1-cx1__EX__DIF.1-GAMMA__#1/raw_value")).shape)
                for idx, gamma in enumerate(get_dataset(h5file,
                                                        DatasetPathContains("d13-1-cx1__EX__DIF.1-GAMMA__#1/raw_value"))):
                    gamma_array[idx] = gamma
            except AttributeError:
                try:
                    gamma_array = numpy.zeros(get_dataset(h5file,
                                                          DatasetPathContains("D13-1-CX1__EX__DIF.1-GAMMA__#1/raw_value")).shape)
                    for idx, gamma in enumerate(get_dataset(h5file,
                                                            DatasetPathContains("D13-1-CX1__EX__DIF.1-GAMMA__#1/raw_value"))):
                        gamma_array[idx] = gamma
                except AttributeError:
                    gamma_array = 0
    return delta_array, gamma_array
