import os
import csv
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ================== ENV ==================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# ================== HELPERS ==================
def safe_text(text: str, limit: int = 4000) -> str:
    """Telegram-safe message length"""
    if not text:
        return ""
    return text[:limit]

# ================== DATA ==================
BRANCHES = {
    "CHALBAR ЗАГС": "chalbar_zags.csv",
    "CHALBAR ЦЕНТР": "chalbar_center.csv",
}

POSITIONS = [
    "Официант",
    "Бармен",
    "Повар",
    "Хостес",
    "Кальян-мастер",
    "Менеджер смены",
    "Раннер",
    "Другое",
]

# ================== STATES ==================
(
    NAME,
    AGE,
    CONTACTS,
    POSITION,
    EXPERIENCE,
    STUDY,
    PLACE,
    BRANCH,
    CONFIRM,
) = range(9)

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "👋 Привет! Это *CHALBAR | Вакансии*\n\n"
        "🤗 Как тебя зовут?",
        parse_mode="Markdown"
    )
    return NAME

# ================== FLOW ==================
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("🎂 Сколько тебе лет?")
    return AGE



async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text.strip()

    keyboard = [
        [KeyboardButton("📱 Отправить номер", request_contact=True)],
        [KeyboardButton("📨 Оставить Telegram")]
    ]

    await update.message.reply_text(
        "😉 Оставь свой номер или Telegram. Мы ведь не хотим тебя потерять",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return CONTACTS


async def get_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Если отправили номер через кнопку
    if update.message.contact:
        context.user_data["contacts"] = update.message.contact.phone_number

    # Если нажали кнопку Telegram
    elif update.message.text == "📨 Оставить Telegram":
        username = update.effective_user.username

        if username:
            context.user_data["contacts"] = f"@{username}"
        else:
            await update.message.reply_text(
                "У тебя не указан username 😔\n"
                "Напиши его вручную (пример: @example)"
            )
            return CONTACTS

    # Если просто написали текст вручную
    else:
        context.user_data["contacts"] = update.message.text.strip()

    keyboard = [[p] for p in POSITIONS]
    await update.message.reply_text(
        "😌 Какая должность тебе интересна?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return POSITION


async def get_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["position"] = update.message.text.strip()
    await update.message.reply_text(
        "😎 Расскажи про свой опыт работы",
        reply_markup=ReplyKeyboardRemove()
    )
    return EXPERIENCE


async def get_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["experience"] = update.message.text.strip()

    await update.message.reply_text(
        "🎓 Учишься ли ты? Если да — очно или заочно?"
    )

    return STUDY


async def get_study(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["study"] = update.message.text.strip()

    await update.message.reply_text(
        "🏠 Где территориально проживаешь?"
    )

    return PLACE


async def get_place(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["place"] = update.message.text.strip()

    keyboard = [[b] for b in BRANCHES.keys()]

    await update.message.reply_text(
        "📍 В каком филиале тебе будет комфортно работать?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

    return BRANCH


async def get_branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    branch = update.message.text.strip()
    context.user_data["branch"] = branch

    text = (
    "📋 *Проверь анкету:*\n\n"
    f"👤 Имя: {context.user_data['name']}\n"
    f"🎂 Возраст: {context.user_data['age']}\n"
    f"📞 Контакты: {context.user_data['contacts']}\n"
    f"💼 Должность: {context.user_data['position']}\n"
    f"😎 Опыт: {context.user_data['experience']}\n"
    f"🎓 Учёба: {context.user_data['study']}\n"
    f"🏠 Проживание: {context.user_data['place']}\n"
    f"📍 Филиал: {branch}\n\n"
    "Отправляем?"
)

    keyboard = [["Да", "Нет"]]
    await update.message.reply_text(
        safe_text(text),
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return CONFIRM

# ================== CONFIRM ==================
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.message.text.lower().strip()

    if answer != "да":
        await update.message.reply_text(
            "❌ Анкета отменена. Напиши /start чтобы начать заново.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    branch = context.user_data["branch"]
    filename = BRANCHES.get(branch)

    # ---- SAVE TO CSV ----
    if filename:
        with open(filename, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
    context.user_data["name"],
    context.user_data["age"],
    context.user_data["contacts"],
    context.user_data["position"],
    context.user_data["experience"],
    context.user_data["study"],
    context.user_data["place"],
    branch,
])

    # ---- SEND TO HR ----
    hr_text = (
    f"📋 *Новая анкета ({branch})*\n\n"
    f"👤 Имя: {context.user_data['name']}\n"
    f"🎂 Возраст: {context.user_data['age']}\n"
    f"📞 Контакты: {context.user_data['contacts']}\n"
    f"💼 Должность: {context.user_data['position']}\n"
    f"😎 Опыт: {context.user_data['experience']}\n"
    f"🎓 Учёба: {context.user_data['study']}\n"
    f"🏠 Проживание: {context.user_data['place']}"
)

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=safe_text(hr_text),
        parse_mode="Markdown"
    )

    await update.message.reply_text(
        "✅ Анкета отправлена! HR свяжется с тобой 👌",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Отменено. Напиши /start",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ================== MAIN ==================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
       states={
    NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
    AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
    CONTACTS: [
        MessageHandler(filters.CONTACT, get_contacts),
        MessageHandler(filters.TEXT & ~filters.COMMAND, get_contacts),
    ],
    POSITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_position)],
    EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_experience)],
    STUDY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_study)],
    PLACE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_place)],
    BRANCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_branch)],
    CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
},
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    print("🤖 CHALBAR HR BOT запущен")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
