# sesopenko/yomisub

**yomisub** is a desktop application for automatically generating subtitles for video files using AI-powered
transcription with OpenAI Whisper. It is designed to assist with language learning by enabling users to watch foreign
television shows and movies with native-language subtitles, even when official subtitles are unavailable.

![](docs/Screenshot%20from%202025-04-19%2016-39-48.png)

The application includes:

- A GTK-based graphical user interface
- File picker for selecting video files
- Audio track selection for videos with multiple language tracks
- Whisper model selection (e.g., tiny, base, medium, large-v2)
- Subtitle generation in `.srt` format, saved alongside the video file

This tool was created to support language immersion and comprehension, particularly for learners of Japanese.

---

## Requirements

* Python 3.11

Tested on Debian with the following installation process:

```bash
sudo apt update


# install system dependencies

sudo apt install python3.11-venv ffmpeg python3-gi python3-gi-cairo gir1.2-gtk-3.0 libgirepository1.0-dev gir1.2-gtk-3.0

# add system site package to venv
python3 -m venv .venv --system-site-packages

# reload venv
source .venv/bin/activate

# test that gi can now be imported while in the venv
python -c "import gi"

# install pip dependencies
source .venv/bin/activate
pip install -r requirements.txt
```

## Running

```bash
python3 yomisub.py
```

Choose a model which will fit within the VRAM space of your GPU. Smaller models are faster but less accurate.

Whisper will download the chosen model to `~/.cache/whisper`

## License

This project is open source under the MIT License. See [LICENSE.txt](LICENSE.txt) for full details.

© 2025 Sean Esopenko