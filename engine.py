import os
import numpy as np
import librosa
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import tqdm

# --- FFMPEG CONFIGURATION ---
try:
    import imageio_ffmpeg
    os.environ["FFMPEG_BINARY"] = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    os.environ["FFMPEG_BINARY"] = "ffmpeg"

from moviepy.editor import VideoClip, AudioFileClip

class ProVisualizer:
    def __init__(self, audio_path, output_path, params=None):
        self.audio_path = audio_path
        self.output_path = output_path
        
        # Default Parameters
        self.params = {
            'resolution': (1920, 1080),
            'fps': 60,
            'color_a': "#00f2ff",
            'color_b': "#7000ff",
            'cycle_speed': 2.0,
            'travel_speed': 15.0,
            'rotation_force': 1.2,
            'shake_force': 40.0,
            'star_size': 10.0,
            'logo_path': "",
            'mark_path': ""
        }
        if params:
            self.params.update(params)
            
        self.width, self.height = self.params['resolution']
        self.fps = self.params['fps']
        
        # Internal State
        self.duration = 0
        self.stft = None
        self.rms_energy = None
        self.sample_rate = 0
        
        # Assets
        self.logo_img = self.load_asset(self.params['logo_path'])
        self.mark_img = self.load_asset(self.params['mark_path'])
        
        # Background Stars System
        self.init_stars()
        self.offset = 0
        self.current_angle = 0
        self.color_time = 0

    def load_asset(self, path):
        if path and os.path.exists(path):
            try:
                img = Image.open(path).convert("RGBA")
                return img
            except:
                return None
        return None

    def init_stars(self):
        self.stars = []
        for _ in range(600):
            self.stars.append({
                'x': (np.random.random() - 0.5) * self.width * 3.5,
                'y': (np.random.random() - 0.5) * self.height * 3.5,
                'z': np.random.random() * self.width,
                'brightness': 0.4 + np.random.random() * 0.6,
                'pulse': np.random.random() * np.pi * 2,
                'pulse_speed': 0.02 + np.random.random() * 0.05,
                'is_nova': np.random.random() > 0.97
            })

    def hex_to_rgb(self, hex):
        hex = hex.lstrip('#')
        return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))

    def lerp_color(self, c1, c2, t):
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        return (r, g, b)

    def analyze_audio(self):
        print(f"[INFO] Analyzing Audio Features...")
        y, sr = librosa.load(self.audio_path, sr=44100, mono=True)
        self.duration = librosa.get_duration(y=y, sr=sr)
        self.sample_rate = sr
        self.stft = np.abs(librosa.stft(y, hop_length=512))
        self.rms_energy = librosa.feature.rms(y=y, hop_length=512)[0]

    def make_frame(self, t):
        # 1. Base Setup
        idx = int(t * self.sample_rate / 512)
        idx = min(idx, self.stft.shape[1] - 1)
        
        # Frequency normalization (Scaling for visuals)
        stft_max = np.max(self.stft) if self.stft.any() else 1.0
        bass = np.max(self.stft[1:6, idx]) / (stft_max * 0.7 + 0.1) 
        bass = min(1.0, bass)
        
        rms = self.rms_energy[idx] if self.rms_energy is not None else 0
        
        # 2. Timing & Colors
        travel = self.params['travel_speed']
        self.offset = (self.offset + (travel + (bass * 70)) * 0.18) % 2000
        
        self.color_time = t * self.params['cycle_speed']
        color_t = (np.sin(self.color_time) + 1) / 2
        c1 = self.hex_to_rgb(self.params['color_a'])
        c2 = self.hex_to_rgb(self.params['color_b'])
        active_color = self.lerp_color(c1, c2, color_t)
        
        # 3. Shake Calculation
        shake_limit = self.params['shake_force']
        sx = (np.random.random() - 0.5) * (bass**2) * shake_limit
        sy = (np.random.random() - 0.5) * (bass**2) * shake_limit
        
        # 4. Drawing Logic
        img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 255))
        draw = ImageDraw.Draw(img)
        
        center = (self.width // 2 + sx, self.height // 2 + sy)

        # Draw Stars
        star_base = self.params['star_size']
        for s in self.stars:
            frame_t = 1/self.fps
            s['z'] -= ((travel * 0.12 * 60 * frame_t) + (bass * 28 * 60 * frame_t))
            if s['z'] < 1: s['z'] = self.width
            
            s['pulse'] += s['pulse_speed']
            twinkle = (np.sin(s['pulse']) + 1) / 2
            
            pos_x = center[0] + (s['x'] / s['z']) * (self.width / 2)
            pos_y = center[1] + (s['y'] / s['z']) * (self.height / 2)
            
            nova_boost = (bass * 5) if (s['is_nova'] and bass > 0.8) else 1
            size = (1 - s['z'] / self.width) * star_base * (0.8 + twinkle * 0.4) * nova_boost
            
            if 0 <= pos_x < self.width and 0 <= pos_y < self.height and size > 0.1:
                alpha = int((1 - s['z'] / self.width) * s['brightness'] * (0.5 + twinkle * 0.5) * 255)
                draw.ellipse([pos_x - size, pos_y - size, pos_x + size, pos_y + size], 
                             fill=(255, 255, 255, alpha))

        # Rotate Tunnel
        self.current_angle += (self.params['rotation_force'] * 0.015 + bass * 0.04)
        
        # Tunnel Lines (60fps simulation means we need to draw lines from center)
        # Note: PIL doesn't support rotation easily for dynamic lines, so we use math
        for i in range(12):
            angle = (i / 12) * np.pi * 2 + self.current_angle
            line_len = 3000
            lx = center[0] + np.cos(angle) * line_len
            ly = center[1] + np.sin(angle) * line_len
            alpha = int((0.3 + bass * 0.4) * 255)
            draw.line([center[0], center[1], lx, ly], fill=active_color + (alpha,), width=4)
        
        # Tunnel Circles
        for i in range(15):
            line_z = ((i * 180 - self.offset) % 2000 + 2000) % 2000
            radius = (2000 / max(1, line_z)) * 120
            alpha = int(max(0, 1 - (line_z / 2000)) * 255)
            width = int(max(1, 15 * (1 - line_z / 2000)))
            
            draw.ellipse([center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius], 
                         outline=active_color + (alpha,), width=width)

        # Center Logo & Glow
        # Radial gradient approximation with multiple circles
        for r in range(800, 0, -50):
            alpha = int(max(0, (1 - r/800) * (0.2 + bass * 0.5)) * 255)
            draw.rectangle([0, 0, self.width, self.height], fill=active_color + (alpha,))
            # Wait, the HTML does a full screen overlay. Let's do that.
            break # Just one overlay is enough for performance in PIL
            
        # Draw the Logo
        if self.logo_img:
            logo_bass_scale = 1 + bass * 0.15
            target_h = int(self.height * 0.45 * logo_bass_scale)
            target_w = int(self.logo_img.width * (target_h / self.logo_img.height))
            
            logo_resized = self.logo_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            # Simple glow effect (paste copy behind)
            logo_pos = (self.width // 2 - target_w // 2, self.height // 2 - target_h // 2)
            img.paste(logo_resized, logo_pos, logo_resized)

        # Watermark
        if self.mark_img:
            mw = 270
            mh = int((self.mark_img.height / self.mark_img.width) * mw)
            mark_resized = self.mark_img.resize((mw, mh), Image.Resampling.LANCZOS)
            mark_pos = (self.width - mw - 60, self.height - mh - 60)
            img.paste(mark_resized, mark_pos, mark_resized)

        return np.array(img.convert('RGB'))

    def export(self):
        self.analyze_audio()
        print(f"[INFO] Exporting NEBULA Visualizer...")
        clip = VideoClip(self.make_frame, duration=self.duration)
        audio_clip = AudioFileClip(self.audio_path)
        clip = clip.set_audio(audio_clip)
        clip.write_videofile(self.output_path, fps=self.fps, codec='libx264', audio_codec='aac', bitrate="12000k")
        print(f"[SUCCESS] Video Saved: {self.output_path}")

if __name__ == "__main__":
    pass
