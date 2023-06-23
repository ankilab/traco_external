import numpy as np
import pandas as pd
import logging

from scipy.spatial.distance import cdist, euclidean
from scipy.optimize import linear_sum_assignment

PENALTY_N_WRONG_HEXBUGS = 1_000  # only applies if the amount of predicted hexbugs is between 1 and 4
PENALTY_MORE_THAN_FOUR_HEXBUGS = 1_000_000
PENALTY_WRONG_NUMBER_FRAMES = 10_000


def get_score(path_to_prediction: str, path_to_gt: str, log: bool = False) -> int:
    """
    Calculate the score for the given prediction and ground truth files.
    :param path_to_prediction: Path to the prediction .csv file.
    :param path_to_gt: Path to the ground truth .csv file.
    :param log: Boolean to indicate if the log should be written to a file.
    :return: Score for the given prediction and ground truth files.
    """
    final_score = 0

    if log:
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(path_to_prediction.replace(".csv", "_log.log"))
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)

    # Load the data
    pred_df = pd.read_csv(path_to_prediction, index_col=0)
    gt_df = pd.read_csv(path_to_gt, index_col=0)

    # check if the predictions dataframe has at least one row
    if pred_df.shape[0] == 0:
        raise ValueError("The prediction DataFrame does not contain any rows.")

    # Check if DataFrames have the required columns
    required_columns = ['t', 'hexbug', 'x', 'y']
    if not _validate_dataframe_structure(pred_df, required_columns):
        raise ValueError(f"The prediction DataFrame does not have the required columns: {required_columns}")
    else:
        pass

    # Get the number of frames and check if they are equal
    n_frames_gt = gt_df['t'].max() + 1
    n_frames_pred = pred_df['t'].max() + 1

    if n_frames_gt != n_frames_pred:
        final_score += PENALTY_WRONG_NUMBER_FRAMES * np.abs(n_frames_gt - n_frames_pred)

        if log:
            logger.info(f"Penalty for wrong number of frames: "
                        f"{PENALTY_WRONG_NUMBER_FRAMES * np.abs(n_frames_gt - n_frames_pred)}")

        # set n_frames depending on which one is smaller
        n_frames = min(n_frames_gt, n_frames_pred)
    else:
        n_frames = n_frames_gt

    # Loop over all frames
    for idx in range(n_frames):
        if log:
            logger.info(f"Frame {idx}")

        # Get the data for the current frame
        frame_gt_df = gt_df[gt_df['t'] == idx]
        frame_pred_df = pred_df[pred_df['t'] == idx]

        # Check the number of hexbugs and apply penalties if necessary
        n_hexbugs_gt = frame_gt_df['hexbug'].nunique()
        n_hexbugs_pred = frame_pred_df['hexbug'].nunique()
        if n_hexbugs_pred > 4:
            # To prevent submissions with a lot of random guesses
            final_score += PENALTY_MORE_THAN_FOUR_HEXBUGS
            if log:
                logger.info(f"Penalty for more than four hexbugs: {PENALTY_MORE_THAN_FOUR_HEXBUGS}")
        else:
            final_score += (np.abs(n_hexbugs_pred - n_hexbugs_gt) * PENALTY_N_WRONG_HEXBUGS)
            if log:
                logger.info(f"Penalty for wrong number of hexbugs: "
                            f"{np.abs(n_hexbugs_pred - n_hexbugs_gt) * PENALTY_N_WRONG_HEXBUGS}")

        # Calculate the distance between the hexbugs
        distance_matrix = cdist(list(frame_gt_df[['x', 'y']].values),
                                list(frame_pred_df[['x', 'y']].values), 'euclidean')

        # Calculate the final score
        row_ind, col_ind = linear_sum_assignment(distance_matrix)  # Hungarian algorithm
        for i, j in zip(row_ind, col_ind):
            final_score += distance_matrix[i, j]
            if log:
                logger.info(f"Distance between hexbug {frame_gt_df['hexbug'].iloc[i]} and "
                            f"{frame_pred_df['hexbug'].iloc[j]}: {distance_matrix[i, j]}")

        if log:
            logger.info("")

    if log:
        logger.info(f"\nFinal score: {final_score}")
        logger.removeHandler(handler)
        handler.close()

    return final_score


def _validate_dataframe_structure(df: pd.DataFrame, required_columns: list) -> bool:
    """
    Validate if a Pandas DataFrame has the required columns.

    Args:
        df (pd.DataFrame): The DataFrame to validate.
        required_columns (list): A list of column names that should be present in the DataFrame.

    Returns:
        bool: True if the DataFrame has the required columns, False otherwise.
    """
    # Get the columns present in the DataFrame
    columns = df.columns.tolist()

    # Check if all required columns are present in the DataFrame
    if set(required_columns).issubset(columns):
        return True
    else:
        return False


def get_score_with_id_matching(path_to_prediction: str, path_to_gt: str) -> int:
    """
    OLD CODE SNIPPET WHICH IS NOT RELEVANT ANYMORE.
    """
    raise NotImplementedError("This function is not relevant anymore.")

    final_score = 0

    # Load the data
    pred_df = pd.read_csv(path_to_prediction, index_col=0)
    gt_df = pd.read_csv(path_to_gt, index_col=0)

    # Determine how many frames we have and how many hexbugs are used in the video of the ground truth
    n_frames = gt_df['t'].max()
    n_hexbugs_gt = gt_df['hexbug'].nunique()
    n_hexbugs_pred = pred_df['hexbug'].nunique()

    # Apply penalties if the amount of predicted hexbugs is wrong
    if n_hexbugs_pred < 1:
        final_score += PENALTY_ZERO_HEXBUGS
    elif n_hexbugs_pred > 4:
        final_score += PENALTY_MORE_THAN_FOUR_HEXBUGS
    else:
        final_score += (np.abs(n_hexbugs_pred - n_hexbugs_gt) * PENALTY_N_WRONG_HEXBUGS)

        # Match the predicted hexbugs in the first frame with the ground truth
    # --> the matching IDs are used in all the following frames
    distance_matrix = cdist(list(gt_df[gt_df['t'] == 0][['x', 'y']].values),
                            list(pred_df[pred_df['t'] == 0][['x', 'y']].values))
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


# define main function call
if __name__ == "__main__":
    # extract args
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("path_to_prediction", help="path to the prediction file")
    parser.add_argument("path_to_gt", help="path to the ground truth file")
    parser.add_argument("--log", help="log the score", action="store_true")
    args = parser.parse_args()

    # calculate score
    print(f"Score: {get_score(args.path_to_prediction, args.path_to_gt, args.log)}")
