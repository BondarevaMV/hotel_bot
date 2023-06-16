import datetime
from loader import bot
from telebot.types import Message
from database import models
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from states.all_state import UserStateHistory


@bot.message_handler(commands=["history"])
def history(message: Message) -> None:

	"""Функция просмотра истории поиска.
		Отправляет соообщение с просьбой ввести дату,
		отправляет календарь,
		сохраняет id последнего сообщения,
		удаляет сообщение, введенное пользователем ранее

		:param
		message (Message): сообщение введённое пользователем
		"""
	bot.set_state(message.from_user.id, UserStateHistory.history, message.chat.id)
	calendar, step = DetailedTelegramCalendar(calendar_id=3, max_date=datetime.datetime.today().date()).build()
	msd = bot.send_message(message.from_user.id, f'За какой день хотите посмотреть историю?', reply_markup=calendar)
	bot.delete_message(message.chat.id, message.message_id)
	with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
		data['last_id'] = msd.message_id


@bot.callback_query_handler(func=DetailedTelegramCalendar().func(calendar_id=3))
def call(c) -> None:

	"""Функция, которая сохраняет дату,
	делает запрос к базе и отправлет ответ пользователю,
	удаляет сообщение, введенное пользователем ранее

		"""
	result, key, step = DetailedTelegramCalendar(calendar_id=3).process(c.data)
	if not result and key:
		bot.edit_message_text(f"Select {LSTEP[step]}", c.message.chat.id, c.message.message_id, reply_markup=key)

	elif result:
		with bot.retrieve_data(c.from_user.id, c.message.chat.id) as data:
			data['history_day'] = result
			bot.delete_message(c.message.chat.id, data['last_id'])
			bot.edit_message_text(f"You selected {result}", c.message.chat.id, c.message.message_id)
			bot.send_message(c.from_user.id, models.read_info_day(result))
	bot.delete_state(c.from_user.id, c.message.chat.id)
