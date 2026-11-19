import threading
from functools import partial
from pathlib import Path

import gi

from .models import DEFAULT_MODEL, MODELS
from .workflow import format_track_label, make_generation_request, run_generation

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk


class SubtitleApp(Gtk.Window):
    def __init__(self, probe_audio_tracks, generate_subtitles):
        super().__init__(title="Subtitle Generator")
        self.probe_audio_tracks = probe_audio_tracks
        self.generate_subtitles = generate_subtitles
        self.audio_tracks = []
        self.set_border_width(10)
        self.set_default_size(400, 100)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        self.file_chooser = Gtk.FileChooserButton(title="Choose a video file", action=Gtk.FileChooserAction.OPEN)
        self.file_chooser.set_filter(self.create_video_filter())
        vbox.pack_start(self.file_chooser, True, True, 0)

        self.audio_track_combo = Gtk.ComboBoxText()
        self.audio_track_combo.set_sensitive(False)
        vbox.pack_start(self.audio_track_combo, True, True, 0)

        self.file_chooser.connect("file-set", self.on_file_chosen)

        frame = Gtk.Frame(label="Model Selection")
        model_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        frame.add(model_box)
        vbox.pack_start(frame, True, True, 0)

        self.model_buttons = {}

        first_button = None

        for model_name in MODELS:
            btn = Gtk.RadioButton.new_with_label_from_widget(first_button, model_name)
            if first_button is None:
                first_button = btn
            model_box.pack_start(btn, True, True, 0)
            self.model_buttons[model_name] = btn

        self.model_buttons[DEFAULT_MODEL].set_active(True)

        self.button = Gtk.Button(label="Generate Subtitles")
        self.button.connect("clicked", self.on_generate_clicked)
        vbox.pack_start(self.button, True, True, 0)

        self.status_label = Gtk.Label(label="")
        vbox.pack_start(self.status_label, True, True, 0)

    def get_selected_model(self):
        for model, btn in self.model_buttons.items():
            if btn.get_active():
                return model
        return DEFAULT_MODEL

    def on_file_chosen(self, widget):
        filepath = self.file_chooser.get_filename()
        self.audio_tracks = []
        self.audio_track_combo.remove_all()
        self.audio_track_combo.set_sensitive(False)

        if not filepath:
            return

        try:
            self.audio_tracks = self.probe_audio_tracks(Path(filepath))
            for track in self.audio_tracks:
                self.audio_track_combo.append_text(format_track_label(track))

            if self.audio_tracks:
                self.audio_track_combo.set_active(0)
                self.audio_track_combo.set_sensitive(True)
                self.status_label.set_text("Audio tracks loaded.")
            else:
                self.status_label.set_text("No audio tracks found.")

        except Exception as error:
            self.status_label.set_text(f"Error reading audio tracks: {error}")

    def create_video_filter(self):
        video_filter = Gtk.FileFilter()
        video_filter.set_name("Video Files")
        video_filter.add_mime_type("video/mp4")
        video_filter.add_pattern("*.mp4")
        video_filter.add_pattern("*.mov")
        video_filter.add_pattern("*.mkv")
        return video_filter

    def on_generate_clicked(self, widget):
        filepath = self.file_chooser.get_filename()
        if not filepath:
            self.status_label.set_text("Please select a video file.")
            return

        try:
            request = make_generation_request(
                Path(filepath),
                self.audio_tracks,
                self.audio_track_combo.get_active(),
                self.get_selected_model(),
            )
        except ValueError as error:
            self._show_error_dialog(str(error))
            return

        self.button.set_sensitive(False)
        self.status_label.set_text("Processing...")
        threading.Thread(target=self._run_subtitle_generation, args=(request,)).start()

    def _run_subtitle_generation(self, request):
        run_generation(
            self.generate_subtitles,
            request,
            report_status=partial(GLib.idle_add, self.status_label.set_text),
            report_error=partial(GLib.idle_add, self._show_error_dialog),
            on_finished=partial(GLib.idle_add, self.button.set_sensitive, True),
        )

    def _show_error_dialog(self, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="An error occurred",
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
        self.status_label.set_text("An error occurred.")
