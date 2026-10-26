import asyncio
import os
import urllib.parse
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# Токен вашего бота
TOKEN = "8850219341:AAHw_ft-a7imdnQk1fiub0FVzIIdaGHPUiE"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Временное хранилище текстов в памяти бота
user_texts = {}

# Словарь языков
LANGUAGES = {
    "en": ("🇺🇸", "Английский"), "ru": ("🇷🇺", "Русский"), "de": ("🇩🇪", "Немецкий"),
    "fr": ("🇫🇷", "Французский"), "es": ("🇪🇸", "Испанский"), "it": ("🇮🇹", "Итальянский"),
    "zh": ("🇨🇳", "Китайский"), "ja": ("🇯🇵", "Японский"), "ko": ("🇰🇷", "Корейский"),
    "ar": ("🇸🇦", "Арабский"), "tr": ("🇹🇷", "Турецкий"), "pl": ("🇵🇱", "Польский"),
    "uk": ("🇺🇦", "Украинский"), "kk": ("🇰🇿", "Казахский"), "by": ("🇧🇾", "Белорусский"),
    "pt": ("🇵🇹", "Португальский"), "nl": ("🇳🇱", "Нидерландский"), "sv": ("🇸🇪", "Шведский"),
    "cs": ("🇨🇿", "Чешский"), "he": ("🇮🇱", "Иврит")
}

# Настройки веб-сервера пустышки для Render
async def handle_root(request):
    return web.Response(text="Бот работает!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_root)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Веб-сервер заглушка успешно запущен на порту {port}")

# ИСПРАВЛЕННАЯ НАДЁЖНАЯ СИСТЕМА ПЕРЕВОДА GOOGLE
async def translate_text(text: str, target_lang: str) -> str:
    try:
        url = f"https://googleapis.com{target_lang}&dt=t&q={urllib.parse.quote(text)}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Правильно вытаскиваем текст перевода из первого элемента массива
                    if data and data[0]:
                        translated = "".join([part[0] for part in data[0] if part[0]])
                        return translated
    except Exception as e:
        print(f"Ошибка перевода: {e}")
    return "ошибка_перевода"

# Сетка кнопок
def get_language_keyboard():
    builder = InlineKeyboardBuilder()
    for code, (emoji, name) in LANGUAGES.items():
        builder.add(types.InlineKeyboardButton(text=f"{emoji} {name}", callback_data=f"to_lang:{code}"))
    builder.adjust(3)
    return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я продвинутый бот-переводчик.\n\n"
        "Вы можете отправить мне **обычный текст** или **записать голосовое сообщение**, "
        "а затем выбрать язык для перевода!",
        parse_mode="Markdown",
        reply_markup=get_language_keyboard()
    )

# ИСПРАВЛЕННЫЙ ЛЕГКИЙ ОБРАБОТЧИК ГОЛОСА
@dp.message(F.voice)
async def handle_voice(message: types.Message):
    status_msg = await message.answer("⏳ Скачиваю и распознаю ваше голосовое сообщение...")
    
    try:
        file_info = await bot.get_file(message.voice.file_id)
        file_url = f"https://telegram.org{TOKEN}/{file_info.file_path}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as resp:
                if resp.status != 200:
                    raise Exception("Не удалось скачать файл")
                voice_bytes = await resp.read()

        google_url = "https://google.com"
        headers = {"Content-Type": "audio/ogg; codecs=opus; rate=48000"}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(google_url, data=voice_bytes, headers=headers) as resp:
                if resp.status == 200:
                    text_resp = await resp.text()
                    import json
                    data = json.loads(text_resp)
                    # Исправлено чтение результата
                    if "hypotheses" in data and len(data["hypotheses"]) > 0:
                        recognized_text = data["hypotheses"][0]["utterance"]
                    elif "result" in data and len(data["result"]) > 0:
                        recognized_text = data["result"][0]["alternative"][0]["transcript"]
                    else:
                        raise Exception("Речь не распознана")
                else:
                    raise Exception(f"Ошибка API: {resp.status}")
            
        user_texts[message.from_user.id] = recognized_text
        
        await status_msg.edit_text(
            f"🗣 **Распознанный текст:**\n_«{recognized_text}»_\n\nНа какой язык его перевести?",
            parse_mode="Markdown",
            reply_markup=get_language_keyboard()
        )
        
    except Exception as e:
        print(f"Ошибка распознавания: {e}")
        await status_msg.edit_text("❌ Не удалось считать аудио. Пожалуйста, отправьте ваш текст обычным сообщением.")

# Обработчик текста
@dp.message()
async def handle_text(message: types.Message):
    if not message.text: return
    user_texts[message.from_user.id] = message.text
    await message.answer("Текст получен. На какой язык его перевести? Выберите из списка:", reply_markup=get_language_keyboard())

# ОБРАБОТЧИК КНОПОК С СУПЕР-ОЗВУЧКОЙ ДЛЯ ВСЕХ ЯЗЫКОВ
@dp.callback_query(F.data.startswith("to_lang:"))
async def handle_translation_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    text_to_translate = user_texts.get(user_id, "")
    
    if not text_to_translate:
        await callback.message.edit_text("Сначала отправьте текст или голосовое сообщение.")
        await callback.answer()
        return

    target_lang = callback.data.split(":")[-1]
    emoji, lang_name = LANGUAGES.get(target_lang, ("🌐", "Выбранный язык"))

    await callback.message.edit_text(f"⏳ Перевожу и генерирую озвучку на {lang_name.lower()}...")
    translated = await translate_text(text_to_translate, target_lang=target_lang)
    
    if translated == "ошибка_перевода":
        await callback.message.edit_text("⚠️ Не удалось перевести. Попробуйте еще раз.")
        await callback.answer()
        return

    encoded_text = urllib.parse.quote(translated)
    google_tts_url = f"https://google.com{target_lang}&client=tw-ob&q={encoded_text}"

    audio_builder = InlineKeyboardBuilder()
    audio_builder.add(types.InlineKeyboardButton(text="🔊 Прослушать произношение", url=google_tts_url))

    await callback.message.edit_text(
        f"{emoji} **Перевод на {lang_name.lower()}:**\n\n{translated}", 
        parse_mode="Markdown",
        reply_markup=audio_builder.as_markup()
    )
    await callback.answer()

async def main():
    await start_web_server()
    print("Бот успешно запущен! Доступен перевод голоса и текста.")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
