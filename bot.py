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

# ================== НАСТРОЙКИ ==================
import os

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))


BRANCHES = {
    "CHALBAR ЗАГС": "chalbar_zags.csv",
    "CHALBAR СИПА": "chalbar_sipa.csv",
    "CHALBAR ЦЕНТР": "chalbar_center.csv",
}

POSITIONS = [
    "Официант",
    "Бармен",
    "Повар",
    "Хостес",
    "Кальян-мастер",
    "Менеджер смены",
    "Другое",
]

# ================== СОСТОЯНИЯ ==================
(
    NAME,
    AGE,
    CONTACTS,
    POSITION,
    EXPERIENCE,
    STUDY,
    BRANCH,
    CONFIRM,
) = range(8)

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "👋 Привет! Это CHALBAR | Вакансии\n\n"
        "🤗 Как тебя зовут?"
    )
    return NAME


# ================== ВОПРОСЫ ==================
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("🎂 Сколько тебе лет?")
    return AGE


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["age"] = update.message.text

    keyboard = [[KeyboardButton("📱 Отправить номер", request_contact=True)]]
    await update.message.reply_text(
        "😉 Оставь свой номер. Мы ведь не хотим тебя потерять",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return CONTACTS


async def get_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        context.user_data["contacts"] = update.message.contact.phone_number
    else:
        context.user_data["contacts"] = update.message.text

    keyboard = [[p] for p in POSITIONS]
    await update.message.reply_text(
        "😌 Какая должность тебе интересна?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return POSITION


async def get_position(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Другое":
        await update.message.reply_text(
            "✍️ Напиши, пожалуйста, какую должность ты имеешь в виду",
            reply_markup=ReplyKeyboardRemove()
        )
        return POSITION

    context.user_data["position"] = text
    await update.message.reply_text(
        "😎 Расскажи про свой опыт работы",
        reply_markup=ReplyKeyboardRemove()
    )
    return EXPERIENCE


async def get_experience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["experience"] = update.message.text
    await update.message.reply_text(
        "🤔 Учишься ли ты? Если да, то как: очно / заочно"
    )
    return STUDY


async def get_study(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["study"] = update.message.text

    keyboard = [[b] for b in BRANCHES.keys()]
    await update.message.reply_text(
        "📍 В каком филиале тебе будет комфортно работать?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return BRANCH


async def get_branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    branch = update.message.text

    if branch not in BRANCHES:
        await update.message.reply_text("❌ Выбери филиал кнопкой")
        return BRANCH

    context.user_data["branch"] = branch

    text = (
        "📝 Проверь анкету:\n\n"
        f"Имя: {context.user_data['name']}\n"
        f"Возраст: {context.user_data['age']}\n"
        f"Контакты: {context.user_data['contacts']}\n"
        f"Должность: {context.user_data['position']}\n"
        f"Опыт: {context.user_data['experience']}\n"
        f"Учёба: {context.user_data['study']}\n"
        f"Филиал: {branch}\n\n"
        "Отправляем?"
    )

    keyboard = [["Да", "Нет"]]
    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return CONFIRM


# ================== CONFIRM ==================
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text != "Да":
        await update.message.reply_text(
            "❌ Анкета отменена. Напиши /start",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    filename = BRANCHES[context.user_data["branch"]]

    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            context.user_data["name"],
            context.user_data["age"],
            context.user_data["contacts"],
            context.user_data["position"],
            context.user_data["experience"],
            context.user_data["study"],
        ])

    hr_text = (
        "📋 Новая анкета\n\n"
        f"Имя: {context.user_data['name']}\n"
        f"Возраст: {context.user_data['age']}\n"
        f"Контакты: {context.user_data['contacts']}\n"
        f"Должность: {context.user_data['position']}\n"
        f"Опыт: {context.user_data['experience']}\n"
        f"Учёба: {context.user_data['study']}\n"
        f"Филиал: {context.user_data['branch']}"
    )

    await context.bot.send_message(chat_id=ADMIN_ID, text=hr_text)

    await update.message.reply_text(
        "✅ Анкета отправлена! HR свяжется с тобой 👌",
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
            BRANCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_branch)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
        },
        fallbacks=[],
    )

    app.add_handler(conv)
    print("🤖 HR-бот CHALBAR запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()


