from flask import Flask, request, jsonify
import subprocess
import uuid
import os

app = Flask(__name__)

@app.route("/process", methods=["POST"])
def process_video():
    data = request.get_json()

    video_url = data["video_url"]
    audio_url = data["audio_url"]
    duration = int(data["duration"])  # in seconds

    output_id = str(uuid.uuid4())

    input_video = f"{output_id}_video.mp4"
    input_audio = f"{output_id}_audio.mp3"
    final_output = f"{output_id}_final.mp4"

    # Download video and audio
    subprocess.run(["curl", "-L", video_url, "-o", input_video], check=True)
    subprocess.run(["curl", "-L", audio_url, "-o", input_audio], check=True)

    # Trim video to duration + 2s (as buffer to avoid audio cutoff)
    trimmed_video = f"{output_id}_trimmed.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", input_video,
        "-t", str(duration + 2),
        "-c", "copy",
        trimmed_video
    ], check=True)

    # Combine trimmed video with audio
    subprocess.run([
        "ffmpeg", "-y",
        "-i", trimmed_video,
        "-i", input_audio,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy",
        "-shortest", final_output
    ], check=True)

    # Upload to file.io and return the link
    result = subprocess.run(
        ["curl", "-F", f"file=@{final_output}", "https://file.io"],
        capture_output=True, text=True
    )

    # Cleanup
    for f in [input_video, input_audio, trimmed_video, final_output]:
        if os.path.exists(f):
            os.remove(f)

    return jsonify(result=result.stdout)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
