from telebot.handler_backends import State, StatesGroup


class UserStateLowrprice(StatesGroup):
	city = State()
	photo_hotel = State()


class UserStateBestdeal(UserStateLowrprice):
	min_price = State()
	max_price = State()


class UserStateHistory(StatesGroup):
	history = State()
