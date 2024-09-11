import spleeter
from pydub import AudioSegment, effects
import whisper
import torch
import subprocess
import ffmpeg
import os
import shutil


device = "cuda" if torch.cuda.is_available() else "cpu"

models = {}

def load_all_models():
    global models
    models["small"] = whisper.load_model("small", device=device)
    models['base'] = whisper.load_model("base", device=device)
load_all_models()


def get_model_by_choice(model_choice):
    return models.get(model_choice, models["small"])


def delete_everything_in_folder(folder_path):
    shutil.rmtree(folder_path)
    os.mkdir(folder_path)

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


def subtitles(vocals_path, audio_name, whisper_model):
    result = whisper_model.transcribe(vocals_path)

    with open(f"fix_audio/{audio_name}_normalized/subtitles.srt", "w") as f:
        for i, segment in enumerate(result["segments"]):
            start_time = segment["start"]
            end_time = segment["end"]
            text = segment["text"]

            start_formatted = str(int(start_time // 3600)).zfill(2) + ":" + \
                              str(int((start_time % 3600) // 60)).zfill(2) + ":" + \
                              str(int(start_time % 60)).zfill(2) + "," + \
                              str(int((start_time * 1000) % 1000)).zfill(3)

            end_formatted = str(int(end_time // 3600)).zfill(2) + ":" + \
                            str(int((end_time % 3600) // 60)).zfill(2) + ":" + \
                            str(int(end_time % 60)).zfill(2) + "," + \
                            str(int((end_time * 1000) % 1000)).zfill(3)

            f.write(f"{i+1}\n{start_formatted} --> {end_formatted}\n{text.strip()}\n\n")


def ffmpeg_command_video(background_path, audio_path, subtitles_path, output_path):
    return [
        "ffmpeg",
        "-y",
        "-i", background_path,
        "-i", audio_path,
        "-vf",
        f"fade=t=in:st=0:d=1,fade=t=out:st=29:d=1,subtitles={subtitles_path}:force_style='FontSize=12,PrimaryColour=&HFFFFFF&'",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        output_path
    ]


def ffmpeg_command_audio(background_path, audio_path, subtitles_path, output_path):
    return [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-i", background_path,
        "-i", audio_path,
        "-vf",
        f"fade=t=in:st=0:d=1,fade=t=out:st=29:d=1,subtitles={subtitles_path}:force_style='FontSize=24,PrimaryColour=&HFFFFFF&'",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path
    ]


def rndr_video_audio(av_name, background_path):
    audio_path_minus = f"fix_audio/{av_name}_normalized/accompaniment.wav"
    audio_path_plus = f"fix_audio/{av_name}_normalized.wav"
    subtitles_path = f"fix_audio/{av_name}_normalized/subtitles.srt"
    output_path_minus = f"fix_audio/{av_name}_normalized/{av_name}_minus_output.mp4"
    output_path_plus = f"fix_audio/{av_name}_normalized/{av_name}_plus_output.mp4"
    command_minus = ffmpeg_command_audio(background_path, audio_path_minus, subtitles_path, output_path_minus)
    command_plus = ffmpeg_command_audio(background_path, audio_path_plus, subtitles_path, output_path_plus)
    try:
        subprocess.run(command_minus, check=True)
        subprocess.run(command_plus, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении команды: {e}")


def rndr_video_video(av_name, background_path):
    audio_path_minus = f"fix_audio/{av_name}_normalized/accompaniment.wav"
    audio_path_plus = f"fix_audio/{av_name}_normalized.wav"
    subtitles_path = f"fix_audio/{av_name}_normalized/subtitles.srt"
    output_path_minus = f"fix_audio/{av_name}_normalized/{av_name}_minus_output.mp4"
    output_path_plus = f"fix_audio/{av_name}_normalized/{av_name}_plus_output.mp4"
    command_minus = ffmpeg_command_video(background_path, audio_path_minus, subtitles_path, output_path_minus)
    command_plus = ffmpeg_command_video(background_path, audio_path_plus, subtitles_path, output_path_plus)

    try:
        subprocess.run(command_minus, check=True)
        subprocess.run(command_plus, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении команды: {e}")


def output_video(av_name, audio_format, background_path, model_choice="small", flag=True):
    normalized_audio_name = f"fix_audio/{av_name}_normalized.wav"

    whisper_model = get_model_by_choice(model_choice)

    normalized_audio(av_name, audio_format)

    audio_split(normalized_audio_name, "fix_audio")

    subtitles(f"fix_audio/{av_name}_normalized/vocals.wav", audio_name=av_name, whisper_model=whisper_model)

    if flag:
        rndr_video_audio(av_name, background_path)
    else:
        rndr_video_video(av_name, background_path)
