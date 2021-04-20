import os
import requests
import json
from datetime import date, timedelta
import telebot
from telebot import types
import tg_text as template


tg_bot_token = os.environ['TG_BOT_TOKEN']
open_weather_token = os.environ['OWM_TOKEN']
bot = telebot.AsyncTeleBot(tg_bot_token)
weather_check_city = 'http://api.openweathermap.org/data/2.5/weather'
weather_city = 'http://api.openweathermap.org/data/2.5/forecast'
weather_geo = 'http://api.openweathermap.org/data/2.5/onecall'
MONTH = {
    1: 'января',
    2: 'февраля',
    3: 'марта',
    4: 'апреля',
    5: 'мая',
    6: 'июня',
    7: 'июля',
    8: 'августа',
    9: 'сентября',
    10: 'октября',
    11: 'ноября',
    12: 'декабря',
}

states = {}
cities = {}
geo = {}

try:
    data = json.load(open('db/data.json', 'r', encoding='utf-8'))
except FileNotFoundError:
    data = {
        'states': {},
        'cities': {},
        'geo': {},
    }


def change_data(key, user_id, value):
    data[key][user_id] = value
    json.dump(data,
              open('db/data.json', 'w', encoding='utf-8'),
              indent=2,
              ensure_ascii=False)


@bot.message_handler(func=lambda message: True)
def where_user(message):
    user_id = str(message.from_user.id)
    if user_id not in data['states']:
        change_data('states', user_id, 'main')

    state_user = data['states'].get(user_id)
    if state_user == 'main':
        main_handler(message)
    elif state_user == 'weather':
        weather_handler(message)
    elif state_user == 'check_city':
        check_city(message)
    elif state_user == 'weather_status':
        weather_status(message)


def main_handler(message):
    user_id = str(message.from_user.id)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('/start'), types.KeyboardButton('/weather'))

    if message.text == '/start' or message.text == '/back':
        if message.text == '/back':
            bot.send_message(user_id, template.start(), reply_markup=markup)
            change_data('states', user_id, 'main')
        else:
            bot.send_message(user_id, template.start(), reply_markup=markup)
            change_data('states', user_id, 'main')
    elif message.text == '/weather':

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('/weather'), types.KeyboardButton('/city'),
                   types.KeyboardButton('/geo', request_location=True), types.KeyboardButton('/back'))

        bot.send_message(user_id, template.weather_help(), reply_markup=markup)
        change_data('states', user_id, 'weather')
    else:
        bot.send_message(user_id, template.wrong_text(), reply_markup=markup)


@bot.message_handler(content_types=['location'])
def weather_handler(message):
    user_id = str(message.from_user.id)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('/weather'), types.KeyboardButton('/city'),
               types.KeyboardButton('/geo', request_location=True), types.KeyboardButton('/back'))

    # Приветствие в погоде!
    if message.text == '/weather':
        bot.send_message(user_id, template.weather_help(), reply_markup=markup)
    # Поиск города!
    elif message.text == '/city':
        bot.send_message(user_id, template.weather_handler_city(), reply_markup=markup)
        change_data('states', user_id, 'check_city')
    # Поиск геолокации!
    elif message.location:
        location = [message.location.latitude, message.location.longitude]
        change_data('geo', user_id, location)
        bot.send_message(user_id, 'Погода по геолокации на СЕГОДНЯ!', reply_markup=markup)
        weather_geo_check(message)
        change_data('states', user_id, 'main')
    # Возврат в начальное меню
    elif message.text == '/back':

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('/start'), types.KeyboardButton('/weather'))

        bot.send_message(user_id, template.start(), reply_markup=markup)
        change_data('states', user_id, 'main')
    else:
        bot.send_message(user_id, template.wrong_text(), reply_markup=markup)


