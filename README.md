# TRACO repository
This repository contains the code and the data for the [Tracking Olympiad](https://traco.anki.xyz/) seminar.

## Data
The training data is available in the `training` folder. It contains 100 annotated videos of HexBugs.

The Leaderboard data is available in the `leaderboard_data` folder. It contains 5 videos of HexBugs. 
We also added the ground truth annotations such that you can evaluate your predictions locally. 

NOTE: The Leaderboard on the website is currently still buggy. We are working on fixing it.

## Annotation GUI
The annotation GUI is available in the python file `traco_annotation_gui.py`. It can be run with the following command:

```python traco_annotation_gui.py```

We recommend using Python 3.6 or higher. The GUI requires the following packages:
- PyQt6
- Pandas
- imageio (```pip install imageio-ffmpeg```)
- pyqtgraph
- matplotlib
- numpy

Annotate the videos by left-clicking on the head of a HexBug. Note that you have to select the HexBug ID on the right 
side of the GUI before annotating. You can also use A and D keys to move the video forward and backward frame by frame.

## Score
The score of the annotation is calculated by the `get_score.py` script. It can be run with the following command:

```python get_score.py --path_to_prediction <path_to_prediction_file> --path_to_gt <path_to_gt_file> --log```

Specifying the `--log` flag will save the scores for each frame and how the HexBug IDs were matched in a log file.

We also added some unit tests for the score calculation in the `score_tests` folder.

## Contributing
Feel free to contribute to the repository by improving the score calculation or the annotation GUI. 
Please create a pull request for your changes.