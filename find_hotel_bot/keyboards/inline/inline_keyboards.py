from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def num_hotel():
    keyboard = InlineKeyboardMarkup()
    for i in range(1, 11):
        keyboard.add(InlineKeyboardButton(text=f'{i}', callback_data=f'num_hotel: {i}'))
    return keyboard


def num_photo_hotel():
    keyboard = InlineKeyboardMarkup()
    for i in range(6):
        keyboard.add(InlineKeyboardButton(text=f'{i}', callback_data=f'photo_hotel {i}'))
    return keyboard
