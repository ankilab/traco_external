import unittest
from pathlib import Path

import get_score


class GetScoreTestCase(unittest.TestCase):
    """Tests for `get_score.py`."""
    f_path = Path("files/")

    def test_perfect_predictions(self):
        """
        Test if the score is 0 when the predictions are perfect.
        """
        gt_files = ["test005.csv", "test001.csv", "test002.csv",
                    "test003.csv", "test004.csv"]

        # Define the input for the function
        result = 0
        for gt_file in gt_files:
            result += get_score.get_score(str(self.f_path / gt_file), str(self.f_path / gt_file))
        
        # Define the expected output
        expected_output = 0

        self.assertEqual(result, expected_output)

    def test_one_value_wrong(self):
        """
        Test if the score is correct when one value is wrong.
        """
        result = get_score.get_score(str(self.f_path / "test001_one_value_wrong.csv"), str(self.f_path / "test001.csv"))

        # Define the expected output --> One value is wrong in the first frame (x value minus 1)
        expected_output = 1
        self.assertEqual(result, expected_output)

    def test_one_less_hexbug_predicted(self):
        """
        Test if the score is correct when less hexbugs are predicted than in the ground truth.
        """
        result = get_score.get_score(str(self.f_path / "test005_one_less.csv"), str(self.f_path / "test005.csv"))

        # Define the expected output --> One hexbug is missing in each frame (101 frames)
        expected_output = get_score.PENALTY_N_WRONG_HEXBUGS * 101 * 1
        self.assertEqual(result, expected_output)
        
    def test_two_more_hexbugs_predicted(self):
        """
        Test if the score is correct when more hexbugs are predicted than in the ground truth.
        """
        result = get_score.get_score(str(self.f_path / "test005_two_more.csv"), str(self.f_path / "test005.csv"))

        # Define the expected output --> Two hexbugs are too much in each frame (101 frames)
        expected_output = get_score.PENALTY_N_WRONG_HEXBUGS * 101 * 2
        self.assertEqual(result, expected_output)

    def test_columns_wrong(self):
        """
        Test if the score is correct when the columns are wrong.
        """
        # Define the expected output --> columns are missing --> raise ValueError
        expected_output = ValueError
        self.assertRaises(expected_output,
                          get_score.get_score,
                          str(self.f_path / "test001_wrong_columns.csv"),
                          str(self.f_path / "test001.csv"))


# Run the tests when the script is executed
if __name__ == '__main__':
    unittest.main()