import os
import uuid
import json
import requests
import subprocess
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
from celery import Celery

app = Celery('worker', broker='redis://red-d1lq916mcj7s73ar5ejg:6379', backend='redis://red-d1lq916mcj7s73ar5ejg:6379')

@app.task
def process_video_audio(video_url, audio_url, caption_data, audio_duration):
    job_id = str(uuid.uuid4())
    video_path = f'{job_id}_video.mp4'
    audio_path = f'{job_id}_audio.mp3'
    output_path = f'{job_id}_final.mp4'

    with open(video_path, 'wb') as f:
        f.write(requests.get(video_url).content)

    with open(audio_path, 'wb') as f:
        f.write(requests.get(audio_url).content)

    trimmed_video_path = f'{job_id}_trimmed.mp4'
    subprocess.run([
        'ffmpeg', '-y', '-i', video_path, '-t', str(audio_duration),
        '-c:v', 'copy', '-c:a', 'aac', trimmed_video_path
    ], check=True)

    video = VideoFileClip(trimmed_video_path)
    captions = []

    for word_info in caption_data:
        word = word_info['word']
        start = word_info['startMs'] / 1000
        end = word_info['endMs'] / 1000

        txt_clip = TextClip(
            word,
            fontsize=80,
            font='Arial-Bold',
            color='white',
            stroke_color='black',
            stroke_width=3,
            size=(video.w, None),
            method='caption'
        ).set_start(start).set_end(end).set_position('center')

        captions.append(txt_clip)

    final = CompositeVideoClip([video] + captions)
    final = final.set_audio(AudioFileClip(audio_path))
    final.write_videofile(output_path, codec='libx264', audio_codec='aac', threads=4)

    return {'status': 'done', 'output': output_path}
