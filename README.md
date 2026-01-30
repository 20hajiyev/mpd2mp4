# mpd2mp4

A Python-based tool for downloading and converting MPD (MPEG-DASH) streams to MP4 format.

## Features

- 🎬 Download video from MPD manifest URLs
- 📁 Process local MPD manifest files
- 🔄 Automatic best quality selection (video + audio)
- 📊 Real-time download progress display
- 🛠️ FFmpeg integration with fallback options

## Requirements

- Python 3.8+
- FFmpeg (optional, but recommended)

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/20hajiyev/mpd2mp4.git
   cd mpd2mp4
   ```

2. **Create a virtual environment (recommended):**

   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script:

```bash
python main.py
```

### Options

1. **Download from URL:**
   - Enter the `.mpd` URL when prompted
   - Provide a filename for the output (e.g., `video.mp4`)

2. **Convert local MPD file:**
   - Enter the local file path to the `.mpd` file
   - The tool will process it using FFmpeg

### Example

```
=== MPD to MP4 Downloader ===

[Info] Using bundled FFmpeg from: ...
Enter the .mpd URL or Local File Path: https://example.com/video.mpd
Enter the desired output filename (e.g., video.mp4): my_video.mp4

[Info] Starting download for: my_video.mp4...
[Downloading] Progress: 45.2% | Speed: 2.5MiB/s | ETA: 00:30
[Finished] Download complete. Processing/Merging...
[Success] Successfully saved as 'my_video.mp4'
```

## Technical Details

- Uses **yt-dlp** for downloading and processing MPD streams
- Uses **FFmpeg** for merging video/audio streams and local file processing
- Supports both remote URLs and local MPD files
- Automatically detects if MPD contains remote or local references

## Dependencies

| Package | Description |
|---------|-------------|
| `yt-dlp` | Video downloading library |
| `imageio-ffmpeg` | Bundled FFmpeg binaries |

## License

This project is open source and available under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

