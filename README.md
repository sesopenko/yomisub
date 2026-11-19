# sesopenko/yomisub

**yomisub** is a desktop application for automatically generating subtitles for video files using
whisper.cpp. It is designed to assist with language learning by enabling users to watch foreign
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

## Debian 13 setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and the native
dependencies below. The Python project uses Python 3.13 on x86-64. Enable Debian's
`non-free-firmware` repository component for AMD firmware.

```bash
sudo apt update
sudo apt install build-essential pkg-config python3-dev libcairo2-dev \
  libgirepository-2.0-dev gir1.2-gtk-3.0 ffmpeg git cmake libvulkan-dev \
  glslc mesa-vulkan-drivers vulkan-tools firmware-amd-graphics
```

### Build the Vulkan transcription engine

Build [whisper.cpp v1.9.5](https://github.com/ggml-org/whisper.cpp/releases/tag/v1.9.5)
once. Add the build's `bin` directory to your shell startup file to keep
`whisper-cli` available in future terminals.

```bash
git clone --branch v1.9.5 --depth 1 https://github.com/ggml-org/whisper.cpp.git "$HOME/.local/src/whisper.cpp"
cmake -S "$HOME/.local/src/whisper.cpp" -B "$HOME/.local/src/whisper.cpp/build" \
  -DCMAKE_BUILD_TYPE=Release -DGGML_VULKAN=ON
cmake --build "$HOME/.local/src/whisper.cpp/build" --parallel --target whisper-cli
export PATH="$HOME/.local/src/whisper.cpp/build/bin:$PATH"
vulkaninfo --summary
```

### Install and run yomisub

From the yomisub checkout, move any legacy `.venv` aside before the first sync.

```bash
uv sync --locked
uv run --locked python yomisub.py
```

Choose a model that fits in your GPU's VRAM. The app downloads the selected
multilingual model on first use and caches it in `~/.cache/yomisub/models/`.

To verify GPU use, generate subtitles for a short video with a language-tagged
audio track and the `tiny` model. Check for the Radeon in the Vulkan device list
and a `using Vulkan0 backend` line for that device in the terminal. Mesa may
display the RX 9060 XT as `AMD Radeon Graphics (RADV GFX1200)`. When multiple
GPUs are available, use the Radeon device index from `vulkaninfo --summary` with
`GGML_VK_VISIBLE_DEVICES`. This example selects physical device 1.

```bash
GGML_VK_VISIBLE_DEVICES=1 uv run --locked python yomisub.py
```

## Development

`yomisub.py` launches the application. The `yomisub/` package contains the GTK interface,
subtitle workflow, and adapters for media probing and extraction, model caching, Whisper
transcription, and SRT output.

Run the unit tests after installing the project dependencies. The tests run without
a display, downloads, or media binaries.

```bash
uv run --locked python -m unittest discover -s tests
```

## License

This project is open source under the MIT License. See [LICENSE.txt](LICENSE.txt) for full details.

© 2025 Sean Esopenko
