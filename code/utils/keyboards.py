from VKLong.VKLong import KeyboardGenerator, KeyboardColor

# Выбор пола:
key_choice_sex = KeyboardGenerator(one_time=True)
key_choice_sex.add_text_button("Мужской", color=KeyboardColor.BLUE)
key_choice_sex.add_text_button("Женский", color=KeyboardColor.BLUE)
key_choice_sex = key_choice_sex.get_keyboard_json()


# Кнопка поиска:
key_search = KeyboardGenerator(one_time=False)
key_search.add_text_button("🔎 Поиск", color=KeyboardColor.GREEN)
key_search = key_search.get_keyboard_json()