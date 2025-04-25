import pickle
import textwrap

import gi

from subtitles.tokenization import group_japanese_words

# © 2025 Sean Esopenko
# https://github.com/sesopenko/yomisub

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import re
import gc
import torch
import whisperx
from whisperx import DiarizationPipeline
import srt
from datetime import timedelta
import os
from pathlib import Path
from textwrap import fill
import subprocess
import json
import pycountry
import threading

import logging
import os
import csv

import unicodedata

log_level = os.getenv("LOGGING_LEVEL", "INFO").upper()
logging.basicConfig(
    level=log_level,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)

CONFIG_PATH = Path.home() / ".config" / "yomisub"
HF_TOKEN_FILE = CONFIG_PATH / "huggingface_token.txt"
TEMP_HOME = Path.home() / ".temp" / "yoomisub"

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
            "large-v1": "large-v1 (10 GB)",
            "large-v2": "large-v2 (12 GB)",
            "large-v3": "large-v3 (12+ GB)"
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

        hf_button = Gtk.Button(label="Configure Hugging Face")
        hf_button.connect("clicked", self.on_configure_huggingface_clicked)
        vbox.pack_start(hf_button, True, True, 0)

        self.status_label = Gtk.Label(label="")
        vbox.pack_start(self.status_label, True, True, 0)

    def get_selected_model(self):
        for model, btn in self.model_buttons.items():
            if btn.get_active():
                return model
        return "medium"  # fallback

    def on_configure_huggingface_clicked(self, widget):
        dialog = Gtk.Dialog(
            title="Hugging Face Configuration",
            transient_for=self,
            flags=0,
        )
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Save", Gtk.ResponseType.OK)

        box = dialog.get_content_area()
        box.set_spacing(10)

        instructions = Gtk.Label()
        instructions.set_markup(
            '1. Get a token: <a href="https://hf.co/settings/tokens">https://hf.co/settings/tokens</a>\n'
            '2. Select Read access to contents of all public gated repos you can access\n'
            '3. Paste your token below\n'
            '4. Accept model access: <a href="https://huggingface.co/pyannote/segmentation-3.0">'
            'https://huggingface.co/pyannote/segmentation-3.0</a>\n'
            '5. Click Save'
        )
        instructions.set_justify(Gtk.Justification.LEFT)
        instructions.set_line_wrap(True)
        instructions.set_selectable(True)
        instructions.set_use_markup(True)

        box.add(instructions)

        entry = Gtk.Entry()

        token_label = Gtk.Label()
        token_label.set_justify(Gtk.Justification.LEFT)
        token_label.set_markup(
            'Huggingface Token:'
        )
        box.add(token_label)
        entry.set_placeholder_text("Paste your Hugging Face token here")
        entry.set_visibility(False)  # hide characters like a password
        entry.set_invisible_char("*")  # optional: set masking char
        # Pre-fill if already saved
        if HF_TOKEN_FILE.exists():
            with open(HF_TOKEN_FILE, "r", encoding="utf-8") as f:
                entry.set_text(f.read().strip())

        box.add(entry)

        dialog.show_all()
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            token = entry.get_text().strip()
            CONFIG_PATH.mkdir(parents=True, exist_ok=True)
            with open(HF_TOKEN_FILE, "w", encoding="utf-8") as f:
                f.write(token)
            self.status_label.set_text("✅ Hugging Face token saved.")
        else:
            self.status_label.set_text("Cancelled Hugging Face configuration.")

        dialog.destroy()

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
            logging.info("Extracting audio to %s via ffmpeg", audio_path)

            subprocess.run([
                "ffmpeg", "-y", "-i", filepath,
                "-map", f"0:a:{track_index}", "-acodec", "pcm_s16le",
                str(audio_path)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            device = "cuda" if torch.cuda.is_available() else "cpu"
            model_name = self.get_selected_model()
            GLib.idle_add(self.status_label.set_text, f"Loading Whisper Model for device {device}...")
            logger.info("Loading Whisper Model %s for device %s", model_name, device)
            model = whisperx.load_model(model_name, device=device)



            GLib.idle_add(self.status_label.set_text, "Transcribing with Whisper...")
            logger.info("Transcribing with Whisper for language %s", lang_code)
            result = model.transcribe(str(audio_path), language=lang_code)
            logger.info(f"Transcription result type: {type(result)}, value: {result}")
            del model
            self.free_cache()

            # Load alignment model for better timing
            GLib.idle_add(self.status_label.set_text, f"Loading alignment model for device {device}")
            logger.info("Loading alignment model for device %s", device)
            model_a, metadata = whisperx.load_align_model(language_code=lang_code, device=device)
            GLib.idle_add(self.status_label.set_text, "Re-aligning with Whisper...")
            logger.info("Re-aligning with Whisper for language %s", lang_code)
            aligned_result = whisperx.align(
                result["segments"], model_a, metadata, str(audio_path), device=device
            )

            del model_a
            self.free_cache()

            GLib.idle_add(self.status_label.set_text, f"Loading diarizer model for device {device}...")
            logger.info("Loading diarizer model...")
            token = None
            if HF_TOKEN_FILE.exists():
                with open(HF_TOKEN_FILE, "r", encoding="utf-8") as f:
                    token = f.read().strip()
            else:
                GLib.idle_add(self._show_error_dialog, "Could not retrieve huggingface token. Configure Huggingface.")
                return

            diarize_model = DiarizationPipeline(use_auth_token=token, device=device)

            GLib.idle_add(self.status_label.set_text, "Diarizing to detect speakers...")
            logger.info("Diarizing to detect speakers...")
            diarize_segments = diarize_model(audio=str(audio_path))

            # Inject speaker labels into transcription segments
            aligned_result["segments"] = whisperx.assign_word_speakers(diarize_segments, aligned_result)
            word_segments = aligned_result["segments"]

            GLib.idle_add(self.status_label.set_text, "Transforming to SRT subtitles...")
            logger.info("Transforming to SRT subtitles for language %s", lang_code)

            subtitles = []
            idx = 1
            _pickle_temp(word_segments['word_segments'], 'word_segments')
            tokenized_words = word_segments['word_segments']
            if lang_code == "ja":
                tokenized_words = group_japanese_words(word_segments['word_segments'])
            for idx, start, end, text in split_by_speaker(tokenized_words, lang_code):
                subtitles.append(srt.Subtitle(
                    index=idx,
                    start=timedelta(seconds=start),
                    end=timedelta(seconds=end),
                    content=text
                ))

            srt_path = Path(filepath).with_name(Path(filepath).stem + f".{lang_code}.srt")
            logger.info("Writing SRT subtitles to %s", srt_path)
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt.compose(subtitles))

            audio_path.unlink(missing_ok=True)

            # Write debug info to CSV
            debug_csv_path = Path(filepath).with_name(Path(filepath).stem + f".{lang_code}.debug.csv")
            logger.info(f"Writing debug CSV to {debug_csv_path}")

            with open(debug_csv_path, "w", encoding="utf-8", newline="") as csvfile:
                fieldnames = ["start", "end", "word", "speaker"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for word in word_segments['word_segments']:
                    writer.writerow({
                        "start": word.get("start", ""),
                        "end": word.get("end", ""),
                        "word": word.get("word", ""),
                        "speaker": word.get("speaker", "")
                    })

            logger.info(f"deleted {srt_path}")

            GLib.idle_add(self.status_label.set_text, f"✅ Subtitles saved to {srt_path}")
            logger.info(f"saved to {srt_path}")

        except Exception as e:
            logger.error(e)
            GLib.idle_add(self._show_error_dialog, f"Error: {str(e)}")

    def free_cache(self):
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

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

def clean_repetitions(text, max_repeats=5):
    # Collapse long runs of the same character (like ー or え)
    return re.sub(r'(.)\1{'+str(max_repeats)+r',}', lambda m: m.group(1) * max_repeats + '…', text)

def is_cjk_char(char):
    """Rudimentary check for CJK characters by Unicode block."""
    return any([
        '\u4e00' <= char <= '\u9fff',  # CJK Unified Ideographs
        '\u3040' <= char <= '\u309f',  # Hiragana
        '\u30a0' <= char <= '\u30ff',  # Katakana
        '\uff00' <= char <= '\uffef',  # Full-width roman + half-width kana
    ])

def is_mostly_cjk(text, threshold=0.5):
    cjk_count = sum(1 for c in text if is_cjk_char(c))
    return cjk_count / max(1, len(text)) > threshold

def build_subtitle_text(words):
    raw_text = "".join(w["word"] for w in words).strip()
    if is_mostly_cjk(raw_text):
        return raw_text
    else:
        return " ".join(w["word"] for w in words).strip()

def _pickle_temp(to_save, name):
    TEMP_HOME.mkdir(parents=True, exist_ok=True)
    path = TEMP_HOME / f"{name}.pickle"
    with open(path, "wb") as f:
        pickle.dump(to_save, f)

def split_by_speaker(words, lang_code, max_chars=80, max_duration=4.0, max_repeats=5):
    subs = []
    current = []
    current_speaker = words[0].get('speaker', "")
    current_start = words[0]['start']
    current_end = words[0]['end']
    idx = 1

    for i, word in enumerate(words):
        if not word.get("word"):
            continue

        speaker = word.get("speaker", "")
        word_start = word["start"]
        word_end = word["end"]

        # Check if we should split
        text = build_subtitle_text(words)
        should_split = (
            speaker != current_speaker or
            len(text) > max_chars or
            (word_end - current_start) > max_duration
        )

        if current and should_split:
            subtitle_text = build_subtitle_text(current)
            subtitle_text = clean_repetitions(subtitle_text, max_repeats)
            if subtitle_text:
                current_end = min(current_end, current_start + max_duration)  # Cap to max_duration
                subs.append((idx, current_start, current_end, subtitle_text))
                idx += 1

            current = []
            current_start = word_start
            current_speaker = speaker

        current.append(word)
        current_end = word_end

    # Final subtitle
    if current:
        subtitle_text = " ".join(w["word"] for w in current).strip()
        subtitle_text = clean_repetitions(subtitle_text, max_repeats)
        if subtitle_text:
            current_end = min(current_end, current_start + max_duration)  # Cap to max_duration
            subs.append((idx, current_start, current_end, subtitle_text))

    return subs

def is_repeated_char_text(text):
    # Remove any ellipses or spacing first
    text = text.replace('…', '').replace(' ', '')
    if not text:
        return None
    first_char = text[0]
    return first_char if all(c == first_char for c in text) else None

def collapse_redundant_subs(subs, time_threshold=0.25):
    collapsed = []
    prev_sub = None

    for sub in subs:
        idx, start, end, text = sub
        repeated_char = is_repeated_char_text(text)

        if prev_sub:
            prev_idx, prev_start, prev_end, prev_text = prev_sub
            prev_repeated_char = is_repeated_char_text(prev_text)

            # Same repeated character
            same_repetition = repeated_char and prev_repeated_char and repeated_char == prev_repeated_char
            close_in_time = (start - prev_end) < time_threshold

            if same_repetition and close_in_time:
                # Extend previous subtitle’s end time
                prev_sub = (prev_idx, prev_start, end, prev_text)
                continue
            else:
                collapsed.append(prev_sub)

        prev_sub = sub

    if prev_sub:
        collapsed.append(prev_sub)

    # Re-number the indexes
    for i, (idx, start, end, text) in enumerate(collapsed, 1):
        collapsed[i - 1] = (i, start, end, text)

    return collapsed


def split_words_to_subtitles(words, max_chars=80, max_duration=4.0):
    subtitles = []
    current = []
    current_start = words[0]['start']
    current_end = words[0]['end']
    idx = 1

    for word in words:
        if not word.get("word"):  # skip empty tokens
            continue

        current.append(word)
        current_end = word["end"]

        current_text = " ".join(w["word"] for w in current)
        current_duration = current_end - current_start

        if len(current_text) > max_chars or current_duration > max_duration:
            subtitles.append((
                idx,
                current_start,
                current_end,
                current_text
            ))
            idx += 1
            current = []
            if word.get("word"):
                current_start = word["start"]

    if current:
        current_text = " ".join(w["word"] for w in current)
        subtitles.append((
            idx,
            current_start,
            current_end,
            current_text
        ))

    return subtitles

if __name__ == "__main__":
    win = SubtitleApp()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
