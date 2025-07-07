from flask import Flask, request, jsonify, send_from_directory
import subprocess
import uuid
import os
import requests

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process_video():
    try:
        # Extract POST data
        data = request.json or request.form
        video_url = data.get('video_url')
        audio_url = data.get('audio_url')
        caption_text = data.get('caption_text', '')
        duration = int(data.get('duration', 60))

        # Generate unique ID for temp files
        unique_id = str(uuid.uuid4())

        # File paths
        video_path = f"{unique_id}_video.mp4"
        audio_path = f"{unique_id}_audio.mp3"
        output_path = f"{unique_id}_final.mp4"

        # Download video
        with open(video_path, 'wb') as f:
            f.write(requests.get(video_url).content)

        # Download audio
        with open(audio_path, 'wb') as f:
            f.write(requests.get(audio_url).content)

        # Run ffmpeg to merge
        command = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            output_path
        ]
        subprocess.run(command, check=True)

        # Return success with public URL path
        return jsonify({
            "message": "Video processed successfully.",
            "output_path": f"https://{request.host}/files/{output_path}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/files/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename, as_attachment=False)


if __name__ == '__main__':
    app.run(debug=True)
