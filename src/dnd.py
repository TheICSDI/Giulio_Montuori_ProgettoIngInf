from DataManager import PartyManager, InviteManager, CharacterManager
import logging
import json
import random
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

# For ConversationHandler
SELECT = range(1)
SHEET, CHOICE, EDIT = range(3)
# For InlineKeyboardButton
SLOT1, SLOT2, SLOT3, DEL = range(4)
# R, C, B, D, F, P, S, W, I= range(9)

data_party = PartyManager("JSON/parties.json")
data_invite = InviteManager("JSON/invites.json")
data_character = CharacterManager("JSON/characters.json")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def extract_id(reply):

    start_string = "Invito: "

    i_start = reply.find(start_string)
    if i_start == -1:
        return None
    i_start += len(start_string)

    return int(reply[i_start:])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # username = update.message.from_user.username
    # party_id = isInvited(username)

    await update.message.reply_text("Benvenuto su D&D 5e Telegram bot!\nScrivi /help per più imformazioni su come giocare \U0001F604.")


async def help_command(update: Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("TODO")

async def create_party(update: Update, context:ContextTypes.DEFAULT_TYPE): #il creatore del party satà automaticamente il DM
    chat_id = update.message.chat_id
    full_name = update.message.from_user.full_name
    party_id, isMaster = data_party.getPartyIsMaster(chat_id)

    if party_id is None:
        # need to syncronize this
        await data_party.create(chat_id, full_name)
        await update.message.reply_text(f"Party creato! Adesso sei il manster del party di id {party_id}!.\nSe l'utente è provvisto puoi usare /send_invite <@username>.\nAltrimenti poi generare un codice invito con il comando /generate_invite.")
        return

    else:
        await update.message.reply_text("Fai già parte di un party.\nRicorda puoi partecipare solo ad un party alla volta.")
        await update.message.reply_text("Se desideri uscire prova il comando /exit")

async def buildingInviteList(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.from_user.username
    invites = data_invite.getInvites(username)

    if not invites:
        await update.message.reply_text("Non hai inviti in sospeso.")
        return SELECT # probabilmente da cambiare

    reply_keyboard = []
    for invite in invites:
        invite_id = invite["id"]
        party_id = invite["party_id"]
        button = KeyboardButton(text=f"Party ID: {party_id}, Codice Invito: {invite_id}")
        reply_keyboard.append([button])

    button = KeyboardButton(text="/cancel")
    reply_keyboard.append([button])
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    await update.message.reply_text("Selezione l'invito da accettare", reply_markup=reply_markup)
    return SELECT


async def accepting_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):

    invite_id = extract_id(update.message.text)

    chat_id = update.message.chat_id
    party_id = data_party.getPartyID(chat_id)

    if party_id is None:
        name = update.message.from_user.full_name
        username = update.message.from_user.username
        party_id, reply = await data_invite.joinParty(data_party, invite_id, chat_id, username, name)
        await update.message.reply_text(reply, reply_markup=ReplyKeyboardRemove(),)

        if party_id > 0:
            dm_id = data_party.getMaster(party_id)
            await context.bot.send_message(chat_id=dm_id, text=f"L'utente {name} è appena entrato nel tuo party.")


    else:
        await update.message.reply_text("Fai già parte di un party.\nRicorda puoi partecipare solo ad un party alla volta.")
        await update.message.reply_text("Se desideri uscire prova il comando /exit", reply_markup=ReplyKeyboardRemove(),)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancels and ends the conversation."""
    await update.message.reply_text("Operazione cancellata.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def remove_player(update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    reply = await data_party.removePlayer(chat_id=chat_id, party_id=None, name=None)
    await update.message.reply_text(reply)

async def kick_player(update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    party_id, isMaster = data_party.getPartyIsMaster(chat_id)

    if isMaster:
        if len(context.args) != 0:
            reply = await data_party.removePlayer(chat_id=None, party_id=party_id, name=context.args[0])
            await update.message.reply_text(reply)

        else:

            keyboard = []
            players = data_party.getMembers(party_id)
            for player in players:

                if player["chat_id"] != chat_id:
                    name = player["name"]
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
    result = query.data

    if result[0] == "Annulla":
        await query.edit_message_text(text="Operazione annullata con successo")

    else:
        reply = await data_party.removePlayer(chat_id=None, party_id=result[1], name=result[0])
        await query.edit_message_text(text=reply)
        return

async def send_invite(update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if len(context.args) == 0:
        await update.message.reply_text("Per mandare un invito devi specificare l'username dell'utente.\nInvita l'utente usando il comando /invite <@username>")
        return

    party_id, isMaster = data_party.getPartyIsMaster(chat_id)

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

    usr_invite = usr_invite[1:]   #remove @
    if data_invite.checkInvite(usr_invite, party_id) is True:
        await update.message.reply_text(f"l'utente {usr_invite} è già stato invitato in questo party.\nSe l'utente non trova l'invito può usare il comando /show_invites.")
        return

    await data_invite.create(party_id, usr_invite)

    await update.message.reply_text(f"L'utente @{usr_invite} è stato invitato correttamente.\nL'utente puoi visionare gli inviti con il comando /show_invites")

async def generate_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    party_id, isMaster = data_party.getPartyIsMaster(chat_id)

    if party_id is None:
        await update.message.reply_text("Devi essere in un party per generare un invito.")
        return

    if isMaster is False:
        await update.message.reply_text("Solo il Master può generare inviti.")
        return

    invite_id = await data_party.getLastId() + 1

    await data_invite.create(party_id, invite_id, False)

    await update.message.reply_text(f"Ecco il codice invito: {invite_id}.\nPuoi condividerlo a SOLO un utente e può usare il comando /accept_invite per entrare.")


async def show_invites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.from_user.username
    invites = data_invite.getInvites(username)

    if not invites:
        await update.message.reply_text("Non hai inviti in sospeso.")
        return

    invite_message = "Hai ricevuto i seguenti inviti:\n"
    for invite in invites:
        invite_id = invite["id"]
        party_id = invite["party_id"]
        invite_message += f"Party ID: {party_id}, Codice Invito: {invite_id}\n"

    invite_message += "Usa il comando /accept_invite per unirti al party desiderato."
    await update.message.reply_text(invite_message)


async def party_info(update: Update, context: ContextTypes.DEFAULT_TYPE): # TODO Aggiugere i dati del character dopo che lo creo
    chat_id = update.message.chat_id
    party_id, isMaster = data_party.getPartyIsMaster(chat_id)
    reply = f"Party {party_id} composto da :\n"

    if party_id is None:
        await update.message.reply_text("Non sei in nessun party.\nPer maggiori informazioni usa il comando /help")
        return

    members = data_party.getMembers(party_id)

    for member in members:
        name = member["name"]
        reply += f"Nome : {name} "
        if member["master"] is True:
            reply += "DM"

        reply += "\n"

    await update.message.reply_text(reply)

async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    num = random.randint(1, 6)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=str(num))

async def roll_6(update: Update, context: ContextTypes.DEFAULT_TYPE):
    num = random.randint(1, 6)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=str(num))
    return ConversationHandler.END

async def character_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    """
    chat_id = update.message.chat_id

    slot1 = InlineKeyboardButton("SLOT1", callback_data="SLOT1")
    slot2 = InlineKeyboardButton("SLOT2", callback_data="SLOT2")
    slot3 = InlineKeyboardButton("SLOT3", callback_data="SLOT3")
    button = InlineKeyboardButton("DEL", callback_data="DEL")
    keyboard = [[slot1], [slot2], [slot3], [button]]

    try:
        characters = data_character.getCharacters(chat_id)

    except KeyError:
        await data_character.create(chat_id)
        characters = data_character.getCharacters(chat_id)

    for i, character in enumerate(characters):
        if character != 0:
            name = character["nickname"]
            button = InlineKeyboardButton(f"{name}", callback_data=f"SLOT{i}")
            keyboard[i] = [button]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Ecco gli slot con i tuoi personaggi.\nClicca per avere più informazioni o creare un personaggio.", reply_markup=reply_markup)
    return SHEET

async def sheetKeyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    """
    query = update.callback_query
    await query.answer()
    chat_id = update.callback_query.from_user.id
    result = query.data

    """
    if "choice_data" in context.user_data:  # Here, retrieve stored data.
        result = context.user_data["choice_data"]
        del context.user_data["choice_data"]  # Don't forget to delete it once used.
    else:
        result = query.data
        context.user_data["choice_data"] = result
    """

    r = InlineKeyboardButton("RACE", callback_data=f"R{result[-1]}")
    c = InlineKeyboardButton("CLASS", callback_data=f"C{result[-1]}")
    b = InlineKeyboardButton("BACKGROUD", callback_data=f"B{result[-1]}")
    d = InlineKeyboardButton("DETAILS", callback_data=f"D{result[-1]}")
    f = InlineKeyboardButton("FEATS", callback_data=f"F{result[-1]}")
    p = InlineKeyboardButton("PROFICIENCY", callback_data=f"P{result[-1]}")
    s = InlineKeyboardButton("SPELLS", callback_data=f"S{result[-1]}")
    w = InlineKeyboardButton("WEAPONS", callback_data=f"W{result[-1]}")
    indietro = InlineKeyboardButton("BACK", callback_data="I{result[-1]}")

    keyboard = [[r, c], [b, d], [f, p], [s, w], [indietro]]


    choice = data_character.getCharacters(chat_id)

    if choice[int(result[-1])] != 0:
        nickname = choice[int(result[-1])]["nickname"]

    else:
        await data_character.createCharacter(chat_id, result[-1])
        nickname = choice[int(result[-1])]["nickname"]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=f"Ecco il datasheet del tuo personaggio {nickname} clicca per ricevere più informazioni o per modificare i dati presenti", reply_markup=reply_markup)
    return CHOICE

"""
async def choiceSheet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.callback_query.from_user.id
    await query.answer()
    result = query.data


    choice = data_character.getCharacters(chat_id)
    choice = choice[int(result[-1])]

    button1 = InlineKeyboardButton("EDIT", callback_data=f"E{result}")
    button2 = InlineKeyboardButton("BACK", callback_data=f"X{result[-1]}")
    keyboard = [[button1, button2]]

    if result[0] == "R":
        text = choice["race"]

    elif result[0] == "C":
        text = choice["class"]

    elif result[0] == "B":
        text = choice["background"]

    elif result[0] == "D":
        text = choice["details"]

    elif result[0] == "F":
        text = choice["feats"]

    elif result[0] == "P":
        text = "weapon proficiencies:\n"
        text += str(choice["weapon_proficiencies"])
        text += "\narmor proficiencies:\n"
        text += str(choice["armor_proficiencies"])

    elif result[0] == "S":
        text = choice["spells"]

    elif result[0] == "W":
        text = choice["weapons"]

    elif result[0] == "I":
        text = choice["race"]


    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    return EDIT
"""
async def choiceSheet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    """
    query = update.callback_query
    chat_id = update.callback_query.from_user.id
    await query.answer()
    result = query.data

    choice = data_character.getCharacters(chat_id)
    choice = choice[int(result[-1])]

    button1 = InlineKeyboardButton("EDIT", callback_data=f"E{result}")
    button2 = InlineKeyboardButton("BACK", callback_data=f"X{result[-1]}")
    keyboard = [[button1, button2]]

    section_key = result[0]

    # Get the corresponding key for the JSON sections
    section_keys = {
        "R": "race",
        "C": "class",
        "B": "background",
        "D": "details",
        "F": "feats",
        "P": "weapon_proficiencies",  # assuming this stands for proficiencies
        "S": "spells",
        "W": "weapons",
        "I": "items",  # assuming this stands for items
    }

    # If the key exists, format the data, otherwise set the text to an error message
    if section_key in section_keys:
        text = format_data(choice, section_keys[section_key])
    else:
        text = "⚠️ Unknown section."

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    return EDIT



async def editCharacter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    """
    query = update.callback_query
    # chat_id = update.callback_query.from_user.id
    await query.answer()
    result = query.data


    return ConversationHandler.END

def format_data(choice: dict, key: str, indent: str = '') -> str:
    """Format data for display recursively."""
    data = choice[key]
    text = ""

    # Function to format each element of data
    def format_element(element, indent=''):
        nonlocal text
        if isinstance(element, dict):
            for k, v in element.items():
                if isinstance(v, list):
                    for i, item in enumerate(v):
                        text += f"{indent}🔹 {k.capitalize()} {i+1}:\n"
                        format_element(item, indent + '  ')
                elif isinstance(v, dict):
                    text += f"{indent}🔹 {k.capitalize()}:\n"
                    format_element(v, indent + '  ')
                else:
                    text += f"{indent}🔹 {k.capitalize()}: {v}\n"
        elif isinstance(element, list):
            for i, item in enumerate(element):
                text += f"{indent}🔹 Item {i+1}:\n"
                format_element(item, indent + '  ')
        else:
            text += f"{indent}🔹 {element}\n"

    format_element(data)
    return text


if __name__ == '__main__':

    application = ApplicationBuilder().token(TOKEN).arbitrary_callback_data(True).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("accept_invite", buildingInviteList)],
        states={
            SELECT: [MessageHandler(filters.Regex("^Party ID: (\d+), Codice Invito: (\d+)$"), accepting_invite)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    character_creation = ConversationHandler(
            entry_points=[CommandHandler("character", character_list)],
            states={
                SHEET:[
                    CallbackQueryHandler(sheetKeyboard, pattern="^SLOT(\d)$"),
                    # CallbackQueryHandler(delSheetEntry, pattern= "^" + str(DEL) + "$")
                    ],
                CHOICE:[
                    CallbackQueryHandler(choiceSheet, pattern="^R(\d)$|^C(\d)$|^B(\d)$|^D(\d)$|^F(\d)$|^P(\d)$|^S(\d)$|^W(\d)$"),
                    ],
                EDIT:[
                    CallbackQueryHandler(editCharacter, pattern="^E(\S)$"),
                    CallbackQueryHandler(sheetKeyboard, pattern="^X(\d)$"),
                    ]
            },
            fallbacks=[]
    )


# TODO inseire un comando non valido
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('create', create_party))
    # application.add_handler(CommandHandler('join', join_party))
    application.add_handler(CommandHandler('exit', remove_player))
    application.add_handler(CommandHandler('kick', kick_player))
    # application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler('send_invite', send_invite))
    application.add_handler(CommandHandler('generate_invite', generate_invite))
    application.add_handler(CommandHandler('show_invites', show_invites))
    application.add_handler(CommandHandler('party', party_info))
    # application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    application.add_handler(CommandHandler('roll', roll))
    application.add_handler(conv_handler)
    application.add_handler(character_creation)

    application.run_polling()
