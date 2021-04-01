import cv2
import math
import sys
import os
from skimage import io

'''
    Tiling has so far been implemented such that an optimal divisor is sought that brings the tile resolution as close to a user defined resolution
    A future way of doing it might be to find a "best practice" resolution for the entire pipeline and then add padding functionality to this, to force the tiling into a certain resolution.
    However, tileWriter still does support irregular tiles, it's just not nice to have irregular tiles for downstream functionality.
'''
def calculateOptimalTileSize(img_path, target_X, target_Y):
    """Calculates the optimal tile size to cut the given image into to get tiles the size of target_X, target_Y

    Parameters
    ----------
    img_path : str
        Path to input image.
    target_X : int
        Desired X-resolution.
    target_Y : int
        Desired Y-resolution

    Returns
    -------
    int, int
        Returns optimal X and Y-resolutions to tile the input image in to get the target resolution, while retaining evenly sized tiles.
    """
    img=io.imread(img_path)
    shape = img.shape
    def roundUpTo100(x):
        result = x if x % 100 == 0 else x + 100 - x % 100
        return result
    optimal_x = findOptimalDivisor(roundUpTo100(shape[1]), target_X)
    optimal_y = findOptimalDivisor(roundUpTo100(shape[0]), target_Y)
    return int(optimal_x), int(optimal_y)


def writeTiles(img_path, prefix,tile_size_x, tile_size_y, ):
    # img = cv2.imread(img_path, 1)
    img = io.imread(img_path)
    # Don't forget, cv2 works with shape = (y, x), meaning rows, columns
    img_shape=img.shape
    offset_x = tile_size_x
    offset_y = tile_size_y
    tile_size = (tile_size_x, tile_size_y)
    offset = (offset_x, offset_y)
    for i in range(int(math.ceil(img_shape[0]/(offset[1] * 1.0)))):
        for j in range(int(math.ceil(img_shape[1]/(offset[0] * 1.0)))):
            # Multiplier is used for calculating the tile number, it represents how many tiles will be created on the x-axis
            multiplier = (int(math.ceil(img_shape[1]/(offset[0] * 1.0)))) 
            cropped_img = img[offset[1]*i:min(offset[1]*i+tile_size[1], img_shape[0]), offset[0]*j:min(offset[0]*j+tile_size[0], img_shape[1])]
            tile_number = multiplier*int(i) + int(j) +1
            cv2.imwrite(f"{prefix}_tiled_{tile_number}.tif", cropped_img)


def findOptimalDivisor(number: int, target_quotient: int):
    """Finds the optimal int divisor for the given number that results in the quotient as close to the given quotient as possible

    Parameters
    ----------
    number : int
        The number that will be divided by the optimal divisor
    target_quotient : int
        The quotient that you want the result of the division to be as close to as possible

    Returns
    -------
    int
        Returns the result of the optimal divison
    """
    divisors = [i for i in range(1,number) if number % i==0]
    quotients = [number/divisor for divisor in divisors]
    min_loss = min(quotients, key=lambda x:abs(int(x)-int(target_quotient)))
    return min_loss

image = sys.argv[1]
prefix = os.path.splitext(image)[0]
tile_x, tile_y = calculateOptimalTileSize(image,sys.argv[2], sys.argv[3])
print(tile_x, tile_y)
writeTiles(image, prefix, tile_size_x=tile_x, tile_size_y=tile_y)