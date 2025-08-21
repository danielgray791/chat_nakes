# 7371600782:AAHD6LMjbqDmkTBiR93ASaB4AstOft5Sdfk
import asyncio
import re
import os
import sys
import traceback
import base64
import utils
import lib.provider as provider

import filetype
import telebot
import aiohttp

from lib.provider import split_message, escape
from lib.provider.models.chatuser import ChatUser
from lib.provider.models.mongodb import MongoDB
from templates import Chat as ChatTemplates
from typing import Optional, Tuple, List, Union

from telebot.async_telebot import AsyncTeleBot
from telebot.types import (
    Update,
    Message, 
    User,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)

class CommandHandler: 
    def __init__(
        self, 
        bot: AsyncTeleBot, 
        admin_bot: AsyncTeleBot
    ):
        @bot.message_handler(content_types=['photo'])
        async def photo_handler(message: Message): 
            tg_user = message.from_user
            caption = message.caption + " "
            my_bot = await bot.get_me()
            reply = message.reply_to_message
            
            if caption and caption.startswith("/desc") or reply and reply.from_user.username == my_bot.username: 
        
                if caption.startswith("/desc@"): 
                    command = caption.split("@")
                    if len(command) > 1 and command[1][:len(my_bot.username) + 1] != my_bot.username + " ": 
                        return
        
                if tg_user.username == "GroupAnonymousBot": 
                    await bot.reply_to(
                        message, 
                        ChatTemplates.ANONYMOUS_NOT_ALLOWED
                    )
                    return
                    
                subbed, callback_text = await utils.check_subscription(message, tg_user, admin_bot)
                if subbed is False: 
                    await bot.reply_to(
                        message, 
                        callback_text, 
                        parse_mode="MarkdownV2"
                    )
                    return
        
                prompt = caption
                if caption.startswith("/desc"): 
                    args = caption.split(" ")
                    prompt = " ".join(args[1:]).strip()
        
        
                if not prompt: 
                    await bot.reply_to(
                        message, 
                        ChatTemplates.VISION_CHAT_USAGE_MESSAGE, 
                        parse_mode="MarkdownV2"
                    )
                    return
        
                user = await utils.user_handler(tg_user)
                config = user.config
                
                if config.vision is False: 
                    await bot.reply_to(
                        message, 
                        ChatTemplates.VISION_NOT_SUPPORT(config), 
                        parse_mode="MarkdownV2"
                    )
                    return
          
                photo_uri = await utils.get_photo_uri(message, bot)
                prompt = (prompt, photo_uri)
                result_chunks = await utils.chat(user, prompt)
                
                for text_chunk in result_chunks: 
                    msg = await bot.reply_to(
                        message, 
                        text_chunk, 
                        parse_mode="MarkdownV2"
                    )
        
                await user.save()
        
        @bot.message_handler(commands=['chat'])
        async def chat_command(message: Message): 
            text = message.text + " "
            tg_user = message.from_user
            my_bot = await bot.get_me()
        
            if tg_user.username == "GroupAnonymousBot": 
                await bot.reply_to(
                    message, 
                    ChatTemplates.ANONYMOUS_NOT_ALLOWED
                )
                return
        
            subbed, callback_text = await utils.check_subscription(message, tg_user, admin_bot)
            if subbed is False: 
                await bot.reply_to(
                    message, 
                    callback_text, 
                    parse_mode="MarkdownV2"
                )
            else: 
                if text.startswith("/chat@"): 
                    command = text.split("@")
                    if len(command) > 1 and not command[1].startswith(my_bot.username + " "): 
                        return
        
                args = text.split(" ")
                prompt = " ".join(args[1:]).strip()
        
                if not prompt: 
                    await bot.reply_to(
                        message, 
                        ChatTemplates.CHAT_USAGE_MESSAGE, 
                        parse_mode="MarkdownV2"
                    )
                    return
        
                user = await utils.user_handler(tg_user)
                result_chunks = await utils.chat(user, prompt)
        
                for text_chunk in result_chunks: 
                    msg = await bot.reply_to(
                        message, 
                        text_chunk,
                        parse_mode="MarkdownV2"
                    ) 
                    
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
                await bot.reply_to(
                    message, 
                    ChatTemplates.ANONYMOUS_NOT_ALLOWED
                )
                return
        
            subbed, callback_text = await utils.check_subscription(message, tg_user, admin_bot)
            if subbed is False: 
                await bot.reply_to(
                    message, 
                    callback_text, 
                    parse_mode="MarkdownV2"
                )
            else: 
                user = await utils.user_handler(tg_user)
                config = user.config
                vision = "Ya" if config.vision else "Tidak"
        
                await bot.reply_to(
                    message, 
                    ChatTemplates.VISION_NOT_SUPPORT(config, vision), 
                    parse_mode="MarkdownV2"
                )
        
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
                await bot.reply_to(
                    message, 
                    ChatTemplates.ANONYMOUS_NOT_ALLOWED
                )
                return
        
            subbed, callback_text = await utils.check_subscription(message, tg_user, admin_bot)
            if subbed is False: 
                await bot.reply_to(
                    message, 
                    callback_text, 
                    parse_mode="MarkdownV2"
                )
            else: 
                user = await utils.user_handler(tg_user)
                config = user.config
                item_name = config.provider.item_name
        
                history = user.history[item_name]
                history.clear()
                
                await bot.reply_to(
                    message, 
                    ChatTemplates.CLEAR_CHAT
                )
                await user.save()
        
        @bot.message_handler(commands=['clearip'])
        async def clear_ip_command(message: Message): 
            text = message.text + " "
            tg_user = message.from_user
            my_bot = await bot.get_me()
            
            if text.startswith("/clearip@"): 
                command = text.split("@")
                if len(command) > 1 and command[1][:len(my_bot.username) + 1] != my_bot.username + " ": 
                    return
        
            if tg_user.username == "GroupAnonymousBot": 
                await bot.reply_to(
                    message, 
                    ChatTemplates.ANONYMOUS_NOT_ALLOWED
                )
                return
        
            subbed, callback_text = await utils.check_subscription(message, tg_user, admin_bot)
            if subbed is False: 
                await bot.reply_to(
                    message, 
                    callback_text, 
                    parse_mode="MarkdownV2"
                )
            else: 
                await db.clear("ip_list")
                await bot.reply_to(
                    message, 
                    ChatTemplates.CLEAR_IP
                )
        
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
                await bot.reply_to(
                    message, 
                    ChatTemplates.ANONYMOUS_NOT_ALLOWED
                )
                return
        
            subbed, callback_text = await utils.check_subscription(message, tg_user, admin_bot)
            if subbed is False: 
                await bot.reply_to(
                    message, 
                    callback_text, 
                    parse_mode="MarkdownV2"
                )
            else: 
                await bot.reply_to(
                    message, 
                    ChatTemplates.CONFIG_MENU_MESSAGE, 
                    reply_markup=ChatTemplates.CONFIG_MENU_MARKUP(tg_user)
                )
        
        
        @bot.callback_query_handler(func=lambda call: True)
        async def callback_query_feeder(call: CallbackQuery): 
            tg_user = call.from_user
            message = call.message
            text = message.text
            chat_id = message.chat.id
            message_id = message.message_id
            reply_markup = message.reply_markup
        
            if tg_user.username == "GroupAnonymousBot": 
                await bot.reply_to(
                    message, 
                    ChatTemplates.ANONYMOUS_NOT_ALLOWED
                )
                return
        
            subbed, callback_text = await utils.check_subscription(message, tg_user, admin_bot)
            if subbed is False: 
                await bot.answer_callback_query(
                    call.id, 
                    callback_text, 
                    parse_mode="MarkdownV2"
                )
                return
            
            user = await utils.user_handler(tg_user)
            call_data_list = call.data.split(".")
            caller_id, menu, action = call_data_list[:3]
            
            if caller_id != user.id: 
                await bot.answer_callback_query(
                    call.id, 
                    ChatTemplates.INLINE_CALLBACK_UNAUTHORIZED, 
                    show_alert=True
                )
                return
            
            user.menu = menu
            user.action = action
        
            if action == "display": 
                await bot.edit_message_text(
                    ChatTemplates.DISPLAY_CONFIG_MESSAGE(user), 
                    chat_id, 
                    message_id, 
                    reply_markup=ChatTemplates.DISPLAY_CONFIG_MARKUP(caller_id), 
                    parse_mode="MarkdownV2"
                )
            elif action == "change_provider": 
                providers = provider.providers.values()
                change_provider_callback = call_data_list[3:]
        
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
                    await bot.edit_message_text(
                        ChatTemplates.CHANGE_PROVIDER_MESSAGE(user), 
                        chat_id, 
                        message_id, 
                        reply_markup=ChatTemplates.CHANGE_PROVIDER_MARKUP(caller_id), 
                        parse_mode="MarkdownV2"
                    )
            elif action.startswith("pagemdl_"): 
                page = int(user.action[8:])
                await bot.edit_message_reply_markup(
                    chat_id, 
                    message_id, 
                    reply_markup=ChatTemplates.CHANGE_MODEL_MARKUP(user, caller_id, page) 
                )
            elif action == "change_model": 
                change_model_callback = call_data_list[3:]
        
                if change_model_callback: 
                    model_name, vision, = change_model_callback
                    user.config.model = model_name
                    user.config.vision = vision == "True"
        
                if text.startswith("Model Sekarang: "): 
                    prev_model_name = text[:16]
                    if prev_model_name != user.config.model: 
                        await bot.edit_message_text(
                            ChatTemplates.CHANGE_MODEL_MESSAGE(user),
                            chat_id, 
                            message_id,
                            reply_markup=reply_markup,
                            parse_mode="MarkdownV2"
                        )
                else: 
                    await bot.edit_message_text(
                        ChatTemplates.CHANGE_MODEL_MESSAGE(user),
                        chat_id, 
                        message_id, 
                        reply_markup=ChatTemplates.CHANGE_MODEL_MARKUP(user, caller_id, 0),
                        parse_mode="MarkdownV2"
                    )
        
            elif action == "display_menu": 
                await bot.edit_message_text(
                    ChatTemplates.CONFIG_MENU_MESSAGE, 
                    chat_id, 
                    message_id, 
                    reply_markup=ChatTemplates.CONFIG_MENU_MARKUP(user), 
                    parse_mode="MarkdownV2"
                )
        
            await user.save()
            await bot.answer_callback_query(call.id)
        
        @bot.message_handler(commands=['test'])
        async def test_command(message: Message): 
            tg_user = message.from_user
            my_bot = await bot.get_me()
            user_id = tg_user.id
            full_name = tg_user.full_name
        
            user = await utils.user_handler(user_id)
        
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
                    await bot.reply_to(
                        message, 
                        ChatTemplates.ANONYMOUS_NOT_ALLOWED
                    )
                    return
        
                subbed, callback_text = await utils.check_subscription(message, tg_user, admin_bot)
                if subbed is False: 
                    await bot.reply_to(
                        message, 
                        callback_text, 
                        parse_mode="MarkdownV2"
                    )
                else: 
                    user = await utils.user_handler(tg_user)
                    result_chunks = await utils.chat(user, text)
        
                    for text_chunk in result_chunks: 
                        msg = await bot.reply_to(
                            message, 
                            text_chunk, 
                            parse_mode="MarkdownV2"
                        )
        
                    await user.save()
