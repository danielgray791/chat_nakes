from telebot.types import (
    User,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from lib.provider.models import chatuser
from lib.provider import escape, providers

class Chat: 
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
        "*Selamat datang,*\n"
        "Ai Know Bot ini milik https://bit\.ly/WebinarNakesGratis\n"
        "Untuk mengakses fitur lengkap Ai Know bot ini,\n\n"
        "Silahkan \n"
        "*WAJIB* follow\n"
        "https://t\.me/infoseminarpelataransehat\n"
        "Channel Info Seminar SKP Kemenkes Pelataran Sehat 🥇🥇🏆\n\n"
        "Terima kasih"
    )

    ANONYMOUS_NOT_ALLOWED = "Anda tidak diperkenankan menggunakan bot ini sebagai Anonymous Admin"

    @staticmethod
    def VISION_NOT_SUPPORT(config: chatuser.Config, vision: str = "Tidak") -> str: 
        return escape(
            f"Model Terpilih: `{config.model}`\n"
            f"Support Vision: `{vision}`\n\n"
            "Sebelum menggunakan perintah ini ganti terlebih dahulu Penyedia Model ke `V2` (WAJIB)" 
            "dan Jangan Lupa Model Harus Support Vision\n\n"
            "Silahkan kirim gambar menggunakan caption yang diisi dengan perintah\n"
            f"{Chat.VISION_CHAT_USAGE_MESSAGE}"
        )
    
    CLEAR_CHAT = "Konteks Percakapan Berhasil Di Bersihkan"

    CLEAR_IP = "IP List Berhasil Di Reset"

    @staticmethod
    def CONFIG_MENU_MARKUP(user: User) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            keyboard=[
                [InlineKeyboardButton("Menampilkan Konfigurasi", callback_data=f"{user.id}.config.display")],
                [InlineKeyboardButton("Mengganti Penyedia Model", callback_data=f"{user.id}.config.change_provider")],
                [InlineKeyboardButton("Mengganti Model", callback_data=f"{user.id}.config.change_model")]
            ],
        )

    CONFIG_MENU_MESSAGE = "Menu Konfigurasi Chat"

    INLINE_CALLBACK_UNAUTHORIZED = "Hanya Yang Memanggil Tombol Ini Yang Bisa Mengakses!"

    @staticmethod
    def DISPLAY_CONFIG_MESSAGE(user: chatuser.ChatUser) -> str:  
        vision = "Ya" if user.config.vision else "Tidak"
        return (
            "*Chat Config* \n"
            f"Model \= `{user.config.model}`\n"
            f"Model Support Vision \= `{vision}`\n"
            f"Provider \= `{user.config.provider.name}`"
        )
    
    @staticmethod
    def DISPLAY_CONFIG_MARKUP(caller_id: int) -> InlineKeyboardMarkup: 
        return InlineKeyboardMarkup(
            keyboard=[
                [
                    InlineKeyboardButton("Kembali", callback_data=f"{caller_id}.config.display_menu")
                ]
            ]
        )
    
    @staticmethod
    def CHANGE_PROVIDER_MARKUP(caller_id: int) -> InlineKeyboardMarkup: 
        return InlineKeyboardMarkup(
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
    
    @staticmethod
    def CHANGE_PROVIDER_MESSAGE(user: chatuser.ChatUser) -> str: 
        return f"Penyedia Sekarang: `{user.config.provider.name}`", 

    @staticmethod
    def CHANGE_MODEL_MARKUP(user: chatuser.ChatUser, caller_id: int, page: int) -> InlineKeyboardMarkup: 
        item_name = user.config.provider.item_name
        selected_provider = providers[item_name]

        return selected_provider.inline_keyboard_markup(caller_id, page)
    
    @staticmethod
    def CHANGE_MODEL_MESSAGE(user: chatuser.ChatUser) -> str: 
        return f"Model Sekarang: `{user.config.model}`"
    