def check_city(message):
    user_id = str(message.from_user.id)

    today = date.today()
    day1 = date.today() + timedelta(days=1)
    day2 = date.today() + timedelta(days=2)
    day3 = date.today() + timedelta(days=3)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton(f'{today.day}'), types.KeyboardButton(f'{day1.day}'),
               types.KeyboardButton(f'{day2.day}'), types.KeyboardButton(f'{day3.day}'))

    while True:
        try:
            city = message.text.lower()
            params_check_city = {
                'q': city,
                'appid': open_weather_token,
                'lang': 'ru',
            }
            weather_request = requests.get(weather_check_city, params=params_check_city)
            weather_json = weather_request.json()

            # Это присвоение произойдет, если город введен верно.
            # Простая проверка.
            check = weather_json['weather']
            change_data('cities', user_id, city)
            bot.send_message(user_id,
                             f'ПРОГНОЗ ПОГОДЫ ДЛЯ ГОРОДА - {str(data["cities"][user_id]).upper()} : \n'
                             f'Сегодня: {today.day} {MONTH[today.month]} 🗓️\nНа какую дату? 🗂️\n'
                             f'Доступные даты: {today.day} {MONTH[today.month]}, '
                             f'{day1.day} {MONTH[day1.month]}, '
                             f'{day2.day} {MONTH[day2.month]}, '
                             f'{day3.day} {MONTH[day3.month]}.\n'
                             f'Просто введи доступное число 👍\n'
                             f'Например - {day2.day}', reply_markup=markup)
            change_data('states', user_id, 'weather_status')
            break
        except KeyError:
            bot.send_message(user_id, 'Неверно введен город! Попробуйте еще раз!')
            break


def weather_status(message):
    user_id = str(message.from_user.id)

    today = date.today()
    day1 = date.today() + timedelta(days=1)
    day2 = date.today() + timedelta(days=2)
    day3 = date.today() + timedelta(days=3)

    day = 0

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('/start'), types.KeyboardButton('/weather'))

    if str(message.text).isdigit() and int(message.text) == today.day:
        pass
    elif str(message.text).isdigit() and int(message.text) == day1.day:
        day = 1
    elif str(message.text).isdigit() and int(message.text) == day2.day:
        day = 2
    elif str(message.text).isdigit() and int(message.text) == day3.day:
        day = 3

    params = {
        'q': data['cities'][user_id],
        'appid': open_weather_token,
        'units': 'metric',
        'lang': 'ru'
    }
    weather_request = requests.get(weather_city, params=params)
    weather = weather_request.json()
    weather_for_user = {
        'temp_min': weather['list'][day]['main']['temp_min'],
        'temp_max': weather['list'][day]['main']['temp_max'],
        'feels_like': weather['list'][day]['main']['feels_like'],
        'description': weather['list'][day]['weather'][0]['description'],
        'wind': weather['list'][day]['wind']['speed'],
    }
    if str(message.text).isdigit() and int(message.text) in [i for i in range(today.day, day3.day + 1)]:
        bot.send_message(user_id,
                         f'Температура от {weather_for_user["temp_min"]} до {weather_for_user["temp_max"]}, '
                         f'{str(weather_for_user["description"]).capitalize()}!\n'
                         f'Ощущается как {weather_for_user["feels_like"]}!\n'
                         f'Скорость ветра - {weather_for_user["wind"]}.',
                         reply_markup=markup)
        bot.send_message(user_id, template.start())
        change_data('states', user_id, 'main')
    elif message.text == '/back':
        bot.send_message(user_id, template.start(), reply_markup=markup)
        change_data('states', user_id, 'main')
    else:

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton(f'{today.day}'), types.KeyboardButton(f'{day1.day}'),
                   types.KeyboardButton(f'{day2.day}'), types.KeyboardButton(f'{day3.day}'),
                   types.KeyboardButton('/back'))

        bot.send_message(user_id,
                         'Неверно введена дата! Попробуйте еще раз!\n'
                         f'Сегодня: {today.day} {MONTH[today.month]} 🗓️\nНа какую дату? 🗂️\n'
                         f'Можно узнать погоду до {day3.day} {MONTH[day3.month]}, '
                         f'просто введя доступное число 👍\n'
                         f'Например - {today.day}',
                         reply_markup=markup)


def weather_geo_check(message):
    user_id = str(message.from_user.id)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('/start'), types.KeyboardButton('/weather'))

    params = {
        'lat': data['geo'][user_id][0],
        'lon': data['geo'][user_id][1],
        'exclude': 'current,minutely,hourly,alerts',
        'appid': open_weather_token,
        'units': 'metric',
        'lang': 'ru'
    }
    weather_request = requests.get(weather_geo, params=params)
    weather = weather_request.json()
    bot.send_message(user_id,
                     f'Температура утром - {weather["daily"][0]["temp"]["morn"]}°C\n'
                     f'Днем - {weather["daily"][0]["temp"]["day"]}°C\n'
                     f'Вечером - {weather["daily"][0]["temp"]["eve"]}°C\n'
                     f'На улице сегодня - {weather["daily"][0]["weather"][0]["description"]}\n'
                     f'Ощущается как {weather["daily"][0]["feels_like"]["day"]}°C\n'
                     f'Скорость ветра - {weather["daily"][0]["wind_speed"]} м/с.',
                     reply_markup=markup)
    change_data('states', user_id, 'main')


bot.polling()
