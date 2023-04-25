import numpy as np
import pandas as pd

from scipy.spatial.distance import cdist, euclidean
from scipy.optimize import linear_sum_assignment

PENALTY_MORE_THAN_FIVE_HEXBUGS = 500_000
PENALTY_ZERO_HEXBUGS = 500_000
PENALTY_N_WRONG_HEXBUGS = 100_000 # only applies if the amount of predicted hexbugs is between 1 and 5

def get_score(path_to_upload: str, path_to_gt:str):
    final_score = 0

    # Load the data
    pred_df = pd.read_csv(path_to_upload, index_col=0)
    gt_df = pd.read_csv(path_to_gt, index_col=0)

    # Determine how many frames we have and how many hexbugs are used in the video of the ground truth
    n_frames = gt_df['t'].max()
    n_hexbugs_gt = gt_df['hexbug'].nunique()    
    n_hexbugs_pred = pred_df['hexbug'].nunique()
            
    # Apply penalties if the amount of predicted hexbugs is wrong
    if n_hexbugs_pred < 1:
        final_score += PENALTY_ZERO_HEXBUGS
    elif n_hexbugs_pred > 5:
        final_score += PENALTY_MORE_THAN_FIVE_HEXBUGS
    else:
        final_score += (np.abs(n_hexbugs_pred - n_hexbugs_gt) * PENALTY_N_WRONG_HEXBUGS)  
    
    # Match the predicted hexbugs in the first frame with the ground truth 
    # --> the matching IDs are used in all the following frames
    distance_matrix = cdist(list(gt_df[gt_df['t'] == 0][['x', 'y']].values), list(pred_df[pred_df['t'] == 0][['x', 'y']].values))
    row_ind, col_ind = linear_sum_assignment(distance_matrix)  # Hungarian algorithm

    matched_ids = {}
    for i, j in zip(row_ind, col_ind):
        matched_ids[f"{i}"] = j
    
    # Iterate over each frame and calculate distances
    for i in range(n_frames):
        frame_gt_df = gt_df[gt_df['t'] == i]
        frame_pred_df = pred_df[pred_df['t'] == i]
        for j in range(n_hexbugs_gt):
            row_gt = frame_gt_df[frame_gt_df['hexbug'] == j]
            row_pred = frame_pred_df[frame_pred_df['hexbug'] == matched_ids[str(j)]]
            score = euclidean(list(row_gt[['x', 'y']].values[0]), list(row_pred[['x', 'y']].values[0]))
            final_score += score

    return final_score

if __name__ == "__main__":
    print("Score: ", get_score("files/zeroes.csv", "files/threeHB.csv"))