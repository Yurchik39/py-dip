import sqlite3

users_db = sqlite3.connect('db/users.db')
users = users_db.cursor()

users.execute("""CREATE TABLE IF NOT EXISTS main
(
    user_id BIGINT,
    first_name TEXT,
    sex TEXT,
    preferred_sex TEXT,
    preferred_age_from INTEGER,
    preferred_age_to INTEGER,
    search_offset BIGINT,
    registration_stage TEXT

)""")

users.execute("""CREATE TABLE IF NOT EXISTS viewed_profiles
(
    user_id BIGINT,
    viewed_profile_id BIGINT
)""")
