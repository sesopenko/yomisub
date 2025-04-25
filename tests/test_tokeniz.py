import unittest
from datetime import timedelta
from pathlib import Path
import pickle

import srt

from subtitles.split_by_speaker import split_by_speaker
from subtitles.tokenization import group_japanese_words


class TestTokenizer(unittest.TestCase):
    def test_group_japanese_words_bert(self):
        pickle_path = Path.home() / ".temp" / "yoomisub" / "word_segments.pickle"

        with open(pickle_path, "rb") as f:
            aligned_chars = pickle.load(f)

        # Make sure it runs and returns something
        result = group_japanese_words(aligned_chars)

        assert isinstance(result, list)
        assert all("word" in w for w in result)
        assert all("start" in w for w in result)
        assert all("end" in w for w in result)

    def test_split_by_speaker(self):
        pickle_path = Path.home() / ".temp" / "yoomisub" / "word_segments.pickle"

        with open(pickle_path, "rb") as f:
            aligned_chars = pickle.load(f)
        input = group_japanese_words(aligned_chars)
        subtitles = []
        idx = 1
        for idx, start, end, text in split_by_speaker(input, "ja"):
            subtitles.append(srt.Subtitle(
                index=idx,
                start=timedelta(seconds=start),
                end=timedelta(seconds=end),
                content=text
            ))
        assert subtitles


if __name__ == '__main__':
    unittest.main()
