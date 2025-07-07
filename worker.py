from celery import Celery
import os
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
import tempfile
import requests
import json

def create_celery_app(app=None):
    redis_url = os.getenv("REDIS_URL")
    celery = Celery(
        "worker",
        broker=redis_url,
        backend=redis_url,
    )
    celery.conf.update(task_track_started=True)
    return celery

celery = create_celery_app()

@celery.task(name="worker.process_video")
def process_video(video_url, audio_url, caption_data, duration, task_id):
    duration = float(duration)
    word_data = json.loads(caption_data)

    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = os.path.join(tmpdir, "video.mp4")
        audio_path = os.path.join(tmpdir, "audio.mp3")
        output_path = os.path.join(tmpdir, "output.mp4")

        with open(video_path, "wb") as f:
            f.write(requests.get(video_url).content)
        with open(audio_path, "wb") as f:
            f.write(requests.get(audio_url).content)

        video = VideoFileClip(video_path).subclip(0, duration)
        audio = AudioFileClip(audio_path)
        video = video.set_audio(audio)

        caption_clips = []
        for item in word_data:
            word = item["word"]
            start = float(item["startMs"]) / 1000
            end = float(item["endMs"]) / 1000

            txt_clip = TextClip(
                word,
                fontsize=70,
                font="Arial-Bold",
                color="white",
                stroke_color="black",
                stroke_width=3,
                method="caption",
                size=(video.w, None)
            ).set_position("center").set_start(start).set_end(end)

            caption_clips.append(txt_clip)

        final = CompositeVideoClip([video] + caption_clips)
        final.write_videofile(output_path, codec="libx264", audio_codec="aac")

        print(f"Generated video at {output_path}")
