from fractions import Fraction as F
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import wave

from yomisub.audio import ClockError, decoded_origin, extract_crop, selected_streams, video_span
from yomisub.domain import AudioSource, RecordingClock, SampleInterval
from yomisub.ports import AudioFile


class AudioTests(unittest.TestCase):
    def test_track_index_and_ordinal(self):
        streams = [{"codec_type": "video", "index": 0}, {"codec_type": "audio", "index": 1,
                    "channels": 1}, {"codec_type": "audio", "index": 3, "channels": 2,
                    "channel_layout": "stereo", "tags": {"language": "jpn"}}]
        selected = selected_streams(streams)[1]
        self.assertEqual((selected.index, selected.audio_ordinal, selected.language), (3, 1, 'ja'))

    def test_delayed_and_early_audio(self):
        video = {"time_base": "1/1000", "start_pts": 10000, "duration_ts": 2000}
        start, duration = video_span(None, video)
        frames = [{"best_effort_timestamp": 10250, "nb_samples": 44100}]
        origin, n = decoded_origin(frames, 44100, F(1, 1000))
        clock = RecordingClock(44100, n, origin - start, duration, start)
        analysis = AudioSource("mix", "original", 16000, 16000)
        self.assertEqual(analysis.recording_sample(1, clock), F(441, 160))
        self.assertEqual(clock.playback_time(analysis.recording_sample(1, clock)), F(4001, 16000))
        early = RecordingClock(8000, 8000, F(-1, 2), duration)
        self.assertFalse(SampleInterval(early, 0, 4000).playable)
        self.assertTrue(SampleInterval(early, 4000, 5000).playable)
        self.assertEqual(analysis.recording_sample(8000, early), 4000)

    def test_discontinuity_rejected_and_container_rounding_allowed(self):
        frames = [{"best_effort_timestamp": 0, "nb_samples": 1024},
                  {"best_effort_timestamp": 23, "nb_samples": 1024}]
        self.assertEqual(decoded_origin(frames, 44100, F(1, 1000)), (0, 2048))
        frames[1]["best_effort_timestamp"] = 30
        with self.assertRaisesRegex(ClockError, 'discontinuity'):
            decoded_origin(frames, 44100, F(1, 1000))

    def test_outward_rounding_and_clip_at_end(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            path = root / 'source.wav'
            with wave.open(str(path), 'wb') as wav:
                wav.setparams((1, 2, 44100, 20, 'NONE', 'not compressed'))
                wav.writeframes(bytes(range(40)))
            clock = RecordingClock(44100, 20, F(1, 4), F(2), F(10))
            parent = AudioFile(AudioSource('original', None, 44100, 20), path)
            analysis = AudioSource('mix', 'original', 16000, 8)
            actual = extract_crop(parent, analysis, 1, 2, clock, root/'crop.wav', 'test')
            self.assertEqual((actual.source.origin, actual.source.frames), (2, 4))
            self.assertEqual(actual.source.requested_recording_bounds, (F(441,160), F(441,80)))
            with wave.open(str(actual.path)) as wav:
                self.assertEqual(wav.readframes(4), bytes(range(4,12)))
            end = extract_crop(parent, analysis, 6, 12, clock, root/'end.wav', 'end').source
            self.assertEqual(end.origin + end.frames, 20)
