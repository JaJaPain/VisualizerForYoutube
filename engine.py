import os
import numpy as np
import librosa
from PIL import Image, ImageDraw, ImageFilter
import tqdm

# --- FFMPEG CONFIGURATION ---
# We use imageio-ffmpeg as the source of truth for the binary
try:
    import imageio_ffmpeg
    os.environ["FFMPEG_BINARY"] = imageio_ffmpeg.get_ffmpeg_exe()
    print(f"[FFMPEG] Using binary at: {os.environ['FFMPEG_BINARY']}")
except ImportError:
    print("[FFMPEG] imageio-ffmpeg not found. Re-installing...")
    import subprocess
    subprocess.check_call(["pip", "install", "imageio-ffmpeg"])
    import imageio_ffmpeg
    os.environ["FFMPEG_BINARY"] = imageio_ffmpeg.get_ffmpeg_exe()

# Now safe to import MoviePy
from moviepy.editor import VideoClip, AudioFileClip

class ProVisualizer:
    def __init__(self, audio_path, output_path, resolution=(1920, 1080), fps=60):
        self.audio_path = audio_path
        self.output_path = output_path
        self.width, self.height = resolution
        self.fps = fps
        self.duration = 0
        
        # Audio Analysis storage
        self.stft = None
        self.rms_energy = None
        self.sample_rate = 0
        
        # Aesthetics Seed
        self.seed = abs(hash(os.path.basename(audio_path)))
        np.random.seed(self.seed % (2**32))
        self.theme_color = (np.random.randint(0, 100), np.random.randint(150, 255), np.random.randint(200, 255))
        
    def analyze_audio(self):
        print(f"[INFO] Analyzing Audio Features...")
        try:
            # Standardizing SR to 44.1k to ensure consistent frequency mapping across sources
            y, sr = librosa.load(self.audio_path, sr=44100, mono=True)
            self.duration = librosa.get_duration(y=y, sr=sr)
            self.sample_rate = sr
            
            # STFT params: hop_length = 512, n_fft = 2048 (Standard)
            # This yields frequency bins from 0 to 22.05kHz
            self.stft = np.abs(librosa.stft(y, hop_length=512, n_fft=2048))
            
            # RMS for overall volume pulse (Synced frames to STFT)
            self.rms_energy = librosa.feature.rms(y=y, hop_length=512)[0]
            print(f"[SUCCESS] Analysis complete. STFT frames: {self.stft.shape[1]}")
        except Exception as e:
            print(f"[ERROR] Audio analysis failed: {e}")
            raise

    def get_time_index(self, t):
        if self.stft is None:
            return 0
        # Map time t (seconds) to the correct STFT frame index
        idx = int(t * self.sample_rate / 512)
        return max(0, min(idx, self.stft.shape[1] - 1))

    def draw_glowing_circle(self, draw, center, radius, color, glow_size=40):
        # Prevent zero or negative radius crash
        radius = max(1.0, float(radius))
        for r in range(int(radius + glow_size), int(radius), -4):
            # Soft radial glow falloff
            dist_p = (r - radius) / glow_size
            alpha = int(45 * (1.0 - dist_p))
            glow_col = color + (alpha,)
            draw.ellipse([center[0]-r, center[1]-r, center[0]+r, center[1]+r], fill=glow_col)
        # Inner solid core
        draw.ellipse([center[0]-radius, center[1]-radius, center[0]+radius, center[1]+radius], fill=(255, 255, 255, 255))

    def make_frame(self, t):
        # 1. Create Base Canvas
        base_img = Image.new('RGBA', (self.width, self.height), (10, 12, 18, 255))
        draw = ImageDraw.Draw(base_img)
        center = (self.width // 2, self.height // 2)

        try:
            # 2. Extract Frequency/Pulse Data for this timestamp
            idx = self.get_time_index(t)
            
            # RMS Volume Pulse (Drives the central core)
            rms = self.rms_energy[idx] if self.rms_energy is not None and len(self.rms_energy) > idx else 0
            vol_pulse = 1.0 + (rms * 2.8) # Adjusted sensitivity
            base_radius = 160 * vol_pulse
            
            # 3. Draw Core Glow
            self.draw_glowing_circle(draw, center, base_radius, self.theme_color)

            # 4. Draw Radial Frequency Bars
            if self.stft is not None:
                num_bars = 180
                # Take the lower half of the spectrum (0 - 11kHz) for visually interesting movement
                stft_segment = self.stft[:512, idx]
                seg_size = len(stft_segment)
                
                for i in range(num_bars):
                    angle = (i / num_bars) * (2 * np.pi)
                    
                    # Logarithmic/Grouped frequency mapping
                    f_idx = int((i / num_bars) * seg_size)
                    f_idx = min(f_idx, seg_size - 1)
                    f_val = stft_segment[f_idx]
                    
                    # Higher frequencies don't move as much, so we scale them up for visual fidelity
                    # bass bars (i < 20) are naturally strong, high ones (i > 100) need boost
                    boost = 1.0 + (i / num_bars) * 1.5
                    bar_len = f_val * 400 * boost
                    
                    start_r = base_radius + 15
                    end_r = start_r + bar_len
                    
                    x1 = center[0] + start_r * np.cos(angle)
                    y1 = center[1] + start_r * np.sin(angle)
                    x2 = center[0] + end_r * np.cos(angle)
                    y2 = center[1] + end_r * np.sin(angle)
                    
                    # Elegant Cyan/Theme gradient bars
                    draw.line([x1, y1, x2, y2], fill=self.theme_color + (210,), width=3)
        except Exception as e:
            # Resilience: Prevent one failed frame from stopping the whole video
            print(f"[RECOVERABLE ERROR] Frame t={t:.2f} failed: {e}")

        return np.array(base_img.convert('RGB'))

    def export(self):
        self.analyze_audio()
        print(f"[INFO] Exporting @ {self.width}x{self.height} ({self.fps} fps)...")
        
        # Clip generation
        clip = VideoClip(self.make_frame, duration=self.duration)
        audio_clip = AudioFileClip(self.audio_path)
        clip = clip.set_audio(audio_clip)
        
        # Render H.264
        clip.write_videofile(self.output_path, fps=self.fps, codec='libx264', audio_codec='aac', bitrate="8000k")
        print(f"[SUCCESS] Export Finished: {self.output_path}")

if __name__ == "__main__":
    pass
