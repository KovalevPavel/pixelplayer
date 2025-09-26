    
import json
import mimetypes
import os
import subprocess


def get_audio_params(input_path: str):
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json", "-show_format", "-show_streams",
        input_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    info = json.loads(result.stdout)
    stream = info["streams"][0]
    tags = info.get("format").get("tags")
    mime_type, _ = mimetypes.guess_type(input_path)

    return {
        "bit_rate": int(stream.get("bit_rate", 128000)),
        "sample_rate": int(stream.get("sample_rate", 44100)),
        "channels": int(stream.get("channels", 2)),
        "tags": {
            "artist": tags.get("artist"),
            "album": tags.get("album"),
            "mime": mime_type,
            "track_title": tags.get("title"),
            "track_number": tags.get("track"),
            "genre": tags.get("genre"),
        }
    }

def convert_audio(file_id: str, file_path: str, output_path: str):
    params = get_audio_params(input_path=file_path)
    out_dir = f"{output_path}/{file_id}"

    os.makedirs(out_dir, exist_ok=True)

    command = [
        'ffmpeg',
        '-i', file_path, # путь до обрабатываемого файла
        '-vn',
        '-ar', f"{params['sample_rate']}",
        '-ac', f"{params['channels']}",
        '-hls_time', '10', # размер чанка
        '-b:a', f"{params['bit_rate']}",
        "-hls_segment_filename", os.path.join(out_dir, "segment_%03d.ts"), # правило именования файла с чанком
        os.path.join(out_dir, "playlist.m3u8"), # имя манифеста
    ]
    subprocess.run(command, check=True)