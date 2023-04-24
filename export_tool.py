import pandas as pd
import json

# Formatting each frame

def coordinate_from_array(array):
    #array: [<frame_id>, <object_class>, <x>, <y>]
    frame, id, x ,y = array
    labelN = {
        'frame': frame, #int: frame id
        'id': id, #int: object id
        'x': x, #int: x coordinate
        'y': y  #int: y coordinate
    }
    return labelN


## ! convert from yolo output to csv format

# def coordinate_from_yolo(frame, array):
#     #array: [<object_class>, <x>, <y>, <width>, <height>]
#     id, x, y, _, _ = array
#     labelN = {
#         'frame': frame, #int: frame id
#         'id': id, #int: object id
#         'x': x, #int: x coordinate
#         'y': y  #int: y coordinate
#     }
#     return labelN


# This function saves a list of dictionaries to a csv file
def save_list(list_with_values: list, path: str):
    df = pd.DataFrame(list_with_values)
    df = df.sort_values(by = ['hexbug', 't'],ignore_index=True) # we sort the values by hexbug and frame
    # now the values are in the correct order, so we save the csv file
    print('Saving to csv')
    df.to_csv(path)
    print('Done')
    

def traco_to_csv(traco_path, csv_path):
    print('Opening file: ', traco_path)
    with open(traco_path, 'r') as traco_file:
        rois = json.load(traco_file)['rois']
    
    tmp = [] # -> creating an empty list to append the values contained in "rois"
    for roi in rois:
        # we create a dictionary for each roi in the correct format
        e = {
            't': roi['z'],
            'hexbug': roi['id'],
            'x': roi['pos'][0],
            'y': roi['pos'][1]
        }
        # and we append it to the list
        tmp.append(e)
    # we save the list to a csv file
    saveList(tmp, csv_path)



def from_array_to_dict(array, tmp = None):
    #array: [<frame_id>, <object_class>, <x>, <y>]
    #array: [<frame>, <hexbug_id>, <x>, <y>]
    frame, id, x ,y = array
    if tmp is None: # --> If there is no list to append the values contained in "array" we create an empty list
        tmp = []
    # we create a dictionary for each roi in the correct format
    e = {
            't': frame,
            'hexbug': id,
            'x': x,
            'y': y
        }
    tmp.append(e)
    return tmp