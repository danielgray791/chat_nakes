import asyncio
import base64
import inspect

import filetype

from telebot.types import Message, User
from telebot.asyncio_helper import ApiException
from telebot.async_telebot import AsyncTeleBot

import lib.provider as provider
from lib.provider import split_message, escape
from lib.provider.models.chatuser import ChatUser
from templates import Chat as ChatTemplates

from typing import Union, Tuple, Optional, List, Mapping

ALLOWED_GROUPS: Mapping[str, int] = {
    "admininfoseminar": -1002374870153,
    "diskusiinfoseminar": -1002445614395,
    "channelinfoseminar": -1002316256863
}

ALLOWED_GROUP_IDS = ALLOWED_GROUPS.values()

async def check_subscription(msg: Message, user: User, admin_bot: AsyncTeleBot) -> Tuple[bool, str]:     
    chat_type = msg.chat.type
    chat_id = msg.chat.id

    if chat_type != "private" and chat_id not in ALLOWED_GROUP_IDS: 
        return False, ChatTemplates.NOT_JOINED_MESSAGE
    
    async def is_member(user_id: int) -> bool: 
        admininfoseminar_id = ALLOWED_GROUPS.get("admininfoseminar")
        
        flagged = ["left", "restricted", "banned"]
        groups = ALLOWED_GROUPS.values()

        for group_id in groups: 
            if group_id == admininfoseminar_id: 
                continue

            try: 
                chat_member = await admin_bot.get_chat_member(group_id, user_id)
            except ApiException as err: 
                return False

            if chat_member.status in flagged: 
                return False
            
        return True

    user_id = user.id
    user_is_member = await is_member(user_id)
    if user_is_member is False: 
        return False, ChatTemplates.NOT_JOINED_MESSAGE

    return True, ""

async def user_handler(user: User) -> Optional[ChatUser]: 
    user_id = user.id
    full_name = user.full_name

    user = await ChatUser.get(user_id)
    if user is None: 
        user = ChatUser(user_id, full_name)
        await user.save()
           
    return user

async def chat(user: ChatUser, prompt: Union[str, Tuple[str, str]]) -> List[str]: 
    config = user.config
    model_ins = config.model_ins
    item_name = config.provider.item_name
    selected_provider = provider.providers[item_name]
    selected_model = selected_provider.get_model(config.model)
    chat_client = await model_ins(item_name)

    kwargs = {}
    kwargs["model"] = selected_model.id
    kwargs["history"] = user.history[item_name]

    print("Chat: ", {"prompt": prompt, "kwargs": kwargs})

    # print(config) 
    if inspect.iscoroutinefunction(chat_client.chat): 
        try:
            response = await chat_client.chat(prompt, **kwargs)
        finally:
            # Always call destroy instance, even if an exception occurs
            await chat_client.destroy()
    else:
        response = await asyncio.to_thread(chat_client.chat, prompt, **kwargs)
    
    response = response.replace("scira.ai", "chat.openai.com").replace("fragments.e2b.dev", "chat.openai.com")
    print("Chat Response", {"response": response})
    
    chunked_response = split_message(escape(response))
    return chunked_response

async def get_photo_uri(message: Message, bot: AsyncTeleBot) -> str: 
    photo_id = message.photo[-1].file_id
    file_info = await bot.get_file(photo_id)

    photo_file = await bot.download_file(file_info.file_path)
    kind = filetype.guess(photo_file)
    base64_photo = base64.b64encode(photo_file).decode('utf-8')
    photo_uri = f"data:{kind.mime};base64,{base64_photo}"

    return photo_uri
