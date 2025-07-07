import os
import uuid
from flask import Flask, request, jsonify
from celery import Celery

app = Flask(__name__)

app.config['CELERY_BROKER_URL'] = 'redis://red-d1lq916mcj7s73ar5ejg:6379'
app.config['CELERY_RESULT_BACKEND'] = 'redis://red-d1lq916mcj7s73ar5ejg:6379'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

@app.route('/')
def index():
    return 'API is live.'

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    video_url = data['video_url']
    audio_url = data['audio_url']
    caption_data = data['caption_data']
    duration = data['audioLengthInSeconds']
    
    task = process_video_audio.apply_async(args=[video_url, audio_url, caption_data, duration])
    return jsonify({'task_id': task.id}), 202
