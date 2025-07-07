import os
import subprocess
import json
from celery import Celery

# Use your Redis URL here
redis_url = 'redis://red-d1lq916mcj7s73ar5ejg:6379'

app = Celery('worker', broker=redis_url, backend=redis_url)

@app.task
def process_video_audio(video_url, audio_url, caption_data, duration):
    """
    This task:
    - Downloads the video and audio
    - Applies captions with timing and big font size
    - Trims video and audio to the duration
    - Combines audio and video into final output
    """

    # Prepare filenames
    video_file = '/tmp/input_video.mp4'
    audio_file = '/tmp/input_audio.mp3'
    output_file = '/tmp/output_video.mp4'

    # Download video
    subprocess.run(['wget', '-O', video_file, video_url], check=True)

    # Download audio
    subprocess.run(['wget', '-O', audio_file, audio_url], check=True)

    # Build the complex filter for captions from caption_data (list of words with startMs and endMs)
    # caption_data example: [{"word": "Hello", "startMs": 0, "endMs": 500}, ...]
    captions = json.loads(caption_data)

    # Create subtitles file (.ass) with big bold two-layer style captions
    ass_file = '/tmp/captions.ass'
    with open(ass_file, 'w', encoding='utf-8') as f:
        f.write('[Script Info]\n')
        f.write('ScriptType: v4.00+\n')
        f.write('Collisions: Normal\n')
        f.write('PlayResX: 1920\n')
        f.write('PlayResY: 1080\n')
        f.write('\n[V4+ Styles]\n')
        f.write('Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, '
                'Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, '
                'Alignment, MarginL, MarginR, MarginV, Encoding\n')
        # Two layers style for outline and shadow
        f.write('Style: BigCaption1, Arial, 72, &H00FFFFFF, &H000000FF, &H00000000, &H80000000, 1, 0, 0, 0, 100, 100, 0, 0, 3, 3, 0, 2, 10, 10, 10, 1\n')
        f.write('Style: BigCaption2, Arial, 72, &H00FFFFFF, &H00000000, &H00000000, &H00000000, 1, 0, 0, 0, 100, 100, 0, 0, 1, 1, 0, 2, 10, 10, 10, 1\n')
        f.write('\n[Events]\n')
        f.write('Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n')

        for c in captions:
            start = ms_to_ass_time(c['startMs'])
            end = ms_to_ass_time(c['endMs'])
            text = c['word'].replace('{', '').replace('}', '')  # basic sanitize
            # Layer 1 (shadow)
            f.write(f'Dialog: 1,{start},{end},BigCaption1,,0,0,0,,{text}\n')
            # Layer 2 (main text)
            f.write(f'Dialog: 0,{start},{end},BigCaption2,,0,0,0,,{text}\n')

    # Trim video and audio to duration and add subtitles
    cmd = [
        'ffmpeg',
        '-y',
        '-i', video_file,
        '-i', audio_file,
        '-filter_complex', f"[0:v][1:a]concat=n=1:v=1:a=1[v][a];[v]subtitles={ass_file}:force_style='Fontsize=72,PrimaryColour=&H00FFFFFF' [vsub]",
        '-map', '[vsub]',
        '-map', '[a]',
        '-t', str(duration),
        output_file
    ]

    # Run ffmpeg command
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr}")

    # Return path or URL of output video - you may want to upload it somewhere
    return output_file


def ms_to_ass_time(ms):
    """Convert milliseconds to ASS subtitle time format: H:MM:SS.CS"""
    cs = int((ms % 1000) / 10)
    s = int((ms / 1000) % 60)
    m = int((ms / 60000) % 60)
    h = int(ms / 3600000)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
