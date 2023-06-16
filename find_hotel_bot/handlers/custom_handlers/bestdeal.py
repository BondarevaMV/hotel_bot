from telebot.types import Message
from states.all_state import UserStateBestdeal
from loader import bot
from keyboards.inline import inline_keyboards


@bot.message_handler(state=UserStateBestdeal.min_price)
def get_min_price(message: Message) -> None:
	if message.text.isdigit():
		msd = bot.send_message(message.from_user.id, f'Минимальная цена: {message.text}. А какая максимальная цена?')
		with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
			data["min_price"] = int(message.text)
			bot.delete_message(message.chat.id, data['last_id'])
			data['last_id'] = msd.message_id

		bot.set_state(message.from_user.id, UserStateBestdeal.max_price, message.chat.id)
		bot.delete_message(message.chat.id, message.message_id)

	else:
		bot.send_message(message.from_user.id, f'Введите, пожалуйста, минимальную цену в долларах')


@bot.message_handler(state=UserStateBestdeal.max_price)
def get_max_price(message: Message) -> None:
	if message.text.isdigit():
		msd = bot.send_message(message.from_user.id, f'Максимальная цена: {message.text}. Сколько фотографий отеля нужно (если не нужны - введите 0)? ', reply_markup=inline_keyboards.num_photo_hotel())
		with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
			data["max_price"] = int(message.text)
			bot.delete_message(message.chat.id, data['last_id'])
			data['last_id'] = msd.message_id
		bot.delete_message(message.chat.id, message.message_id)
	else:
		bot.send_message(message.from_user.id, f'Введите, пожалуйста, максимальную цену в долларах')
