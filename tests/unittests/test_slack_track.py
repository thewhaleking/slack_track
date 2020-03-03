from datetime import date
import unittest

import slack_track


class TestSlackTrack(unittest.TestCase):
    def test_flatten_dict(self):
        initial_dict = {
            "one": 1,
            "two": 2.0,
            "three": "three",
            "four": {
                4: 4,
                "five": [1, 2, 3, 4, 5]
            }
        }
        flat = slack_track.flatten_dict(initial_dict)
        expected_result = {
            "one": 1,
            "two": 2.0,
            "three": "three",
            4: 4,
            "five": [1, 2, 3, 4, 5]
        }
        self.assertDictEqual(flat, expected_result)

    def test_items_to_rows(self):
        users = [
            {"name": "user0",
             "deleted": False},
            {"name": "user1",
             "deleted": True}
        ]
        today = date.today()
        rows = list(slack_track.items_to_rows(users, ("name", "deleted", "date")))
        expected_list = [['user0', False, str(today)], ['user1', True, str(today)]]
        self.assertListEqual(rows, expected_list)


if __name__ == '__main__':
    unittest.main()
