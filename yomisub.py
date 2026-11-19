# © 2025 Sean Esopenko
# https://github.com/sesopenko/yomisub

from functools import partial

from yomisub.generation import generate_subtitles
from yomisub.gtk_app import Gtk, SubtitleApp
from yomisub.media import extract_audio, probe_audio_tracks
from yomisub.models import get_model_path
from yomisub.subtitles import write_subtitles
from yomisub.whisper import prepare_transcriber


def main():
    generate = partial(
        generate_subtitles,
        extract_audio=extract_audio,
        get_model_path=get_model_path,
        prepare_transcriber=prepare_transcriber,
        write_subtitles=write_subtitles,
    )
    window = SubtitleApp(probe_audio_tracks, generate)
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
