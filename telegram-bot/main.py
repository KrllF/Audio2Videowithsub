import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ContentType, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router, F
from config import TOKEN, background_path_video, background_path_audio
from func_file import output_video, delete_files_in_folder
import subprocess


logging.basicConfig(level=logging.INFO)

all_media_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fix_audio')

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

fix_dir = "fix_audio"
os.makedirs(fix_dir, exist_ok=True)


@router.message(F.text == "/start")
async def send_welcome(message: types.Message):
    await message.answer("Здравствуйте! Пришлите аудио и получите видео с субтитрами.")


@router.message(F.text == "/help")
async def send_help(message: types.Message):
    await message.answer(
        "Это учебный телеграм-бот, который предлагает пользователям инновационный способ работы с аудио и видео. "
        "Бот позволяет загружать видеозаписи или аудиофайлы, после чего выполняет ряд автоматизированных шагов для обработки контента."
        "\n1. Загрузка медиафайлов: Пользователи могут просто отправить ботe свои аудио или видеофайлы, и он автоматически сохранит их для дальнейшей обработки."
        "\n2. Сепарация вокала и инструментала: С помощью инструмента Spleeter бот отделяет вокал от фоновой музыки и других инструментов, создавая отдельные аудио дорожки."
        "\n3. Преобразование голоса в текст: Далее, используя систему Whisper, бот преобразует отделённый вокал в текст, эффективно создавая транскрипцию речи."
        "\n4. Создание видео с субтитрами: После этого бот объединяет инструментальную дорожку и текстовые субтитры с помощью FFmpeg, создавая новое видео, в котором будут отображаться готовые субтитры."
        "\nВ результате пользователи получают улучшенное видео с чёткими субтитрами, что делает контент более доступным и удобным для восприятия."
    )


@router.message(F.content_type == ContentType.AUDIO)
@router.message(F.content_type == ContentType.VOICE)
async def handle_audio(message: types.Message):
    delete_files_in_folder("fix_audio")

    try:
        if message.audio:
            audio_file = message.audio
            audio_format = audio_file.mime_type.split('/')[-1]
            file_id = audio_file.file_id
        else:
            audio_file = message.voice
            audio_format = "ogg"
            file_id = audio_file.file_id

        file = await bot.get_file(file_id)
        file_name = f"audio_file.{audio_format}"
        file_path = os.path.join(file_name)
        await bot.download_file(file.file_path, file_path)
        output_video("audio_file", audio_format, background_path_audio)


        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Видео с голосом", callback_data="with_voice"),
                InlineKeyboardButton(text="Видео без голоса", callback_data="without_voice")
            ]
        ])

        await message.reply("Выберите, что вы хотите получить:", reply_markup=keyboard)

    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")


@router.callback_query(F.data == "with_voice")
async def handle_with_voice(callback_query: types.CallbackQuery):
    try:
        await callback_query.answer("Создаю видео с вокалом...")

        video_file_path = os.path.join(all_media_dir, 'audio_file_normalized', "audio_file_plus_output.mp4")
        video_input_file = FSInputFile(video_file_path)
        await bot.send_video(chat_id=callback_query.message.chat.id, video=video_input_file)
    except Exception as e:
        await callback_query.message.reply(f"Произошла ошибка: {e}")


@router.callback_query(F.data == "without_voice")
async def handle_without_voice(callback_query: types.CallbackQuery):
    try:
        await callback_query.answer("Создаю видео без вокала...")
        video_file_path = os.path.join(all_media_dir, 'audio_file_normalized', "audio_file_minus_output.mp4")
        video_input_file = FSInputFile(video_file_path)
        await bot.send_video(chat_id=callback_query.message.chat.id, video=video_input_file)
    except Exception as e:
        await callback_query.message.reply(f"Произошла ошибка: {e}")

@router.message(F.content_type == ContentType.VIDEO)
@router.message(F.content_type == ContentType.VIDEO_NOTE)
async def handle_video(message: types.Message):
    delete_files_in_folder("fix_audio")

    try:
        if message.video:
            video_file = message.video
            video_format = video_file.mime_type.split('/')[-1]
            file_id = video_file.file_id
        else:
            video_file = message.video_note
            video_format = "mp4"
            file_id = video_file.file_id

        file = await bot.get_file(file_id)
        file_name = f"video_file.{video_format}"
        file_path = os.path.join(file_name)
        await bot.download_file(file.file_path, file_path)

        output_video("video_file", video_format, "video_file.mp4")

        await message.answer("Создаю видео с субтитрами...")

        video_file_path = os.path.join(all_media_dir, 'video_file_normalized', "video_file_plus_output.mp4")
        video_input_file = FSInputFile(video_file_path)
        await bot.send_video(chat_id=message.chat.id, video=video_input_file)

    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")



async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
