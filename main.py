import asyncio
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



# видео
# Глобальный список или структура данных для хранения file_id видео
video_file_ids = {}

@dp.channel_post_handler(content_types=['video'])
async def handle_channel_video(message: types.Message):
    video_file_id = message.video.file_id
    video_title = message.caption or 'Без названия'
    await save_video_file_id(video_title, video_file_id)


async def search_videos_by_title(query):
    # Поиск похожих видео по запросу (предполагается, что названия видео уникальны)
    results = {title: file_id for title, file_id in video_file_ids.items() if query.lower() in title.lower()}
    return results


# Video selection based on a search query
video_refs = {}


@dp.message_handler(regexp='(?i).*')
async def handle_text(message: types.Message):
    search_query = message.text.strip().lower()
    # Сохраняем запрос пользователя
    await save_user_query(user_id=message.from_user.id, query=search_query)
    search_query = message.text.strip().lower()
    search_results = await search_videos_by_title(search_query)

    if search_results:
        if len(search_results) == 1:
            # If there is only one result, send it immediately.
            _, file_id = search_results[0]
            await bot.send_video(message.from_user.id, file_id)
        else:
            # If there are multiple results, send a selection keyboard.
            keyboard = InlineKeyboardMarkup()
            for title, file_id in search_results:
                # Create a unique reference ID for the file_id
                ref_id = str(len(video_refs) + 1)
                video_refs[ref_id] = file_id  # Map ref_id to file_id
                # Ensure the callback data does not exceed 64 bytes.
                callback_data = f"video_{ref_id}" if len(f"video_{ref_id}") <= 64 else f"video_{ref_id[:60]}"
                keyboard.add(InlineKeyboardButton(text=title, callback_data=callback_data))
            await bot.send_message(message.from_user.id, "Выберите видео:", reply_markup=keyboard)
    else:
        await message.reply("Видео по запросу не найдены.")


@dp.callback_query_handler(lambda c: c.data.startswith('video_'))
async def handle_video_choice(callback_query: types.CallbackQuery):
    ref_id = callback_query.data.split('_')[1]
    file_id = video_refs.get(ref_id)
    if file_id:
        await bot.send_video(callback_query.from_user.id, file_id)
    else:
        await callback_query.answer("Ошибка: видео не найдено!")

    await callback_query.answer()


# A stub function for shortening your file_id or retrieving it based on a short ID
def create_short_id_for(file_id):
    # This should create a shorter version of the file_id or hash it and return
    # Hashing is one approach but it requires a way to resolve hash back to file_id
    # TODO: Implement this function
    pass


def lookup_file_id_from_short_id(short_id):
    # This should take the short ID and return the corresponding file_id
    # TODO: Implement this function
    pass


#база данных видео

async def init_db(db_name="bot.db"):
    async with aiosqlite.connect(db_name) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS videos (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            file_id TEXT NOT NULL)""")
        await db.commit()
#база данных запросов
async def init_db(db_name="bot.db"):
    async with aiosqlite.connect(db_name) as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS videos (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT NOT NULL,
                            file_id TEXT NOT NULL)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS user_queries (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            query TEXT NOT NULL,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
        await db.commit()

async def save_user_query(user_id, query):
    async with aiosqlite.connect('bot.db') as db:
        await db.execute("INSERT INTO user_queries (user_id, query) VALUES (?, ?)", (user_id, query))
        await db.commit()


# Сохранение file_id видео
async def save_video_file_id(title, file_id):
    async with aiosqlite.connect('bot.db') as db:
        await db.execute("INSERT INTO videos (title, file_id) VALUES (?, ?)", (title, file_id))
        await db.commit()

# Поиск видео по запросу
async def search_videos_by_title(query):
    async with aiosqlite.connect('bot.db') as db:
        cursor = await db.execute("SELECT title, file_id FROM videos WHERE title LIKE ?", (f"%{query}%",))
        return await cursor.fetchall()





# запускаем бота
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())  # Инициализация базы данных перед запуском бота
    executor.start_polling(dp, skip_updates=True)


