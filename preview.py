import os, sys, re, gdal
from spectral import *
from gdalconst import *
import numpy as np
from Tkinter import *
from PIL import Image, ImageEnhance
import tkFileDialog, Tkconstants


def closest_channel (dict, value):
	"""Finds closest channel for specified
	return number of channel as integer value
	"""
	no_channels = []
	fraction = float("inf")
	for key, wavelength in dict_channel.items():
		ret = abs(wavelength-value)
		if (ret < fraction):
			fraction = ret
			no_channel = int(key)
	return no_channel


def get_band (dataset, channel_value):
	"""Getting band on specified channel value
	return as array of values
	"""
	return dataset.GetRasterBand(closest_channel(dict_channel, channel_value)-1)


def generate_previews ():
	"""Generating previews of pix files"""
	#Iterating over folder and finding files with .pix and .hdr suffixes, then putting to lists
	for i in os.listdir(dirname):
	    if i.endswith(".pix") and i.startswith("CASI_"):
	    	pix_list.append(i)	
	    if i.endswith(".hdr") and i.startswith("CASI_"):
	        hdr_list.append(i)

	#Iterating over list with .pix and .hdr file names and finding for the same name
	for pix_name in pix_list:
		for hdr_name in hdr_list:
			if pix_name.startswith(hdr_name[:-4]):
				#If the names are the same open file and read lines
				with open(dirname+"/"+hdr_name, "r") as file:
					lines = (file.readlines())
					for channel in lines:
						#Putting channels to dictionary (number of channel : wavelength)
						if (channel.startswith("Channel")):
							split_list = channel.split(" ")
							dict_channel[int(split_list[1])] = float(re.findall("\d+\.\d+", split_list[2])[0])
					
					#Opening reading of pix file
					dataset = gdal.Open(dirname+"/"+pix_name, GA_ReadOnly)

					#Getting size of pix file
					cols = dataset.RasterXSize
					rows = dataset.RasterYSize

					#Creating numpy array fill with zeros
					rgbArray = np.zeros((rows,cols,3))
					
					#Putting data to ndarray				
					rgbArray[..., 0] = get_band(dataset, 640).ReadAsArray (0, 0, cols, rows)
					rgbArray[..., 1] = get_band(dataset, 550).ReadAsArray (0, 0, cols, rows)
					rgbArray[..., 2] = get_band(dataset, 460).ReadAsArray (0, 0, cols, rows)
					
					#Saving image in specified folder
					minv = (float(minimum.get())/100)
					maxv = (float(maximum.get())/100)

					save_rgb(dirname+"/"+pix_name+'.jpg', rgbArray, stretch=(minv, maxv))
									
					#Insert message in the textbox
					messageBox.insert(END, "Preview of "+pix_name+" was created\n")
														
					#Closing dataset
					dataset = None

					#Clearing dictionary with channel values
					dict_channel.clear()
				break
	del pix_list[:]
	del hdr_list[:]

def openDirectory():
	"""Opening directory with pix and hdr files"""
	global dirname 
	dirname = tkFileDialog.askdirectory(parent=root, title='Select folder with pix files')
	

#Creating dictionary and list for storing names of files (.pix and .hdr) and channel numbers 
dict_channel = {}
pix_list = []
hdr_list = []

root = Tk()
root.title("Preview generator")

#Clip from left and right
Label(root, text="Minimum [%]:").grid(row=0)
Label(root, text="Maximum [%]:").grid(row=1)

minimum = Entry(root)
maximum = Entry(root)

minimum.insert(0, "0")
maximum.insert(0, "0")

minimum.grid(row=0, column=1)
maximum.grid(row=1, column=1)

Button(root, text = 'Choose folder', fg = 'black', command=openDirectory).grid(row=2, column=0)
Button(root, text="Generate previews", command=generate_previews).grid(row=2, column=1)

messageBox=Text(root, height="10", width="70")
messageBox.grid(row=3, columnspan=2)

root.mainloop()

			
			
	




