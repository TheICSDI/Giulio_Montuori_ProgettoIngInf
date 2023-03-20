import logging
import json
import random
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, MessageHandler, CallbackQueryHandler, Application, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

TOKEN = '5856331893:AAGotmP4Ws9jX4aowvi13JkfUlIQZH1uYfI'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

with open("dnd_data.json", "r") as f:
    dnd_data = json.load(f)

def save_data():
    with open("dnd_data.json", "w") as f:
        json.dump(dnd_data, f, indent=2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    await update.message.reply_text("Benvenuto su D&D 5e Telegram bot!\nScrivi /help per più imformazioni su come giocare \U0001F604.")

async def help_command(update: Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("DA FARE")

async def create_party(update: Update, context:ContextTypes.DEFAULT_TYPE): #il creatore del party satà automaticamente il DM
    party_id = random.randint(1000, 9999)  #TODO DA MIGLIORARE
    chat_id = update.message.chat_id

    for party in dnd_data["parties"]:
        if party["id"] == party_id:
            await update.message.reply_text("Esiste un già un party con quel codice!\nSe vuoi unirti usa il comando /join {party_id}")
            return

    new_party = {
        "id": party_id,
        "members": [
            {
                "chat_id": chat_id,
                "character": context.user_data.get("character", None),
                "master": True,
            }
        ]
    }
    dnd_data["parties"].append(new_party)
    save_data()

    await update.message.reply_text(f"Party creato! Adesso sei il manster del party di id {party_id}!.\nCondividi l'id del perty per far entre altri giocatori o invitali con /invite <@username>.")

async def join_party(update:Update, context:ContextTypes.DEFAULT_TYPE): #il creatore del party sarà il DM
    if len(context.args) == 0:
        await update.message.reply_text("Please provide the party ID to join. Usage: /join_party <party_id>")

    party_id = int(context.args[0])
    chat_id = update.message.chat_id

    for party in dnd_data["parties"]:
        if party["id"] == party_id:
            for member in party["members"]:
                if member["chat_id"] == chat_id:
                    await update.message.reply_text("You are already a member of this party.")
                    return

            party["members"].append({
                "chat_id": chat_id,
                "character": context.user_data.get("character", None),
                "master": False,
            })
            save_data()
            await update.message.reply_text(f"Successfully joined party {party_id}!")
            return

    await update.message.reply_text("Invalid party ID. Please check the party ID and try again.")

async def remove_player(update:Update, context:ContextTypes.DEFAULT_TYPE): #per ora rimuove solo se stesso
    party_id = int(context.args[0])                                        #TODO poter rimuove un utente dal DM
    chat_id = update.message.chat_id

    for party in dnd_data["parties"]:
        if party["id"] == party_id:
            for member in party["members"]:
                if member["chat_id"] == chat_id:
                    party["members"].remove(member)
                    if len(party["members"]) == 0:
                        dnd_data["parties"].remove(party)
                        save_data()
                        await update.message.reply_text(f"Rimosso con successo dal party e party {party_id} elimitato")
                        return
                    
                    save_data()
                    await update.message.reply_text(f"Rimosso con successo dal party {party_id}!")
                    return
                
            await update.message.reply_text("Non sei presente in quel party")
            return
    await update.message.reply_text(f"Non esiste un party {party_id} come id")

async def send_invite(update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if len(context.args) == 0:
        await update.message.reply_text("Per mandare un invito devi specificare l'username dell'utente.\nInvita l'utente usando il comando /invite <@username>")
        return

    party_id, isMaster = getParty_isMaster(chat_id)

    if party_id == None:
        await update.message.reply_text("Devi essere in un party per mandare inviti.")
        return

    if isMaster == False:
        await update.message.reply_text("Solo il Master può mandare inviti.")
        return
    
    usr_invite = context.args[0]
    if usr_invite.startswith('@') == False:
        await update.message.reply_text("L'username non è valido.\nPerfavore inserisci un username valido del tipo <@username>")
        return

    usr_invite = usr_invite[1:]   #rimuove @

    new_invite = {
        "id": party_id["id"],
        "username": usr_invite,
    }
    dnd_data["invites"].append(new_invite)
    save_data()

    await update.message.reply_text(f"L'utente @{usr_invite} è stato invitato correttamente.\nRiceverà l'invito all'avvio del bot tramite /start o con il comando /show_invites")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if(len(context.args) == 0):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Niente da rendere maiuscolo")

    else:
        text_caps = ' '.join(context.args).upper()
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)
        #await context.bot.send_message(chat_id=update.effective_chat.id, text=str(len(context.args))) conta il numero di argomenti

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    await query.edit_message_text(text=f"Selected option: {query.data}")


async def scelta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Rosso \U0001F534", callback_data="\U0001F534"),
            InlineKeyboardButton("Blu \U0001F535", callback_data="\U0001F535"),
        ],
        [
            InlineKeyboardButton("Nero \U000026AB", callback_data="\U000026AB"),
            InlineKeyboardButton("Giallo \U0001F7E1", callback_data="\U0001F7E1"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Scegli un colore:", reply_markup=reply_markup)



async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    num = random.randint(1, 20)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=str(num))
    
def getParty_isMaster(chat_id):
    for party in dnd_data["parties"]:
        for member in party["members"]:
            if member["chat_id"] == chat_id:
                return party, member["master"]

    return None, False


if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    

    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('create', create_party))
    application.add_handler(CommandHandler('join', join_party))
    application.add_handler(CommandHandler('remove', remove_player))
    application.add_handler(CommandHandler('send_invite', send_invite))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    application.add_handler(CommandHandler('caps', caps))
    application.add_handler(CommandHandler('roll', roll))
    application.add_handler(CommandHandler('scelta', scelta))
    application.add_handler(CallbackQueryHandler(button))
    
    application.run_polling()
    

"""


# Party management functions


def list_party_members(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    party = None

    for p in dnd_data["parties"]:
        for member in p["members"]:
            if member["chat_id"] == chat_id:
                party = p
                break

    if party is None:
        update.message.reply_text("You are not a member of any party. Create a new party with /create_party or join an existing party with /join_party <party_id>.")
        return

    members_list = ""
    for member in party["members"]:
        character = member["character"]
        if character:
            members_list += f"{character['name']} ({character['race']} {character['class']})\n"
        else:
            members_list += "Unnamed character\n"

    update.message.reply_text(f"Party {party['id']} members:\n{members_list}")

# Add the new handlers to the main function

def main():
    # ...
    dispatcher.add_handler(CommandHandler("create_party", create_party))
    dispatcher.add_handler(CommandHandler("join_party", join_party))
    dispatcher.add_handler(CommandHandler("list_party_members", list_party_members))
    # ...a\

"""
