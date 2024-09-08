import spleeter
from pydub import AudioSegment, effects
import whisper
import torch
import subprocess
import ffmpeg
import os

device = "cuda" if torch.cuda.is_available() else "cpu"

model_whisper_base = whisper.load_model("base", device=device)
model_whisper_medium = whisper.load_model("medium", device=device)

# audio_name
# audio_format
def normalized_audio(audio_name, audio_format):
    audio = AudioSegment.from_file(audio_name + '.' + audio_format)
    normalized_audio = effects.normalize(audio)
    normalized_audio.export(f"fix_audio/{audio_name}_normalized.wav", format="wav")

def audio_split(input_file, output_folder):
    command = [
        "spleeter", "separate",  # Command for Spleeter to separate
        "-p", "spleeter:2stems",  # Model parameters: 2 parts (vocal and instrumental)
        "-o", output_folder,      # Path to save output files
        input_file                # Path to input audio file (specified without the -i flag)
    ]

    # Run the command
    subprocess.run(command)

def subtitles(vocals_path, audio_name):

    result = model_whisper_medium.transcribe(vocals_path)

    with open(f"fix_audio/{audio_name}_normalized/subtitles.srt", "w") as f:
        for i, segment in enumerate(result["segments"]):
            start_time = segment["start"]
            end_time = segment["end"]
            text = segment["text"]

            # Форматируем время в нужный формат для .srt
            start_formatted = str(int(start_time // 3600)).zfill(2) + ":" + \
                              str(int((start_time % 3600) // 60)).zfill(2) + ":" + \
                              str(int(start_time % 60)).zfill(2) + "," + \
                              str(int((start_time * 1000) % 1000)).zfill(3)

            end_formatted = str(int(end_time // 3600)).zfill(2) + ":" + \
                            str(int((end_time % 3600) // 60)).zfill(2) + ":" + \
                            str(int(end_time % 60)).zfill(2) + "," + \
                            str(int((end_time * 1000) % 1000)).zfill(3)

            f.write(f"{i+1}\n{start_formatted} --> {end_formatted}\n{text.strip()}\n\n")

def rndr_video(audio_name):
    background_path = "total_black_background.jpg"
    audio_path = f"fix_audio/{audio_name}_normalized/accompaniment.wav"
    subtitles_path = f"fix_audio/{audio_name}_normalized/subtitles.srt"
    output_path = f"fix_audio/{audio_name}_normalized/{audio_name}_output.mp4"

    # Команда FFmpeg
    command = [
        "ffmpeg",
        "-loop", "1",
        "-i", background_path,
        "-i", audio_path,
        "-vf", f"subtitles={subtitles_path}",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path
    ]

    # Запуск команды
    try:
        subprocess.run(command, check=True)
        print("Видео успешно создано.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении команды: {e}")

def output_video(audio_name, audio_format):
    normalized_audio_name = f"fix_audio/{audio_name}_normalized.wav"

    normalized_audio(audio_name, audio_format)

    audio_split(normalized_audio_name, "fix_audio")

    if os.path.exists(normalized_audio_name):
        os.remove(normalized_audio_name)
        print(f"Deleted file: {normalized_audio_name}")
    else:
        print(f"File not found: {normalized_audio_name}")

    subtitles(f"fix_audio/{audio_name}_normalized/vocals.wav", audio_name=audio_name)
    rndr_video(audio_name)


