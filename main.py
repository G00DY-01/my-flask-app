from flask import Flask, request, jsonify
import subprocess
import os
import uuid
import requests
import json

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_video():
    data = request.get_json()

    video_url = data.get('video_url')
    audio_url = data.get('audio_url')

    if not video_url or not audio_url:
        return jsonify({"error": "Missing video_url or audio_url"}), 400

    # Generate unique filenames
    session_id = str(uuid.uuid4())
    video_file = f"{session_id}_video.mp4"
    audio_file = f"{session_id}_audio.mp3"
    final_output = f"{session_id}_final.mp4"

    # Download video
    subprocess.run(['curl', '-L', '-o', video_file, video_url], check=True)
    # Download audio
    subprocess.run(['curl', '-L', '-o', audio_file, audio_url], check=True)

    # Combine video and audio
    subprocess.run([
        'ffmpeg', '-y',
        '-i', video_file,
        '-i', audio_file,
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-c:v', 'copy',
        '-shortest',
        final_output
    ], check=True)

    # Upload to file.io
    result = subprocess.run(
        ['curl', '-F', f'file=@{final_output}', 'https://file.io'],
        capture_output=True, text=True
    )

    # Clean up temporary files
    os.remove(video_file)
    os.remove(audio_file)
    os.remove(final_output)

    # Return parsed JSON
    return jsonify(json.loads(result.stdout))

if __name__ == '__main__':
    app.run(debug=True)
