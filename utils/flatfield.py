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

def correct_and_unfold_data(flatImg: numpy.ndarray, images: numpy.ndarray, deltas: numpy.ndarray, gammas: numpy.ndarray, contextual_data: dict):
    self.correct_double_pixels()
    if len(deltas) == 1 and len(gammas) == 1:
        self.compute_geometry(deltas[0], gammas[0])
        for data in images:
            self.unfold_data(data, deltas[0], gammas[0])
    if len(deltas) > 1:
        for data, delta in images, deltas:
            self.compute_geometry(delta, gammas[0])
            self.unfold_data(data, delta, gammas[0])
    if len(gammas) > 1:
        for data, gamma in images, gammas:
            self.compute_geometry(deltas[0], gamma)
            self.unfold_data(data, deltas[0], gamma)

def correct_and_unfold_data(flatImg: numpy.ndarray, data: numpy.ndarray, contextual_data: dict, inputDataFolder, outputPath):
    #flatfields correction
    factorIdoublePixel = 1.0 #make suree it is properly resetted to 1, in case it was not modified in the header

    if not flatImg is None:
        flatImg = 1.0*flatImg / flatImg.mean() 
	flatImg_inv = 1.0/flatImg 
	flatImg_inv[numpy.isnan(flatImg_inv)] = -10000000
	flatImg_inv[numpy.isinf(flatImg_inv)] = -10000000
        
    #geometry informations*********************************
    calib = contextual_data["distance"]  # pixels in 1 deg.76.78
    XcenDetector = contextual_data["x"] + 3 * (contextual_data["x"]//80) # Corrected positions (add 3 pixels whenever cross 80 * i in X)
    YcenDetector = contextual_data["y"] + 3 * (contextual_data["y"]//120) # position of direct beam on xpad at (delltaOffset, gamOffset). Use the 'corrected' positions (add 3 pixels whenever cross 120 in Y)
    deltaOffset = contextual_data["delta_offset"]
    gamOffset  = contextual_data["gamma_offset"] # positions in diffracto angles for which the above values XcenDetector, YcenDetectors are reported
    chip_sizeX = 80; chip_sizeY = 120 # chip dimension, in pixels (X = horiz, Y = vertical)
    numberOfModules = data.shape()[1]//chip_sizeY
    numberOfChips = data.shape()[2]//chip_sizeX # detector dimension, XPAD S-140
    lines_to_remove_array = [0, -3]; # adding 3 more lines, corresponding to the double pixels on the last and 1st line of the modules
    #******************************************************

    deg2rad = numpy.pi/180; inv_deg2rad = 1/deg2rad
    distance = calib/numpy.tan(1.0*deg2rad); # distance xpad to sample, in pixel units
        
    #calculate the total number of lines to remove from the image
    lines_to_remove = 0; #initialize to 0 for calculating the sum. For xpad 3.2 these lines (negative value) will be added
    for i in range (0, numberOfModules):
	lines_to_remove +=  lines_to_remove_array[i]
    #size of the resulting (corrected) image
    image_corr1_sizeY = numberOfModules * chip_sizeY - lines_to_remove;
    image_corr1_sizeX = (numberOfChips - 1) * 3 + numberOfChips * chip_sizeX # considers the 2.5x pixels

    #---------- double pix corr ---------
    #=====================================
    newX_array = numpy.zeros(image_corr1_sizeX); newX_Ifactor_array = numpy.zeros(image_corr1_sizeX)
    for x in range(0, 79): # this is the 1st chip (index chip = 0)
	newX_array[x] = x; 
	newX_Ifactor_array[x] = 1 # no change in intensity
	
    newX_array[79] = 79; newX_Ifactor_array[79] = 1/factorIdoublePixel;
    newX_array[80] = 79; newX_Ifactor_array[80] = 1/factorIdoublePixel;
    newX_array[81] = 79; newX_Ifactor_array[81] = -1
	
    for indexChip in range (1, 6):
	temp_index0 = indexChip * 83 
	for x in range(1, 79): # this are the regular size (130 um) pixels
	    temp_index = temp_index0 + x
	    newX_array[temp_index] = x + 80*indexChip
	    newX_Ifactor_array[temp_index] = 1 # no change in intensity
	newX_array[temp_index0] = 80*indexChip; newX_Ifactor_array[temp_index0] = 1/factorIdoublePixel # 1st double column
	newX_array[temp_index0-1] = 80*indexChip; newX_Ifactor_array[temp_index0-1] = 1/factorIdoublePixel
	newX_array[temp_index0+79] = 80*indexChip+79; newX_Ifactor_array[temp_index0+79] = 1/factorIdoublePixel # last double column
	newX_array[temp_index0+80] = 80*indexChip+79; newX_Ifactor_array[temp_index0+80] = 1/factorIdoublePixel
	newX_array[temp_index0+81] = 80*indexChip+79; newX_Ifactor_array[temp_index0+81] = -1
	
    for x in range (6*80+1, 560): # this is the last chip (index chip = 6)
	temp_index = 18 + x
	newX_array[temp_index] = x
	newX_Ifactor_array[temp_index] = 1 # no change in intensity
	
    newX_array[497] = 480; newX_Ifactor_array[497] = 1/factorIdoublePixel;
    newX_array[498] = 480; newX_Ifactor_array[498] = 1/factorIdoublePixel;
	
    newY_array = numpy.zeros(image_corr1_sizeY); # correspondance oldY - newY
    newY_array_moduleID = numpy.zeros(image_corr1_sizeY); # will keep trace of module index

    newYindex = 0;
    for moduleIndex in range (0, numberOfModules):
	for chipY in range (0, chip_sizeY):
	    y = chipY + chip_sizeY * moduleIndex
	    newYindex = y - lines_to_remove_array[moduleIndex] * moduleIndex
	    newY_array[newYindex] = y
	    newY_array_moduleID[newYindex] = moduleIndex

    #END---------- double pix corr ---------
    #==========================================
	
        """
        #create the folder to save data if it does not exist
	try:
		os.stat(outputPath)
	except:
		os.mkdir(outputPath)
	fileSavePath = outputPath + "scan_%d/"%(scanNo)	
	try:
		os.stat(fileSavePath)
	except:
		os.mkdir(fileSavePath)		

	pathData = inputDataFolder 
	fileName = fileNameRoot + str(scanNo) + ".nxs" 
	#read here the scan informations (delta, gamma)
	with h5py.File(pathData+fileName,'r') as f: #will properly close it once the indented code is executed
	        group1 = f.get(f.keys()[0])
	        #deltaArray = numpy.array(group1['DIFFABS/D13-1-CX1__EX__DIF.1-DELTA__#1/raw_value'])
	        gam = numpy.array(group1['DIFFABS/d13-1-cx1__ex__dif.1-gamma/raw_value/'])

	#reading images in the .nxs file 	
	file1 = tables.openFile(pathData+fileName)	
	fileNameRoot1 = file1.root._v_groups.keys()[0]
	command = "file1.root.__getattr__(\""+str(fileNameRoot1)+"\")"

        
     
	
	##############################Si fichier trop lourd##############
	xpadImage=eval(command+".scan_data.data_"+GLOBAL_xpad_dataset+".read(0)")
	for partie in range(1,144+1): #679 pouyr le scan 592
	       xpadImage_p = eval(command+".scan_data.data_"+GLOBAL_xpad_dataset+".read(%s)"%(partie))
	       #print numpy.shape(xpadImage_p)
	       xpadImage = numpy.append(xpadImage, xpadImage_p, axis=0)
	####################################
	
     ########### Sinon
	#xpadImage = eval(command+".scan_data.data_"+GLOBAL_xpad_dataset+".read()")
	#print xpadImage	
	deltaArray = eval(command+".scan_data.data_15.read()")
							
	file1.close()

        """
	
    for pointIndex in range (deltaArray.shape[0]):	

	delta = deltaArray[pointIndex]  
	#extracting the XY coordinates for the rest of the scan transformation
	#========psiAve = 1, deltaPsi = 1=============================================	
        
	diffracto_delta_rad = (delta + deltaOffset) * deg2rad
	sindelta = numpy.sin(diffracto_delta_rad); cosdelta = numpy.cos(diffracto_delta_rad)
	diffracto_gam_rad = (gam + gamOffset) * deg2rad 
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
	
	corrX = distance; # for xpad3.2 like
	corrZ = YcenDetector - y_matrix # for xpad3.2 like
	corrY = XcenDetector - x_matrix # sign is reversed
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
	thisSize = image_corr1_sizeX * image_corr1_sizeY
	thisImage = xpadImage[pointIndex]  
	thisImage = flatImg_inv * thisImage
	thisImage = ndimage.median_filter(thisImage, 3)

	"""
	#masking the bad pixels
	thisImage[110:122, 373:385] =  -1000000000
	thisImage[112:118, 541:547] =  -1000000000
        """

	thisCorrectedImage = numpy.zeros((image_corr1_sizeY, image_corr1_sizeX))
	Ifactor = newX_Ifactor_array # x
	newY_array = newY_array.astype('int')
	newX_array = newX_array.astype('int')

	for x in range (0, image_corr1_sizeX): 
	    thisCorrectedImage[:, x] = thisImage[newY_array[:], newX_array[x]]
	    if Ifactor[x] < 0:
		#print "%s %s" %(x, Ifactor[x])
		thisCorrectedImage[:, x] = (thisImage[newY_array[:], newX_array[x] - 1] + thisImage[newY_array[:], newX_array[x] + 1]) / 2.0 / factorIdoublePixel
	thisCorrectedImage[numpy.isnan(thisCorrectedImage)] = -100000

	# correct the double lines (last and 1st line of the modules, at their junction)
	lineIndex1 = chip_sizeY - 1 # last line of module1 = 119, is the 1st line to correct
	lineIndex5 = lineIndex1 + 3 + 1 # 1st line of module2 (after adding the 3 empty lines), becomes the 5th line tocorrect
	lineIndex2 = lineIndex1 + 1; lineIndex3 = lineIndex1 + 2; lineIndex4 = lineIndex1 + 3
	#thisSize = image_corr1_sizeX*image_corr1_sizeY #out of the loop
	#IntensityArray = numpy.zeros(thisSize)

	i1 = thisCorrectedImage[lineIndex1, :]; i5 = thisCorrectedImage[lineIndex5, :]
	i1new = i1 / factorIdoublePixel; i5new = i5 / factorIdoublePixel; i3 = (i1new + i5new) / 2.0
	thisCorrectedImage[lineIndex1, :] = i1new; thisCorrectedImage[lineIndex2, :] = i1new
	thisCorrectedImage[lineIndex3, :] = i3;
	thisCorrectedImage[lineIndex5, :] = i5new; thisCorrectedImage[lineIndex4, :] = i5new
	
	IntensityArray = thisCorrectedImage.T.reshape(image_corr1_sizeX * image_corr1_sizeY)
	#this is the corrected intensity of each pixel, on the image having the new size

	#saving the Intensity file (in correspondence with XY file)  
	xyzLine = ""
	for x in range (0, image_corr1_sizeX):
	    for y in range (0, image_corr1_sizeY):
		xyzLine += ""+str(twoThArray[y, x])+" "+str(psiArray[y, x])+" "+str(thisCorrectedImage[y, x])+"\n"
	#saving the file
	#####ATTENTION####
	XYZlogFileName = "raw_%d.txt" %(pointIndex+0)#modifier cette valeur selon le découpage...
	with open(fileSavePath+XYZlogFileName, "a") as saveFile:
	    saveFile.write(xyzLine)
