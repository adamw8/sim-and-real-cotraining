#!/usr/bin/env python3

import argparse
import subprocess
import os
import json
import tempfile
import shutil

def create_status_overlay(input_video, output_video, is_success, extend_final=2):
    """
    Create a video with a status indicator and 2x in the bottom right corner.
    
    Args:
        input_video (str): Path to input MP4 file
        output_video (str): Path to output MP4 file
        is_success (bool): True for success, False for failure
        extend_final (int): Number of seconds to extend the final frame (default: 2)
    """
    # Get video dimensions and duration
    probe_cmd = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height:format=duration',
        '-of', 'json',
        input_video
    ]
    result = subprocess.run(probe_cmd, capture_output=True, text=True)
    video_info = json.loads(result.stdout)
    width = int(video_info['streams'][0]['width'])
    height = int(video_info['streams'][0]['height'])
    duration = float(video_info['format']['duration'])
    
    # Set text and colors based on success/failure
    status_text = "Successful Trial (2x speed)" if is_success else "Failed Trial (2x speed)"
    text_color = "darkgreen" if is_success else "darkred"
    box_color = "green@0.5" if is_success else "red@0.5"
    
    # Create the filter complex string with matching format from images_to_video.py
    filter_complex = (
        f"[0:v]drawtext=text='{status_text}':"
        f"fontcolor={text_color}:"
        f"fontsize={height//20}:"
        f"box=1:"
        f"boxcolor={box_color}:"
        f"boxborderw=5:"
        f"x=(w-text_w)/2:"  # Center horizontally
        f"y=(h-text_h-40),"  # Keep near bottom
        f"format=yuv420p,"
        f"tpad=stop_mode=clone:stop_duration={extend_final}[v]"
    )
    
    # Create the final video
    cmd = [
        'ffmpeg', '-y',
        '-i', input_video,
        '-filter_complex', filter_complex,
        '-map', '[v]',
        '-map', '0:a?',  # Copy audio if present
        '-c:v', 'libx264',
        '-c:a', 'copy',
        '-preset', 'medium',
        '-crf', '23',
        output_video
    ]
    
    subprocess.run(cmd)

def main():
    parser = argparse.ArgumentParser(description='Add status indicator and 2x to video')
    parser.add_argument('input_video', help='Path to input MP4 file')
    parser.add_argument('output_video', help='Path to output MP4 file')
    parser.add_argument('--success', type=int, choices=[0, 1], required=True,
                      help='1 for success, 0 for failure')
    parser.add_argument('--extend-final', type=int, default=2,
                      help='Number of seconds to extend the final frame (default: 2)')
    
    args = parser.parse_args()
    
    create_status_overlay(args.input_video, args.output_video, bool(args.success), args.extend_final)

if __name__ == '__main__':
    main() 