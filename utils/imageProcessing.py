from h5py import Dataset, File
from PyQt5.QtWidgets import QMessageBox, QProgressBar, QApplication, QWidget
from scipy import ndimage
from utils.nexusNavigation import get_dataset, DatasetPathWithAttribute, DatasetPathContains

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

def correct_and_unfold_data(flat_image: numpy.ndarray, images: numpy.ndarray, path :str, contextual_data: dict) -> [set]:

    # Result
    unfolded_data = []

    # Constant that will help us during the computation
    deg2rad = numpy.pi / 180
    inv_deg2rad = 1 / (numpy.pi/180)

    # We assign
    calib = contextual_data["distance"]  # pixels in 1 deg.76.78
    chip_size_x = 80
    chip_size_y = 120 # chip dimension, in pixels (X = horiz, Y = vertical)
    x_center_detector = contextual_data["x"] + 3 * (contextual_data["x"] // chip_size_x) # Corrected positions (add 3 pixels whenever cross 80 * i in X)
    y_center_detector = contextual_data["y"] + 3 * (contextual_data["y"] // chip_size_y) # position of direct beam on xpad at (delltaOffset, gamOffset). Use the 'corrected' positions (add 3 pixels whenever cross 120 in Y)
    delta_offset = contextual_data["delta_offset"]
    gamma_offset = contextual_data["gamma_offset"] # positions in diffracto angles for which the above values XcenDetector, YcenDetectors are reported
    number_of_modules = images.shape[1] // chip_size_y
    number_of_chips = images.shape[2] // chip_size_x # detector dimension, XPAD S-140
    distance = contextual_data["distance"] / numpy.tan(1.0 * deg2rad)
    lines_to_remove_array = [0, -3]

    if not flat_image is None:
        factorIdoublePixel = 1.0
        flat_image = 1.0 * flat_image / flat_image.mean()
        flat_image_inv = 1.0 / flat_image
        flat_image_inv[numpy.isnan(flat_image_inv)] = -10000000
        flat_image_inv[numpy.isinf(flat_image_inv)] = -10000000
    else:
        flat_image_inv = numpy.ones_like(images[0])
        factorIdoublePixel = 2.5

    lines_to_remove = -3
    #size of the resulting (corrected) image
    image_corr1_sizeY = number_of_modules * chip_size_y - lines_to_remove
    image_corr1_sizeX = (number_of_chips - 1) * 3 + number_of_chips * chip_size_x

    newX_array = numpy.zeros(image_corr1_sizeX); newX_Ifactor_array = numpy.zeros(image_corr1_sizeX)
    for x in range(0, 79): # this is the 1st chip (index chip = 0)
        newX_array[x] = x
        newX_Ifactor_array[x] = 1 # no change in intensity

    newX_array[79] = 79; newX_Ifactor_array[79] = 1/factorIdoublePixel
    newX_array[80] = 79; newX_Ifactor_array[80] = 1/factorIdoublePixel
    newX_array[81] = 79; newX_Ifactor_array[81] = -1

    for indexChip in range (1, 6):
        temp_index0 = indexChip * 83
        for x in range(1, 79): # this are the regular size (130 um) pixels
            temp_index = temp_index0 + x
            newX_array[temp_index] = x + 80 * indexChip
            newX_Ifactor_array[temp_index] = 1 # no change in intensity
        newX_array[temp_index0] = 80 * indexChip; newX_Ifactor_array[temp_index0] = 1 / factorIdoublePixel # 1st double column
        newX_array[temp_index0 - 1] = 80 * indexChip; newX_Ifactor_array[temp_index0 - 1] = 1 / factorIdoublePixel
        newX_array[temp_index0 + 79] = 80 * indexChip + 79; newX_Ifactor_array[temp_index0 + 79] = 1 / factorIdoublePixel # last double column
        newX_array[temp_index0 + 80] = 80 * indexChip + 79; newX_Ifactor_array[temp_index0 + 80] = 1 / factorIdoublePixel
        newX_array[temp_index0 + 81] = 80 * indexChip + 79; newX_Ifactor_array[temp_index0 + 81] = -1

    for x in range (6 * 80 + 1, 560): # this is the last chip (index chip = 6)
        temp_index = 18 + x
        newX_array[temp_index] = x
        newX_Ifactor_array[temp_index] = 1 # no change in intensity

    newX_array[497] = 480; newX_Ifactor_array[497] = 1/factorIdoublePixel
    newX_array[498] = 480; newX_Ifactor_array[498] = 1/factorIdoublePixel

    newY_array = numpy.zeros(image_corr1_sizeY); # correspondance oldY - newY
    newY_array_moduleID = numpy.zeros(image_corr1_sizeY) # will keep trace of module index

    newYindex = 0
    for moduleIndex in range (0, number_of_modules):
        for chipY in range (0, chip_size_y):
            y = chipY + chip_size_y * moduleIndex
            newYindex = y - lines_to_remove_array[moduleIndex] * moduleIndex
            newY_array[newYindex] = y
            newY_array_moduleID[newYindex] = moduleIndex

    # Collect deltas and gammas.
    deltas, gammas = get_angles(path)
    # for idx, data in enumerate(images):
    index = 2
    if index == 2:
        data = images[2]
        for pointIndex in range(deltas.shape[0]):
            delta = deltas[pointIndex]
	    #extracting the XY coordinates for the rest of the scan transformation
            #========psiAve = 1, deltaPsi = 1=============================================

            diffracto_delta_rad = (delta + delta_offset) * deg2rad
            sindelta = numpy.sin(diffracto_delta_rad); cosdelta = numpy.cos(diffracto_delta_rad)
            diffracto_gam_rad = (gammas[0] + gamma_offset) * deg2rad
            singamma = numpy.sin(diffracto_gam_rad); cosgamma = numpy.cos(diffracto_gam_rad)

            #the array thisCorrectedImage contains the corrected image (double pixels corrections)
            twoThArray = numpy.zeros((image_corr1_sizeY, image_corr1_sizeX))
            psiArray = numpy.zeros((image_corr1_sizeY, image_corr1_sizeX))

            x_line = numpy.linspace(0, image_corr1_sizeX - 1, image_corr1_sizeX)
            x_matrix = numpy.zeros((image_corr1_sizeX,  image_corr1_sizeY))
            for a in range (image_corr1_sizeY):
                x_matrix[:, a] = x_line[:]

            y_line = numpy.linspace(0, image_corr1_sizeY - 1, image_corr1_sizeY)
            y_matrix = numpy.zeros((image_corr1_sizeX,  image_corr1_sizeY))
            for a in range (image_corr1_sizeX):
                y_matrix[a, :] = y_line[:]

            corrX = distance # for xpad3.2 like
            corrZ = y_center_detector - y_matrix # for xpad3.2 like
            corrY = x_center_detector - x_matrix # sign is reversed
            tempX = corrX; tempY = corrZ * (-1.0); tempZ = corrY

            x1 = tempX * cosdelta - tempZ * sindelta
            y1 = tempY
            z1 = tempX * sindelta + tempZ * cosdelta
            #apply Rz(-gamma); due to geo consideration on the image, the gamma rotation should be negative for gam>0
            #apply the same considerations as for the delta, and keep gam values positive
            corrX = x1 * cosgamma + y1 * singamma
            corrY = -x1 * singamma + y1 * cosgamma
            corrZ = z1
            #calculate the square values and normalization
            corrX2 = corrX * corrX; corrY2 = corrY * corrY; corrZ2 = corrZ * corrZ
            norm = numpy.sqrt(corrX2 + corrY2 + corrZ2)
            #calculate the corresponding angles
            #delta = angle between vector(corrX, corrY, corrZ) and the vector(1,0,0)
            thisdelta = numpy.arccos(corrX / norm) * inv_deg2rad
            #psi = angle between vector(0, corrY, corrZ) and the vector(0,1,0)

            sign = numpy.sign(corrZ)
            cos_psi_rad = corrY / numpy.sqrt(corrY2 + corrZ2)
            psi = numpy.arccos(cos_psi_rad) * inv_deg2rad * sign

            psi[psi<0] += 360
            psi -= 90
            psiArray = psi.T
            twoThArray = thisdelta.T
            #end geometry

            #dealing now with the intensitiespointIndex
            thisImage = data[pointIndex]
            thisImage = flat_image_inv * thisImage
            thisImage = ndimage.median_filter(thisImage, 3)

            thisCorrectedImage = numpy.zeros((image_corr1_sizeY, image_corr1_sizeX))
            Ifactor = newX_Ifactor_array # x
            newY_array = newY_array.astype('int')
            newX_array = newX_array.astype('int')

            for x in range (0, image_corr1_sizeX):
                thisCorrectedImage[:, x] = thisImage[newY_array[:], newX_array[x]]
                if Ifactor[x] < 0:
                    thisCorrectedImage[:, x] = (thisImage[newY_array[:], newX_array[x] - 1] + thisImage[newY_array[:], newX_array[x] + 1]) / factorIdoublePixel
                    thisCorrectedImage[numpy.isnan(thisCorrectedImage)] = -100000

            # correct the double lines (last and 1st line of the modules, at their junction)
            lineIndex1 = chip_size_y - 1 # last line of module1 = 119, is the 1st line to correct
            lineIndex5 = lineIndex1 + 3 + 1 # 1st line of module2 (after adding the 3 empty lines), becomes the 5th line tocorrect
            lineIndex2 = lineIndex1 + 1; lineIndex3 = lineIndex1 + 2; lineIndex4 = lineIndex1 + 3

            i1 = thisCorrectedImage[lineIndex1, :]; i5 = thisCorrectedImage[lineIndex5, :]
            i1new = i1 / factorIdoublePixel; i5new = i5 / factorIdoublePixel; i3 = (i1new + i5new) / 2.0
            thisCorrectedImage[lineIndex1, :] = i1new; thisCorrectedImage[lineIndex2, :] = i1new
            thisCorrectedImage[lineIndex3, :] = i3
            thisCorrectedImage[lineIndex5, :] = i5new; thisCorrectedImage[lineIndex4, :] = i5new

            IntensityArray = thisCorrectedImage.T.reshape(image_corr1_sizeX * image_corr1_sizeY)
            #this is the corrected intensity of each pixel, on the image having the new size            
            tth = []; psi = []; corrected = []
            for x in range (0, image_corr1_sizeX):
                for y in range (0, image_corr1_sizeY):
                    tth.append(twoThArray[y, x])
                    psi.append(psiArray[y, x])
                    corrected.append(thisCorrectedImage[y, x])
            unfolded_data.append((pointIndex, tth, psi, corrected))
    return unfolded_data

def get_angles(path: str) -> (numpy.ndarray, numpy.ndarray):
        with File(path, mode='r') as h5file:
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
