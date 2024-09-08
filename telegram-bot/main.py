import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ContentType, InputFile
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router, F
from config import TOKEN
from func_file import output_video
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

fix_dir = "fix_audio"
os.makedirs(fix_dir, exist_ok=True)

@router.message(F.text == "/start")
async def send_welcome(message: types.Message):
    await message.answer("Здравствуйте! Пришлите аудио и получите видео с субтитрами.")

@router.message(F.content_type == ContentType.AUDIO)
@router.message(F.content_type == ContentType.VOICE)
async def handle_audio(message: types.Message):
    audio_file = message.audio if message.audio else message.voice
    file_name = f"{audio_file.file_id}.ogg"
    file_path = os.path.join(fix_dir, file_name)

    await bot.download(audio_file.file_id, destination=file_path)

    audio_name = os.path.splitext(file_name)[0]
    audio_format = "ogg"

    output_video(audio_name, audio_format)

    video_path = f"fix_audio/{audio_name}_normalized/{audio_name}_output.mp4"

    if os.path.exists(video_path):
        await message.answer_video(video=InputFile(video_path), caption="Вот ваше видео!")
    else:
        await message.answer("Произошла ошибка при создании видео.")

    if os.path.exists(file_path):
        os.remove(file_path)
    if os.path.exists(video_path):
        os.remove(video_path)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
