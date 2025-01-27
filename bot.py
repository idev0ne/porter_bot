import asyncio
import os
import re
from datetime import datetime
from typing import List, Union

from aiogram import Bot
from aiogram import types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import ChatMemberUpdated, ChatMemberStatus, CallbackQuery, ReplyKeyboardRemove
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv, find_dotenv

import button
import db
import defs
from states import *

load_dotenv(find_dotenv())
storage = MemoryStorage()
bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher(bot, storage=storage)
scheduler = AsyncIOScheduler()


async def on_startup(_):
    print('Bot is running')
    db.start_db()


async def data_collection():
    time_now = datetime.now()
    unix_time = int(time_now.timestamp())
    data = db.output_deferred_planned_posts()
    try:
        if data:
            for tuple_element in data:
                users = db.output_users_by_channel_id(tuple_element[1])
                tasks = []
                if unix_time >= int(tuple_element[5]):
                    for i in users:
                        if tuple_element[4]:
                            media_group = defs.json_to_media_group(tuple_element[4])
                            await bot.send_media_group(chat_id=i[1], media=media_group)
                            db.delete_deferred_planned_posts(tuple_element[0])
                        else:
                            await bot.copy_message(chat_id=i[1], from_chat_id=tuple_element[2],
                                                   message_id=tuple_element[3])
                            db.delete_deferred_planned_posts(tuple_element[0])
                else:
                    return

                await asyncio.gather(*tasks)
    except Exception as error:
        print(error)


scheduler.add_job(data_collection, "interval", seconds=10)
scheduler.start()


class AlbumMiddleware(BaseMiddleware):

    album_data: dict = {}

    def __init__(self, latency: Union[int, float] = 0.01):
        self.latency = latency
        super().__init__()

    async def on_process_message(self, message: types.Message, data: dict):
        if not message.media_group_id:
            return

        try:
            self.album_data[message.media_group_id].append(message)
            raise CancelHandler()
        except KeyError:
            self.album_data[message.media_group_id] = [message]
            await asyncio.sleep(self.latency)

            message.conf["is_last"] = True
            data["album"] = self.album_data[message.media_group_id]

    async def on_post_process_message(self, message: types.Message, result: dict, data: dict):
        if message.media_group_id and message.conf.get("is_last"):
            del self.album_data[message.media_group_id]


@dp.my_chat_member_handler()
async def on_my_chat_member_update(chat_member_update: ChatMemberUpdated):
    bot_user = await bot.me

    if chat_member_update.new_chat_member.user.id == bot_user.id:
        if chat_member_update.new_chat_member.status == ChatMemberStatus.ADMINISTRATOR:
            chat = chat_member_update.chat
            chat_title = chat.title
            chat_id = chat.id
            db.add_channel(chat.id, chat.title)
            print(f"Бот добавлен как администратор в канал: {chat_title} (ID: {chat_id})")
            await bot.send_message(chat_id=os.getenv('ADMIN_ID'),
                                   text=f'Бот добавлен как администратор в канал: {chat_title} (ID: {chat_id})')

        elif chat_member_update.new_chat_member.status != ChatMemberStatus.ADMINISTRATOR:
            chat = chat_member_update.chat
            chat_title = chat.title
            chat_id = chat.id
            db.delete_channel(chat.id)
            print(f"В этом канале бот больше не администратор: {chat_title} (ID: {chat_id})")
            await bot.send_message(chat_id=os.getenv('ADMIN_ID'),
                                   text=f'В этом канале бот больше не администратор: {chat_title} (ID: {chat_id})')


@dp.message_handler(commands='start', user_id=os.getenv('ADMIN_ID'))
async def start(message: types.Message):
    await bot.send_message(message.from_user.id, text="Добро пожаловать!", reply_markup=button.main_menu())


@dp.chat_join_request_handler()
async def chat_join_request_handler(chat_join_request: types.ChatJoinRequest):
    await bot.get_chat_member(chat_join_request.chat.id, chat_join_request.from_user.id)
    user_id = chat_join_request.user_chat_id
    chat_id = chat_join_request.chat.id
    db.add_user(user_id, chat_id)
    data = db.get_welcome_post()
    await bot.copy_message(chat_id=chat_join_request.from_user.id, from_chat_id=data[0][0], message_id=data[0][1],
                           reply_markup=button.confirm(db.output_button_text()[0]))
    await asyncio.sleep(1)
    await bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)


@dp.message_handler(text='Посмотреть запланированные посты', user_id=os.getenv('ADMIN_ID'))
async def create_post(message: types.Message):
    data = db.output_planned_posts()
    if not data:
        await bot.send_message(chat_id=message.chat.id, text=f'На данный момент постов не запланировано')
        return
    for tuple_element in data:
        formatted_time = datetime.fromtimestamp(tuple_element[4]).strftime("%H:%M %d.%m.%Y")
        if tuple_element[3]:
            media_group = defs.json_to_media_group(tuple_element[3])
            await bot.send_message(chat_id=message.chat.id, text=f'Канал: {tuple_element[0]}')
            await bot.send_media_group(chat_id=message.from_user.id, media=media_group)
            await bot.send_message(chat_id=message.chat.id, text=f'Время постинга: {formatted_time}')
        else:
            await bot.send_message(chat_id=message.chat.id, text=f'Канал: {tuple_element[0]}')
            await bot.copy_message(chat_id=message.from_user.id, from_chat_id=tuple_element[1],
                                   message_id=tuple_element[2])
            await bot.send_message(chat_id=message.chat.id, text=f'Время постинга: {formatted_time}')



