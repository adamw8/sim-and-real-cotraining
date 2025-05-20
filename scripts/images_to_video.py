#!/usr/bin/env python3

import os
import subprocess
import argparse
from pathlib import Path
import shutil

def images_to_video(image_dir, output_path, fps=10, text="Human Teleop Demo in Target Sim (2x speed)"):
    """
    Convert a directory of images to an MP4 video using ffmpeg.
    
    Args:
        image_dir (str): Path to directory containing images
        output_path (str): Path to save the output video
        fps (int): Frames per second for the output video
        text (str): Text to display in the video
    """
    # Get all image files and sort them numerically
    image_files = []
    for f in os.listdir(image_dir):
        if f.lower().endswith(('.png', '.jpg', '.jpeg')):
            try:
                # Extract number from filename (assuming format like "frame_001.png" or "1.png")
                num = int(''.join(filter(str.isdigit, f)))
                image_files.append((num, f))
            except ValueError:
                print(f"Warning: Skipping file {f} as it doesn't contain a valid number")
                continue
    
    # Sort files by their numeric value
    image_files.sort(key=lambda x: x[0])
    
    if not image_files:
        raise ValueError("No valid image files found in the directory")
    
    # Calculate how many frames we need to add to reach 18 seconds
    total_frames_needed = 18 * fps
    current_frames = len(image_files)
    frames_to_add = max(0, total_frames_needed - current_frames)
    
    # Create a temporary directory for the padding frames
    temp_dir = os.path.join(os.path.dirname(output_path), 'temp_frames')
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Copy the last frame multiple times to pad to 18 seconds
        last_frame = os.path.join(image_dir, image_files[-1][1])
        for i in range(frames_to_add):
            shutil.copy2(last_frame, os.path.join(temp_dir, f'pad_{i:04d}.png'))
        
        # Create a temporary file listing all images
        temp_list = os.path.join(os.path.dirname(output_path), 'temp_file_list.txt')
        with open(temp_list, 'w') as f:
            # Write all frames except the last one
            for _, filename in image_files[:-1]:
                f.write(f"file '{os.path.join(image_dir, filename)}'\n")
                f.write(f"duration {1/fps}\n")
            
            # Write the last frame
            f.write(f"file '{os.path.join(image_dir, image_files[-1][1])}'\n")
            f.write(f"duration {1/fps}\n")
            
            # Write the padding frames
            for i in range(frames_to_add):
                f.write(f"file '{os.path.join(temp_dir, f'pad_{i:04d}.png')}'\n")
                f.write(f"duration {1/fps}\n")
        
        # Use ffmpeg to create the video with text overlay
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file if it exists
            '-f', 'concat',
            '-safe', '0',
            '-i', temp_list,
            '-vsync', 'vfr',
            '-vf', f"drawtext=text='{text}':fontcolor=white:fontsize=20:box=1:boxcolor=black@0.5:boxborderw=5:x=(w-text_w)/2:y=(h-text_h-20)",  # Center text at bottom
            '-pix_fmt', 'yuv420p',  # Better compatibility
            '-c:v', 'libx264',  # Use H.264 codec
            '-preset', 'medium',  # Encoding preset
            '-crf', '23',  # Constant Rate Factor
            output_path
        ]
        
        # Run ffmpeg command
        subprocess.run(cmd, check=True)
        print(f"Video saved to {output_path}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error creating video: {e}")
        raise
    finally:
        # Clean up temporary files
        if os.path.exists(temp_list):
            os.remove(temp_list)
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def main():
    parser = argparse.ArgumentParser(description='Convert a directory of images to an MP4 video using ffmpeg')
    parser.add_argument('image_dir', help='Directory containing the images')
    parser.add_argument('output_path', help='Path to save the output video')
    parser.add_argument('--fps', type=int, default=10, help='Frames per second (default: 10)')
    parser.add_argument('--preset', default='medium', 
                      choices=['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 
                              'medium', 'slow', 'slower', 'veryslow'],
                      help='FFmpeg encoding preset (default: medium)')
    parser.add_argument('--crf', type=int, default=23,
                      help='Constant Rate Factor (18-28 is good, lower = better quality)')
    parser.add_argument('--text', default='Human Teleop Demo in Target Sim (2x speed)',
                      help='Text to display in bottom right corner (default: Human Teleop Demo in Target Sim (2x speed))')
    parser.add_argument('--font-size', type=int, default=20,
                      help='Font size for the text (default: 20)')
    
    args = parser.parse_args()
    
    # Convert paths to absolute paths
    image_dir = os.path.abspath(args.image_dir)
    output_path = os.path.abspath(args.output_path)
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    images_to_video(image_dir, output_path, args.fps, args.text)

if __name__ == '__main__':
    main() 