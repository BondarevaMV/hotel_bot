from telebot.types import Message
from states.all_state import UserStateLowrprice, UserStateBestdeal
from rapid_api import request_for_api
from keyboards.inline import inline_keyboards
from loader import bot
import datetime
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP


@bot.message_handler(commands=["lowprice", "highprice", "bestdeal"])
def start_search(message: Message) -> None:

	"""Функция начала поиска, устанавливает состояние UserStateLowrprice.city.
	Отправляет соообщение с просьбой ввести название города,
	сохраняет название, команду, id последнего сообщения и время запроса,
	удаляет сообщение, введенное пользователем ранее

	:param
	message (Message): сообщение введённое пользователем
	"""

	bot.set_state(message.from_user.id, UserStateLowrprice.city, message.chat.id)
	msd = bot.send_message(message.from_user.id, f'Введите название города, в котором будем искать')
	bot.delete_message(message.chat.id, message.message_id)

	with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
		data['command'] = message.text[1:]
		data['start_date'] = datetime.datetime.now()
		data['last_id'] = msd.message_id


@bot.message_handler(state=UserStateLowrprice.city)
def get_city(message: Message) -> None:

	"""Функция, которая:
		отправляет соообщение с просьбой ввести количество отелей для поиска,
		выдаёт клавиатуру,
		сохраняет название города и id последнего сообщения,
		удаляет сообщение, введенное пользователем ранее, а также предыдущее сообщение бота

		:param
		message (Message): сообщение введённое пользователем
		"""

	if message.text:
		msd = bot.send_message(message.from_user.id, f'Город {message.text} записан, сколько отелей найти? (не более 10)', reply_markup=inline_keyboards.num_hotel())
		with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
			bot.delete_message(message.chat.id, data['last_id'])
			data["city"] = message.text
			data['last_id'] = msd.message_id
		bot.delete_message(message.chat.id, message.message_id)
	else:
		bot.send_message(message.from_user.id, f'В названии города должны быть использованы только буквы')


@bot.callback_query_handler(func=lambda button: button.data.startswith('num_hotel'))
def call(c) -> None:

	"""Функция, которая:
		отправляет соообщение с просьбой выбора даты заезда,
		выдаёт календарь,
		сохраняет количество отелей для поиска и id последнего сообщения,
		удаляет сообщение, введенное пользователем ранее, а также предыдущее сообщение бота

		:param
		message (Message): сообщение введённое пользователем
		"""

	bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id)
	msd = bot.send_message(c.from_user.id, f'Будем искать {c.data} отелей. Когда вас ждать? ')
	with bot.retrieve_data(c.from_user.id, c.message.chat.id) as data:
		bot.delete_message(c.message.chat.id, data['last_id'])
		data["num_hotel"] = int(c.data[10:])
		data['last_id'] = msd.message_id

	calendar, step = DetailedTelegramCalendar(calendar_id=1, min_date=datetime.date.today()).build()
	bot.send_message(c.message.chat.id, f'Select {LSTEP[step]}', reply_markup=calendar)


@bot.callback_query_handler(func=DetailedTelegramCalendar().func(calendar_id=1))
def call(c) -> None:

	"""Функция, которая:
		выдаёт календарь,
		сохраняет выбранную дату и id двух последних сообщений,
		удаляет сообщение, введенное пользователем ранее, а также предыдущее сообщение бота

		:param
		message (Message): сообщение введённое пользователем
		"""

	result, key, step = DetailedTelegramCalendar(calendar_id=1).process(c.data)
	if not result and key:
		bot.edit_message_text(f"Select {LSTEP[step]}", c.message.chat.id, c.message.message_id, reply_markup=key)

	elif result:
		with bot.retrieve_data(c.from_user.id, c.message.chat.id) as data:
			data['check_in_date'] = result
			bot.delete_message(c.message.chat.id, data['last_id'])
			calendar, step = DetailedTelegramCalendar(calendar_id=2, min_date=result).build()
			msd1 = bot.edit_message_text(f"You selected {result}", c.message.chat.id, c.message.message_id)
			msd = bot.send_message(c.message.chat.id, f'Select {LSTEP[step]}', reply_markup=calendar)
			data['last_id'] = msd.message_id
			data['last_id1'] = msd1.message_id


@bot.callback_query_handler(func=DetailedTelegramCalendar().func(calendar_id=2))
def call(c) -> None:

	"""Функция, которая:
		в случает сценария "bestdeal" переходит UserStateBestdeal.min_price, а
		при других командах переходит к выбору количества фотографий
		сохраняет выбранную дату и id двух последних сообщений,
		удаляет сообщение, введенное пользователем ранее, а также предыдущее сообщение бота

		:param
		message (Message): сообщение введённое пользователем
		"""

	result, key, step = DetailedTelegramCalendar(calendar_id=2).process(c.data)
	if not result and key:
		bot.edit_message_text(f"Select {LSTEP[step]}", c.message.chat.id, c.message.message_id, reply_markup=key)

	elif result:
		with bot.retrieve_data(c.from_user.id, c.message.chat.id) as data:
			data['check_out_date'] = result
			bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id)
			bot.delete_message(c.message.chat.id, data['last_id'])
			bot.delete_message(c.message.chat.id, data['last_id1'])
			if data['command'] == "bestdeal":
				msd = bot.send_message(c.from_user.id,
				                 f'Вы планируете уехать: {result}. Минимальная цена (в долларах)?')
				data['last_id'] = msd.message_id
				bot.set_state(c.from_user.id, UserStateBestdeal.min_price, c.message.chat.id)
			else:
				msd = bot.send_message(c.from_user.id,
				                 f'Вы планируете уехать {result}. Сколько фотографий отеля нужно (если не нужны - введите 0)? ', reply_markup=inline_keyboards.num_photo_hotel())
				data['last_id'] = msd.message_id


@bot.callback_query_handler(func=lambda button: button.data.startswith('photo_hotel'))
def call(c) -> None:

	"""Функция, которая:
		сохраняет количество фотографий для поиска,
		делает запрос к API, циклом выводит найденные данные
		удаляет предыдущее сообщение бота

		:param
		message (Message): сообщение введённое пользователем
		"""

	bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id)
	with bot.retrieve_data(c.from_user.id, c.message.chat.id) as data:
		data["photo_hotel"] = int(c.data[11:])
		bot.delete_message(c.message.chat.id, data['last_id'])

		info = request_for_api.find_hotel(data)
		if isinstance(info, dict):
			for i_text, i_list in info.items():
				bot.send_message(c.from_user.id, i_text)
				bot.send_media_group(c.message.chat.id, i_list)
		else:
			for i_text in info:
				bot.send_message(c.from_user.id, i_text)
	bot.delete_state(c.from_user.id, c.message.chat.id)