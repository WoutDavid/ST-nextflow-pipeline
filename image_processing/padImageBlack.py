import cv2
import os
import sys
import math
from matplotlib import pyplot as plt
from icecream import ic
from PIL import Image
# important for giant tiff files, otherwise PIL thinks it's malware
Image.MAX_IMAGE_PIXELS = None



def getResolution(filepath):
    """Prints the resolution of the given image.

    Parameters
    ----------
    filepath : str
        Path to input image.

    Returns
    -------
    int, int
        returns the amount of width and height pixels the input image has: (X,Y)
    """
    im = Image.open(filepath)
    width, height = im.size
    return width, height

def pad(filepath, target_width, target_height, expected_width=0, expected_height=0):
    #returns an openCV image, probably to be saved by imwrite by the caller

    #Note hare that i use ceil to round up, this might cause some unwanted behaviour in the future.
    currentWidth, currentHeight = getResolution(filepath)

    widthToAdd = math.floor((target_width - currentWidth)/2)
    heightToAdd = math.floor((target_height - currentHeight)/2)
    img = cv2.cv2.imread(filepath, cv2.cv2.IMREAD_ANYDEPTH)
    #In case there is still a difference in pixels to add and the wanted resolution, add that difference to the right or top,
    # depending on whether the difference is in width or in height respectively
    differenceWidth = (target_width-currentWidth) - widthToAdd*2
    differenceHeight = (target_height-currentHeight) - heightToAdd*2

    paddedImage = cv2.cv2.copyMakeBorder(img, heightToAdd+differenceHeight, heightToAdd, widthToAdd, widthToAdd+differenceWidth, cv2.cv2.BORDER_CONSTANT)
    newHeight = paddedImage.shape[0]
    newWidth = paddedImage.shape[1]

    if expected_height == 0 or expected_width == 0:
        pass
    else:
        if expected_width != newWidth:
            print("Warning: Width of resulting padded image is not equal to the entered expected width")
        if expected_height != newHeight:
            print("Warning: Height of resulting padded image is not equal to the entered expected height")
    return paddedImage 

image = sys.argv[1]
prefix = os.path.splitext(image)[0]
target_x = sys.argv[2]
target_y = sys.argv[3]

image_padded = pad(image, 22000,22000)
cv2.imwrite(f"{prefix}_padded.tif")
