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
            end = ms_to_timestamp(int(w
