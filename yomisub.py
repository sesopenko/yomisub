# © 2025 Sean Esopenko
# https://github.com/sesopenko/yomisub

import json
import shutil
import subprocess
import threading
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen

import gi
import pycountry
import srt

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

MODEL_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main"
MODELS = ("tiny", "base", "small", "medium", "large-v2")


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

        first_button = None

        for model_name in MODELS:
            btn = Gtk.RadioButton.new_with_label_from_widget(first_button, model_name)
            if first_button is None:
                first_button = btn  # set first radio group
            model_box.pack_start(btn, True, True, 0)
            self.model_buttons[model_name] = btn

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

    def on_generate_clicked(self, widget):
        filepath = self.file_chooser.get_filename()
        if not filepath:
            self.status_label.set_text("Please select a video file.")
            return

        track_index = self.audio_track_combo.get_active()
        track_label = self.audio_track_combo.get_active_text() or ""
        lang_code = normalize_lang_code(track_label.rpartition("(")[2].removesuffix(")").strip())
        if (
            lang_code == "und"
            or len(lang_code) not in (2, 3)
            or not lang_code.isascii()
            or not lang_code.isalpha()
        ):
            self._show_error_dialog("Could not determine the language of the selected audio track.")
            return

        self.button.set_sensitive(False)
        self.status_label.set_text("Processing...")
        threading.Thread(
            target=self._run_subtitle_generation,
            args=(Path(filepath), track_index, lang_code, self.get_selected_model()),
        ).start()

    def _run_subtitle_generation(self, video_path, track_index, lang_code, model_name):
        try:
            srt_path = generate_subtitles(
                video_path, track_index, lang_code, model_name,
                lambda message: GLib.idle_add(self.status_label.set_text, message),
            )
            GLib.idle_add(self.status_label.set_text, f"Subtitles saved to {srt_path}")
        except Exception as error:
            GLib.idle_add(self._show_error_dialog, str(error))
        finally:
            GLib.idle_add(self.button.set_sensitive, True)

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


def get_model_path(model_name, report_status):
    cache_dir = Path.home() / ".cache" / "yomisub" / "models"
    model_path = cache_dir / f"ggml-{model_name}.bin"
    if model_path.is_file():
        return model_path

    report_status(f"Downloading the {model_name} model...")
    cache_dir.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=cache_dir) as temp_dir:
        download_path = Path(temp_dir) / model_path.name
        with urlopen(f"{MODEL_URL}/{model_path.name}", timeout=60) as response:
            with download_path.open("wb") as download:
                shutil.copyfileobj(response, download)
            content_length = response.headers.get("Content-Length")
        size = download_path.stat().st_size
        if not size or (content_length is not None and size != int(content_length)):
            raise RuntimeError(f"The {model_name} model download was incomplete. Try again.")
        download_path.replace(model_path)
    return model_path


def generate_subtitles(video_path, track_index, lang_code, model_name, report_status):
    whisper_cli = shutil.which("whisper-cli")
    if whisper_cli is None:
        raise RuntimeError("whisper-cli is missing from PATH. Follow the setup in README.md.")

    with TemporaryDirectory(prefix="yomisub-") as temp_dir:
        audio_path = Path(temp_dir) / "audio.wav"
        output_stem = Path(temp_dir) / "transcript"

        report_status("Extracting audio...")
        subprocess.run([
            "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-i", str(video_path),
            "-map", f"0:a:{track_index}", "-ac", "1", "-ar", "16000",
            "-c:a", "pcm_s16le", str(audio_path),
        ], check=True)

        model_path = get_model_path(model_name, report_status)
        report_status("Transcribing with whisper.cpp...")
        try:
            subprocess.run([
                whisper_cli, "--model", str(model_path), "--file", str(audio_path),
                "--language", lang_code, "--output-srt", "--output-file", str(output_stem),
            ], stdout=subprocess.DEVNULL, check=True)
        except subprocess.CalledProcessError as error:
            raise RuntimeError("whisper-cli failed to transcribe the audio. See the terminal for details.") from error

        report_status("Generating subtitles...")
        subtitles = list(srt.parse(output_stem.with_suffix(".srt").read_text(encoding="utf-8")))
        for subtitle in subtitles:
            subtitle.end = min(
                subtitle.end + timedelta(seconds=0.5),
                subtitle.start + timedelta(seconds=6),
            )

    srt_path = video_path.with_name(f"{video_path.stem}.{lang_code}.srt")
    with TemporaryDirectory(prefix=".yomisub-", dir=srt_path.parent) as temp_dir:
        output_path = Path(temp_dir) / srt_path.name
        output_path.write_text(srt.compose(subtitles), encoding="utf-8")
        output_path.replace(srt_path)
    return srt_path


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
