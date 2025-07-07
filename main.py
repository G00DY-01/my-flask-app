from flask import Flask, request, jsonify
from worker import create_celery_app
import os
import uuid

app = Flask(__name__)
celery = create_celery_app(app)

@app.route("/", methods=["GET"])
def index():
    return "processing"

@app.route("/process", methods=["POST"])
def process():
    data = request.json
    task_id = str(uuid.uuid4())

    celery.send_task(
        "worker.process_video",
        args=[
            data["video_url"],
            data["audio_url"],
            data["caption_data"],
            data["duration"],
            task_id,
        ],
    )

    return jsonify({"status": "processing", "task_id": task_id})
