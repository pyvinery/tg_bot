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
