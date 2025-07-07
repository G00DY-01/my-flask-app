from flask import Flask, request, jsonify
from worker import process_video_audio

app = Flask(__name__)

@app.route('/')
def index():
    return '==> Your service is live 🎉', 200

@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()

    video_url = data.get('video_url')
    audio_url = data.get('audio_url')
    caption_data = data.get('caption_data')
    duration = data.get('audioLengthInSeconds') or data.get('duration')

    if not all([video_url, audio_url, caption_data, duration]):
        return jsonify({"error": "Missing required parameters"}), 400

    # Send the processing task to Celery worker asynchronously
    task = process_video_audio.apply_async(args=[video_url, audio_url, caption_data, duration])

    return jsonify({"task_id": task.id, "status": "processing"}), 202

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
