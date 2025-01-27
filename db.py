import sqlite3 as sqlt
from datetime import datetime

import defs

db_name = 'user_database.db'


def start_db():
    base = sqlt.connect(db_name)
    base.execute('CREATE TABLE IF NOT EXISTS "User" ("id"	INTEGER NOT NULL UNIQUE,'
                 '"user_id"         INTEGER,'
                 '"channel_id"      INTEGER,'
                 '"flag"            INTEGER,'
                 'PRIMARY KEY("id" AUTOINCREMENT))')
    base.execute('CREATE TABLE IF NOT EXISTS "Channel" ("id"	INTEGER NOT NULL UNIQUE,'
                 '"channel_id"      INTEGER,'
                 '"channel_title"   BLOB,'
                 'PRIMARY KEY("id" AUTOINCREMENT))')
    base.execute('CREATE TABLE IF NOT EXISTS "Message" ("id"	INTEGER NOT NULL UNIQUE,'
                 '"title"           BLOB,'
                 '"chat_id"         INTEGER,'
                 '"message_id"      INTEGER,'
                 'PRIMARY KEY("id" AUTOINCREMENT))')
    base.execute('CREATE TABLE IF NOT EXISTS "Welcome_post_templates" ('
                 '"chat_id"         INTEGER,'
                 '"message_id"      INTEGER,'
                 'PRIMARY KEY("chat_id", "message_id"))')
    base.execute('CREATE TABLE IF NOT EXISTS "Button_templates" ("id"	INTEGER NOT NULL UNIQUE,'
                 '"button_text"     BLOB,'
                 'PRIMARY KEY("id" AUTOINCREMENT))')
    base.execute('CREATE TABLE IF NOT EXISTS "Response" ("id"	INTEGER NOT NULL UNIQUE,'
                 '"button_text"     BLOB,'
                 'PRIMARY KEY("id" AUTOINCREMENT))')
    base.execute('CREATE TABLE IF NOT EXISTS "Deferred_planned_posts" ("id"	INTEGER NOT NULL UNIQUE,'
                 '"channel_id"         BLOB,'
                 '"message_chat_id" INTEGER,'
                 '"message_id"      INTEGER,'
                 '"media_group_data"   TEXT,'
                 '"post_time"       INTEGER,'
                 'PRIMARY KEY("id" AUTOINCREMENT))')
    base.commit()


def create_planned_send_post(channel_id, message_chat_id, message_id, media_group_data, post_time):
    try:
        with sqlt.connect(db_name) as conn:
            dt = datetime.strptime(post_time, "%H:%M %d.%m.%Y")
            unix_time = int(dt.timestamp())
            cur = conn.cursor()
            if media_group_data:
                media_group = defs.media_group_to_json(media_group_data)
                cur.execute('INSERT INTO Deferred_planned_posts VALUES (null, ?, null, null, ?, ?)',
                            (channel_id, media_group, unix_time))
            else:
                cur.execute('INSERT INTO Deferred_planned_posts VALUES (null, ?, ?, ?, null, ?)',
                            (channel_id, message_chat_id, message_id, unix_time))
        return True
    except Exception as e:
        print(f'[INFO] create_planned_send_post error: {e}')
        return False

def output_deferred_planned_posts():
    with sqlt.connect(db_name) as conn:
        cur = conn.cursor()
        data = cur.execute('SELECT * FROM Deferred_planned_posts').fetchall()
        if data:
            return data
        else:
            return False


def output_users_by_channel_id(channel_id):
    with sqlt.connect(db_name) as conn:
        cur = conn.cursor()
        data = cur.execute('SELECT * FROM User WHERE channel_id = ?', (channel_id, ))
        if data:
            return data
        else:
            return False


def delete_deferred_planned_posts(id):
        with sqlt.connect(db_name) as conn:
            cur = conn.cursor()
            cur.execute('DELETE FROM Deferred_planned_posts WHERE id = ?', (id,))
            conn.commit()


def output_channel_data():
    with sqlt.connect(db_name) as conn:
        cur = conn.cursor()
        data = cur.execute('SELECT channel_id, channel_title FROM Channel').fetchall()
        print(data)
        if data:
            return data
        else:
            return False


def output_planned_posts():
    with sqlt.connect(db_name) as conn:
        cur = conn.cursor()
        data = cur.execute('SELECT channel_id, message_chat_id, message_id, media_group_data, post_time '
                           'FROM Deferred_planned_posts').fetchall()
        if data:
            return data
        else:
            return False


def add_button_text(text):
    with sqlt.connect(db_name) as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM Button_templates')
        cur.execute('INSERT INTO Button_templates VALUES (null, ?)', (text,))


def add_button_response(text):
    with sqlt.connect(db_name) as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM Response')
        cur.execute('INSERT INTO Response VALUES (null, ?)', (text,))


def output_response_text():
    with sqlt.connect(db_name) as conn:
        cur = conn.cursor()
        data = cur.execute('SELECT button_text FROM Response').fetchone()
        return data[0]


def output_button_text():
    with sqlt.connect(db_name) as conn:
        cur = conn.cursor()
        data = cur.execute('SELECT button_text FROM Button_templates').fetchone()
        if data is None:
            return '1'
        else:
            return data


def add_channel(channel_id, channel_title):
    with sqlt.connect(db_name) as conn:
        cur = conn.cursor()
        data = cur.execute('SELECT * FROM Channel where channel_id = ?', (channel_id,)).fetchone()
        if data is None:
            cur.execute('INSERT INTO Channel VALUES (null, ?, ?)', (channel_id, channel_title))
            return True
        else:
            return False


def delete_channel(channel_id):
    with sqlt.connect(db_name) as conn:
        cur = conn.cursor()
        data = cur.execute('SELECT * FROM Channel WHERE channel_id = ?', (channel_id,)).fetchone()
        if data is not None:
            cur.execute('DELETE FROM Channel WHERE channel_id = ?', (channel_id,))
            return True
        else:
            return False


def add_user(user_id, channel_id):
    with sqlt.connect(db_name) as conn:
        cur = conn.cursor()
        data = cur.execute('SELECT * FROM User WHERE user_id = ? AND channel_id = ?', (user_id, channel_id)).fetchone()
        if data is None:
            cur.execute('INSERT INTO User VALUES (null, ?, ?, ?)', (user_id, channel_id, 1))
            return True
        else:
            return False


def output_users():
    with sqlt.connect(db_name) as conn:
        cur = conn.cursor()
        data = cur.execute('SELECT user_id FROM User').fetchall()
        data = [item[0] for item in data]
    return data


def get_welcome_post():
    with sqlt.connect(db_name) as conn:
        cur = conn.cursor()
        data = cur.execute('SELECT * FROM Welcome_post_templates').fetchall()
        return data


def edit_welcome_post(chat_id, message_id):
    with sqlt.connect(db_name) as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM Welcome_post_templates;')
        cur.execute('INSERT INTO Welcome_post_templates VALUES (?, ?)', (chat_id, message_id))
