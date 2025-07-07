import os
import uuid
import json
import requests
import subprocess
from flask import Flask, request, send_file

app = Flask(__name__)

# Caption styling (edit as needed)
CAPTION_STYLE = {
    "fontfile": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "fontsize": 48,
    "fontcolor": "white",
    "borderw": 2,
    "box": 1,
    "boxcolor": "black@0.5",
    "shadowcolor": "black",
    "shadowx": 2,
    "shadowy": 2
}

def generate_caption_file(word_durations, output_path):
    """
    Create an SRT file with word-level timings
    """
    def ms_to_srt_time(ms):
        seconds, milliseconds = divmod(ms, 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

    with open(output_path, "w", encoding="utf-8") as f:
        for i, word in enumerate(word_durations):
            start = ms_to_srt_time(int(word["startMs"]))
            end = ms_to_srt_time(int(word["endMs"]))
            f.write(f"{i+1}\n{start} --> {end}\n{word['word']}\n\n")

def generate_captioned_video(input_video, subtitles_path, captioned_output):
    """
    Overlay subtitles (SRT) on video using FFmpeg
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-vf", f"subtitles={subtitles_path}:force_style='FontName=DejaVuSans-Bold,FontSize={CAPTION_STYLE['fontsize']},PrimaryColour=&HFFFFFF&,BorderStyle=1,Outline=1,Shadow=1'",
        "-c:a", "copy",
        captioned_output
    ]
    subprocess.run(cmd, check=True)

def merge_audio_with_video(video_path, audio_path, final_output_path):
    """
    Combine captioned video with TTS audio (replace original audio)
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        final_output_path
    ]
    subprocess.run(cmd, check=True)

@app.route('/process', methods=['POST'])
def process():
    try:
        data = request.get_json()

        input_path = data.get('input_path')  # Trimmed video path
        audio_path = data.get('audio_path')  # Murf audio path
        word_durations = data.get('word_durations')  # Caption word timings

        if not input_path or not audio_path or not word_durations:
            return {"error": "Missing one of: input_path, audio_path, word_durations"}, 400

        if not os.path.exists(input_path) or not os.path.exists(audio_path):
            return {"error": "Input or audio file does not exist"}, 404

        base = os.path.splitext(os.path.basename(input_path))[0]
        srt_path = f"files/{base}_captions.srt"
        captioned_video_path = f"files/{base}_captioned.mp4"
        final_output_path = f"files/{base}_final.mp4"

        # Step 1: Generate subtitle file
        generate_caption_file(word_durations, srt_path)

        # Step 2: Overlay subtitles on video
        generate_captioned_video(input_path, srt_path, captioned_video_path)

        # Step 3: Combine audio with captioned video
        merge_audio_with_video(captioned_video_path, audio_path, final_output_path)

        return send_file(final_output_path, as_attachment=True)

    except subprocess.CalledProcessError as e:
        return {"error": f"FFmpeg error: {e}"}, 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Unexpected error: {str(e)}"}, 500

if __name__ == '__main__':
    app.run(debug=True)