@dp.message_handler(text="Настройки⚙️", user_id=os.getenv('ADMIN_ID'))
async def settings(message: types.Message):
    await bot.send_message(chat_id=message.chat.id, text=f'Выберите вариант:', reply_markup=button.settings_menu())


@dp.message_handler(text='Обновить приветственный пост', user_id=os.getenv('ADMIN_ID'))
async def welcome_post(message: types.Message):
    await bot.send_message(chat_id=message.chat.id, text=f'Пришлите приветственный пост: ', reply_markup=button.back())
    await WelcomePost.wl_post1.set()


@dp.message_handler(state=WelcomePost.wl_post1)
async def save_welcome_post(message: types.Message, state: FSMContext):
    db.edit_welcome_post(message.chat.id, message.message_id)
    await bot.send_message(message.chat.id, text=f'Приветственный пост добавлен', reply_markup=button.main_menu())
    await state.finish()


@dp.message_handler(text='Обновить текст кнопки', user_id=os.getenv('ADMIN_ID'))
async def create_post(message: types.Message):
    await bot.send_message(chat_id=message.chat.id, text=f'Введите текст кнопки: ',
                           reply_markup=button.back())
    await EditButtonText.EditButtonText1.set()


@dp.message_handler(state=EditButtonText.EditButtonText1)
async def save_sample_name(message: types.Message, state: FSMContext):
    db.add_button_text(message.text)
    await bot.send_message(chat_id=message.chat.id, text=f'Текст кнопки установлен - "{message.text}"\n',
                           reply_markup=button.main_menu())
    await state.finish()
    # sys.exit(-1)


@dp.message_handler(text='Обновить текст после нажатия', user_id=os.getenv('ADMIN_ID'))
async def update_button_response(message: types.Message):
    await bot.send_message(chat_id=message.chat.id, text=f'Введите текст кнопки: ',
                           reply_markup=button.back())
    await EditButtonResponseText.EditButtonResponseText1.set()


@dp.message_handler(state=EditButtonResponseText.EditButtonResponseText1)
async def save_sample_name(message: types.Message, state: FSMContext):
    db.add_button_response(message.text)
    await bot.send_message(chat_id=message.chat.id, text=f'Текст после нажатия установлен',
                           reply_markup=button.main_menu())
    await state.finish()


@dp.message_handler(text='Рассылка пользователям📝', user_id=os.getenv('ADMIN_ID'))
async def mailing_menu(message: types.Message):
    await bot.send_message(message.from_user.id, text=f"Выберите вариант рассылки: ", reply_markup=button.mailing())


@dp.message_handler(text='Рассылка всем и сейчас', user_id=os.getenv('ADMIN_ID'))
async def send_user(message: types.Message, state: FSMContext):
    if db.output_channel_data():
        await bot.send_message(message.from_user.id, text=f"Ожидаю пост для рассылки: ", reply_markup=button.back())
        await MassSend.MSend.set()
    else:
        await bot.send_message(chat_id=message.chat.id, text=f'Бот не добавлен как администратор ни в один канал',
                               reply_markup=button.main_menu())
        await state.finish()


@dp.message_handler(state=MassSend.MSend, is_media_group=True, content_types=types.ContentType.ANY)
async def handle_albums(message: types.Message, album: List[types.Message], state: FSMContext):
    media_group = types.MediaGroup()
    good, bad = 0, 0
    await state.finish()
    errors_list = []
    for obj in album:
        if obj.photo:
            file_id = obj.photo[-1].file_id
        else:
            file_id = obj[obj.content_type].file_id

        try:
            media_group.attach({"media": file_id, "type": obj.content_type, "caption": obj.caption})
        except ValueError:
            return await message.answer("This type of album is not supported by aiogram.")
    for i in db.output_users():
        try:
            await bot.send_media_group(chat_id=i, media=media_group)
            good += 1
        except Exception as e:
            bad += 1
            errors_list.append(e)
    await bot.send_message(message.from_user.id, 'Рассылка завершена!\n'
                                                 f'Доставлено: {good}\n'
                                                 f'Не доставлено: {bad}\n'
                                                 f'Ошибки {set(errors_list)}',
                           reply_markup=button.main_menu())


@dp.message_handler(state=MassSend.MSend, content_types=['text', 'photo', 'video', 'animation'])
async def send_user(message: types.Message, state: FSMContext):
    good, bad = 0, 0
    await state.finish()
    errors_list = []
    for i in db.output_users():
        try:
            await bot.copy_message(chat_id=i, from_chat_id=message.chat.id,message_id=message.message_id)
            good += 1
        except Exception as e:
            bad += 1
            errors_list.append(e)
    await bot.send_message(message.from_user.id, 'Рассылка завершена!\n'
                                                 f'Доставлено: {good}\n'
                                                 f'Не доставлено: {bad}\n'
                                                 f'Ошибки {set(errors_list)}',
                           reply_markup=button.main_menu())


