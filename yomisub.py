# © 2025 Sean Esopenko
# https://github.com/sesopenko/yomisub

from yomisub.audio import FFmpegAudio
from yomisub.gtk_app import Gtk, SubtitleApp
from yomisub.production import build_generator


def generate(request, progress):
    return build_generator()(request, progress)


def create_window():
    return SubtitleApp(FFmpegAudio().list_tracks, generate)


def main():
    window = create_window()
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
