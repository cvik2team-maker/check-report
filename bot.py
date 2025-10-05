import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

BOT_TOKEN = '8320156225:AAHJNhtShgxaSKwMiwArEM_aN9w5R1qM2T4'
CONTACT_USER_ID = 782807882  # Replace with Telegram user ID of contact

logging.basicConfig(level=logging.INFO)
user_notes = {}

def build_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data="approve"),
            InlineKeyboardButton("⚠️ Error", callback_data="error"),
            InlineKeyboardButton("❓ Ask Details", callback_data="ask"),
        ],
        [
            InlineKeyboardButton("✏️ Edit", callback_data="edit"),
            InlineKeyboardButton("📄 Attach Note", callback_data="note"),
            InlineKeyboardButton("➡️ Send for Approval", callback_data="send"),
        ]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a message to forward!")

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text
    # Forward to contact with inline buttons
    sent = await context.bot.send_message(
        CONTACT_USER_ID,
        f"Forwarded message from @{update.message.from_user.username or update.message.from_user.first_name}:\n{msg}",
        reply_markup=build_buttons()
    )
    # Track who sent what (for sending status back)
    context.chat_data[sent.message_id] = update.message.chat_id

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    sender_chat_id = context.chat_data.get(query.message.message_id)

    if query.data == "approve":
        await query.answer("Approved!")
        if sender_chat_id:
            await context.bot.send_message(sender_chat_id, "✅ Approved: " + query.message.text)
    elif query.data == "error":
        await query.answer("Marked as error, pending review.")
        if sender_chat_id:
            await context.bot.send_message(sender_chat_id, "⚠️ Error, pending review: " + query.message.text)
    elif query.data == "ask":
        await query.answer("Requesting details or note.")
        if sender_chat_id:
            await context.bot.send_message(sender_chat_id, "❓ Please provide more details or write a note. (Status: Pending, not clear)")
    elif query.data == "edit":
        await query.answer("Request to edit.")
        if sender_chat_id:
            await context.bot.send_message(sender_chat_id, "✏️ Please edit and correct your message.")
    elif query.data == "note":
        await query.answer("Attach a note (reply to this message).")
        user_notes[query.message.message_id] = sender_chat_id
        await context.bot.send_message(CONTACT_USER_ID, "📄 Please reply to this message with your note to attach.")
    elif query.data == "send":
        await query.answer("Sending back for approval.")
        if sender_chat_id:
            await context.bot.send_message(sender_chat_id, "➡️ Sent back for approval.")

async def attach_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only allow replies to messages that requested a note
    if update.message.reply_to_message:
        orig_msg_id = update.message.reply_to_message.message_id
        sender_chat_id = user_notes.get(orig_msg_id)
        if sender_chat_id:
            await context.bot.send_message(sender_chat_id, f"📄 Note attached: {update.message.text}")
            del user_notes[orig_msg_id]

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), forward_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.REPLY & filters.TEXT, attach_note))
    app.run_polling()

if __name__ == "__main__":
    main()
