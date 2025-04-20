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

sudo apt install \
    python3.11-venv \
    ffmpeg \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    libgirepository1.0-dev \
    espeak-ng \
    libespeak-ng1 \
    libsndfile1 \
    build-essential \
    python3-dev

# add system site package to venv
python3 -m venv .venv --system-site-packages

# reload venv
source .venv/bin/activate

# test that gi can now be imported while in the venv
python -c "import gi"

# install pip dependencies
source .venv/bin/activate

# install torch.  See https://pytorch.org/get-started/locally/
# Example for CUDA 12.4
pip3 install torch torchvision torchaudio

# append location to cudnn libraries at end of .venv/bin/activate
# use the proper location of your own venv:
# export LD_LIBRARY_PATH="/home/sean/src/github.com/sesopenko/yomisub/.venv/lib/python3.11/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH"

# if running in pycharm build target set the above environment variable in the build settings

# Install WhisperX
pip install git+https://github.com/m-bain/whisperx.git

pip install pyannote.audio


pip install -r requirements.txt
```

## Get a hugging face access token

1. https://huggingface.co/settings/tokens
2. Create new token, give it a name and read access to personal and gated repos
3. add a line to `~/.bashrc`: `export HF_TOKEN=your_actual_token_here`
4. Add HF_TOKEN environment variable to pycharm build configuration
5. Go to https://huggingface.co/pyannote/segmentation-3.0
6. Agree to access repository

## Running

```bash
python3 yomisub.py
```

Choose a model which will fit within the VRAM space of your GPU. Smaller models are faster but less accurate.

Whisper will download the chosen model to `~/.cache/whisper`

## License

This project is open source under the MIT License. See [LICENSE.txt](LICENSE.txt) for full details.

© 2025 Sean Esopenko