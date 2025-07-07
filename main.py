# Get audio duration using ffprobe
result = subprocess.run([
    "ffprobe", "-i", input_audio,
    "-show_entries", "format=duration",
    "-v", "quiet",
    "-of", "csv=p=0"
], capture_output=True, text=True)

audio_duration = float(result.stdout.strip())
video_duration = round(audio_duration + 3, 2)  # Max 3 seconds extra

# Trim video to match audio duration (+ up to 3 seconds)
trimmed_video = f"{output_id}_trimmed_video.mp4"
subprocess.run([
    "ffmpeg", "-y",
    "-i", input_video,
    "-t", str(video_duration),
    "-c", "copy",
    trimmed_video
])

# Merge trimmed video + audio
subprocess.run([
    "ffmpeg", "-y",
    "-i", trimmed_video,
    "-i", input_audio,
    "-map", "0:v:0",
    "-map", "1:a:0",
    "-shortest",
    final_output
], check=True)
