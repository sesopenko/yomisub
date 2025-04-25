import gc
import logging

import luigi
import whisperx
import pickle
import os
from optuna.terminator.improvement.emmr import torch

from tasks.extract_audio import ExtractAudio

class TranscribeAudio(luigi.Task):
    video_path = luigi.Parameter(
        description="Path to the wav audio file to transcribe=",
    )
    show_name = luigi.Parameter()
    lang_code = luigi.Parameter(
        description="ISO 639-1 2 letter anguage code of the audio file to transcribe=",
    )
    model_name = luigi.Parameter(
        description="Name of whisperx model to use",
    )

    def requires(self):
        return ExtractAudio(
            video_path=self.video_path,
            show_name=self.show_name,
        )
    def output(self):
        base_name = os.path.splitext(os.path.basename(self.video_path))[0]
        transcription_path = f"data/transcriptions/{self.show_name}_{base_name}.pkl"
        return luigi.LocalTarget(transcription_path)

    def run(self):
        logger = logging.getLogger("luigi-interface")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Loading Whisper Model %s for device %s", self.model_name, device)
        model = whisperx.load_model(self.model_name, device=device)
        logger.info("Transcribing with Whisper for language %s", self.lang_code)
        result = model.transcribe(str(self.input().path), language=self.lang_code)
        os.makedirs(os.path.dirname(self.output().path), exist_ok=True)
        with open(self.output().path, "wb") as f:
            pickle.dump(result, f)
        del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()



