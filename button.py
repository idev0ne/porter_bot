from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup


def confirm(button_name):
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(KeyboardButton(f"{button_name}"))
    return m


def main_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(KeyboardButton('Посмотреть запланированные посты'))
    m.add(KeyboardButton('Рассылка пользователям📝'))
    m.add(KeyboardButton('Настройки⚙️'))
    return m


def settings_menu():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(KeyboardButton('Обновить приветственный пост'))
    m.insert(KeyboardButton('Обновить текст кнопки'))
    m.add(KeyboardButton('Обновить текст после нажатия'))
    m.add(KeyboardButton('Назад'))
    return m


def mailing():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(KeyboardButton('Рассылка всем и сейчас'))
    m.insert(KeyboardButton('Запланированная рассылка'))
    m.add(KeyboardButton('Назад'))
    return m


def back():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(KeyboardButton("Назад"))
    return m


def channels_list(channel_list):
    keyboard = InlineKeyboardMarkup(row_width=2)
    for channel_id, name in channel_list:
        keyboard.insert(InlineKeyboardButton(text=name, callback_data=str(channel_id)))
    keyboard.add(InlineKeyboardButton(text="Выбрать все", callback_data="all"))
    keyboard.add(InlineKeyboardButton(text="Назад", callback_data="back"))
    return keyboard


def confirmation():
    m = ReplyKeyboardMarkup(resize_keyboard=True)
    m.add(KeyboardButton("Запланировать✅"))
    m.insert(KeyboardButton("Главное Меню 🏠"))
    return m
