# Repository Guidelines

## Project Structure

`yomisub.py` contains the GTK 3 desktop application, including the file picker, audio track and Whisper model selection, transcription worker, and SRT writer. `README.md` documents installation and usage. `requirements.txt` pins Python dependencies, and `docs/` holds the screenshot used by the README.

## Local Development

Use Python 3.11 and follow the Debian setup in `README.md` for GTK 3, PyGObject, and FFmpeg. The system FFmpeg package supplies both `ffmpeg` and `ffprobe`.

- `python3.11 -m venv .venv --system-site-packages` creates a virtual environment that can import Debian's `gi` package.
- `source .venv/bin/activate` activates the environment. Run `python -c "import gi"` to check GTK bindings, then `python -m pip install -r requirements.txt` to install the Python dependencies.
- `python yomisub.py` launches the application. Whisper downloads the selected model on first use and caches it in `~/.cache/whisper`.

## Coding Style

Use four spaces per indentation level, `snake_case` for functions and variables, and `CapWords` for classes such as `SubtitleApp`. Follow existing callback names such as `on_file_chosen`. Run transcription in the worker thread and schedule GTK widget updates from the worker with `GLib.idle_add`. The repository has no configured formatter or linter.

## Testing

There is no checked-in test suite or coverage requirement. Run `python -m py_compile yomisub.py` for a syntax check. For changes to subtitle generation, launch the app with a short video that has a language-tagged audio track and select the `tiny` model for a quick check. Verify that the app writes `<video-stem>.<language-code>.srt` beside the video and that it contains readable text and valid timestamps. For changes to track selection, also test with a video that has multiple audio tracks.

## Commits and Pull Requests

Use short, descriptive commit subjects, following examples such as “Display model selection and tweak subtitle timing”. In the pull request, describe the behavior change and list the checks you ran. Link a related issue when one exists and include a screenshot for visible GTK changes.
