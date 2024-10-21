import asyncio
import re
import os
import sys
import traceback
import base64
import provider

import filetype
import telebot
import aiohttp

from provider import split_message, escape
from chatuser import ChatUser
from typing import Optional, Tuple, List, Union

from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import Response

from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot
from telebot.types import (
    Update,
    Message, 
    User,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

load_dotenv()
# TOKEN = "7056403843:AAHnZQnvICeFIxjamfxxzuicxfKqXi3dKzg" # test
TOKEN = os.getenv("TOKEN")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
WEBHOOK = os.getenv("WEBHOOK")

admin_bot = AsyncTeleBot(ADMIN_TOKEN)
bot = AsyncTeleBot(TOKEN)

setted = False
async def index(request: Request): 
    global setted

    if not setted: 
        await bot.delete_webhook()

        url = WEBHOOK + "/webhook"
        await asyncio.sleep(1)
        await bot.set_webhook(url=url)
        setted = True
        
    return Response("Webhook set", status_code=200)

async def webhook(request: Request): 
    try: 
        data = await request.json()
        async with aiohttp.ClientSession() as session:
            async with session.post(WEBHOOK + "/handle_updates", json=data, timeout=1) as response: 
                pass
    except Exception as e: 
        print("Error: ", traceback.print_exc())

    return Response("ok", status_code=200)

async def handle_updates(request: Request): 
    data = await request.body()
    print("Data: ", data)
    json_data = data.decode("utf-8")
    update = Update.de_json(json_data)
    await bot.process_new_updates([update])
    return Response("ok", status_code=200)
    
app = Starlette(routes=[
    Route("/", endpoint=index),
    Route("/webhook", endpoint=webhook, methods=["POST"]),
    Route("/handle_updates", endpoint=handle_updates, methods=["POST"])
])

CHAT_USAGE_MESSAGE = (
    "*Penggunaan*\n"
    "`/chat <prompt>`\n\n"
    "*Contoh*\n"
    "`/chat apa itu kucing?`"
)

VISION_CHAT_USAGE_MESSAGE = (
    "*Penggunaan*\n"
    "`/desc <prompt>`\n\n"
    "*Contoh*\n"
    "`/desc gambar apa ini?`"
)

NOT_JOINED_MESSAGE = (
    "Maaf anda tidak diperbolehkan untuk mengakses bot ini\!"
)

DONATE_MESSAGE = (
    "Hai, terima kasih sudah mau berdonasi! Bot ini sepenuhnya dikelola oleh relawan, "
    "jadi kontribusi Anda sangat berarti bagi kelangsungan dan perkembangan bot ini. "
    "Kami dengan senang hati menerima donasi melalui metode berikut:"
)

DONATE_MARKUP = InlineKeyboardMarkup(
    keyboard=[
        [InlineKeyboardButton("Donasi via Saweria", url="https://saweria.co/ainewsid")],
        [InlineKeyboardButton("Donasi via Buy Me A Coffee", url="https://buymeacoffee.com/ainewsid")]
    ],
) 

CONFIG_MENU_MARKUP = lambda user_id: InlineKeyboardMarkup(
    keyboard=[
        [InlineKeyboardButton("Menampilkan Konfigurasi", callback_data=f"{user_id}.config.display")],
        [InlineKeyboardButton("Mengganti Penyedia Model", callback_data=f"{user_id}.config.change_provider")],
        [InlineKeyboardButton("Mengganti Model", callback_data=f"{user_id}.config.change_model")]
    ],
)

async def check_subscription(msg: Message) -> Tuple[bool, str]: 
    groups_map = {
        "aiartidn": -1002155873968,
        "aitipsid": -1002211742885,
        "forumaiindonesia": -1001218880477,
        "ainewsid": -1002070055371,
        "admininfoseminar": -1002374870153,
        "diskusiinfoseminar": -1002445614395,
        "Revins_co": -1001727916136,
        "Ekspresi_karakter": -1001777139262,
        "familyties_02": -1002192232202,
        "mencarimomentum": -1002246524544
    }

    allowed_chat_ids = list(groups_map.values())

    chat_type = msg.chat.type
    chat_id = msg.chat.id

    if chat_type == "private": 
        return True, ""
    
    if chat_id not in allowed_chat_ids: 
        return False, NOT_JOINED_MESSAGE

    return True, ""

async def user_handler(user: User) -> Optional[ChatUser]: 
    user_id = user.id
    full_name = user.full_name

    user = await ChatUser.get(user_id)
    if user is None: 
        user = ChatUser(user_id, full_name)
        await user.save()
           
    return user

async def chat(user: ChatUser, prompt: Union[str, Tuple[str, str]]) -> List: 
    config = user.config
    model_ins = config.model_ins
    item_name = config.provider.item_name

    kwargs = {}
    kwargs["model"] = config.model.replace("_dot_", ".")
    kwargs["history"] = user.history[item_name]

    # print("Chat: ", {"prompt": prompt, "kwargs": kwargs})

    # print(config)
    response = await asyncio.to_thread(model_ins.chat, prompt, **kwargs)
    # print("Chat Response", {"response": response})
    
    chunked_response = split_message(escape(response))
    return chunked_response

async def get_photo_uri(message: Message) -> str: 
    photo_id = message.photo[-1].file_id
    file_info = await bot.get_file(photo_id)

    photo_file = await bot.download_file(file_info.file_path)
    kind = filetype.guess(photo_file)
    base64_photo = base64.b64encode(photo_file).decode('utf-8')
    photo_uri = f"data:{kind.mime};base64,{base64_photo}"

    return photo_uri

@bot.message_handler(content_types=['photo'])
async def photo_handler(message: Message): 
    tg_user = message.from_user
    caption = message.caption + " "
    my_bot = await bot.get_me()
    
    if caption and caption.startswith("/desc"): 

        if caption.startswith("/desc@"): 
            command = caption.split("@")
            if len(command) > 1 and command[1][:len(my_bot.username) + 1] != my_bot.username + " ": 
                return

        if tg_user.username == "GroupAnonymousBot": 
            return await bot.reply_to(message, "Anda tidak diperkenankan menggunakan bot ini sebagai Anonymous Admin")
            
        subbed, callback_text = await check_subscription(message)
        if subbed is False: 
            return await bot.reply_to(message, callback_text, parse_mode="MarkdownV2")

        args = caption.split(" ")
        prompt = " ".join(args[1:]).strip()

        if not prompt: 
            return await bot.reply_to(message, VISION_CHAT_USAGE_MESSAGE, parse_mode="MarkdownV2")

        user = await user_handler(tg_user)
        config = user.config
        
        if config.vision is False: 
            return await bot.reply_to(message, escape(f"Model Terpilih: `{config.model}`\nSupport Vision: `Tidak`\n\nSebelum menggunakan perintah ini ganti terlebih dahulu Penyedia Model ke `Open Ai V2` (WAJIB) dan Jangan Lupa Model Harus Support Vision\n\nSilahkan kirim gambar menggunakan caption yang diisi dengan perintah\n{VISION_CHAT_USAGE_MESSAGE}"), parse_mode="MarkdownV2")
  
        photo_uri = await get_photo_uri(message)
        prompt = (prompt, photo_uri)
        result_chunks = await chat(user, prompt)
        
        for text_chunk in result_chunks: 
            msg = await bot.reply_to(message, text_chunk, parse_mode="MarkdownV2") 

        await bot.edit_message_text(text_chunk, msg.chat.id, msg.message_id, reply_markup=DONATE_MARKUP, parse_mode="MarkdownV2")
        await user.save()

@bot.message_handler(commands=['chat'])
async def chat_command(message: Message): 
    text = message.text + " "
    tg_user = message.from_user
    my_bot = await bot.get_me()

    if tg_user.username == "GroupAnonymousBot": 
        return await bot.reply_to(message, "Anda tidak diperkenankan menggunakan bot ini sebagai Anonymous Admin")

    subbed, callback_text = await check_subscription(message)
    if subbed is False: 
        await bot.reply_to(message, callback_text, parse_mode="MarkdownV2")
    else: 
        if text.startswith("/chat@"): 
            command = text.split("@")
            if len(command) > 1 and not command[1].startswith(my_bot.username + " "): 
                return

        args = text.split(" ")
        prompt = " ".join(args[1:]).strip()

        if not prompt: 
            return await bot.reply_to(message, CHAT_USAGE_MESSAGE, parse_mode="MarkdownV2")

        user = await user_handler(tg_user)
        result_chunks = await chat(user, prompt)

        for text_chunk in result_chunks: 
            msg = await bot.reply_to(message, text_chunk, parse_mode="MarkdownV2") 
        await bot.edit_message_text(text_chunk, msg.chat.id, msg.message_id, reply_markup=DONATE_MARKUP, parse_mode="MarkdownV2")
        
        await user.save()

@bot.message_handler(commands=['desc'])
async def desc_command(message: Message): 
    text = message.text + " "
    tg_user = message.from_user
    my_bot = await bot.get_me()

    if text.startswith("/desc@"): 
        command = text.split("@")
        if len(command) > 1 and command[1][:len(my_bot.username) + 1] != my_bot.username + " ": 
            return

    if tg_user.username == "GroupAnonymousBot": 
        return await bot.reply_to(message, "Anda tidak diperkenankan menggunakan bot ini sebagai Anonymous Admin")

    subbed, callback_text = await check_subscription(message)
    if subbed is False: 
        await bot.reply_to(message, callback_text, parse_mode="MarkdownV2")
    else: 
        user = await user_handler(tg_user)
        config = user.config
        vision = "Ya" if config.vision else "Tidak"

        return await bot.reply_to(message, escape(f"Model Terpilih: `{config.model}`\nSupport Vision: `{vision}`\n\nSebelum menggunakan perintah ini ganti terlebih dahulu Penyedia Model ke `Open Ai V2` (WAJIB) dan Jangan Lupa Model Harus Support Vision\n\nSilahkan kirim gambar menggunakan caption yang diisi dengan perintah\n{VISION_CHAT_USAGE_MESSAGE}"), parse_mode="MarkdownV2")
        await bot.reply_to(message, f"Sebelum menggunakan perintah ini ganti terlebih dahulu Penyedia Model ke `\"Open Ai V2\"` \(WAJIB\) dan Jangan Lupa Model Harus Support Vision\n\nSilahkan kirim gambar menggunakan caption yang diisi dengan perintah\n{VISION_CHAT_USAGE_MESSAGE}", parse_mode = "MarkdownV2")

@bot.message_handler(commands=['clear'])
async def clear_chat_command(message: Message): 
    text = message.text + " "
    tg_user = message.from_user
    my_bot = await bot.get_me()
    
    if text.startswith("/clear@"): 
        command = text.split("@")
        if len(command) > 1 and command[1][:len(my_bot.username) + 1] != my_bot.username + " ": 
            return

    if tg_user.username == "GroupAnonymousBot": 
        return await bot.reply_to(message, "Anda tidak diperkenankan menggunakan bot ini sebagai Anonymous Admin")

    subbed, callback_text = await check_subscription(message)
    if subbed is False: 
        await bot.reply_to(message, callback_text, parse_mode="MarkdownV2")
    else: 
        user = await user_handler(tg_user)
        config = user.config
        item_name = config.provider.item_name

        history = user.history[item_name]
        history.clear()
        
        await bot.reply_to(message, "Konteks Percakapan Berhasil Di Bersihkan")
        await user.save()

@bot.message_handler(commands=['config'])
async def config_command(message: Message): 
    tg_user = message.from_user
    text = message.text + " "
    my_bot = await bot.get_me()

    if text.startswith("/config@"): 
        command = text.split("@")
        if len(command) > 1 and command[1][:len(my_bot.username) + 1] != my_bot.username + " ": 
            return

    if tg_user.username == "GroupAnonymousBot": 
        return await bot.reply_to(message, "Anda tidak diperkenankan menggunakan bot ini sebagai Anonymous Admin")

    subbed, callback_text = await check_subscription(message)
    if subbed is False: 
        await bot.reply_to(message, callback_text, parse_mode="MarkdownV2")
    else: 
        await bot.reply_to(message, "Menu Konfigurasi Chat", reply_markup=CONFIG_MENU_MARKUP(tg_user.id))

@bot.message_handler(commands=['donate'])
async def donate_command(message: Message): 
    tg_user = message.from_user
    text = message.text + " "
    my_bot = await bot.get_me()

    if text.startswith("/donate@"): 
        command = text.split("@")
        if len(command) > 1 and command[1][:len(my_bot.username) + 1] != my_bot.username + " ": 
            return

    await bot.reply_to(message, DONATE_MESSAGE, reply_markup=DONATE_MARKUP)


@bot.callback_query_handler(func=lambda call: True)
async def callback_query_feeder(call: CallbackQuery): 
    tg_user = call.from_user
    message = call.message
    text = message.text
    chat_id = message.chat.id
    message_id = message.message_id

    if tg_user.username == "GroupAnonymousBot": 
        return await bot.reply_to(message, "Anda tidak diperkenankan menggunakan bot ini sebagai Anonymous Admin")

    subbed, callback_text = await check_subscription(message)
    if subbed is False: 
        return await bot.answer_callback_query(call.id, callback_text, parse_mode="MarkdownV2")
    
    user = await user_handler(tg_user)
    call_data_list = call.data.split(".")
    caller_id, menu, action = call_data_list[:3]
    
    if caller_id != user.id: 
        return await bot.answer_callback_query(call.id, text="Hanya Yang Memanggil Tombol Ini Yang Bisa Mengakses!", show_alert=True)
    
    user.menu = menu
    user.action = action

    if action == "display": 
        vision = "Ya" if user.config.vision else "Tidak"
        display_config_message = (
            "*Chat Config* \n"
            f"Model \= `{user.config.model}`\n"
            f"Model Support Vision \= `{vision}`\n"
            f"Provider \= `{user.config.provider.name}`"
        )

        markup = InlineKeyboardMarkup(
            keyboard=[
                [
                    InlineKeyboardButton("Kembali", callback_data=f"{caller_id}.config.display_menu"),
                ]
            ],
        )
        await bot.edit_message_text(display_config_message, chat_id, message_id, reply_markup=markup, parse_mode="MarkdownV2")
    elif action == "change_provider": 
        providers = provider.providers.values()
        change_provider_callback = call_data_list[3:]

        markup = InlineKeyboardMarkup(
            keyboard=[
                [
                    InlineKeyboardButton(provider.name, callback_data=f"{caller_id}.config.change_provider.{provider.item_name}_{provider.name}")
                    for provider in providers
                ],
                [
                    InlineKeyboardButton("Kembali", callback_data=f"{caller_id}.config.display_menu")
                ]
            ]
        )

        if change_provider_callback: 
            item_name, name = change_provider_callback[0].split("_")
            selected_provider = provider.providers[item_name]
            default_model_name = selected_provider.default_model
            model = selected_provider.get_model(default_model_name)

            user.config.model = model.name
            user.config.vision = model.vision
            user.config.provider.item_name = item_name
            user.config.provider.name = name

        prev_provider_name = text.replace("Penyedia Sekarang: ", "")
        if prev_provider_name != user.config.provider.name: 
            await bot.edit_message_text(f"Penyedia Sekarang: `{user.config.provider.name}`", chat_id, message_id, reply_markup=markup, parse_mode="MarkdownV2")

    elif action == "change_model": 
        item_name = user.config.provider.item_name
        models = provider.providers[item_name].models
        change_model_callback = call_data_list[3:]

        markup = InlineKeyboardMarkup(
            keyboard=[
                [ InlineKeyboardButton(model.name, callback_data=f"{caller_id}.config.change_model.{model.name}.{model.vision}") ]
                for model in models   
            ] + [
                [ InlineKeyboardButton("Kembali", callback_data=f"{caller_id}.config.display_menu") ]
            ]
        )

        if change_model_callback: 
            model_name, vision, = change_model_callback
            user.config.model = model_name
            user.config.vision = vision == "True"

        prev_model_name = text.replace("Model Sekarang: ", "")
        if prev_model_name != user.config.model: 
            await bot.edit_message_text(f"Model Sekarang: `{user.config.model}`", chat_id, message_id, reply_markup=markup, parse_mode="MarkdownV2")

    elif action == "display_menu": 
        markup = CONFIG_MENU_MARKUP(user.id)
        await bot.edit_message_text("Menu Konfigurasi Chat", chat_id, message_id, reply_markup=markup, parse_mode="MarkdownV2")

    await user.save()
    await bot.answer_callback_query(call.id)

@bot.message_handler(commands=['test'])
async def test_command(message: Message): 
    tg_user = message.from_user
    my_bot = await bot.get_me()
    user_id = tg_user.id
    full_name = tg_user.full_name

    user = await ChatUser.get(user_id)
    if user is None: 
        user = ChatUser(user_id, full_name)
        # await user.save()

    await bot.reply_to(message, message.json)
    await bot.reply_to(message, my_bot.username)

@bot.message_handler(func=lambda message: True)
async def text_feeder(message: Message): 
    text = message.text
    tg_user = message.from_user
    my_bot = await bot.get_me()
    
    reply = message.reply_to_message
    if reply and reply.from_user.username == my_bot.username:  
        if tg_user.username == "GroupAnonymousBot": 
            return await bot.reply_to(message, "Anda tidak diperkenankan menggunakan bot ini sebagai Anonymous Admin")

        subbed, callback_text = await check_subscription(message)
        if subbed is False: 
            await bot.reply_to(message, callback_text, parse_mode="MarkdownV2")
        else: 
            user = await user_handler(tg_user)
            result_chunks = await chat(user, text)

            for text_chunk in result_chunks: 
                msg = await bot.reply_to(message, text_chunk, parse_mode="MarkdownV2")

            await bot.edit_message_text(text_chunk, msg.chat.id, msg.message_id, reply_markup=DONATE_MARKUP, parse_mode="MarkdownV2")
            await user.save()