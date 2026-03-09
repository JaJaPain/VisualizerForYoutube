# ðŸŽµ Pro Visualizer: Quick Start Guide

I've set up a professional-grade music visualizer system for you! It uses **Librosa** for advanced audio analysis and **MoviePy** for 1080p video rendering.

## ðŸ“ Project Location
The files are located in your mastering app directory:
`d:\MasteringApp\visualizer\`

- `engine.py`: The "brain" of the visualizer (Audio + Visual Logic).
- `render.py`: The CLI tool to generate your videos.
- `venv/`: The isolated Python environment with all required libraries.

## ðŸš€ How to Render your Video
Once you have your mastered WAV file, you can generate a visualizer from the terminal:

1.  Open **PowerShell** in the `d:\MasteringApp\visualizer` directory.
2.  Run the following command:
    ```powershell
    .\venv\Scripts\python.exe render.py "C:\Path\To\YourMasteredFile.wav"
    ```
3.  The video will be saved as `YourMasteredFile_visualizer.mp4` by default.

### Custom Options:
- **Change Resolution**: `--res 1920x1080` or `--res 3840x2160` (for 4K!)
- **Change Frame Rate**: `--fps 60` for super-smooth YouTube motion.
- **Custom Output Path**: `-o "C:\MyYouTube\Vids\Song_Video.mp4"`

## ðŸŽ¨ Aesthetic Features
- **Central Core Pulse**: The inner sphere glows and pulses in perfect sync with the Bass/Kick.
- **Frequency Ribbons**: 180 individual bars dance around the core, reflecting the song's Mid/High energy.
- **Dynamic Theming**: Every song gets a unique color palette automatically generated from its unique signature.

## ðŸ› ï¸ Modifying the "Look"
Open `engine.py` and tweak these parameters:
- `num_bars`: Increase to 360 for a denser, more complex spectrum.
- `glow_size`: Increase for a dreamier, softer look.
- `bar_len`: Scale up the multiplier for more aggressive movement.

## ðŸ’¡ YouTube Pro Tips
1.  **Bitrate**: I've set it to **8,000k** by default for crisp 1080p quality on YouTube.
2.  **Audio Sync**: The tool uses your raw mastered audio as the sound source, so there is **ZERO** quality loss in the video export.

