# Repository Guidelines

## Project Structure

`yomisub.py` wires the production components and launches the GTK 3 application. The `yomisub/` package contains the GTK interface, subtitle workflow, and separate modules for media, model caching, Whisper, and SRT output. Unit tests are in `tests/`. `pyproject.toml` declares Python dependencies and `uv.lock` pins them. `README.md` documents installation and usage, and `docs/` holds the screenshot used by the README.

## Local Development

Use Python 3.13 with uv. Follow the Debian 13 setup in `README.md` for native GTK 3 and FFmpeg dependencies and the Vulkan-enabled `whisper-cli` build.

- `uv sync --locked` installs the Python dependencies into `.venv`.
- `uv run --locked python yomisub.py` launches the application. The app caches downloaded models in `~/.cache/yomisub/models/`.

## Coding Style

Use four spaces per indentation level, `snake_case` for functions and variables, and `CapWords` for classes such as `SubtitleApp`. Follow existing callback names such as `on_file_chosen`. Run transcription in the worker thread and schedule GTK widget updates from the worker with `GLib.idle_add`. The repository has no configured formatter or linter.

## Testing

Run `uv lock --check`, `uv run --locked python -m unittest discover -s tests`, and `uv run --locked python -m compileall -q yomisub.py yomisub tests`. The unit tests run without a display, downloads, or media binaries. For subtitle changes, test a short video with a language-tagged audio track and the `tiny` model. Verify that `<video-stem>.<language-code>.srt` contains readable text and valid timestamps. For GPU changes, check the terminal for the active Vulkan backend. For track selection changes, test a video with multiple audio tracks.

## Commits and Pull Requests

Use short, descriptive commit subjects, following examples such as “Display model selection and tweak subtitle timing”. In the pull request, describe the behavior change and list the checks you ran. Link a related issue when one exists and include a screenshot for visible GTK changes.
