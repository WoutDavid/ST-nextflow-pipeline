import math
from icecream import ic
from collections import Counter
from skimage import io
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# compares two tuples and sees if they are "the same", as defined by an interval of allowed pixel mismatch
def compareTuplesValues(ref_tuple, target_tuple, pixel_mismatch: int):
    # x and y here are meaningless, only thing that's important is that the respective coordinates are in the same column for both tuples
    x_interval = (ref_tuple[0]-pixel_mismatch,ref_tuple[0]+pixel_mismatch)
    y_interval = (ref_tuple[1]-pixel_mismatch,ref_tuple[1]+pixel_mismatch)
    if x_interval[0] < target_tuple[0] < x_interval[1] and y_interval[0] < target_tuple[1] < y_interval[1] :
        return True
    else:
        return False
# Define euclidean distance between a tuple
def calculateEuclideanDistance2D(ref_tuple, target_tuple):
    dist = math.sqrt((ref_tuple[0] - target_tuple[0])**2+(ref_tuple[1]-target_tuple[1])**2)
    return dist

def filterSpotsBasedOnSigmas(path_to_spots: str, num_stdev=1):
    original_array = np.genfromtxt(path_to_spots, delimiter=',', skip_header=1)
    original_array = original_array.astype(int)
    sigmas = original_array[:, 3]
    average = np.mean(sigmas)
    stdev = np.std(sigmas)
    interval = (math.floor(average-(stdev*num_stdev)), math.ceil(average+(stdev*num_stdev)))
    filtered_spots = original_array[np.logical_and(original_array[:,3] >= interval[0], original_array[:,3] < interval[1])]
    num_spots_filtered_out = int(len(original_array) - len(filtered_spots))

# This function assumes that the given csv's are for the same tile, it does not check that beforehand
def checkSpotsInRoundPrecision(ref_spots_csv: str, round_spots_csv_list, round_nr,original_image="", pixel_distance= 0):
    # read in spots as np array for quick parsing. columns: 0 = tile, 1 = Y, 2=X, 3=Sigma
    ref_array = np.genfromtxt(ref_spots_csv, delimiter=',', skip_header=1)
    ref_array = ref_array.astype(int)

    # round_spots_csv_list will be a list of filepath that point towards the hybs detected on a specific channel, we want to combine those
    # columns: 0 = tile, 1=Round, 2=Channel, 3 = Y, 4=X, 5=Sigma
    channel_array_list=[]
    for channel in round_spots_csv_list:
        try:
            temp_array = np.genfromtxt(channel, delimiter=',', skip_header=1).astype(int)
            # If one of the spot detected lists is empty, it shouldn't be included
            if not len(temp_array)==0:
                channel_array_list.append(temp_array)
        except:
            pass

    # Parse ref arrays
    array_of_tuples = map(tuple, ref_array[:,(1,2)])
    ref_tuples = list(array_of_tuples)

    # Parse round arrays
    try:
        channel_array = np.vstack(channel_array_list)
    # It could be that this tile doesn't actually contain any spots, in that case return should be empty
    except ValueError:
        return
    array_of_tuples = map(tuple, channel_array[:,(3,4)])
    round_tuples = list(array_of_tuples)
    # Now we have a list of tuples where each tuple is an Y,X

    # this is not going to be optimized in any way, time will tell if it is necessary or not
    all_closest_ref_point_dict = {} # key = spot in round, value = spot in reference
    all_closest_distance_dict = {}  # key = spot in round, value = distance to closest ref spot
    closest_ref_point_dict = {} # key = spot in round, value = spot in reference
    closest_distance_dict = {}  # key = spot in round, value = distance to closest ref spot
    for round_tuple in round_tuples:
        # min returns the original iterable, not the result of the key function
        closest_ref_point = min(ref_tuples, key=lambda x: calculateEuclideanDistance2D(round_tuple, x))
        closest_distance =  calculateEuclideanDistance2D(round_tuple, closest_ref_point)
        all_closest_ref_point_dict[round_tuple] = closest_ref_point
        all_closest_distance_dict[round_tuple] = closest_distance
        if closest_distance <= pixel_distance:
            # print(f"round_tuple = {round_tuple}, closest_ref_tuple = {closest_ref_point}, with distance = {closest_distance}")
            closest_ref_point_dict[round_tuple] = closest_ref_point
            closest_distance_dict[round_tuple] = closest_distance

    # create the table of info
    attribute_dict = {}
    nr_matched_spots =  len(closest_ref_point_dict)
    nr_round_spots_total = len(all_closest_ref_point_dict) 
    nr_unmatched_spots = nr_round_spots_total - len(closest_ref_point_dict)
    attribute_dict['Round #'] = round_nr
    attribute_dict['# matched spots'] = nr_matched_spots
    attribute_dict['# unmatched spots'] = nr_unmatched_spots
    attribute_dict['Ratio of matched spots'] = round(nr_matched_spots / nr_round_spots_total, 3)*100

    if original_image:
        # read in image, pure for plotting purposes
        original_image = io.imread(original_image)
        fig, axs = plt.subplots(1,2)
        axs[0].imshow(original_image, cmap='gray')
        axs[0].set_title("Reference")
        axs[1].imshow(original_image, cmap='gray')
        axs[1].set_title("Round")
        for key, value in closest_ref_point_dict.items():
            # key & value in format: (Y,X)
            color=np.random.rand(3,)
            circ1 = plt.Circle((key[1],key[0]), 2, color=color)
            circ2 = plt.Circle((value[1],value[0]), 2, color=color)
            axs[0].add_patch(circ1)
            axs[1].add_patch(circ2)

        # Plot duplicate assignement counted
        fig, axs = plt.subplots(1,1)
        axs.set_title("Multiple assigned reference spots plotted by counts")
        axs.set_xlabel("# round spots a reference spot is assigned to")
        axs.set_ylabel("# times counted")
        closest_ref_points = closest_ref_point_dict.values()
        counted_dict = Counter(closest_ref_points)
        duplicate_ref_point_dict ={k: v for k, v in counted_dict.items() if v > 1}
        axs.hist(duplicate_ref_point_dict.values())
        for rect in axs.patches:
            height = rect.get_height()
            axs.annotate(f'{int(height)}', xy=(rect.get_x()+rect.get_width()/2, height), 
                        xytext=(0, 5), textcoords='offset points', ha='center', va='bottom') 
        # plt.show()
    return closest_ref_point_dict, attribute_dict

