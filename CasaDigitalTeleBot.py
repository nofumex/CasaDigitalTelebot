from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, ConversationHandler, filters
)
from flask import Flask, request
import threading

from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MANAGER_CHAT_ID = int(os.getenv("MANAGER_CHAT_ID"))

PROMO, GET_NAME, GET_CONTACT, SELECT_SERVICE, CUSTOM_SERVICE = range(5)

flask_app = Flask(__name__)

@flask_app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return {"status": "no data"}, 400

    name = data.get("name")
    contact = data.get("contact")
    service = data.get("service")
    message = data.get("message")

    telegram_text = (
        f"🌐 Новая заявка с сайта:\n\n"
        f"👤 Имя: {name}\n"
        f"📞 Контакт: {contact}\n"
        f"📦 Услуга: {service}\n"
        f"📝 О проекте: {message}"
    )

    import requests
    requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage", params={
        "chat_id": MANAGER_CHAT_ID,
        "text": telegram_text
    })

    return {"status": "ok"}, 200

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🔥 Добро пожаловать в Casa Digital — агентство, которое помогает бизнесу расти и развиваться!\n\n"
        "📈 Мы создаём не просто сайты — мы строим инструменты для развития:\n\n"
        "🔹 Разработка сайтов\n"
        "🔹 Контекстная реклама\n"
        "🔹 Брендинг\n"
        "🔹 Digital-маркетинг\n\n"
        "Выберите, с чего начнём 👇"
    )
    keyboard = [
        [InlineKeyboardButton("🎁 Ввести промокод", callback_data="promo")],
        [InlineKeyboardButton("💬 Консультация", callback_data="consult")],
        [InlineKeyboardButton("📦 Выбор услуги", callback_data="services")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_html(welcome_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if query.data == "promo":
        await query.message.reply_text("Введите ваш промокод:")
        return PROMO

    elif query.data == "consult":
        has_discount = context.user_data.get("has_discount", False)
        await query.message.reply_text(
            "💡 Вы получили бесплатную консультацию!\nНаш менеджер скоро свяжется с вами."
        )
        await context.bot.send_message(
            chat_id=MANAGER_CHAT_ID,
            text=(
                f"🚨 Новый запрос на консультацию!\n"
                f"👤 Пользователь: @{user.username or 'Без username'} (ID: {user.id})\n"
                f"Скидка активирована: {'Да' if has_discount else 'Нет'}"
            )
        )
        return ConversationHandler.END

    elif query.data == "services":
        await show_services(update, context)
        return ConversationHandler.END

    elif query.data == "apply":
        await query.message.reply_text("Как вас зовут?")
        return GET_NAME

async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    services_text = (
        "📦 <b>Наши услуги:</b>\n\n"
        "🖥️ <b>Разработка сайтов</b>\n"
        "Современные, быстрые и конвертирующие веб-сайты\n"
        "— Адаптивный дизайн\n— SEO-оптимизация\n— Быстрая загрузка\n\n"
        "🎯 <b>Контекстная реклама</b>\n"
        "Реклама в Google и Яндекс\n"
        "— Google Ads\n— Яндекс.Директ\n— Аналитика ROI\n\n"
        "🎨 <b>Брендинг</b>\n"
        "Уникальный фирменный стиль\n"
        "— Логотип\n— Фирменный стиль\n\n"
        "📢 <b>Digital-маркетинг</b>\n"
        "Комплексное продвижение\n"
        "— SMM\n— Email-маркетинг\n— Контент-стратегия"
    )
    keyboard = [[InlineKeyboardButton("✍️ Подать заявку", callback_data="apply")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_html(services_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_html(services_text, reply_markup=reply_markup)

async def handle_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip().upper()
    if code == "WELCOME10":
        await update.message.reply_text("🎉 Промокод принят! Вы получили скидку 10%.")
        context.user_data["has_discount"] = True
        await show_services(update, context)  # Показываем услуги сразу после промокода
    else:
        await update.message.reply_text(
            "❗ Такой промокод не найден.\n"
            "Ищите действующие предложения на нашем сайте: https://casadigital.ru/"
        )
        context.user_data["has_discount"] = False
    return ConversationHandler.END

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Оставьте контакт: номер телефона или email")
    return GET_CONTACT

async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["contact"] = update.message.text
    keyboard = [
        [KeyboardButton("Разработка сайта"), KeyboardButton("Контекстная реклама")],
        [KeyboardButton("Брендинг"), KeyboardButton("Digital-маркетинг")],
        [KeyboardButton("Другое")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Выберите услугу:", reply_markup=reply_markup)
    return SELECT_SERVICE

async def get_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Другое":
        await update.message.reply_text("Пожалуйста, напишите, какую услугу вы хотите заказать:", reply_markup=ReplyKeyboardRemove())
        return CUSTOM_SERVICE
    else:
        context.user_data["service"] = text
        return await finish_application(update, context)

async def get_custom_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["service"] = update.message.text
    return await finish_application(update, context)

async def finish_application(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data.get("name")
    contact = context.user_data.get("contact")
    service = context.user_data.get("service")
    user = update.message.from_user
    has_discount = context.user_data.get("has_discount", False)

    text = (
        f"📝 Новая заявка из Telegram:\n\n"
        f"👤 Имя: {name}\n"
        f"📞 Контакт: {contact}\n"
        f"📦 Услуга: {service}\n\n"
        f"👤 Пользователь: @{user.username or 'Без username'} (ID: {user.id})\n"
        f"Скидка активирована: {'Да' if has_discount else 'Нет'}"
    )

    await context.bot.send_message(chat_id=MANAGER_CHAT_ID, text=text)
    await update.message.reply_text("✅ Спасибо! Ваша заявка отправлена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def run_flask():
    flask_app.run(port=8000)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler)],
        states={
            PROMO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_promo)],
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GET_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            SELECT_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_service)],
            CUSTOM_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_custom_service)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    threading.Thread(target=run_flask).start()

    print("✅ Бот запущен. Ожидаем пользователей...")
    app.run_polling()

if __name__ == "__main__":
    main()
