# Импортирование модулей:
import time
import traceback

import VKLong.VKLong.object
import requests

from config import *
from VKLong.VKLong import *
from db.database import *
from utils.keyboards import *
from traceback import print_exc

# Авторизация:

user_token = input("Введите user-token, который будет использоваться для поиска людей: ")

bot = Bot(token=BOT_TOKEN)

# Получение обновлений:
@bot.get_updates
def on_update(event):
    try:
        # Если пришло сообщение:
        if event.type == "message_new":
            message_object = VKLong.VKLong.object.message_new(event.response)
            message = message_object.text.lower()
            user_id = message_object.from_id
            # Если сообщение из личных сообщений:
            if message_object.from_id < 2E9:

                # Если пользователь не зарегистрирован и не указал нужные данные:
                if (user_id,) not in users.execute("SELECT user_id FROM main").fetchall():
                    user_name = bot.execute_api("users.get", {'user_id': user_id})[0]['first_name']
                    users.execute("INSERT INTO main(user_id, first_name, sex, preferred_sex, preferred_age_from, preferred_age_to, search_offset, registration_stage) "
                                 "VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (user_id, user_name, "NULL", "NULL", "NULL", "NULL", 0, "choice_sex"))
                    bot.answer("👋 Привет! Добро пожаловать в VKinder!\n"
                               "\n"
                               "👉 Выбери свой пол на клавиатуре:", key_choice_sex)

                # Регистрация пользователя:
                elif (user_id,) in users.execute("SELECT user_id FROM main WHERE registration_stage != 'finished'").fetchall():
                    registration_stage = users.execute(f"SELECT registration_stage FROM main WHERE user_id = '{user_id}'").fetchall()[0][0]
                    # Выбор своего пола пользователем:
                    if registration_stage == "choice_sex":
                        if message in accepted_sex:
                            users.execute(f"UPDATE main SET registration_stage = 'choice_preferred_sex' "
                                          f"WHERE user_id = '{user_id}'")
                            if message == "мужской":
                                users.execute(f"UPDATE main SET sex = 'male' WHERE user_id = '{user_id}'")
                            elif message == "женский":
                                users.execute(f"UPDATE main SET sex = 'female' WHERE user_id = '{user_id}'")
                            bot.answer("👍 Отлично! С твоим полом определились.\n"
                                       "\n"
                                       "👉 Выбери предпочитаемый пол, с которым хочешь познакомиться: ", key_choice_sex)
                        else:
                            bot.answer("🤚 Упс! Вы выбрали недопустимый пол!\n"
                                       "\n"
                                       "👉 Выбери доступный пол на клавиатуре:", key_choice_sex)

                    # Выбор предпочитаемого пола:
                    elif registration_stage == "choice_preferred_sex":
                        if message in accepted_sex:
                            users.execute(f"UPDATE main SET registration_stage = 'choice_preferred_age' "
                                          f"WHERE user_id = '{user_id}'")
                            if message == "мужской":
                                users.execute(f"UPDATE main SET preferred_sex = 'male' WHERE user_id = '{user_id}'")
                            elif message == "женский":
                                users.execute(f"UPDATE main SET preferred_sex = 'female' WHERE user_id = '{user_id}'")
                            bot.answer("👍 Отлично! С преподчитаемым полом определились!\n"
                                       "\n"
                                       "👉 Теперь укажи диапазон возраста собеседника:\n"
                                       "(например, отправь сообщение: 20-25)")
                        else:
                            bot.answer("🤚 Упс! Вы выбрали недопустимый предпочитаемый пол!\n"
                                       "\n"
                                       "👉 Выбери доступный пол на клавиатуре:", key_choice_sex)

                    # Указание диапазона поиска по возрасту:
                    elif registration_stage == "choice_preferred_age":
                        try:
                            minimal_age = int(message.split('-')[0])
                            maximum_age = int(message.split('-')[1])
                            if minimal_age > maximum_age:
                                minimal_age, maximum_age = maximum_age, minimal_age
                            if 18 <= minimal_age <= 99 and 18 <= maximum_age <= 99:
                                users.execute(f"UPDATE main SET preferred_age_from = '{minimal_age}' WHERE user_id = '{user_id}'")
                                users.execute(f"UPDATE main SET preferred_age_to = '{maximum_age}' WHERE user_id = '{user_id}'")
                                users.execute(f"UPDATE main SET registration_stage = 'finished' WHERE user_id = '{user_id}'")
                                bot.answer("🥳 Отлично! Теперь ты можешь воспользоваться VKinder!\n"
                                           "\n"
                                           '👉 Используй команду - "поиск", чтобы найти подходящего человека!', key_search)

                            else:
                                bot.answer("🤚 Упс! Диапазон поиска должен быть не менее 18-ти и не более 99-ти лет!\n"
                                           "\n"
                                           "👉 Отправь сообщение вида 20-25, чтобы указать возраст поиска:")

                        except ValueError:
                            bot.answer("🤚 Упс! Диапазон поиска должен являться целым числом!\n"
                                       "\n"
                                       "👉 Отправь сообщение вида 20-25, чтобы указать возраст поиска:")

                        except IndexError:
                            bot.answer("🤚 Упс! Ты неправильно указал(а) диапазон возраста!\n"
                                       "\n"
                                       "👉 Отправь сообщение вида 20-25, чтобы указать возраст поиска:")

                # Если пользователь зарегистрирован:
                elif (user_id,) in users.execute("SELECT user_id FROM main WHERE registration_stage = 'finished'").fetchall():
                    if message == "поиск" or message == "🔎 поиск":

                        while True:
                            # Подготовка значение из базы данных:
                            preferred_sex = users.execute(f"SELECT preferred_sex FROM main WHERE user_id = '{user_id}'").fetchall()[0][0]
                            if preferred_sex == "female":
                                preferred_sex = 1
                            elif preferred_sex == "male":
                                preferred_sex = 2
                            age_from = int(users.execute(f"SELECT preferred_age_from FROM main WHERE user_id = '{user_id}'").fetchall()[0][0])
                            age_to = int(users.execute(f"SELECT preferred_age_to FROM main WHERE user_id = '{user_id}'").fetchall()[0][0])
                            offset = int(users.execute(f"SELECT search_offset FROM main WHERE user_id = '{user_id}'").fetchall()[0][0])

                            response = requests.get("https://api.vk.com/method/users.search",
                                                    params={
                                                        'offset': offset,
                                                        'sex': preferred_sex,
                                                        'status': (1, 6),
                                                        'age_from': age_from,
                                                        'age_to': age_to,
                                                        'access_token': user_token,
                                                        'v': 5.131
                                                    }).json()

                            users.execute(f"UPDATE main SET search_offset = search_offset + 1 WHERE user_id = '{user_id}'")
                            users_db.commit()

                            finded_user_object = response['response']['items'][0]
                            is_profile_closed = finded_user_object['is_closed']
                            if not is_profile_closed:
                                photos_object = requests.get("https://api.vk.com/method/photos.getAll",
                                                    params={
                                                        'owner_id': finded_user_object['id'],
                                                        'extended': 1,
                                                        'count': 100,
                                                        'skip_hidden': 1,
                                                        'access_token': user_token,
                                                        'v': 5.131
                                                    }).json()['response']

                                if photos_object['count'] < 3:
                                    pass

                                # Отправка фотографий и ссылки на пользователей:
                                else:
                                    photo_dict = {}
                                    if photos_object['count'] > 100:
                                        photos_object['count'] = 100
                                    for i in range(photos_object['count']):
                                        try:
                                            photo_likes = photos_object['items'][i]['likes']['count']
                                            photo_dict[photo_likes] = f"photo{finded_user_object['id']}_{photos_object['items'][i]['id']}"
                                        except:
                                            break
                                    if photo_dict != {}:
                                        attachment_list = ""
                                        try:
                                            for x in range(3):
                                                attachment_list += f"{photo_dict[max(photo_dict)]},"
                                                photo_dict.pop(max(photo_dict))
                                            bot.answer("👍 Найден подходящий профиль!\n"
                                                       "\n"
                                                       f"🏵 [id{finded_user_object['id']}|{finded_user_object['first_name']} {finded_user_object['last_name']}]\n"
                                                       f"Ссылка: vk.com/id{finded_user_object['id']}",
                                                       attachment=str(attachment_list))
                                            break

                                        except:
                                            pass

                            else:
                                pass



    except KeyError:
        print_exc()
        print("Произошла критическая ошибка!\n"
              f"Полученный ответ от сервера: {event.response}\n")
        time.sleep(10)

    except:
        print_exc()
