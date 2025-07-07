import os
import uuid
import json
import requests
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)
os.makedirs("files", exist_ok=True)

def download_file(url, filename):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

@app.route('/process', methods=['POST'])
def process_video():
    try:
        data = request.get_json()
        video_url = data['video_url']
        audio_url = data['audio_url']
        duration = float(data.get('duration', 60))
        caption_data = data.get('caption_data', [])

        uid = str(uuid.uuid4())
        video_path = f"files/{uid}_video.mp4"
        audio_path = f"files/{uid}_audio.mp3"
        output_path = f"files/{uid}_final.mp4"

        download_file(video_url, video_path)
        download_file(audio_url, audio_path)

        # Trim video to audio length (+1 second buffer)
        trimmed_path = f"files/{uid}_trimmed.mp4"
        subprocess.run([
            "ffmpeg", "-y",
            "-i", video_path,
            "-t", str(duration + 1),
            "-c", "copy",
            trimmed_path
        ], check=True)

        # Generate caption drawtext filter
        drawtext_filters = []
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Adjust if needed

        for word in caption_data:
            start = int(word["startMs"]) / 1000
            end = int(word["endMs"]) / 1000
            text = word["word"].replace("'", "\\'")

            drawtext_filters.append(
                f"drawtext=fontfile='{font_path}':text='{text}':"
                f"enable='between(t,{start},{end})':"
                f"fontcolor=white:fontsize=48:borderw=2:x=(w-text_w)/2:y=h-150"
            )

       # Write filter_complex to file to avoid length limit
        filter_script_path = f"files/{uid}_filters.txt"
        with open(filter_script_path, "w") as f:
            f.write(",".join(drawtext_filters))

        # Use -filter_complex_script to apply filters
        subprocess.run([
            "ffmpeg", "-y",
            "-i", trimmed_path,
            "-filter_complex_script", filter_script_path,
            "-c:a", "copy",
            captioned_path
        ], check=True)

        # Combine captioned video + audio
        subprocess.run([
            "ffmpeg", "-y",
            "-i", captioned_path,
            "-i", audio_path,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac",
            output_path
        ], check=True)

        return jsonify({
            "message": "Video processed successfully.",
            "output_path": f"/{output_path}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
