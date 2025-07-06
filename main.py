from flask import Flask, request, send_file, jsonify
import subprocess
import uuid
import os

app = Flask(__name__)

@app.route("/process", methods=["POST"])
def process_video():
    data = request.get_json()

    video_url = data["video_url"]
    audio_url = data["audio_url"]
    caption_text = data.get("caption_text", "")  # optional
    duration = int(data["duration"])  # seconds

    output_id = str(uuid.uuid4())

    input_video = f"{output_id}_video.mp4"
    input_audio = f"{output_id}_audio.mp3"
    caption_file = f"{output_id}.srt"
    final_output = f"{output_id}_final.mp4"

    # Download video and audio
    subprocess.run(["curl", "-L", video_url, "-o", input_video], check=True)
    subprocess.run(["curl", "-L", audio_url, "-o", input_audio], check=True)

    # Create a basic subtitle file (SRT)
    with open(caption_file, "w") as f:
        f.write(f"1\n00:00:00,000 --> 00:00:{duration:02},000\n{caption_text}\n")

    # Burn audio and subtitles into the video (waits for ffmpeg to finish)
    subprocess.run([
        "ffmpeg", "-y",
        "-i", input_video,
        "-i", input_audio,
        "-map", "0:v:0", "-map", "1:a:0",
        "-vf", f"subtitles={caption_file}",
        "-shortest", final_output
    ], check=True)

    # Return the final video file as a downloadable attachment
    response = send_file(final_output, mimetype='video/mp4', as_attachment=True, download_name=final_output)

    # Cleanup after sending
    for f in [input_video, input_audio, caption_file, final_output]:
        if os.path.exists(f):
            os.remove(f)

    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
