import logging
import json
import random
from datetime import datetime, timedelta
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    filters,
    MessageHandler,
    CallbackQueryHandler,
    Application,
    ConversationHandler
)
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)

TOKEN = '5856331893:AAGotmP4Ws9jX4aowvi13JkfUlIQZH1uYfI'
SELECT, TEST = range(2)

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
    # username = update.message.from_user.username
    # party_id = isInvited(username)

    await update.message.reply_text("Benvenuto su D&D 5e Telegram bot!\nScrivi /help per più imformazioni su come giocare \U0001F604.")


async def help_command(update: Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("TODO")


async def create_party(update: Update, context:ContextTypes.DEFAULT_TYPE): #il creatore del party satà automaticamente il DM
    chat_id = update.message.chat_id
    full_name = update.message.from_user.full_name
    party_id, isMaster = getParty_isMaster(chat_id)

    if party_id is None:
        party_id = dnd_data["parties"][-1]["id"] + 1
        build_party(chat_id, party_id, full_name)
        await update.message.reply_text(f"Party creato! Adesso sei il manster del party di id {party_id}!.\nSe l'utente è provvisto puoi usare /send_invite <@username>.\nAltrimenti poi generare un codice invito con il comando /generate_invite.")
        return

    else:
        await update.message.reply_text("Fai già parte di un party.\nRicorda puoi partecipare solo ad un party alla volta.")
        await update.message.reply_text("Se desideri uscire prova il comando /exit")

async def accept_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.from_user.username
    invites = get_invites_for_user(username)

    if not invites:
        await update.message.reply_text("Non hai inviti in sospeso.")
        return SELECT # probabilmente da cambiare

    reply_keyboard = []
    for invite in invites:
        invite_code = invite["invite_code"]
        party_id = invite["party_id"]
        button = KeyboardButton(text=f"Party ID: {party_id}, Codice Invito: {invite_code}")
        reply_keyboard.append([button])

    button = KeyboardButton(text="/cancel")
    reply_keyboard.append([button])
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    await update.message.reply_text("Selezione l'invito da accettare", reply_markup=reply_markup)
    return SELECT


async def accepting_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # if update.message.text == "/annulla":
    #    return None

    invite_code = extract_code(update.message.text)

    chat_id = update.message.chat_id
    party_id, isMaster = getParty_isMaster(chat_id)

    if party_id is None:
        name = update.message.from_user.full_name
        username = update.message.from_user.username
        party_id, reply = join_with_invite(invite_code, chat_id, username, name)
        await update.message.reply_text(reply, reply_markup=ReplyKeyboardRemove(),)

        if party_id > 0:
            dm_id = get_dm_id(party_id)
            await context.bot.send_message(chat_id=dm_id, text=f"L'utente {name} è appena entrato nel tuo party.")


    else:
        await update.message.reply_text("Fai già parte di un party.\nRicorda puoi partecipare solo ad un party alla volta.")
        await update.message.reply_text("Se desideri uscire prova il comando /exit", reply_markup=ReplyKeyboardRemove(),)

    await context.bot.send_message(chat_id=update.effective_chat.id, text="This is a test please use only the /roll_6 command.")
    return TEST

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text("Operazione cancellata.\nNessun invito accettato", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def remove_player(update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    reply = remove_player_party(chat_id=chat_id, party_id=None, name=None)
    await update.message.reply_text(reply)

async def kick_player(update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    party_id, isMaster = getParty_isMaster(chat_id)

    if isMaster:
        if len(context.args) != 0:
            reply = remove_player_party(chat_id=None, party_id=party_id, name=context.args[0])
            await update.message.reply_text(reply)

        else:
            keyboard = []
            for party in dnd_data["parties"]:
                if party["id"] == party_id:
                    for member in party["members"]:

                        if member["chat_id"] != chat_id:
                            name = member["name"]
                            data = [name, party_id]
                            button = InlineKeyboardButton(f"Nome: {name}", callback_data=data)
                            keyboard.append([button])

            data = ["Annulla"]
            button = InlineKeyboardButton("Annulla", callback_data=data)
            keyboard.append([button])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("Quale membro del party vuoi kickare?\n(Tip. puoi usare il comando anche come /kick <Nome>)", reply_markup=reply_markup)

    else:
        await update.message.reply_text("Solo il Dungeon Master può kickare i membri del party.")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # chat_id = update.callback_query.from_user.id
    # username = update.callback_query.from_user.username

    # Commenti ufficiali di PTB
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()
    await query.edit_message_text(text="CIAO.")
    result = query.data

    if result[0] == "Annulla":
        await query.edit_message_text(text="Operazione annullata con successo")

    else:
        reply = remove_player_party(chat_id=None, party_id=result[1], name=result[0])
        await query.edit_message_text(text=reply)
        return

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
        await update.message.reply_text(f"l'utente {usr_invite} è già stato invitato in questo party.\nSe l'utente non trova l'invito può usare il comando /show_invites.")
        return

    invite_code = dnd_data["invites"][-1]["invite_code"] + 1

    build_invite(party_id, invite_code, usr_invite)

    await update.message.reply_text(f"L'utente @{usr_invite} è stato invitato correttamente.\nL'utente puoi visionare gli inviti con il comando /show_invites")

async def generate_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    party_id, isMaster = getParty_isMaster(chat_id)

    if party_id is None:
        await update.message.reply_text("Devi essere in un party per generare un invito.")
        return

    if isMaster is False:
        await update.message.reply_text("Solo il Master può generare inviti.")
        return

    invite_code = dnd_data["invites"][-1]["invite_code"] + 1

    build_invite(party_id, invite_code, False)

    await update.message.reply_text(f"Ecco il codice invito: {invite_code}.\nPuoi condividerlo a SOLO un utente e può usare il comando /accept_invite per entrare.")


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

    invite_message += "Usa il comando /accept_invite per unirti al party desiderato."
    await update.message.reply_text(invite_message)


async def party_info(update: Update, context: ContextTypes.DEFAULT_TYPE): # TODO Aggiugere i dati del character dopo che lo creo
    chat_id = update.message.chat_id
    party_id, isMaster = getParty_isMaster(chat_id)
    reply = f"Party {party_id} composto da :\n"

    if party_id is None:
        await update.message.reply_text("Non sei in nessun party.\nPer maggiori informazioni usa il comando /help")
        return

    for party in dnd_data["parties"]:
        if party["id"] == party_id:
            for member in party["members"]:
                name = member["name"]
                reply += f"Nome : {name} "
                if member["master"] is True:
                    reply += "DM"

                reply += "\n"

    await update.message.reply_text(reply)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if(len(context.args) == 0):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Niente da rendere maiuscolo")

    else:
        text_caps = ' '.join(context.args).upper()
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)
        # await context.bot.send_message(chat_id=update.effective_chat.id, text=str(len(context.args))) conta il numero di argomenti

async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    num = random.randint(1, 6)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=str(num))

async def roll_6(update: Update, context: ContextTypes.DEFAULT_TYPE):
    num = random.randint(1, 6)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=str(num))
    return ConversationHandler.END

"""
COMANDI AUSILIARI////////////////////////////////////////////////////////////////////////////////////////////////////////
"""

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

def join(chat_id, party_id, full_name):

    for party in dnd_data["parties"]:
        if party["id"] == party_id:
            for member in party["members"]:
                if member["chat_id"] == chat_id:
                    return 0, "Fai già parte di questo party."

            party["members"].append({
                "chat_id": chat_id,
                "name": full_name,
                "character": None,
                "master": False,
            })
            save_data()
            return party_id, f"Unito con successo al party {party_id}!"

    return 0, "Party ID non valido. Per favore controlla l'ID e riprova."

def join_with_invite(invite_code, chat_id, username, full_name):

    for invite in dnd_data["invites"]:
        if invite["invite_code"] == invite_code and invite["username"] == username:
            expiration_time = datetime.strptime(invite["expiration"], "%d/%m/%Y %H:%M:%S")
            if datetime.now() > expiration_time:
                dnd_data["invites"].remove(invite)
                save_data()
                return 0, "Il codice di invito è scaduto. Chiedi al Master del party di generare un nuovo invito."

            party_id = invite["party_id"]
            dnd_data["invites"].remove(invite)
            save_data()
            return join(chat_id, party_id, full_name)

        if invite["invite_code"] > invite_code:
            break

    return 0, "Codice di invito non valido."

def build_party(chat_id, party_id, full_name):

    new_party = {
        "id": party_id,
        "members": [
            {
                "chat_id": chat_id,
                "name": full_name,
                "character": None,
                "master": True,
            }
        ]
    }
    dnd_data["parties"].append(new_party)
    save_data()

def remove_player_party(chat_id, party_id, name):

    for party in dnd_data["parties"]:
        if party_id is None or party_id == party["id"]:
            for member in party["members"]:

                if name is None:
                    if member["chat_id"] == chat_id and member["master"] is False:
                        party["members"].remove(member)
                        save_data()
                        return "Rimosso con successo dal party!"

                    if member["chat_id"] == chat_id and member["master"] is True:
                        dnd_data["parties"].remove(party)
                        save_data()
                        return "Rimosso dal party e party elimitato con successo."

                else:
                    if member["name"] == name:
                        party["members"].remove(member)
                        save_data()
                        return f"Player {name} rimosso con successo"

            if party_id is not None:
                return "L'utente non è presente nel party"

    return "Non sei presente in nessun party"

def get_invites_for_user(username):

    usr_invites = []
    for invite in dnd_data["invites"]:
        if invite["username"] == username:
            usr_invites.append(invite)

    return usr_invites

def get_dm_id(party_id):
    for party in dnd_data["parties"]:
        if party_id == party["id"]:
            return party["members"][0]["chat_id"]

    return 0

def build_invite(party_id, invite_code, usr_invite):

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

def extract_code(reply):

    start_string = "Invito: "

    i_start = reply.find(start_string)
    if i_start == -1:
        return None
    i_start += len(start_string)

    return int(reply[i_start:])

if __name__ == '__main__':

    application = ApplicationBuilder().token(TOKEN).arbitrary_callback_data(True).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("accept_invite", accept_invite)],
        states={
            SELECT: [MessageHandler(filters.Regex("^Party ID: (\d+), Codice Invito: (\d+)$"), accepting_invite)],
            TEST: [CommandHandler("roll_6", roll_6)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )


# TODO inseire un comando non valido
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('create', create_party))
    # application.add_handler(CommandHandler('join', join_party))
    application.add_handler(CommandHandler('exit', remove_player))
    application.add_handler(CommandHandler('kick', kick_player))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler('send_invite', send_invite))
    application.add_handler(CommandHandler('generate_invite', generate_invite))
    application.add_handler(CommandHandler('show_invites', show_invites))
    application.add_handler(CommandHandler('party', party_info))
    # application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    application.add_handler(CommandHandler('caps', caps))
    application.add_handler(CommandHandler('roll', roll))
    application.add_handler(conv_handler)

    application.run_polling()
