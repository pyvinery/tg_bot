import os
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters import Text
from aiogram import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from my_token import TOKEN
from aiogram.utils.exceptions import ChatNotFound



CHANNEL_ID = '@gggggjjkkuytr'  # ID  канала

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())



# Проверка подписки
async def is_user_subscribed(user_id):
    try:
        member_status = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member_status.is_chat_member() or member_status.status in ['administrator', 'creator', 'member']
    except ChatNotFound:
        return False

async def send_subscribe_message(user_id):
    keyboard = InlineKeyboardMarkup()
    subscribe_button = InlineKeyboardButton(text="Подписаться на канал", url=f"https://t.me/{CHANNEL_ID.lstrip('@')}")
    keyboard.add(subscribe_button)
    await bot.send_message(user_id, "Пожалуйста, подпишитесь на наш канал чтобы использовать этого бота.", reply_markup=keyboard)



# команды
@dp.message_handler(commands=['start', 'help'])
async def commands_handler(message: types.Message):
    user_subscribed = await is_user_subscribed(message.from_user.id)
    if not user_subscribed:
        await send_subscribe_message(message.from_user.id)
        return

    if message.text.startswith('/start'):
        await message.answer("Привет! Просто напиши мне что-нибудь и я найду для тебя видео.")
    elif message.text.startswith('/help'):
        await help_command(message)


@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    help_text = (
        "Вот что я могу делать:\n"
        "/start - начать работу с ботом\n"
        "\n"
        "/help - информация о командах\n"
    )
    await message.answer(help_text)


@dp.message_handler(regexp='(?i).*')
async def handle_text(message: types.Message):
    user_subscribed = await is_user_subscribed(message.from_user.id)
    if not user_subscribed:
        await send_subscribe_message(message.from_user.id)
        return

    search_query = message.text.strip()
    if search_query:
        await search_videos(message, search_query)


# видео
def is_video_file(file_name):
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv')
    return file_name.lower().endswith(video_extensions)

def find_videos_by_name(folder_path, query):
    videos_list = []
    for file_name in os.listdir(folder_path):
        if query.lower() in file_name.lower() and is_video_file(file_name):
            videos_list.append(file_name)
    return videos_list


async def search_videos(message: types.Message, search_query: str):
    folder_path = 'D:\\общее\\проект тг фильмы'
    videos = find_videos_by_name(folder_path, search_query)

    if videos:
        #  клавиатура с кнопками
        keyboard = InlineKeyboardMarkup(row_width=1)
        for video_file in videos:
            video_name, _ = os.path.splitext(video_file)  # название видео
            callback_data = f'video_{video_file}'
            keyboard.add(InlineKeyboardButton(text=video_name, callback_data=callback_data))  # текст кнопки
        await message.answer("Выберите видео:", reply_markup=keyboard)
    else:
        await message.reply("Видео по запросу не найдены.")


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('video_'))
async def send_video_callback_query(callback_query: types.CallbackQuery):
    video_name_with_extension = callback_query.data[len('video_'):]
    video_name, _ = os.path.splitext(video_name_with_extension)
    folder_path = 'D:\\общее\\проект тг фильмы'
    video_path = os.path.join(folder_path, video_name_with_extension)
    if os.path.exists(video_path) and os.path.isfile(video_path):
        with open(video_path, 'rb') as video:
            await bot.send_video(callback_query.from_user.id, video, caption=f"Видео: {video_name}")
    else:
        await bot.answer_callback_query(callback_query.id, text="Ошибка: видео не найдено.")
    # удаляем клавиатуру после выбора видео
    await bot.edit_message_reply_markup(callback_query.from_user.id, callback_query.message.message_id)



# запускаем бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)



