import unittest

from organization.naming import extract_show_name


class TestExtractShowName(unittest.TestCase):
    def test_extract_show_name(self):
        test_cases = [
            ("/mnt/data/Cool Anime (2023)/Ep 01/file.mkv", "Cool Anime (2023)"),
            ("/Shows/Fake Show (1999)/Episode 1.mkv", "Fake Show (1999)"),
            ("/media/Fantasy World (2010)/Season 3/ep3.mkv", "Fantasy World (2010)"),
            ("/mnt/tv_shows/英語下さい (2017)/Season 01/S03E04.mkv", "英語下さい (2017)")
        ]

        for input_path, expected in test_cases:
            with self.subTest(path=input_path):
                result = extract_show_name(input_path)
                self.assertEqual(result, expected)

    def test_no_match(self):
        bad_path = "/mnt/random_path/no_show_folder/S01E01.mkv"
        with self.assertRaises(ValueError):
            extract_show_name(bad_path)