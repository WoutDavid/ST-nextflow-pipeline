import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import cv2
from typing import Tuple
reference = "/media/tool/starfish_test_data/ExampleInSituSequencing/DO/REF.TIF"
blobs = "/home/nacho/Documents/Code/communISS/results/blobs/concat_blobs.csv"

''' cv2 coordinate system:
0/0---X--->
 |
 |
 Y
 |
 |
 v
'''

def plotSpotsOnWholeImage(path_to_spotsCSV: str, tile_grid_shape: Tuple[int, int], tile_size_x: int, tile_size_y: int, path_to_original_img=""):
    """Takes a csv of spots as calculated by spotDetection.py and plots them on an untiled empty canvas that has the size of the original image.

    Parameters
    ----------
    path_to_spotsCSV : str
        Path to input csv file that contains the spots. They should include the following columns, spelled as such:
        'Tile', 'X', 'Y', 'Sigma'
    tile_grid_shape : tuple
        Tuple of ints containing the x and y size of the original image (in that order). eg.: (1330, 980) 
    tile_size_x : int
        Number of columns in the tiled images, or the size of the X-axis.
    tile_size_y : int
        Number of rows in the tiled images, or the size of the Y-axis.

    path_to_img : str, optional
        Path to input image of which the spots originate
    """
    # Parse input
    df = pd.read_csv(path_to_spotsCSV)
    
    ## Calculate image properties:
    n_total_tiles = tile_grid_shape[0]*tile_grid_shape[1]
    
    # Create range list of the tiles
    total_tiles_list = list(range(1,n_total_tiles+1))
    # Reshape the range list into the tile grid of the original image.
    tile_array = np.reshape(total_tiles_list, tile_grid_shape)

    # Creating an empty array the size of an original image
    original_x = tile_grid_shape[0] * tile_size_x 
    original_y = tile_grid_shape[1] * tile_size_y
    empty_image=np.zeros((original_y, original_x))
    # Iterate over each spot in the csv
    for row in df.itertuples():
        # extract X and Y coordinates of the respective tile the spot belongs to
        row_location, col_location = np.where(tile_array==row.Tile) # this returns rows and columns, NOT X and Y, which is the opposite
        # unpacking the array structure of the return tuple of np.where
        y_tile_location, x_tile_location = row_location[0], col_location[0]
        # Calculate how many pixels to add in order to plot the spot in the correct tile in the original image
        x_adder = x_tile_location * tile_size_x 
        y_adder = y_tile_location * tile_size_y
        # Calculate the position in the original image
        x_coordinate = row.X + x_adder
        y_coordinate = row.Y + y_adder

        # Give the pixel belonging to the spot a value.
        empty_image[y_coordinate, x_coordinate]=255
    if path_to_original_img:
        fig, axs = plt.subplots(1, 2)
        image = cv2.imread(path_to_original_img)
        axs[0].imshow(image)
        axs[0].set_title('Original image')
        axs[1].imshow(empty_image)
        axs[1].set_title("Detected spots")
        for ax in axs:
            ax.set(xlabel='X-coordinates', ylabel='y-coordinates')
            plt.show()
    else: 
        plt.imshow(empty_image, cmap='gray')
        plt.show()
plotSpotsOnWholeImage(blobs, (2,2), 665, 490)