from loader import key_api
import requests
from database import models
import json
from telebot import types


def api_request(method_endswith,
                params,
                method_type
                ):
	"""Функция реализующая запрос к API

	:param
	method_endswit (str): Меняется в зависимости от запроса. locations/v3/search, либо properties/v2/list
	params (dict): параметры поиска
	method_type (str): Метод\тип запроса GET\POST
	"""

	url = f"https://hotels4.p.rapidapi.com/{method_endswith}"
	if method_type == 'GET':
		return get_request(
		url=url,
		params=params
		)
	else:
		return post_request(
		url=url,
		params=params
		)


def get_request(url, params):
	"""Функция возращающая результат GET-запроса

	:param
	url (str): адрес поиска
	params (dict): параметры поиска
	"""
	headers = {
		"X-RapidAPI-Key": key_api,
		"X-RapidAPI-Host": "hotels4.p.rapidapi.com"
	}
	try:
		response = requests.get(
			url,
			headers=headers,
			params=params,
			timeout=15
			)
		if response.status_code == requests.codes.ok:
			return response.text
	except Exception:
		print("Ошибочка")


def post_request(url, params):
	"""Функция возращающая результат POST-запроса

	:param
	url (str): адрес поиска
	params (dict): параметры поиска
	"""

	headers = {
		"content-type": "application/json",
		"X-RapidAPI-Key": key_api,
		"X-RapidAPI-Host": "hotels4.p.rapidapi.com"
	}
	try:
		response = requests.post(
		url=url,
		headers=headers,
		json=params,
		timeout=15
		)
		if response.status_code == requests.codes.ok:
			return response.text
	except Exception:
		print("Ошибочка")


def find_city_id(data):

	"""Функция поиска id города,
	реализует GET-запрос,
	перебирает найденные значения в случае нахождения типа 'CITY' сохраняет значение и прерывает цикл
	:param
	data (dict): словарь с сохнанёнными значениями
	"""

	response = json.loads(
		api_request('locations/v3/search', {'q': data["city"], 'locale': 'ru_RU'}, 'GET'))
	for i_key in response['sr']:
		if i_key['type'] == 'CITY':
			city_id = i_key['gaiaId']
			data['city_id'] = city_id
			break


def find_hotel(data):

	"""Функция поиска отелей,
	вызывает функцию find_city_id,
	реализует POST-запрос для поиска списка отелей,
	сохраняет в базу данных найденную информацию.
	Сохраняет найденные значения и доступную в запросе информацию (название отеля, цену за ночь, расстояние до центра)
	для каждого найденного отеля делает POST-запрос деталей,
	если пользователь запрашивал фото, то информация для вывода сохраняется в словаре,
	где ключ - строка с данными, а значение - список с url-ами фотографий,
	если фото не запрошено возвращает список строк с данными

	:param
	data (dict): словарь с сохранёнными значениями
	:return
	list или dict
	"""

	find_city_id(data)
	response_hotel = json.loads(api_request('properties/v2/list', params_for_search(data), 'POST'))
	data['dict_id_hotels'] = dict()
	for i_key in response_hotel['data']['propertySearch']['properties']:
		data['dict_id_hotels'][i_key['id']] = {'name': i_key['name'],
		                                       'price': i_key['price']['lead']['amount'],
		                                       'distanceFromDestination': i_key['destinationInfo']['distanceFromMessaging']}

	info = dict() if 0 < int(data["photo_hotel"]) else list()

	for i_key in data['dict_id_hotels']:
		payload_for_detail =  {
			"currency": "USD",
			"eapid": 1,
			"locale": "en_US",
			"siteId": 300000001,
			"propertyId": i_key
		}
		response = json.loads(api_request('properties/v2/detail', payload_for_detail, 'POST'))
		whole_cost = int(data["dict_id_hotels"][i_key]["price"]) * int((data["check_out_date"] - data["check_in_date"]).__str__()[:2])

		text = (f'Название отеля: {data["dict_id_hotels"][i_key]["name"]}'
		        f'\nЦена за ночь: {data["dict_id_hotels"][i_key]["price"]}'
		        f'\nАдрес: {response["data"]["propertyInfo"]["summary"]["location"]["address"]["addressLine"]}'
		        f'\nРасстояние от центра города: {data["dict_id_hotels"][i_key]["distanceFromDestination"]}'
		        f'\nСтоимость за указанный период составит: {whole_cost}')

		if 0 < int(data["photo_hotel"]):
			medias = find_photo(int(data["photo_hotel"]), response)
			info[text] = medias
		else:
			info.append(text)

		models.write_line(data)

	return info


def find_photo(num, response):
	"""Функция поиска фотографий отеля

	:param
		response (dict): результат запроса
		num (int): необходимое количество фотографий
	:return
		list: список с url-ами фотографий
		"""
	medias = list()
	for index, i_photo in enumerate(response["data"]["propertyInfo"]["propertyGallery"]["images"]):
		medias.append(types.InputMediaPhoto(i_photo['image']['url']))
		if index + 1 == num:
			break
	return medias


def params_for_search(data):
	"""Функция настраивающая параметры для поиска

	:param
		data (dict): словарь с сохранёнными значениями

	"""

	payload = {'currency': 'USD',
	           'eapid': 1,
	           'locale': 'ru_RU',
	           'siteId': 300000001,
	           'destination': {
		           'regionId': data['city_id']  # id из первого запроса
	           },
	           'checkInDate': {'day': data['check_in_date'].day, 'month': data['check_in_date'].month, 'year': data['check_in_date'].year},
	           'checkOutDate': {'day': data['check_out_date'].day, 'month': data['check_out_date'].month, 'year': data['check_out_date'].year},
	           'rooms': [{'adults': 1}],
	           'resultsStartingIndex': 0,
	           'resultsSize': data["num_hotel"],
	           'sort': 'PRICE_LOW_TO_HIGH',
	           'filters': {'availableFilter': 'SHOW_AVAILABLE_ONLY'}
	           }

	if data['command'] == "highprice":
		payload['sort'] = 'PRICE_HIGH_TO_LOW'
	elif data['command'] == "bestdeal":
		payload['filters'] = {"price": {"max": data["max_price"], "min": data["min_price"]}}
		payload['sort'] = 'DISTANCE'

	return payload
