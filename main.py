from flask import Flask, request, jsonify
import subprocess
import uuid
import requests
import os

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_video():
    try:
        data = request.get_json()
        video_url = data.get('video_url')
        audio_url = data.get('audio_url')
        duration = float(data.get('duration', 60))

        if not video_url or not audio_url:
            return jsonify({'error': 'Missing video_url or audio_url'}), 400

        uid = str(uuid.uuid4())
        video_path = f"{uid}_video.mp4"
        audio_path = f"{uid}_audio.wav"
        trimmed_path = f"{uid}_trimmed.mp4"
        output_path = f"{uid}_final.mp4"

        # Download video
        video_resp = requests.get(video_url)
        with open(video_path, 'wb') as f:
            f.write(video_resp.content)

        # Download audio
        audio_resp = requests.get(audio_url)
        with open(audio_path, 'wb') as f:
            f.write(audio_resp.content)

        # Trim video to match or slightly exceed audio duration
        max_duration = duration + 3
        subprocess.run([
            'ffmpeg', '-y',
            '-i', video_path,
            '-t', str(max_duration),
            '-c:v', 'copy', '-an',
            trimmed_path
        ], check=True)

        # Merge audio + trimmed video
        subprocess.run([
            'ffmpeg', '-y',
            '-i', trimmed_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-shortest',
            output_path
        ], check=True)

        # Respond with path or info
        return jsonify({
            'message': 'Video processed successfully.',
            'output_path': f'/files/{output_path}'
        })

    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'FFmpeg failed: {e}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
