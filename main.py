import os
import json
import uuid
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

UPLOAD_FOLDER = "files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def download_file(url, filename):
    import requests
    response = requests.get(url)
    with open(filename, "wb") as f:
        f.write(response.content)

def write_srt(captions, filepath):
    def ms_to_timestamp(ms):
        s, ms = divmod(ms, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    with open(filepath, "w", encoding="utf-8") as f:
        for i, word_data in enumerate(captions):
            start = ms_to_timestamp(int(word_data["startMs"]))
            end = ms_to_timestamp(int(word_data["endMs"]))
            text = word_data["word"]
            f.write(f"{i + 1}\n{start} --> {end}\n{text}\n\n")

def overlay_captions(video_path, srt_path, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"subtitles=file='{os.path.abspath(srt_path)}':force_style='FontName=Arial,FontSize=48,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00000000&,BorderStyle=1,Outline=3,Shadow=0'",
        "-c:a", "copy",
        output_path
    ]
    subprocess.run(cmd, check=True)

def combine_audio_video(video_path, audio_path, output_path):
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        output_path
    ]
    subprocess.run(cmd, check=True)

@app.route("/process", methods=["POST"])
def process():
    try:
        data = request.get_json()

        video_url = data["video_url"]
        audio_url = data["audio_url"]
        duration = float(data["duration"])
        captions = data["caption_data"]

        if isinstance(captions, str):
            captions = json.loads(captions)

        uid = str(uuid.uuid4())
        video_path = os.path.join(UPLOAD_FOLDER, f"{uid}_video.mp4")
        audio_path = os.path.join(UPLOAD_FOLDER, f"{uid}_audio.mp3")
        srt_path = os.path.join(UPLOAD_FOLDER, f"{uid}.srt")
        captioned_path = os.path.join(UPLOAD_FOLDER, f"{uid}_captioned.mp4")
        final_path = os.path.join(UPLOAD_FOLDER, f"{uid}_final.mp4")

        download_file(video_url, video_path)
        download_file(audio_url, audio_path)
        write_srt(captions, srt_path)
        overlay_captions(video_path, srt_path, captioned_path)
        combine_audio_video(captioned_path, audio_path, final_path)

        return jsonify({"video": final_path}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
