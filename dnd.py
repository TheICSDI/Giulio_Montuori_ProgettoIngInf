import logging
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, MessageHandler

TOKEN = '5856331893:AAGotmP4Ws9jX4aowvi13JkfUlIQZH1uYfI'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Ciaoo, il bot è in fase di costruzione")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if(len(context.args) == 0):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Niente da rendere maiuscolo")

    else:
        text_caps = ' '.join(context.args).upper()
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)
        #await context.bot.send_message(chat_id=update.effective_chat.id, text=str(len(context.args))) conta il numero di argomenti

async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    num = random.randint(1, 20)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=str(num))
    

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    caps_handler = CommandHandler('caps', caps)
    roll_handler = CommandHandler('roll', roll)

    
    application.add_handler(start_handler)
    application.add_handler(echo_handler)
    application.add_handler(caps_handler)
    application.add_handler(roll_handler)
    
    application.run_polling()
