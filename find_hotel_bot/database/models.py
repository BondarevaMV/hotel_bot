from peewee import *

db = SqliteDatabase('history.db')


class History(Model):

    command = TextField(column_name='Command')
    date = DateField(column_name='Date')
    hotels = TextField(column_name='List hotels')

    class Meta:
        database = db  # модель будет использовать базу данных 'history.db'


def write_line(data):
    History.create(command=data['command'], date=data['start_date'],
                   hotels=[data["dict_id_hotels"][i_hotel]["name"] for i_hotel in data['dict_id_hotels']])


def read_info_day(day):
    list_info = [f'Команда: {i_line.command}. Время начала выполнения: {i_line.date}. Найдены следующие отели: {i_line.hotels}'
                 for i_line in History.select().where(History.date == day)]
    return '\n'.join(list_info)


db.create_tables([History])
