import asyncio
import translators as ts
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = "8850219341:AAEKd3ZWEg7UZ09DRitSsK2744RYSpUUkDo"

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_texts = {}

LANGUAGES = {
    "en": ("🇺🇸", "Английский"),
    "ru": ("🇷🇺", "Русский"),
    "de": ("🇩🇪", "Немецкий"),
    "fr": ("🇫🇷", "Французский"),
    "es": ("🇪🇸", "Испанский"),
    "it": ("🇮🇹", "Итальянский"),
    "zh": ("🇨🇳", "Китайский"),
    "ja": ("🇯🇵", "Японский"),
    "ko": ("🇰🇷", "Корейский"),
    "ar": ("🇸🇦", "Арабский"),
    "tr": ("🇹🇷", "Турецкий"),
    "pl": ("🇵🇱", "Польский"),
    "uk": ("🇺🇦", "Украинский"),
    "kk": ("🇰🇿", "Казахский"),
    "by": ("🇧🇾", "Белорусский"),
    "it": ("🇮🇹", "Итальянский"),
    "pt": ("🇵🇹", "Португальский"),
    "nl": ("🇳🇱", "Нидерландский"),
    "sv": ("🇸🇪", "Шведский"),
    "cs": ("🇨🇿", "Чешский"),
    "he": ("🇮🇱", "Иврит")
}

async def translate_text(text: str, target_lang: str) -> str:
    """
    Переводит текст через Bing. При сбое автоматически переключается на Google.
    """
    try:
        translated = await asyncio.to_thread(
            lambda: ts.translate_text(text, from_language='auto', to_language=target_lang, translator='bing')
        )
        if translated:
            return translated
    except Exception as e:
        print(f"[Резерв] Bing не ответил, пробую Google: {e}")

    try:
        translated = await asyncio.to_thread(
            lambda: ts.translate_text(text, from_language='auto', to_language=target_lang, translator='google')
        )
        if translated:
            return translated
    except Exception as e:
        print(f"[Критическая ошибка] Все сервера заняты: {e}")
        
    return "ошибка_перевода"

def get_language_keyboard():
    builder = InlineKeyboardBuilder()
    for code, (emoji, name) in LANGUAGES.items():
        # callback_data теперь формируется автоматически, например: "to_lang:en"
        builder.add(types.InlineKeyboardButton(text=f"{emoji} {name}", callback_data=f"to_lang:{code}"))
    
    # adjust(3) выстраивает кнопки в красивую сетку по 3 штуки в строке
    builder.adjust(3)
    return builder.as_markup()

# Обработчик команды /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я продвинутый бот-переводчик. Поддерживаю более 20 языков мира!\n\n"
        "Напиши мне любой текст, а затем выбери язык для перевода на клавиатуре ниже:",
        reply_markup=get_language_keyboard()
    )

# Обработчик входящего текста
@dp.message()
async def handle_text(message: types.Message):
    if not message.text:
        return
        
    # Запоминаем текст пользователя по его ID
    user_texts[message.from_user.id] = message.text
        
    await message.answer(
        "Текст получен. На какой язык его перевести? Выберите из списка:", 
        reply_markup=get_language_keyboard()
    )

# один обработчик для 21 го языка
@dp.callback_query(F.data.startswith("to_lang:"))
async def handle_translation_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    text_to_translate = user_texts.get(user_id, "")
    
    if not text_to_translate:
        await callback.message.edit_text("Сначала отправьте текст обычным сообщением в чат.")
        await callback.answer()
        return

    # Достаем код выбранного языка из callback_data
    target_lang = callback.data.split(":")[1]
    emoji, lang_name = LANGUAGES.get(target_lang, ("🌐", "Выбранный язык"))

    await callback.message.edit_text(f"⏳ Перевожу на {lang_name.lower()}...")
    
    # Запускаем перевод
    translated = await translate_text(text_to_translate, target_lang=target_lang)
    
    if translated == "ошибка_перевода":
        await callback.message.edit_text(
            "⚠️ Не удалось подключиться к серверам перевода. Попробуйте нажать кнопку еще раз."
        )
    else:
        await callback.message.edit_text(
            f"{emoji} **Перевод на {lang_name.lower()}:**\n\n{translated}", 
            parse_mode="Markdown"
        )
    await callback.answer()

# Главная функция запуска
async def main():
    print("Бот успешно запущен! Доступен 21 язык для перевода.")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
