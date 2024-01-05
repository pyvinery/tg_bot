import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters import Text
from aiogram import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from my_token import TOKEN


import aiosqlite

DB_PATH = 'db/bot.db'
DB_SETUP_QUERY = """
CREATE TABLE IF NOT EXISTS user_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    query TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

async def setup_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(DB_SETUP_QUERY)
        await db.commit()



def is_video_file(file_name):
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv')
    return file_name.lower().endswith(video_extensions)

def find_videos_by_name(folder_path, query):
    videos_list = []
    for file_name in os.listdir(folder_path):
        if query.lower() in file_name.lower() and is_video_file(file_name):
            videos_list.append(file_name)
    return videos_list

def get_start_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('/start'))
    keyboard.add(KeyboardButton('/help'))
    return keyboard

CHANNEL_ID = '@gggggjjkkuytr'  # Используйте ID или username вашего канала

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


# Проверка статуса подписки пользователя
from aiogram.utils.exceptions import ChatNotFound

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


@dp.message_handler(commands=['start', 'help'])
async def commands_handler(message: types.Message):
    user_subscribed = await is_user_subscribed(message.from_user.id)
    if not user_subscribed:
        await send_subscribe_message(message.from_user.id)
        return

    if message.text.startswith('/start'):
        await message.answer("Привет! Просто напиши мне что-нибудь и я найду для тебя видео.",
                             reply_markup=get_start_keyboard())
    elif message.text.startswith('/help'):
        await help_command(message)


@dp.message_handler(regexp='(?i).*')  # Используем регулярное выражение, чтобы обработать любой текст
async def handle_text(message: types.Message):
    user_subscribed = await is_user_subscribed(message.from_user.id)
    if not user_subscribed:
        await send_subscribe_message(message.from_user.id)
        return

    search_query = message.text.strip()
    if search_query:
        await search_videos(message, search_query)

    @dp.message_handler(commands=['start', 'help'])
    async def commands_handler(message: types.Message):
        user_subscribed = await is_user_subscribed(message.from_user.id)
        if not user_subscribed:
            await send_subscribe_message(message.from_user.id)
            return
        keyboard = get_start_keyboard()
    if message.text.startswith('/start'):
        await message.answer("Привет! Я могу отправлять тебе видео по запросу")
    elif message.text.startswith('/search'):
        await search_command(message)







def is_video_file(file_name):
    video_extensions = ('.mp4', '.avi', '.mov', '.mkv')  # Добавьте нужные расширения файлов
    return file_name.lower().endswith(video_extensions)

def find_videos_by_name(folder_path, query):
    videos_list = []
    for file_name in os.listdir(folder_path):
        if query.lower() in file_name.lower() and is_video_file(file_name):
            videos_list.append(file_name)
    return videos_list


async def search_videos(message: types.Message, search_query: str):
    folder_path = 'D:\\общее\\проект тг фильмы'  # Убедитесь, что путь указан верно
    videos = find_videos_by_name(folder_path, search_query)

    if videos:
        # Создаем клавиатуру с кнопками для каждого видео без расширения файла
        keyboard = InlineKeyboardMarkup(row_width=1)  # row_width=1 для вертикального списка кнопок
        for video_file in videos:
            video_name, _ = os.path.splitext(video_file)  # Название видео без расширения
            callback_data = f'video_{video_file}'  # Callback data с полным названием файла
            keyboard.add(InlineKeyboardButton(text=video_name, callback_data=callback_data))  # Текст кнопки без расширения
        await message.answer("Выберите видео:", reply_markup=keyboard)
    else:
        await message.reply("Видео по запросу не найдены.")




@dp.callback_query_handler(lambda c: c.data and c.data.startswith('video_'))
async def send_video_callback_query(callback_query: types.CallbackQuery):
    # Получаем название видео из callback_data
    video_name_with_extension = callback_query.data[len('video_'):]

    # Теперь получим название видео без расширения
    video_name, _ = os.path.splitext(video_name_with_extension)

    folder_path = 'D:\\общее\\проект тг фильмы' # Убедитесь, что путь указан верно
    video_path = os.path.join(folder_path, video_name_with_extension)  # используйте оригинальное название с расширением для получения пути к файлу

    # Проверяем, существует ли файл, и отправляем его
    if os.path.exists(video_path) and os.path.isfile(video_path):
        with open(video_path, 'rb') as video:
            await bot.send_video(callback_query.from_user.id, video, caption=f"Видео: {video_name}")  # используйте название без расширения для заголовка
    else:
        await bot.answer_callback_query(callback_query.id, text="Ошибка: видео не найдено.")

    # Удаляем клавиатуру после выбора видео
    await bot.edit_message_reply_markup(callback_query.from_user.id, callback_query.message.message_id)



async def set_commands(bot: Bot):
    commands = [
        types.BotCommand(command="/start", description="Начать работу с ботом"),
        types.BotCommand(command="/search", description="Искать видео"),
        types.BotCommand(command="/help", description="Помощь")
    ]
    await bot.set_my_commands(commands)


@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    help_text = (
        "Вот что я могу делать:\n"
        "/start - начать работу с ботом\n"
        "/search <запрос> - поиск и отправка видео по запросу\n"
        "/help - информация о командах и как мной пользоваться\n"
    )
    await message.answer(help_text)








# Запускаем бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)



