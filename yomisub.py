import gi
# © 2025 Sean Esopenko
# https://github.com/sesopenko/yomisub

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import whisper
from moviepy.video.io.VideoFileClip import VideoFileClip  # ✅ updated import for moviepy 2.x
import srt
from datetime import timedelta
import os
from pathlib import Path
import subprocess
import json
import pycountry
import threading

class SubtitleApp(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Subtitle Generator")
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

        # --- Model selection UI ---
        frame = Gtk.Frame(label="Model Selection")
        model_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        frame.add(model_box)
        vbox.pack_start(frame, True, True, 0)

        self.model_buttons = {}

        models = {
            "tiny": "tiny (1 GB)",
            "base": "base (1.5 GB)",
            "small": "small (2.5 GB)",
            "medium": "medium (5.5 GB)",
            "large-v2": "large-v2 (12 GB)"
        }

        first_button = None

        for key, label in models.items():
            btn = Gtk.RadioButton.new_with_label_from_widget(first_button, label)
            if first_button is None:
                first_button = btn  # set first radio group
            model_box.pack_start(btn, True, True, 0)
            self.model_buttons[key] = btn

        # Set default selection
        self.model_buttons["medium"].set_active(True)

        self.button = Gtk.Button(label="Generate Subtitles")
        self.button.connect("clicked", self.on_generate_clicked)
        vbox.pack_start(self.button, True, True, 0)

        self.status_label = Gtk.Label(label="")
        vbox.pack_start(self.status_label, True, True, 0)

    def get_selected_model(self):
        for model, btn in self.model_buttons.items():
            if btn.get_active():
                return model
        return "medium"  # fallback

    def on_file_chosen(self, widget):
        filepath = self.file_chooser.get_filename()
        self.audio_track_combo.remove_all()
        self.audio_track_combo.set_sensitive(False)

        if not filepath:
            return

        try:
            result = subprocess.run([
                "ffprobe", "-v", "error",
                "-select_streams", "a",
                "-show_entries", "stream=index:stream_tags=language",
                "-of", "json",
                filepath
            ], capture_output=True, text=True, check=True)

            data = json.loads(result.stdout)
            audio_streams = data.get("streams", [])

            for stream in audio_streams:
                index = stream.get("index")
                lang = stream.get("tags", {}).get("language", "und")
                label = f"Track {index} ({lang})"
                self.audio_track_combo.append_text(label)

            if audio_streams:
                self.audio_track_combo.set_active(0)
                self.audio_track_combo.set_sensitive(True)
                self.status_label.set_text("Audio tracks loaded.")
            else:
                self.status_label.set_text("No audio tracks found.")

        except Exception as e:
            self.status_label.set_text(f"Error reading audio tracks: {str(e)}")

    def create_video_filter(self):
        video_filter = Gtk.FileFilter()
        video_filter.set_name("Video Files")
        video_filter.add_mime_type("video/mp4")
        video_filter.add_pattern("*.mp4")
        video_filter.add_pattern("*.mov")
        video_filter.add_pattern("*.mkv")
        return video_filter

    import os
    from pathlib import Path

    def on_generate_clicked(self, widget):
        filepath = self.file_chooser.get_filename()
        if not filepath:
            self.status_label.set_text("Please select a video file.")
            return

        self.status_label.set_text("Processing...")

        def run_subtitle_job():
            self._run_subtitle_generation(filepath)

        thread = threading.Thread(target=run_subtitle_job)
        thread.start()
    def _run_subtitle_generation(self, filepath):
        GObject = Gtk.GObject if hasattr(Gtk, 'GObject') else gi.repository.GObject
        from gi.repository import GLib

        try:
            track_index = self.audio_track_combo.get_active()
            track_label = self.audio_track_combo.get_active_text()
            lang_code = "und"
            if track_label and "(" in track_label:
                lang_code = track_label.split("(")[-1].replace(")", "").strip()

            lang_code = normalize_lang_code(lang_code)

            if lang_code == "und":
                GLib.idle_add(self._show_error_dialog, "Could not determine the language of the selected audio track.")
                return

            app_dir = Path.home() / ".local" / "share" / "yomisub"
            app_dir.mkdir(parents=True, exist_ok=True)

            audio_path = app_dir / "temp_audio.wav"

            # Update label on main thread
            GLib.idle_add(self.status_label.set_text, "Extracting audio...")

            subprocess.run([
                "ffmpeg", "-y", "-i", filepath,
                "-map", f"0:a:{track_index}", "-acodec", "pcm_s16le",
                str(audio_path)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            GLib.idle_add(self.status_label.set_text, "Transcribing with Whisper...")

            model_name = self.get_selected_model()
            model = whisper.load_model(model_name)

            result = model.transcribe(str(audio_path), language=lang_code)

            GLib.idle_add(self.status_label.set_text, "Generating subtitles...")

            max_duration = 6.0  # max subtitle duration to prevent huge blocks
            padding = 0.5
            subtitles = []
            for i, segment in enumerate(result['segments']):
                start = timedelta(seconds=segment['start'])
                end_time = min(segment['end'] + padding, segment['start'] + max_duration)
                end = timedelta(seconds=end_time)
                content = segment['text']
                subtitles.append(srt.Subtitle(index=i + 1, start=start, end=end, content=content))

            srt_path = Path(filepath).with_name(Path(filepath).stem + f".{lang_code}.srt")
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt.compose(subtitles))

            audio_path.unlink(missing_ok=True)

            GLib.idle_add(self.status_label.set_text, f"✅ Subtitles saved to {srt_path}")

        except Exception as e:
            GLib.idle_add(self._show_error_dialog, f"Error: {str(e)}")

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


def normalize_lang_code(code):
    code = code.lower()

    # Already 2-letter? Return as is
    if len(code) == 2:
        return code

    # Try converting 3-letter to 2-letter
    try:
        lang = pycountry.languages.get(alpha_3=code)
        if lang and hasattr(lang, 'alpha_2'):
            return lang.alpha_2
    except LookupError:
        pass

    return code  # fallback

if __name__ == "__main__":
    win = SubtitleApp()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
