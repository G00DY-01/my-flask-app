import os
import uuid
import json
import requests
import subprocess
from flask import Flask, request, send_file

app = Flask(__name__)

FILES_DIR = "files"
os.makedirs(FILES_DIR, exist_ok=True)

def download_file(url, suffix):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    local_path = os.path.join(FILES_DIR, f"{uuid.uuid4()}{suffix}")
    with open(local_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return local_path

def generate_srt(caption_data, srt_path):
    def ms_to_srt_time(ms):
        seconds, milliseconds = divmod(int(ms), 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, word in enumerate(caption_data):
            start = ms_to_srt_time(word["startMs"])
            end = ms_to_srt_time(word["endMs"])
            f.write(f"{idx + 1}\n{start} --> {end}\n{word['word']}\n\n")

def overlay_captions(video_path, srt_path, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"subtitles={srt_path}:force_style='FontName=Arial,FontSize=48,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00000000&,BorderStyle=1,Outline=3,Shadow=0'",
        "-c:a", "copy",
        output_path
    ]
    subprocess.run(cmd, check=True)

def merge_audio(captioned_video, audio_path, final_path):
    cmd = [
        "ffmpeg", "-y",
        "-i", captioned_video,
        "-i", audio_path,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "copy",
        "-shortest",
        final_path
    ]
    subprocess.run(cmd, check=True)

@app.route("/process", methods=["POST"])
def process():
    try:
        data = request.get_json()

        video_url = data.get("video_url")
        audio_url = data.get("audio_url")
        caption_data = data.get("caption_data")

        if not video_url or not audio_url or not caption_data:
            return {"error": "Missing video_url, audio_url, or caption_data"}, 400

        # Download video and audio
        video_path = download_file(video_url, ".mp4")
        audio_path = download_file(audio_url, ".mp3")

        # Generate subtitle file
        srt_path = os.path.join(FILES_DIR, f"{uuid.uuid4()}.srt")
        generate_srt(caption_data, srt_path)

        # Overlay subtitles
        captioned_video_path = os.path.join(FILES_DIR, f"{uuid.uuid4()}_captioned.mp4")
        overlay_captions(video_path, srt_path, captioned_video_path)

        # Merge audio
        final_output_path = os.path.join(FILES_DIR, f"{uuid.uuid4()}_final.mp4")
        merge_audio(captioned_video_path, audio_path, final_output_path)

        return send_file(final_output_path, as_attachment=True)

    except subprocess.CalledProcessError as e:
        return {"error": f"FFmpeg failed: {str(e)}"}, 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Unexpected error: {str(e)}"}, 500

if __name__ == "__main__":
    app.run(debug=True)
