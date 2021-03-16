import cv2
import math


def calculateOptimalTileSize(img_path, target_X, target_Y):
    img = cv2.imread(img_path, 1)
    shape = img.shape
    optimal_x = findOptimalDivisor(shape[1], target_X)
    optimal_y = findOptimalDivisor(shape[0], target_Y)
    print(optimal_x, optimal_y)


def tileWriter(img_path, tile_size_x, tile_size_y, output_file, offset_x=None, offset_y=None, discard_irregular=False):
    img = cv2.imread(img_path, 1)
    # Don't forget, cv2 works with shape = (y, x), meaning rows, columns
    img_shape=img.shape
    if offset_x == None or offset_y==None:
        offset_x = tile_size_x
        offset_y = tile_size_y
    tile_size = (tile_size_x, tile_size_y)
    offset = (offset_x, offset_y)
    print(tile_size, offset)
    for i in range(int(math.ceil(img_shape[0]/(offset[1] * 1.0)))):
        for j in range(int(math.ceil(img_shape[1]/(offset[0] * 1.0)))):
            cropped_img = img[offset[1]*i:min(offset[1]*i+tile_size[1], img_shape[0]), offset[0]*j:min(offset[0]*j+tile_size[0], img_shape[1])]
            # Debugging the tiles
            cv2.imwrite(f"{output_file}_tile_{i}_{j}.tif", cropped_img)


def findOptimalDivisor(number, target_quotient):
    divisors = [i for i in range(1,number) if number % i==0]
    quotients = [number/divisor for divisor in divisors]
    min_loss = min(quotients, key=lambda x:abs(x-target_quotient))
    return min_loss


calculateOptimalTileSize("/media/tool/spatial1/stitched_tiff_seperate_channels/ISS1_488_channel_3.tif", 2000, 2000)