def calculateRecall(ref_spots_csv, dict_of_closest_ref_point_dicts):
    # unpack the csv to get a list all spot tuples
    ref_array = np.genfromtxt(ref_spots_csv, delimiter=',', skip_header=1)
    ref_array = ref_array.astype(int)

    array_of_tuples = map(tuple, ref_array[:,(1,2)])
    ref_tuples = list(array_of_tuples) # this elements in this list represent spots found on the ref image
    ic(len(ref_tuples))

    #dict_of_closest_ref_point_dicts is supposed to contain key=int(round_number), value = closest_ref_point_dicts created by checkSpotsInRoundPrecision
    #Make a list of the keys (= round numbers) and sort them, such that searching in the dict is targeted and not iterated, to ensure correct order.
    round_numbers =list(dict_of_closest_ref_point_dicts.keys())
    round_numbers.sort(key=lambda x: int(x))
    ic(round_numbers)

    #Then iterate over each tuple in the ref_tuples, check if it's present in the values() of each round. Log when this stops being the case
    complete_barcodes = [] #If a spot ends up having a complete barcode, add it to this list
    round_not_found = {} # key = round_nr, value = count of how many barcodes did not find a match in the given round
    for ref_tuple in ref_tuples:
        for round_nr in round_numbers:
            matched_ref_points = dict_of_closest_ref_point_dicts[round_nr].values()
            if ref_tuple not in matched_ref_points:
                round_not_found[round_nr]= round_not_found.get(round_nr, 0) + 1
                break
            # If this level is reached, that means that for this spot, there was no round where it wasn't found, meaning that it's a complete barcode
            complete_barcodes.append(ref_tuple)

    attribute_dict = {} # dict that will become a row in the dataframe
    # Duplicates may be present since a several round spots can be assigned to the same ref spot
    complete_barcodes =list(set(complete_barcodes))
    ic(complete_barcodes)
    ic(round_not_found)
    #TOFIX if only 2 rounds are entered, it'll see them as complete barcodes, but none of them are, since the spots aren't detected on round 3 and 4

def spotDetectionQCWorkflow(ref_spots_csv, round_csv_dict):
    dict_of_closest_ref_point_dicts= {}
    rows_list = []
    for k,v in rounds_csv_dict.items():
        try:
            closest_ref_point_dict, attribute_dict = checkSpotsInRoundPrecision(ref_spots_csv, v, k, pixel_distance=3)
            dict_of_closest_ref_point_dicts[k] = closest_ref_point_dict
            rows_list.append(attribute_dict)
        # If no spot are found, it will try to unpack null, which needs to be excepted
        except TypeError:
            pass
    precision_df = pd.DataFrame(rows_list)

    rows_list=[]
    calculateRecall(ref_spots_csv, dict_of_closest_ref_point_dicts)









if __name__=='__main__':
    ref_spots_csv = "/media/Puzzles/starfish_test_data/ExampleInSituSequencing/results_minsigma1_maxsigma2_filter3_hybDetection_thresholdSegmentation_voronoiAssignment/blobs/REF_padded_tiled_3_filtered_blobs.csv"
    # rounds_csv_dict = [f"/media/Puzzles/starfish_test_data/ExampleInSituSequencing/results_minsigma1_maxsigma2_filter3_hybDetection_thresholdSegmentation_voronoiAssignment/hybs/Round{round_nr}_c{i}_padded_registered_tiled_3_filtered_registered_hybs.csv" for i in range(2,6)]
    rounds_csv_dict={}
    for round_nr in range(1,5):
        rounds_csv_dict[round_nr] = []
        for i in range(2,6):
            rounds_csv_dict[round_nr].append(f"/media/Puzzles/starfish_test_data/ExampleInSituSequencing/results_minsigma1_maxsigma2_filter3_hybDetection_thresholdSegmentation_voronoiAssignment/hybs/Round{round_nr}_c{i}_padded_registered_tiled_3_filtered_registered_hybs.csv")
    spotDetectionQCWorkflow(ref_spots_csv, rounds_csv_dict)

    # original_image = "/media/Puzzles/starfish_test_data/ExampleInSituSequencing/results_minsigma1_maxsigma2_filter3_hybDetection_thresholdSegmentation_voronoiAssignment/tiled_DO/REF_padded_tiled_3.tif"
    # attribute_dict = checkSpotsInRoundPrecision(ref_spots_csv, rounds_csv, pixel_distance=3)
