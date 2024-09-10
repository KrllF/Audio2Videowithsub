import spleeter
from pydub import AudioSegment, effects
import whisper
import torch
import subprocess
import ffmpeg
import os

from config import background_path

device = "cuda" if torch.cuda.is_available() else "cpu"

model_whisper = whisper.load_model("small", device=device)

def delete_files_in_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f'Ошибка при удалении файла {file_path}. {e}')

# audio_name
# audio_format
def normalized_audio(audio_name, audio_format):
    audio = AudioSegment.from_file(audio_name + '.' + audio_format)
    normalized_audio = effects.normalize(audio)
    normalized_audio.export(f"fix_audio/{audio_name}_normalized.wav", format="wav")


def audio_split(input_file, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    command = [
        "spleeter", "separate",
        "-p", "spleeter:2stems",
        "-o", output_folder,
        input_file
    ]

    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True)
        print("Аудиофайл успешно разделен.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при разделении аудиофайла: {e}")
        print(f"Стандартный вывод: {e.stdout}")
        print(f"Стандартный поток ошибок: {e.stderr}")
    except Exception as e:
        print(f"Возникла ошибка: {e}")

def subtitles(vocals_path, audio_name):

    result = model_whisper.transcribe(vocals_path)

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

def ffmpeg_command(audio_name, background_path, audio_path, subtitles_path, output_path):
    return [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-i", background_path,
        "-i", audio_path,
        "-vf", f"fade=t=in:st=0:d=1,fade=t=out:st=29:d=1,subtitles={subtitles_path}:force_style='FontSize=24,PrimaryColour=&HFFFFFF&'",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path
    ]

def rndr_video(audio_name):
    audio_path_minus = f"fix_audio/{audio_name}_normalized/accompaniment.wav"
    audio_path_plus = f"fix_audio/{audio_name}_normalized.wav"
    subtitles_path = f"fix_audio/{audio_name}_normalized/subtitles.srt"
    output_path_minus = f"fix_audio/{audio_name}_normalized/{audio_name}_minus_output.mp4"
    output_path_plus = f"fix_audio/{audio_name}_normalized/{audio_name}_plus_output.mp4"
    command_minus = ffmpeg_command(audio_name, background_path, audio_path_minus, subtitles_path, output_path_minus)
    command_plus = ffmpeg_command(audio_name, background_path, audio_path_plus, subtitles_path, output_path_plus)

    try:
        subprocess.run(command_minus, check=True)
        subprocess.run(command_plus, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении команды: {e}")


def output_video(audio_name, audio_format):
    normalized_audio_name = f"fix_audio/{audio_name}_normalized.wav"

    normalized_audio(audio_name, audio_format)

    audio_split(normalized_audio_name, "fix_audio")


    subtitles(f"fix_audio/{audio_name}_normalized/vocals.wav", audio_name=audio_name)
    rndr_video(audio_name)

    if os.path.exists(normalized_audio_name):
        os.remove(normalized_audio_name)
        print(f"Deleted file: {normalized_audio_name}")
    else:
        print(f"File not found: {normalized_audio_name}")



