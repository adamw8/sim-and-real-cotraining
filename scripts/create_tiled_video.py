#!/usr/bin/env python3

import os
import subprocess
import argparse
from pathlib import Path
import shutil
import math

def create_tiled_video(input_video, output_path, fps=20, duration=20, end_grid=5):
    """
    Create a tiled video from a single video with a zooming effect.
    
    Args:
        input_video (str): Path to input video file
        output_path (str): Path to save the output video
        fps (int): Frames per second for the output video
        duration (int): Total duration of the output video in seconds
        end_grid (int): Final grid size (e.g. 5 for 5x5)
    """
    try:
        # Get video dimensions
        probe_cmd = [
            'ffprobe', 
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=p=0',
            input_video
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        width, height = map(int, result.stdout.strip().split(','))
        
        # Calculate dimensions for the grid
        total_width = width * end_grid
        total_height = height * end_grid
        
        # Calculate zoom parameters
        # We'll animate the crop to zoom out from the center tile to the full grid
        # Start with 1x1 tile (center), zoom out to end_grid x end_grid
        
        # Calculate the center tile's position
        center_tile = end_grid // 2
        crop_w = width
        crop_h = height
        out_w = width * end_grid
        out_h = height * end_grid
        
        # Animation: from crop_w/h to out_w/h over the duration
        # We'll use t (time in seconds) in the crop filter
        crop_expr_w = f"if(lte(t,{duration}),{crop_w}+({out_w}-{crop_w})*t/{duration},{out_w})"
        crop_expr_h = f"if(lte(t,{duration}),{crop_h}+({out_h}-{crop_h})*t/{duration},{out_h})"
        crop_expr_x = f"({out_w}-({crop_expr_w}))/2"
        crop_expr_y = f"({out_h}-({crop_expr_h}))/2"
        
        # Build the filter_complex for tiling and zooming
        filter_complex = []
        for i in range(end_grid * end_grid):
            filter_complex.append(f'[{i}:v]scale={width}:{height}[v{i}]')
        for row in range(end_grid):
            row_inputs = []
            for col in range(end_grid):
                idx = row * end_grid + col
                row_inputs.append(f'[v{idx}]')
            filter_complex.append(f"{''.join(row_inputs)}hstack=inputs={end_grid}[row{row}]")
        row_inputs = [f'[row{i}]' for i in range(end_grid)]
        filter_complex.append(f"{''.join(row_inputs)}vstack=inputs={end_grid}[grid]")
        # Now apply the animated crop to zoom out
        filter_complex.append(
            f"[grid]crop=w={crop_expr_w}:h={crop_expr_h}:x={crop_expr_x}:y={crop_expr_y},scale={out_w}:{out_h},fps={fps},format=yuv420p[out]"
        )
        filter_complex_str = ';'.join(filter_complex)
        
        # Create the final video
        input_args = []
        for _ in range(end_grid * end_grid):
            input_args.extend(['-stream_loop', '-1', '-i', input_video])
        cmd = [
            'ffmpeg', '-y',
            *input_args,
            '-filter_complex', filter_complex_str,
            '-map', '[out]',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'medium',
            '-crf', '23',
            '-t', str(duration),
            output_path
        ]
        
        subprocess.run(cmd, check=True)
        print(f"Tiled video saved to {output_path}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error creating video: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Create a tiled video with zooming effect')
    parser.add_argument('input_video', help='Path to input video file')
    parser.add_argument('output_path', help='Path to save the output video')
    parser.add_argument('--fps', type=int, default=20, help='Frames per second (default: 20)')
    parser.add_argument('--duration', type=int, default=20, 
                      help='Total duration of the output video in seconds (default: 20)')
    parser.add_argument('--end-grid', type=int, default=5,
                      help='Final grid size (default: 5 for 5x5)')
    
    args = parser.parse_args()
    
    # Convert paths to absolute paths
    input_video = os.path.abspath(args.input_video)
    output_path = os.path.abspath(args.output_path)
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    create_tiled_video(input_video, output_path, args.fps, args.duration, args.end_grid)

if __name__ == '__main__':
    main() 