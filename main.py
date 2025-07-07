import os
import uuid
from flask import Flask, request, jsonify
from celery import Celery
from celery.result import AsyncResult

app = Flask(__name__)

# Redis URL from environment or fallback
redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Celery setup
celery = Celery(app.name, broker=redis_url, backend=redis_url)

@celery.task(bind=True)
def process_video_audio(self, video_url, audio_url, caption_data, duration):
    # Put your actual video/audio processing logic here.
    # For example, download video/audio, overlay captions, etc.

    import time
    time.sleep(15)  # Simulate a long task

    # Generate a fake output file path (in real usage, save to cloud storage)
    output_url = f"https://yourcdn.com/final_output_{self.request.id}.mp4"
    return {"output_url": output_url}

@app.route("/process", methods=["POST"])
def process():
    data = request.get_json()
    video_url = data.get("video_url")
    audio_url = data.get("audio_url")
    caption_data = data.get("caption_data")
    duration = data.get("duration")

    if not (video_url and audio_url and caption_data and duration):
        return jsonify({"error": "Missing parameters"}), 400

    task = process_video_audio.apply_async(args=[video_url, audio_url, caption_data, duration])
    return jsonify({"task_id": task.id}), 202

@app.route("/status/<task_id>", methods=["GET"])
def task_status(task_id):
    task_result = AsyncResult(task_id, app=celery)
    if task_result.state == "PENDING":
        response = {"state": task_result.state, "status": "Pending..."}
    elif task_result.state == "FAILURE":
        response = {"state": task_result.state, "status": str(task_result.info)}
    elif task_result.state == "SUCCESS":
        response = {"state": task_result.state, "result": task_result.result}
    else:
        response = {"state": task_result.state, "status": str(task_result.info)}

    return jsonify(response)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
