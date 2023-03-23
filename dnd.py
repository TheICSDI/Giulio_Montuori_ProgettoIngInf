import logging
import json
import random
from datetime import datetime, timedelta
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, filters, MessageHandler, CallbackQueryHandler, Application, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, CallbackQuery

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
    username = update.message.from_user.username
    # party_id = isInvited(username)

    await update.message.reply_text("Benvenuto su D&D 5e Telegram bot!\nScrivi /help per più imformazioni su come giocare \U0001F604.")

    if party_id:
        keyboard = [
            [
                InlineKeyboardButton("Si", callback_data=len(party_id)),
                InlineKeyboardButton("No", callback_data="no"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text("Sei stato invitato in un party\U0001F604.\nVuoi entrare nel party?", reply_markup=reply_markup)


async def help_command(update: Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("TODO")

async def create_party(update: Update, context:ContextTypes.DEFAULT_TYPE): #il creatore del party satà automaticamente il DM
    chat_id = update.message.chat_id
    party_id, isMaster = getParty_isMaster(chat_id)

    if party_id is None:
        party_id = dnd_data["parties"][-1]["id"] + 1
        build_party(chat_id, party_id)
        await update.message.reply_text(f"Party creato! Adesso sei il manster del party di id {party_id}!.\nCondividi l'id del perty per far entre altri giocatori o invitali con /invite <@username>.")
        return

    else:
        await update.message.reply_text("Fai già parte di un party.\nRicorda puoi partecipare solo ad un party alla volta.")
        await update.message.reply_text("Se desideri uscire prova il comando /exit")


"""
async def join_party(update:Update, context:ContextTypes.DEFAULT_TYPE): #il creatore del party sarà il DM
    if len(context.args) == 0:
        await update.message.reply_text("Per entrare in un party devi inserire il suo ID.\nRiprova con il comando /join_party <party_id>.")
        return

    chat_id = update.message.chat_id
    party_id, isMaster = getParty_isMaster(chat_id)

    if party_id is None:
        party_id = context.args[0]
        reply = join(chat_id, party_id)
        await update.message.reply_text(reply)
        return

    else:
        await update.message.reply_text("Fai già parte di un party.\nRicorda puoi partecipare solo ad un party alla volta.")
        await update.message.reply_text("Se desideri uscire prova il comando /exit")
"""

async def accept_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Per accettare un invito, inserisci il codice di invito.\nRiprova con il comando /accept_invite <invite_code>.")
        return

    chat_id = update.message.chat_id
    name = update.message.from_user.full_name
    invite_code = int(context.args[0])
    party_id, reply = join_with_invite(chat_id, invite_code)
    await update.message.reply_text(reply)

    if party_id > 0:
        dm_id = get_dm_id(party_id)
        await context.bot.send_message(chat_id=dm_id, text=f"L'utente @{name} è appena entrato nel tuo party.")



async def remove_player(update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    reply = remove(chat_id)
    await update.message.reply_text(reply)


async def send_invite(update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if len(context.args) == 0:
        await update.message.reply_text("Per mandare un invito devi specificare l'username dell'utente.\nInvita l'utente usando il comando /invite <@username>")
        return

    party_id, isMaster = getParty_isMaster(chat_id)

    if party_id is None:
        await update.message.reply_text("Devi essere in un party per mandare inviti.")
        return

    if isMaster is False:
        await update.message.reply_text("Solo il Master può mandare inviti.")
        return

    usr_invite = context.args[0]
    if usr_invite.startswith('@') is False:
        await update.message.reply_text("L'username non è valido.\nPerfavore inserisci un username valido del tipo <@username>")
        return

    usr_invite = usr_invite[1:]   #rimuove @
    if checkInvite(usr_invite, party_id) is True:
        await update.message.reply_text(f"l'utente {usr_invite} è già stato invitato in questo party.\nSe l'utente non trova l'invito può usare il comando /s # converto in stringahow_invites.")
        return

    invite_code = dnd_data["invites"][-1]["invite_code"] + 1
    expiration_time = datetime.now() + timedelta(hours=48) # imposto la scadenza dell'invito a 2 giorni
    expiration_time = expiration_time.strftime("%d/%m/%Y %H:%M:%S") # converto in stringa

    new_invite = {
        "invite_code": invite_code,
        "expiration": expiration_time,
        "party_id": party_id,
        "username": usr_invite,
    }
    dnd_data["invites"].append(new_invite)
    save_data()

    await update.message.reply_text(f"L'utente @{usr_invite} è stato invitato correttamente.\nRiceverà l'invito all'avvio del bot tramite /start o con il comando /show_invites")

async def show_invites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.from_user.username
    invites = get_invites_for_user(username)

    if not invites:
        await update.message.reply_text("Non hai inviti in sospeso.")
        return

    invite_message = "Hai ricevuto i seguenti inviti:\n"
    for invite in invites:
        invite_code = invite["invite_code"]
        party_id = invite["party_id"]
        invite_message += f"Party ID: {party_id}, Codice Invito: {invite_code}\n"

    invite_message += "Usa il comando /accept_invite <invite_code> per unirti al party desiderato."
    await update.message.reply_text(invite_message)



async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if(len(context.args) == 0):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Niente da rendere maiuscolo")

    else:
        text_caps = ' '.join(context.args).upper()
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)
        # await context.bot.send_message(chat_id=update.effective_chat.id, text=str(len(context.args))) conta il numero di argomenti
"""
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.callback_query.from_user.id
    # username = update.callback_query.from_user.username

    # Commenti ufficiali di PTB
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    result = query.data
    if result == "no":
        await query.edit_message_text(text="Invito rifiutato.")

    if len(result) == 4:
        join(chat_id, int(result))
        await query.edit_message_text(text="Invito accettato.\nSei stato aggiunto al party.") #TODO inserire il party_id
        return
"""

async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    num = random.randint(1, 20)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=str(num))

def getParty_isMaster(chat_id):

    for party in dnd_data["parties"]:
        for member in party["members"]:
            if member["chat_id"] == chat_id:
                return party["id"], member["master"]

    return None, False

def checkInvite(username, party_id):

    for invite in dnd_data["invites"]:
        if username == invite["username"] and party_id == invite["party_id"]:
            return True

    return False

def join(chat_id, party_id):

    for party in dnd_data["parties"]:
        if party["id"] == party_id:
            for member in party["members"]:
                if member["chat_id"] == chat_id:
                    return 0, "Fai già parte di questo party."

            party["members"].append({
                "chat_id": chat_id,
                "character": None,
                "master": False,
            })
            save_data()
            return party_id, f"Unito con successo al party {party_id}!"

    return 0, "Party ID non valido. Per favore controlla l'ID e riprova."

def join_with_invite(chat_id, invite_code):

    for invite in dnd_data["invites"]:
        if invite["invite_code"] == invite_code:
            expiration_time = datetime.strptime(invite["expiration"], "%d/%m/%Y %H:%M:%S")
            if datetime.now() > expiration_time:
                dnd_data["invites"].remove(invite)
                save_data()
                return 0, "Il codice di invito è scaduto. Chiedi al Master del party di generare un nuovo invito."

            party_id = invite["party_id"]
            dnd_data["invites"].remove(invite)
            save_data()
            return join(chat_id, party_id)

    return 0, "Codice di invito non valido."

def build_party(chat_id, party_id):

    new_party = {
        "id": party_id,
        "members": [
            {
                "chat_id": chat_id,
                "character": None,
                "master": True,
            }
        ]
    }
    dnd_data["parties"].append(new_party)
    save_data()

def remove(chat_id):

    for party in dnd_data["parties"]:
        for member in party["members"]:
            if member["chat_id"] == chat_id and member["master"] is False:
                party["members"].remove(member)
                save_data()
                return "Rimosso con successo dal party!"

            if member["chat_id"] == chat_id and member["master"] is True:
                dnd_data["parties"].remove(party)
                save_data()
                return "Rimosso dal party e party elimitato con successo."


    return "Non sei presente in nessun party"

def get_invites_for_user(username):

    user_invites = []
    for invite in dnd_data["invites"]:
        if invite["username"] == username:
            user_invites.append(invite)
    return user_invites

def get_dm_id(party_id):
    for party in dnd_data["parties"]:
        if party_id == party["id"]:
            return party["members"][0]["chat_id"]

    return 0

if __name__ == '__main__':

    application = ApplicationBuilder().token(TOKEN).build()


    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('create', create_party))
    # application.add_handler(CommandHandler('join', join_party))
    application.add_handler(CommandHandler("accept_invite", accept_invite))
    application.add_handler(CommandHandler('remove', remove_player))
    application.add_handler(CommandHandler('send_invite', send_invite))
    application.add_handler(CommandHandler('show_invites', show_invites))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    application.add_handler(CommandHandler('caps', caps))
    application.add_handler(CommandHandler('roll', roll))
    # application.add_handler(CallbackQueryHandler(button))

    application.run_polling()