@dp.message_handler(text='Запланированная рассылка', user_id=os.getenv('ADMIN_ID'))
async def planned_mailing(message: types.Message):
    if channel_data := db.output_channel_data():
        temp_message = await bot.send_message(chat_id=message.chat.id, text="🔎", reply_markup=ReplyKeyboardRemove())
        await asyncio.sleep(2)
        await bot.delete_message(chat_id=message.chat.id, message_id=temp_message.message_id)
        await bot.send_message(chat_id=message.chat.id, text=f'Выберите канал: ',
                               reply_markup=button.channels_list(channel_data),)
        await PlannedMailing.PlannedMailing1.set()
    else:
        await bot.send_message(chat_id=message.chat.id, text=f'Бот не добавлен как администратор ни в один канал',
                               reply_markup=button.main_menu())


@dp.callback_query_handler(state=PlannedMailing.PlannedMailing1)
async def select_channel(call: CallbackQuery, state: FSMContext):
    await call.answer()
    async with state.proxy() as data:
        data['channel_id'] = call.data
    await PlannedMailing.next()
    await call.message.edit_text(f"Введите дату и время в формате: ЧЧ:ММ ДД.ММ.ГГГГ")


@dp.message_handler(state=PlannedMailing.PlannedMailing2)
async def entering_date(message: types.Message, state: FSMContext):
    time_regex = r"^([01]\d|2[0-3]):([0-5]\d)\s([0-2]\d|3[01])\.(0[1-9]|1[0-2])\.(\d{4})$"
    if re.match(time_regex, message.text):
        async with state.proxy() as data:
            data['post_date'] = message.text
        await PlannedMailing.next()
        await bot.send_message(chat_id=message.chat.id, text="Пришлите пост:")
    else:
        await bot.send_message(chat_id=message.chat.id, text=f'Ошибка ввода!\n'
                                                             f'Формат ввода: ЧЧ:ММ ДД:ММ:ГГГГ (13:10 08.02.2025)\n'
                                                             f'Повторите ввод:')


@dp.message_handler(state=PlannedMailing.PlannedMailing3, is_media_group=True, content_types=types.ContentType.ANY)
async def media_group_post(message: types.Message, album: List[types.Message], state: FSMContext):
    media_group = types.MediaGroup()
    for obj in album:
        if obj.photo:
            file_id = obj.photo[-1].file_id
        else:
            file_id = obj[obj.content_type].file_id

        try:
            media_group.attach({"media": file_id, "type": obj.content_type, "caption": obj.caption})
        except ValueError:
            return await message.answer("This type of album is not supported by aiogram.")
    async with state.proxy() as data:
        data['media_group'] = media_group
    await PlannedMailing.next()
    await bot.send_message(message.chat.id, text=f'Подтвердите действие:', reply_markup=button.confirmation())


@dp.message_handler(state=PlannedMailing.PlannedMailing3, content_types=['text', 'photo', 'video', 'animation'])
async def text_post(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['chat_id'] = message.chat.id
        data['mess_id'] = message.message_id
    await PlannedMailing.next()
    await bot.send_message(message.chat.id, text=f'Подтвердите действие:', reply_markup=button.confirmation())


@dp.message_handler(state=PlannedMailing.PlannedMailing4, text='Запланировать✅')
async def send_post(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        channel_id = data.get('channel_id')
        chat_id = data.get('chat_id')
        mess_id = data.get('mess_id')
        media_group = data.get('media_group')
        post_date = data.get('post_date')

    if db.create_planned_send_post(channel_id, chat_id, mess_id, media_group, post_date):
        await bot.send_message(message.chat.id, text=f'Вы успешно добавили пост в очередь на публикацию',
                               reply_markup=button.main_menu())
    else:
        await bot.send_message(message.chat.id, text=f'Пост не был добавлен',
                               reply_markup=button.main_menu())
    await state.finish()


@dp.message_handler(text="Назад", state="*")
async def select_channel(message: types.Message, state: FSMContext):
    await state.finish()
    await bot.send_message(chat_id=message.chat.id, text="Главное меню",
                           reply_markup=button.main_menu())


@dp.callback_query_handler(text="back", state="*")
async def select_channel(call: CallbackQuery, state: FSMContext):
    await state.finish()
    await bot.send_message(chat_id=call.message.chat.id, text="Главное меню",
                           reply_markup=button.main_menu())
    await call.answer()


@dp.message_handler(content_types=['text'])
async def post_action(message: types.Message):
    if message.text == db.output_button_text()[0]:
        response_text = db.output_response_text()
        await bot.send_message(chat_id=message.chat.id, text=response_text,
                               reply_markup=types.ReplyKeyboardRemove())
    else:
        pass


if __name__ == '__main__':
    dp.middleware.setup(AlbumMiddleware())
    executor.start_polling(dp, on_startup=on_startup)
