import luigi
import subprocess
import os

class ExtractAudio(luigi.Task):
    video_path = luigi.Parameter()
    show_name = luigi.Parameter()

    def output(self):
        base_name = os.path.splitext(os.path.basename(self.video_path))[0]
        audio_path = f"data/audio/{self.show_name}_{base_name}.wav"
        return luigi.LocalTarget(audio_path)

    def run(self):
        os.makedirs("data/audio", exist_ok=True)
        command = [
            "ffmpeg",
            "-y",
            "-i", self.video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            self.output().path
        ]
        subprocess.run(command, check=True)