import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ContentType,  FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router, F
from config import TOKEN
from func_file import output_video, delete_files_in_folder

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
    await message.answer("Это учебный телеграм-бот, который предлагает пользователям инновационный способ работы с аудио и видео. Бот позволяет загружать видеозаписи или аудиофайлы, после чего выполняет ряд автоматизированных шагов для обработки контента."
        "\n1. Загрузка медиафайлов: Пользователи могут просто отправить ботe свои аудио или видеофайлы, и он автоматически сохранит их для дальнейшей обработки."
        "\n2. Сепарация вокала и инструментала: С помощью инструмента Spleeter бот отделяет вокал от фоновой музыки и других инструментов, создавая отдельные аудио дорожки."
        "\n3. Преобразование голоса в текст: Далее, используя систему Whisper, бот преобразует отделённый вокал в текст, эффективно создавая транскрипцию речи."
        "\n4. Создание видео с субтитрами: После этого бот объединяет инструментальную дорожку и текстовые субтитры с помощью FFmpeg, создавая новое видео, в котором будут отображаться готовые субтитры."
        "\nВ результате пользователи получают улучшенное видео с чёткими субтитрами, что делает контент более доступным и удобным для восприятия.")

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

        # Загружаем файл аудио с Telegram
        file = await bot.get_file(file_id)
        file_name = f"audio_file.{audio_format}"
        file_path = os.path.join(file_name)

        await bot.download_file(file.file_path, file_path)
        # Создаем инлайн-клавиатуру для выбора
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Видео с голосом", callback_data="with_voice"),
                InlineKeyboardButton(text="Видео без голоса", callback_data="without_voice")
            ]
        ])

        output_video("audio_file", audio_format)

        await message.reply("Видео готово. Отправляю...")
        video_file_path = os.path.join(all_media_dir, 'audio_file_normalized', "audio_file_output.mp4")
        video_input_file = FSInputFile(video_file_path)
        await bot.send_video(chat_id=message.chat.id, video=video_input_file)

    except Exception as e:
        await message.reply(f"Произошла ошибка: {e}")

async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
