import argparse
import os
import sys
from engine import ProVisualizer

def main():
    parser = argparse.ArgumentParser(description="Professional Music Visualizer (1080p)")
    parser.add_argument("input", help="Path to the audio file (WAV/MP3)")
    parser.add_argument("--output", "-o", help="Path to save the MP4", default=None)
    parser.add_argument("--fps", "-f", type=int, default=60, help="Frames per second (default: 60)")
    parser.add_argument("--res", "-r", help="Resolution (e.g., 1920x1080)", default="1920x1080")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} not found.")
        sys.exit(1)
        
    width, height = map(int, args.res.split('x'))
    
    if args.output is None:
        args.output = os.path.splitext(args.input)[0] + "_visualizer.mp4"
    
    print("="*40)
    print(" MUSIC VISUALIZER EXPORT ")
    print("="*40)
    print(f"Input:  {args.input}")
    print(f"Output: {args.output}")
    print(f"Res:    {width}x{height} @ {args.fps}fps")
    
    viz = ProVisualizer(args.input, args.output, (width, height), args.fps)
    viz.export()

if __name__ == "__main__":
    main()
