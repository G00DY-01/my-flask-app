import os
import uuid
import json
import requests
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
from celery import Celery

celery = Celery('worker',
    broker='redis://red-d1lq916mcj7s73ar5ejg:6379',
    backend='redis://red-d1lq916mcj7s73ar5ejg:6379'
)

def download_file(url, filename):
    r = requests.get(url)
    with open(filename, 'wb') as f:
        f.write(r.content)

def create_caption_clip(text, start, end):
    caption = TextClip(
        text,
        fontsize=60,
        font='Arial-Bold',
        color='white',
        stroke_color='black',
        stroke_width=2,
        method='caption',
        size=(1080, None)
    ).set_start(start).set_end(end).set_position(('center', 'bottom'))
    return caption

@celery.task(name='worker.process_video_task')
def process_video_task(video_url, audio_url, duration, caption_data):
    video_filename = f'{uuid.uuid4()}.mp4'
    audio_filename = f'{uuid.uuid4()}.mp3'
    output_filename = f'output_{uuid.uuid4()}.mp4'

    download_file(video_url, video_filename)
    download_file(audio_url, audio_filename)

    video = VideoFileClip(video_filename).subclip(0, duration)
    audio = AudioFileClip(audio_filename)
    video = video.set_audio(audio)

    captions = []
    word_durations = json.loads(caption_data)
    for item in word_durations:
        captions.append(create_caption_clip(item['word'], item['startMs'] / 1000, item['endMs'] / 1000))

    final = CompositeVideoClip([video, *captions])
    final.write_videofile(output_filename, codec='libx264', audio_codec='aac')

    return {'output': output_filename}
