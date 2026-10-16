import os
import asyncio
from datetime import datetime, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL = "@henicreatives"

# Your Telegram ID will be added later
ADMIN_ID = os.getenv("ADMIN_ID")

orders = {}
user_data = {}
order_number = 1000


async def is_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not await is_member(user.id, context):
        keyboard = [
            [InlineKeyboardButton(
                "📢 Join Heni Creative Studio",
                url="https://t.me/henicreatives"
            )],
            [InlineKeyboardButton(
                "✅ I've Joined",
                callback_data="check_member"
            )]
        ]

        await update.message.reply_text(
            "👋 Welcome to Heni Creative Studio!\n\n"
            "To use this bot, please join our Telegram channel first.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await show_main_menu(update, context)


async def show_main_menu(update, context):
    keyboard = [
        [
            InlineKeyboardButton("🖼️ Poster", callback_data="design_poster"),
            InlineKeyboardButton("📱 Social Media", callback_data="design_social"),
        ],
        [
            InlineKeyboardButton("🎂 Birthday", callback_data="design_birthday"),
            InlineKeyboardButton("💒 Wedding", callback_data="design_wedding"),
        ],
        [
            InlineKeyboardButton("⛪ Church", callback_data="design_church"),
            InlineKeyboardButton("🎵 Music Cover", callback_data="design_music"),
        ],
        [
            InlineKeyboardButton("🏢 Business", callback_data="design_business"),
            InlineKeyboardButton("✨ Custom", callback_data="design_custom"),
        ],
    ]

    text = (
        "🎨 Heni Creative Studio\n\n"
        "Welcome! What type of design do you need?"
    )

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global order_number

    query = update.callback_query
    await query.answer()

    user = query.from_user

    # Check channel membership
    if query.data == "check_member":
        if await is_member(user.id, context):
            await query.edit_message_text(
                "✅ Membership verified!\n\n"
                "Welcome to Heni Creative Studio 🎨"
            )
            await show_main_menu_from_query(query)
        else:
            await query.answer(
                "❌ You haven't joined the channel yet.",
                show_alert=True
            )
        return

    # Design selection
    if query.data.startswith("design_"):
        design = query.data.replace("design_", "").title()

        user_data[user.id] = {
            "design": design,
            "step": "description"
        }

        await query.edit_message_text(
            f"🎨 Design selected: {design}\n\n"
            "📝 Now send me the text/details you want on the design.\n\n"
            "Example:\n"
            "Name: Heni\n"
            "Event: Birthday\n"
            "Date: September 18"
        )
        return

    # Deadline selection
    if query.data.startswith("time_"):
        hours = int(query.data.replace("time_", ""))

        if user.id not in user_data:
            return

        user_data[user.id]["hours"] = hours

        global order_number
        order_number += 1
        order_id = f"HC-{order_number}"

        deadline = datetime.now() + timedelta(hours=hours)

        order = {
            "id": order_id,
            "user_id": user.id,
            "username": user.username or user.first_name,
            "design": user_data[user.id]["design"],
            "description": user_data[user.id].get("description", ""),
            "hours": hours,
            "deadline": deadline,
            "status": "Pending",
        }

        orders[order_id] = order

        await query.edit_message_text(
            f"✅ Order received!\n\n"
            f"🆔 Order ID: #{order_id}\n"
            f"🎨 Design: {order['design']}\n"
            f"⏰ Delivery time: {hours} hours\n"
            f"📌 Status: Pending\n\n"
            "We will contact you when your design is ready. 🙏"
        )

        # Send order to admin if ADMIN_ID is configured
        if ADMIN_ID:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔵 Start",
                        callback_data=f"startorder_{order_id}"
                    ),
                    InlineKeyboardButton(
                        "✅ Complete",
                        callback_data=f"complete_{order_id}"
                    ),
                ]
            ]

            await context.bot.send_message(
                chat_id=int(ADMIN_ID),
                text=(
                    "🆕 NEW DESIGN ORDER\n\n"
                    f"🆔 #{order_id}\n"
                    f"👤 Customer: @{order['username']}\n"
                    f"🎨 Design: {order['design']}\n"
                    f"⏰ Deadline: {hours} hours\n"
                    f"📝 Details:\n{order['description']}"
                ),
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        return

    # Admin order controls
    if query.data.startswith("startorder_"):
        order_id = query.data.replace("startorder_", "")

        if order_id in orders:
            orders[order_id]["status"] = "In Progress"

            await query.edit_message_text(
                f"🔵 Order #{order_id}\n\n"
                "Status: In Progress"
            )
        return

    if query.data.startswith("complete_"):
        order_id = query.data.replace("complete_", "")

        if order_id in orders:
            orders[order_id]["status"] = "Completed"

            customer_id = orders[order_id]["user_id"]

            await query.edit_message_text(
                f"✅ Order #{order_id}\n\n"
                "Status: Completed"
            )

            await context.bot.send_message(
                chat_id=customer_id,
                text=(
                    f"🎉 Your design is ready!\n\n"
                    f"🆔 Order #{order_id}\n\n"
                    "Please contact Heni Creative Studio to receive your design."
                )
            )


async def show_main_menu_from_query(query):
    keyboard = [
        [
            InlineKeyboardButton("🖼️ Poster", callback_data="design_poster"),
            InlineKeyboardButton("📱 Social Media", callback_data="design_social"),
        ],
        [
            InlineKeyboardButton("🎂 Birthday", callback_data="design_birthday"),
            InlineKeyboardButton("💒 Wedding", callback_data="design_wedding"),
        ],
        [
            InlineKeyboardButton("⛪ Church", callback_data="design_church"),
            InlineKeyboardButton("🎵 Music Cover", callback_data="design_music"),
        ],
        [
            InlineKeyboardButton("🏢 Business", callback_data="design_business"),
            InlineKeyboardButton("✨ Custom", callback_data="design_custom"),
        ],
    ]

    await query.message.reply_text(
        "🎨 Choose your design:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in user_data:
        await update.message.reply_text(
            "Please use /start to begin your order."
        )
        return

    data = user_data[user.id]

    if data.get("step") == "description":
        data["description"] = update.message.text
        data["step"] = "photo"

        await update.message.reply_text(
            "📷 Now send the photo you want to use in the design.\n\n"
            "If you don't need a photo, send /skip"
        )

    elif data.get("step") == "photo":
        await update.message.reply_text(
            "📷 Please send a photo or type /skip."
        )


async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in user_data:
        return

    user_data[user.id]["step"] = "time"

    keyboard = [
        [
            InlineKeyboardButton("⚡ 6 Hours", callback_data="time_6"),
            InlineKeyboardButton("🕐 12 Hours", callback_data="time_12"),
        ],
        [
            InlineKeyboardButton("📅 24 Hours", callback_data="time_24"),
        ],
    ]

    await update.message.reply_text(
        "⏰ In how many hours do you need your design?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id not in user_data:
        return

    if user_data[user.id].get("step") != "photo":
        return

    photo = update.message.photo[-1]

    user_data[user.id]["photo_file_id"] = photo.file_id
    user_data[user.id]["step"] = "time"

    keyboard = [
        [
            InlineKeyboardButton("⚡ 6 Hours", callback_data="time_6"),
            InlineKeyboardButton("🕐 12 Hours", callback_data="time_12"),
        ],
        [
            InlineKeyboardButton("📅 24 Hours", callback_data="time_24"),
        ],
    ]

    await update.message.reply_text(
        "✅ Photo received!\n\n"
        "⏰ In how many hours do you need your design?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is missing.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("skip", skip_photo))

    app.add_handler(CallbackQueryHandler(button_handler))

    app.add_handler(
        MessageHandler(filters.PHOTO, photo_handler)
    )

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
    )

    print("🤖 Heni Creative Studio Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
