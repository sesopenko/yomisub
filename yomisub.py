import gi
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

class SubtitleApp(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Japanese Subtitle Generator")
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

        self.button = Gtk.Button(label="Generate Subtitles")
        self.button.connect("clicked", self.on_generate_clicked)
        vbox.pack_start(self.button, True, True, 0)

        self.status_label = Gtk.Label(label="")
        vbox.pack_start(self.status_label, True, True, 0)

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

        try:
            # Use ~/.local/share/yomisub as working directory
            app_dir = Path.home() / ".local" / "share" / "yomisub"
            app_dir.mkdir(parents=True, exist_ok=True)

            audio_path = app_dir / "temp_audio.wav"
            self.status_label.set_text("Extracting audio...")
            track_index = self.audio_track_combo.get_active()
            if track_index < 0:
                self.status_label.set_text("Please select an audio track.")
                return

            self.status_label.set_text("Extracting audio...")

            # Use ffmpeg to extract the specific audio track
            subprocess.run([
                "ffmpeg", "-y", "-i", filepath,
                "-map", f"0:a:{track_index}", "-acodec", "pcm_s16le",
                str(audio_path)
            ], stderr=subprocess.STDOUT, stdout=None, check=True)

            # Get language code from selected label
            track_label = self.audio_track_combo.get_active_text()
            lang_code = "und"  # fallback if not found


            if track_label and "(" in track_label:
                lang_code = track_label.split("(")[-1].replace(")", "").strip()
            if lang_code == "und":
                dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.OK,
                    text="Could not determine the language of the selected audio track.",
                )
                dialog.format_secondary_text(
                    "Please choose a different audio track or ensure the file has correct language metadata."
                )
                dialog.run()
                dialog.destroy()
                self.status_label.set_text("Aborted: unknown audio track language.")
                return

            lang_code = normalize_lang_code(lang_code)

            self.status_label.set_text("Transcribing with Whisper (slow)...")
            model = whisper.load_model("medium")
            result = model.transcribe(str(audio_path), language="ja")

            self.status_label.set_text("Generating SRT file...")
            subtitles = []
            for i, segment in enumerate(result['segments']):
                start = timedelta(seconds=segment['start'])
                end = timedelta(seconds=segment['end'])
                content = segment['text']
                subtitles.append(srt.Subtitle(index=i + 1, start=start, end=end, content=content))



            # Build filename: /same/path/to/video_basename.lang.srt
            video_path = Path(filepath)
            srt_filename = video_path.with_name(video_path.stem + f".{lang_code}.srt")

            with open(srt_filename, "w", encoding="utf-8") as f:
                f.write(srt.compose(subtitles))

            self.status_label.set_text(f"✅ Subtitles saved to {srt_filename}")

            # Clean up
            audio_path.unlink()

        except Exception as e:
            self.status_label.set_text(f"Error: {str(e)}")

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
