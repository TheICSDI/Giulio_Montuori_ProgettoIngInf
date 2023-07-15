from DataManager import PartyManager, InviteManager, CharacterManager
import logging
import random
from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
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

# telegram bot's token
TOKEN = '5856331893:AAGotmP4Ws9jX4aowvi13JkfUlIQZH1uYfI'

# For ConversationHandler
SELECT = range(1)
LIST, SHEET, CHOICE, EDIT, FINISHED, BACK = range(6)
PARTY, CREATE, JOIN, KICK, EXIT, PROCESS, INVITED, INVITE, INSERISCI, SEL, USERNAME, SET = range(12)
DICE, CUSTOMDICE = range(2)

data_party = PartyManager("JSON/parties.json")
data_invite = InviteManager("JSON/invites.json")
data_character = CharacterManager("JSON/characters.json")
# dice set
dice = ["d4","d6","d8","d10","d12", "d20", "d100"]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def format_data(choice: dict, key: str, indent: str = '', level: int = 0) -> str:
    """Format data for display recursively."""
    text = ""
    level_emojis = ["🔹", "🔸", "▫️", "▪️", "🔘"]

    # Handle recursion
    def format_element(element, indent='', level=0):
        nonlocal text
        emoji = level_emojis[level % len(level_emojis)]
        if isinstance(element, dict):
            for k, v in element.items():
                if isinstance(v, list):
                    for i, item in enumerate(v):
                        text += f"{indent}{emoji} {k.capitalize()} {i}:\n"
                        format_element(item, indent + '  ', level + 1)
                elif isinstance(v, dict):
                    text += f"{indent}{emoji} {k.capitalize()}:\n"
                    format_element(v, indent + '  ', level + 1)
                else:
                    text += f"{indent}{emoji} {k.capitalize()}: {v}\n"
        elif isinstance(element, list):
            for i, item in enumerate(element):
                text += f"{indent}{emoji}{i}:\n"
                format_element(item, indent + '  ', level + 1)
        else:
            text += f"{indent}{emoji} {element}\n"

    # Handle 'proficiencies' as a special case
    if key == "proficiencies":
        text += "⚔️  Weapon_Proficiencies:\n"
        format_element(choice["weapon_proficiencies"], indent + '  ', level + 1)
        text += "🛡️ Armor_Proficiencies:\n"
        format_element(choice["armor_proficiencies"], indent + '  ', level + 1)
    else:
        format_element(choice[key], indent, level)
    return text

def extract_id(reply):
    """
    Extract the invite ID of a given string
    return the ID as int
    """
    start_string = "Invito: "

    i_start = reply.find(start_string)
    if i_start == -1:
        return None
    i_start += len(start_string)

    return int(reply[i_start:])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command """
    chat_id = update.message.chat_id
    logging.info(f"{chat_id} started the chat")

    reply = "Ciao e benvenuto 🎉 su D&D 5e Telegram bot! 🎲🐉\n\nPer gestire il party 🥳 utilizza il comando '/party' 📋\n\nPer Gestire il personaggio 🧙‍♂️ utilizza il comando '/character' 📜\n\nPer lanciare il dado 🎲 usa il comando '/roll'\n\nIl Master del party 👑 può utilizzare il comando '/roll p' per fare un lancio privato🤫\n\nScrivi '/help' 🆘 per più informazioni su come funziona ogni comando 📚😄."

    await update.message.reply_text(reply)

async def helpCommand(update: Update, context:ContextTypes.DEFAULT_TYPE):
    """Handle the /help command """
    chat_id = update.message.chat_id
    logging.info(f"{chat_id} started the chat")

    reply = """ OGNI MENÙ PUÒ ESSERE APERTE SOLO UNA VOLTA\n
Ecco tutti i comandi e come usarli:\n
'/help' mostra questo messaggio\n
'/start' mostra il messaggio iniziale\n
'/party' mostra il menù per gestire i party e gli inviti\n
'/character' mostra il menù per gestire i propri personaggi, il Master può modificare e visualizzare i personaggi dei membri del party con il tasto 'SUPERVISIONE'\n
'/roll' mostra il menù per gestire il lancio del dado, il Master usare il comando '/roll p' per fare un lancio privato\n
'/show_currency' mostra in dettaglio quanto Copper, Silver, Electrum, Gold e Platinum ogni membro del party ha nel suo portafoglio\n
'/pay <currency_type> <ammount>' permette di ai giocatori di pagare direttamente dal proprio portafoglio\n
'/add_currency <character> <currency_type> <ammount>' permette al Master di aggiungere currency nel portafoglio di ogni giocatore
"""
    await update.message.reply_text(reply)

""" Visualizzazione e Modifica del Character """

async def startCharacter(update: Update, context):
    chat_id = update.message.chat_id
    party_id, isMaster = data_party.getPartyIsMaster(chat_id)
    logging.info(f"{chat_id} in startCharacter")

    button = InlineKeyboardButton("CONFERMA", callback_data="SI")
    annulla = InlineKeyboardButton("ANNULLA", callback_data="ANNULLA")
    keyboard = [[button, annulla]]

    if isMaster:
        button1 = InlineKeyboardButton("SUPERVISIONE", callback_data="V")
        keyboard = [[button, annulla], [button1]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Vuoi visualizzare i personaggi?", reply_markup=reply_markup)
    return LIST

async def characterListMaster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.callback_query.from_user.id
    party_id = data_party.getPartyID(chat_id)
    await query.answer()
    # result = query.data
    logging.info(f"{chat_id} in characterListMaster")

    keyboard = []
    members = data_party.getMembers(party_id)
    for i, member in enumerate(members):
        if member["chat_id"] != chat_id:
            character = member["character"]
            if character is None:
                button = InlineKeyboardButton("NON IMPOSTATO", callback_data="None")
            else:
                button = InlineKeyboardButton(f"{character}", callback_data=f"MEM{i}")
            keyboard.append([button])

    button = InlineKeyboardButton("ANNULLA", callback_data="ANNULLA")
    keyboard.append([button])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Ecco gli slot con i personaggi dei membri del party.\nClicca per avere più informazioni e modificare il loro personaggio.", reply_markup=reply_markup)
    return SHEET

async def characterList(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.callback_query.from_user.id
    await query.answer()
    result = query.data
    logging.info(f"{chat_id} in characterList")

    if result[:-1] == "DEL":
        await data_character.removeCharacter(data_party, chat_id, result[-1])

    slot1 = InlineKeyboardButton("SLOT1", callback_data="SLOT0")
    slot2 = InlineKeyboardButton("SLOT2", callback_data="SLOT1")
    slot3 = InlineKeyboardButton("SLOT3", callback_data="SLOT2")
    del1 = InlineKeyboardButton("DEL1", callback_data="DEL0")
    del2 = InlineKeyboardButton("DEL2", callback_data="DEL1")
    del3 = InlineKeyboardButton("DEL3", callback_data="DEL2")
    annulla = InlineKeyboardButton("ANNULLA", callback_data="ANNULLA")
    keyboard = [[slot1], [slot2], [slot3], [del1, del2, del3], [annulla]]

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
    await query.edit_message_text("Ecco gli slot con i tuoi personaggi.\nClicca per avere più informazioni o creare un personaggio.", reply_markup=reply_markup)
    return SHEET

async def sheetKeyboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.callback_query.from_user.id
    result = query.data
    logging.info(f"{chat_id} in sheetKeyboard")

    # Master case
    if result[0] == "M":
        result = str(result)
        r_split = result.split("MEM")
        r_split = int(r_split[1])

        name = InlineKeyboardButton("SET NAME", callback_data=f"NM{r_split}")
        a = InlineKeyboardButton("ATTRIBUTE", callback_data=f"AM{r_split}")
        h = InlineKeyboardButton("HEALT", callback_data=f"HM{r_split}")
        r = InlineKeyboardButton("RACE", callback_data=f"RM{r_split}")
        c = InlineKeyboardButton("CLASS", callback_data=f"CM{r_split}")
        b = InlineKeyboardButton("BACKGROUD", callback_data=f"BM{r_split}")
        d = InlineKeyboardButton("DETAILS", callback_data=f"DM{r_split}")
        f = InlineKeyboardButton("FEATS", callback_data=f"FM{r_split}")
        p = InlineKeyboardButton("PROFICIENCY", callback_data=f"PM{r_split}")
        s = InlineKeyboardButton("SPELLS", callback_data=f"SM{r_split}")
        w = InlineKeyboardButton("WEAPONS", callback_data=f"WM{r_split}")
        indietro = InlineKeyboardButton("BACK", callback_data="M")

        keyboard = [[a, h], [r, c], [b, d], [f, p], [s, w], [indietro]]
        party_id = data_party.getPartyID(chat_id)
        members = data_party.getMembers(party_id)
        nickname = members[r_split]["character"]
        text = f"Ecco il datasheet di {nickname} clicca per ricevere più informazioni o per modificare i dati presenti"

    else:
        choice = data_character.getCharacters(chat_id)

        if choice[int(result[-1])] != 0:
            nickname = choice[int(result[-1])]["nickname"]

        else:
            await data_character.createCharacter(chat_id, result[-1])
            nickname = choice[int(result[-1])]["nickname"]

        name = InlineKeyboardButton("SET NAME", callback_data=f"N{result[-1]}")
        a = InlineKeyboardButton("ATTRIBUTE", callback_data=f"A{result[-1]}")
        h = InlineKeyboardButton("HEALT", callback_data=f"H{result[-1]}")
        r = InlineKeyboardButton("RACE", callback_data=f"R{result[-1]}")
        c = InlineKeyboardButton("CLASS", callback_data=f"C{result[-1]}")
        b = InlineKeyboardButton("BACKGROUD", callback_data=f"B{result[-1]}")
        d = InlineKeyboardButton("DETAILS", callback_data=f"D{result[-1]}")
        f = InlineKeyboardButton("FEATS", callback_data=f"F{result[-1]}")
        p = InlineKeyboardButton("PROFICIENCY", callback_data=f"P{result[-1]}")
        s = InlineKeyboardButton("SPELLS", callback_data=f"S{result[-1]}")
        w = InlineKeyboardButton("WEAPONS", callback_data=f"W{result[-1]}")
        indietro = InlineKeyboardButton("BACK", callback_data="I")

        keyboard = [[name], [a, h], [r, c], [b, d], [f, p], [s, w], [indietro]]
        text = f"Ecco il datasheet del tuo personaggio {nickname} clicca per ricevere più informazioni o per modificare i dati presenti"

    reply_markup = InlineKeyboardMarkup(keyboard)
    # a = InlineKeyboardButton("ATTRIBUTE", callback_data=f"A{result[-1]}")
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    return CHOICE

async def choiceSheet(update: Update, context):
    query = update.callback_query
    chat_id = update.callback_query.from_user.id
    await query.answer()
    result = query.data
    logging.info(f"{chat_id} in choiceSheet")

    button1 = InlineKeyboardButton("EDIT", callback_data=f"E{result}")
    button2 = InlineKeyboardButton("BACK", callback_data=f"X{result[-1]}")
    keyboard = [[button1, button2]]

    if result[1] == "M":
        r_split = result.split("M")
        index = int(r_split[-1])
        button2 = InlineKeyboardButton("BACK", callback_data=f"MEM{r_split[-1]}")
        keyboard = [[button1, button2]]
        party_id = data_party.getPartyID(chat_id)
        members = data_party.getMembers(party_id)
        chat_id = members[int(index)]["chat_id"]
        c_name = members[int(index)]["character"]
        characters = data_character.getCharacters(chat_id)
        for character in characters:
            if character != 0 and character["nickname"] == c_name:
                choice = character

    else:
        choice = data_character.getCharacters(chat_id)
        choice = choice[int(result[-1])]

    try:
        key = data_character.fullKey(result[0])

        text = format_data(choice, key)

        context.user_data["key"] = key
        context.user_data["slot"] = result[1:]

    except KeyError:
        text = "⚠️  Unknown section."

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    return EDIT

async def editCharacter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.callback_query.from_user.id
    await query.answer()
    result = query.data
    logging.info(f"{chat_id} in editCharacter")

    if result[0] == "N":
        context.user_data["key"] = "nickname"
        context.user_data["slot"] = result[-1]
        button1 = InlineKeyboardButton("CANCELS", callback_data=f"SLOT{result[-1]}")
        keyboard = [[button1]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Inserisci il nome:", reply_markup=reply_markup)
    else:
        button1 = InlineKeyboardButton("CANCELS", callback_data=f"{result[1:]}")
        keyboard = [[button1]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Per modificare una riga semplicemente inserisci il nome della riga seguita \"->\" e dal valore nuovo.\nEsempio.\nspeed->5\nPer modificare una riga di una sotto-categoria (si può notare dal cambio di emoji e di indentatura) inserisci il nome della riga non identata e poi quella desiderata e poi il valore nuovo, usare sempre \"->\" per segnare il cambio.\nEsempio.\n0->range->normal->5.\nSe desideri lanciare un dado per scegliere un valore semplicemente scrivi il tipo di dado.\nEsempio.\nstrength->value->d20.", reply_markup=reply_markup)

    return FINISHED

async def settingEdit(update: Update, context):
    # needed variable
    chat_id = update.message.chat_id
    key = context.user_data["key"]
    slot = context.user_data["slot"]
    logging.info(f"{chat_id} in settingEdit")

    if slot[0] == "M":
        button1 = InlineKeyboardButton("BACK", callback_data=f"{key[0].upper()}{slot}")
        index = slot[1:]
        party_id = data_party.getPartyID(chat_id)
        members = data_party.getMembers(party_id)
        chat_id = members[int(index)]["chat_id"]
        c_name = members[int(index)]["character"]
        characters = data_character.getCharacters(chat_id)
        for index, character in enumerate(characters):
            if character != 0 and character["nickname"] == c_name:
                slot = index

    else:
        button1 = InlineKeyboardButton("BACK", callback_data=f"{key[0].upper()}{slot}")

    add_mod = [
            "attribute->strength->value",
            "attribute->dexterity->value",
            "attribute->constitution->value",
            "attribute->intelligence->value",
            "attribute->wisdom->value",
            "attribute->charisma->value",
            "attribute->ability->value",
            ]

    # Getting the imput
    words = update.message.text
    if not words:
        await update.message.reply_text(text="Errore nella letture dell'input.\nProva di nuovo.")
        return FINISHED

    try:
        path, value = words.rsplit('->', 1)
        path = path.lower()

    except ValueError:
        value = words

    if key == "proficiencies":
        full_path = path

    elif key == "nickname":
        full_path = key
        button1 = InlineKeyboardButton("CANCELS", callback_data=f"SLOT{slot}")

    else:
        full_path = key + "->" + path

    if value in dice:
        value = str(random.randint(1, int(value[1:])))

    text = await data_character.setValue(chat_id, slot, full_path, value)
    if not text:
        text = "⚠️  Selezione sconosciuta."

    if full_path in add_mod:
        value = str((int(value) - 10) // 2)
        full_path = full_path[:-5] + "mod"
        await data_character.setValue(chat_id, slot, full_path, value)


    keyboard = [[button1]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=text, reply_markup=reply_markup)
    return FINISHED

async def cancelConversationQuery(update: Update, context):
    query = update.callback_query
    chat_id = update.callback_query.from_user.id
    await query.answer()
    logging.info(f"{chat_id} in cancelConversationQuery")

    await query.edit_message_text(text="Operazione Annullata")
    return ConversationHandler.END

"""DICE & ROLL"""

async def roll(update: Update, context):
    chat_id = update.message.chat_id
    party_id, isMaster = data_party.getPartyIsMaster(chat_id)
    logging.info(f"{chat_id} in roll")

    d4 = InlineKeyboardButton("d4", callback_data="4")
    d6 = InlineKeyboardButton("d6", callback_data="6")
    d8 = InlineKeyboardButton("d8", callback_data="8")
    d10 = InlineKeyboardButton("d10", callback_data="10")
    d12 = InlineKeyboardButton("d12", callback_data="12")
    d20 = InlineKeyboardButton("d20", callback_data="20")
    d100 = InlineKeyboardButton("d100", callback_data="100")
    custom = InlineKeyboardButton("CUSTOM", callback_data="C")
    annulla = InlineKeyboardButton("ANNULLA", callback_data="ANNULLA")

    keyboard = [[d4, d6, d8], [d10, d12, d20], [d100, custom], [annulla]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if not isMaster or len(context.args) == 0:
        text = "\nLancio Privato ❌"
        context.user_data["privato"] = False

    elif context.args[0] == "p" and isMaster:
        text = "\nLancio Privato ✅"
        context.user_data["privato"] = True
        logging.info(f"{chat_id} in")

    await update.message.reply_text(text="Scegli che dado lanciare o lancia una serie di dadi usando il tasto \"CUSTOM\"." + text, reply_markup=reply_markup)
    return DICE

async def diceStandard(update: Update, context):
    query = update.callback_query
    chat_id = update.callback_query.from_user.id
    name = update.callback_query.from_user.full_name
    await query.answer()
    result = query.data
    logging.info(f"{chat_id} in diceStandard")

    if result[0] != "A" and result[0] != "C":
        party_id = data_party.getPartyID(chat_id)
        members = data_party.getMembers(party_id)
        value = str(random.randint(1, int(result)))
        await query.edit_message_text(text=f"Con il lancio di un d{result} hai ottenuto un {value}")
        if not context.user_data["privato"]:
            for member in members:
                if chat_id != member["chat_id"]:
                    m_chat_id = member["chat_id"]
                    await context.bot.send_message(chat_id=m_chat_id, text=f"L'utente {name} ha lanciato un d{result} è ha ottenuto un {value}")

        return ConversationHandler.END

    else:
        annulla = InlineKeyboardButton("ANNULLA", callback_data="ANNULLA")
        keyboard = [[annulla]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Per lanciare più dati usare le seguenti convenzioni.\nPer lanciare più di un dado scrive quanti dadi lanciare e il nome del dado (Es.\"2d10\" \"4d20\").\nPer somma usare la scrittura di un dado singolo (Es. \"d10\" \"d20\") con il simbolo \" + \" per indicare la somma(Es. \"d10 + d20 \" \"d10 + d4 + d6\")", reply_markup=reply_markup)

        return CUSTOMDICE

async def diceCustom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    name = update.message.from_user.full_name
    party_id = data_party.getPartyID(chat_id)
    members = data_party.getMembers(party_id)
    logging.info(f"{chat_id} in diceCustom")

    words = update.message.text
    logging.info(f"User {chat_id}: Provided message: {words}")
    words = words.split(" + ")
    logging.info("User {chat_id}: Split message: {words}")


    if len(words) == 1:
        words = words[0]
        dice_spec = words.split("d")
        dice_spec = list(map(int, dice_spec))

        if "d" + str(dice_spec[1]) in dice:
            text = f"Lanciando {dice_spec[0]} d{dice_spec[1]} hai ottenuto: "
            text_o = f"{name} ha lanciato {dice_spec[0]} d{dice_spec[1]} e ha ottenuto: "
            for i in range(dice_spec[0]):
                value_r = str(random.randint(1, dice_spec[1]))
                text += value_r + ", "
                text_o += value_r + ", "

            text = text[:-2]
            text_o = text_o[:-2]


            if not context.user_data["privato"]:
                for member in members:
                    if chat_id != member["chat_id"]:
                        m_chat_id = member["chat_id"]
                        await context.bot.send_message(chat_id=m_chat_id, text=text_o)

        else:
            text = "⚠️  Unknown section."

    else:
        value = []
        flag = True
        for d in words:
            if d not in dice:
                flag = False
                text = "⚠️  Unknown section."
                break

            else:
                value.append(int(random.randint(1, int(d[1:]))))

        if flag:
            tot = sum(value)
            text = f"Dal lancio composto hai ottenuto un {tot}"
            if not context.user_data["privato"]:
                text_o = f"Dal lancio composto {name} ha ottenuto un {tot}"
                for member in members:
                    if chat_id != member["chat_id"]:
                        m_chat_id = member["chat_id"]
                        await context.bot.send_message(chat_id=m_chat_id, text=text_o)

    await update.message.reply_text(text)
    return ConversationHandler.END

"""Currency"""

async def setCurrency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    party_id, isMaster = data_party.getPartyIsMaster(chat_id)
    logging.info(f"{chat_id} in setCurrency")

    if not isMaster:
        await update.message.reply_text("Solo il DM può impostare le currency.")
        return

    if len(context.args) != 3:
        await update.message.reply_text("Per impostare usa /set_currency <character> <currency> <ammount>")
        return

    text = await data_party.setCurrency(chat_id, context.args[0], context.args[1], context.args[2])

    await update.message.reply_text(text)
    return

async def payCurrency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    party_id, isMaster = data_party.getPartyIsMaster(chat_id)

    if len(context.args) != 2:
        await update.message.reply_text("Per pagare usa /pay_currency <currency> <ammount>")
        return

    character = None
    members = data_party.getMembers(party_id)
    for member in members:
        if member["chat_id"] == chat_id:
            character = member["character"]

    text = await data_party.operCurrency(chat_id, character, context.args[0], "-" + context.args[1])

    await update.message.reply_text(text)
    return

async def addCurrency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    party_id, isMaster = data_party.getPartyIsMaster(chat_id)
    logging.info(f"{chat_id} in addCurrency")

    if not isMaster:
        await update.message.reply_text("Solo il DM può aumentare le monete.")
        return

    if len(context.args) != 3:
        await update.message.reply_text("Per aggiungere moneta /add_currency <character> <currency> <ammount>")
        return

    text = await data_party.setCurrency(chat_id, context.args[0], context.args[1], context.args[2])

    await update.message.reply_text(text)

async def showCurrency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    party_id, isMaster = data_party.getPartyIsMaster(chat_id)
    text = ""
    logging.info(f"{chat_id} in showCurrency")

    # Get the party data for the given party_id
    members = data_party.getMembers(party_id)

    # Iterate over each member in the party
    for member in members:
        # Add the member's name to the text
        name = member["name"]
        text += f"👤 {name}:\n"

        character = member["character"]
        text += f"🎭 Character: {character}\n"

        # Add the member's currency information to the text
        text += "💰 Currency:\n"
        for currency, amount in member["currency"].items():
            text += f"  - {currency.capitalize()}: {amount}\n"

        # Add a line break between members
        text += "\n"

    await update.message.reply_text(text)

""" Party """
async def startParty(update: Update, context):
    chat_id = update.message.chat_id
    # party_id, isMaster = data_party.getPartyIsMaster(chat_id)
    logging.info(f"{chat_id} in startParty")

    button = InlineKeyboardButton("CONFERMA", callback_data="SI")
    annulla = InlineKeyboardButton("ANNULLA", callback_data="ANNULLA")
    keyboard = [[button, annulla]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Vuoi visualizzare i party?", reply_markup=reply_markup)
    return PARTY

async def partyInfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.callback_query.from_user.id
    name = update.callback_query.from_user.full_name
    await query.answer()
    # result = query.data
    logging.info(f"{chat_id}: Inside partyInfo")

    party_id, isMaster = data_party.getPartyIsMaster(chat_id)
    reply = f"Party {party_id} composto da :\n"
    level_emojis = ["🔹", "🔸", "👑"]

    if party_id is None:
        reply = "Non sei in nessun party.\nPer maggiori informazioni usa il comando /help"

        button = InlineKeyboardButton("CREATE", callback_data="P CREATE")
        button1 = InlineKeyboardButton("JOIN", callback_data="P JOIN")
        keyboard = [[button, button1]]

    else:
        button = InlineKeyboardButton("EXIT", callback_data="P EXIT")

        if isMaster:
            button1 = InlineKeyboardButton("KICK", callback_data="P KICK")
            button2 = InlineKeyboardButton("INVITE", callback_data="P INVITE")
            keyboard = [[button2], [button1, button]]

        else:
            button3 = InlineKeyboardButton("SET CHARACTER", callback_data="P SET")
            keyboard = [[button3], [button]]


        members = data_party.getMembers(party_id)

        for member in members:
            name = member["name"]
            text_c = ""

            if not member["master"]:
                character = member["character"]
                text_c = f"\n\t\t{level_emojis[1]}Character : {character}\n"

            reply += f"{level_emojis[0]}Nome : {name}\t\t"

            if member["master"]:
                reply += f"DM {level_emojis[2]}\n"

            reply += text_c

    annulla = InlineKeyboardButton("ANNULLA", callback_data="ANNULLA")
    keyboard.append([annulla])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(reply, reply_markup=reply_markup)
    return PROCESS

async def processParty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.callback_query.from_user.id
    await query.answer()
    result = query.data

    logging.info(f"{chat_id} Result in processParty {result}")
    result = result.split(" ")
    logging.info(f"{chat_id} Result in processParty {result}")

    if result[1] == "CREATE":
        full_name = query.from_user.full_name
        # Building keyboard and button
        button = InlineKeyboardButton("BACK", callback_data="SI")
        button1 = InlineKeyboardButton("ANNULLA", callback_data="ANNULLA")
        keyboard = [[button, button1]]
        reply_markup = InlineKeyboardMarkup(keyboard)


        party_id = await data_party.create(chat_id, full_name)
        await query.edit_message_text(f"Party creato! Adesso sei il Master del party di id {party_id}!.\nPer invitare gli al party gli altri giocatori tramite il tasto 'INVITE' all'interno di '/party'.", reply_markup=reply_markup)
        return PARTY

    elif result[1] == "JOIN":
        username = query.from_user.username
        invites = data_invite.getInvites(username)
        # Building keyboard and button
        button = InlineKeyboardButton("BACK", callback_data="BACK")
        button1 = InlineKeyboardButton("ANNULLA", callback_data="ANNULLA")
        button3 = InlineKeyboardButton("INSERISCI CODICE", callback_data="INSERISCI CODICE")
        keyboard = [[button3], [button, button1]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if not invites:
            reply = "Non hai inviti in sospeso."

        else:
            button2 = InlineKeyboardButton("ACCETTA", callback_data="ACCETTA")
            keyboard = [[button2, button3], [button, button1]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            reply = "Hai ricevuto i seguenti inviti:\n"
            for invite in invites:
                invite_id = invite["id"]
                party_id = invite["party_id"]
                reply += f"Party ID: {party_id}, Codice Invito: {invite_id}\n"

            reply += "Utilizza il menù qui sotto per scegliere il prossimo step."

        await query.edit_message_text(reply, reply_markup=reply_markup)
        return INVITED

    elif result[1] == "INVITE":
        button = InlineKeyboardButton("BACK", callback_data="BACK")
        button1 = InlineKeyboardButton("ANNULLA", callback_data="ANNULLA")
        button2 = InlineKeyboardButton("USERNAME", callback_data="USERNAME")
        button3 = InlineKeyboardButton("CODICE", callback_data="CODE")
        keyboard = [[button2, button3],[button, button1]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Puoi invitare i giocatori in 2 modi:\nTramite il loro username identificativo pubblico (<@username>).\n\nTramite un codice unico generato automaticamente perfetto per invitare sopratutto gli utenti sprovvisti di username", reply_markup=reply_markup)
        return INVITE

    elif result[1] == "EXIT":
        party_id, isMaster = data_party.getPartyIsMaster(chat_id)
        reply = "Sei siuro di voler uscire dal party?"

        if isMaster:
            reply += "\n⚠️⚠️\nSei il master se esci dal party tutto il party verrà cancellato"

        button = InlineKeyboardButton("CONFERMA", callback_data="CONFERMA")
        button1 = InlineKeyboardButton("BACK", callback_data="BACK")
        keyboard = [[button, button1]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(reply, reply_markup=reply_markup)
        return EXIT

    elif result[1] == "SET":
        button1 = InlineKeyboardButton("BACK", callback_data="BACK")
        button2 = InlineKeyboardButton("ANNULLA", callback_data="ANNULLA")
        keyboard = []
        try:
            char = data_character.getCharacters(chat_id)

        except KeyError:
            reply = "Non hai personaggi disponibili, creane uno seguendo il menù del comando '/character'"
            keyboard = [[button1, button2]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(reply, reply_markup=reply_markup)
            return SET

        count = 0
        for i, c in enumerate(char):
            if not isinstance(c, int):
                name = c["nickname"]
                button = InlineKeyboardButton(f"{name}", callback_data=f"{i}")
                keyboard.append([button])
            else:
                count += 1

        keyboard.append([button1, button2])
        reply_markup = InlineKeyboardMarkup(keyboard)

        if count == 0:
            reply = "Non hai personaggi disponibili, creane uno seguendo il menù del comando '/character'"

        else:
            reply = "Seleziona uno dei tuoi personaggi da usare all'interno del party"

        await query.edit_message_text(reply, reply_markup=reply_markup)
        return SET

    elif result[1] == "KICK":
        party_id = data_party.getPartyID(chat_id)
        keyboard = []
        players = data_party.getMembers(party_id)

        for player in players:
            if player["chat_id"] != chat_id:
                name = player["name"]
                button = InlineKeyboardButton(f"Nome: {name}", callback_data=f"{name}!=!{party_id}")
                keyboard.append([button])

        button = InlineKeyboardButton("BACK", callback_data="BACK")
        button1 = InlineKeyboardButton("ANNULLA", callback_data="ANNULLA")
        keyboard.append([button, button1])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Quale membro del party vuoi kickare?", reply_markup=reply_markup)
        return KICK

async def kickButton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the buttons of kickPlayer"""
    query = update.callback_query
    chat_id = update.callback_query.from_user.id
    await query.answer()
    result = query.data
    logging.info(f"{chat_id}: Inside KickButton result = {result}")
    result = result.split("!=!")
    logging.info(f"{chat_id}: Inside KickButton after split result = {result}")

    # Building keyboard and button
    button = InlineKeyboardButton("BACK", callback_data="SI")
    button1 = InlineKeyboardButton("ANNULLA", callback_data="ANNULLA")
    keyboard = [[button, button1]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Remove player
    reply = await data_party.removePlayer(chat_id=None, party_id=int(result[1]), name=result[0])
    await query.edit_message_text(text=reply, reply_markup=reply_markup)

    logging.info("Returning PARTY state")
    return PARTY

async def exitParty(update:Update, context:ContextTypes.DEFAULT_TYPE):
    """Handle the exiting of a party"""
    query = update.callback_query
    chat_id = update.callback_query.from_user.id
    await query.answer()
    logging.info(f"{chat_id}: Inside exitParty")

    # Building keyboard and button
    button = InlineKeyboardButton("BACK", callback_data="SI")
    button1 = InlineKeyboardButton("ANNULLA", callback_data="ANNULLA")
    keyboard = [[button, button1]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Remove player
    reply = await data_party.removePlayer(chat_id=chat_id, party_id=None, name=None)
    await query.edit_message_text(reply, reply_markup=reply_markup)
    return PARTY

async def inviteCheck(update:Update, context:ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.callback_query.from_user.id
    await query.answer()
    result = query.data
    logging.info(f"{chat_id}: Inside inviteCheck")

    if result[0] == "A":
        username = query.from_user.username
        invites = data_invite.getInvites(username)

        keyboard = []
        for invite in invites:
            invite_id = invite["id"]
            party_id = invite["party_id"]
            button = InlineKeyboardButton(f"Party ID: {party_id}, Codice Invito: {invite_id}", callback_data=f"{party_id}-{invite_id}")
            keyboard.append([button])

        button = InlineKeyboardButton("BACK", callback_data="P JOIN")
        keyboard.append([button])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Selezione l'invito da accettare", reply_markup=reply_markup)
        return SEL

    elif result[0] == "I":
        button = InlineKeyboardButton("BACK", callback_data="P JOIN")
        button1 = InlineKeyboardButton("ANNULLA", callback_data="ANNULLA")
        keyboard = [[button, button1]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Scrivi il codice di invito che il master ha generato", reply_markup=reply_markup)
        return INSERISCI

async def generatedInvite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    invite_id = update.message.text
    button1 = InlineKeyboardButton("BACK", callback_data="P JOIN")
    button2 = InlineKeyboardButton("ANNULLA", callback_data="ANNULLA")
    keyboard = [[button1, button2]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if len(invite_id) < 4:
        reply = "Codice di invito non valido"
        party_id = 0
        await update.message.reply_text(reply, reply_markup=reply_markup)
        return INSERISCI

    else:
        invite_id = int(invite_id)
        name = update.message.from_user.full_name
        party_id, reply = await data_invite.joinParty(data_party, invite_id, chat_id, False, name)
        await update.message.reply_text(reply, reply_markup=reply_markup)

        if party_id > 0:
            dm_id = data_party.getMaster(party_id)
            await context.bot.send_message(chat_id=dm_id, text=f"L'utente {name} è appena entrato nel tuo party.")

            return PROCESS

        else:
            return INSERISCI


async def accepting_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.callback_query.message.chat_id
    logging.info(f"{chat_id}: dentro accepting_invite")

    await query.answer()
    result = query.data

    logging.info(f"before result = {result}")
    result = result.split("-")
    logging.info(f"after result = {result}")
    invite_id = int(result[1])
    party_id = data_party.getPartyID(chat_id)

    if party_id is None:
        party_id = int(result[0])
        name = update.callback_query.from_user.full_name
        username = update.callback_query.from_user.username
        party_id, reply = await data_invite.joinParty(data_party, invite_id, chat_id, username, name)
        # Building keyboard and button
        button = InlineKeyboardButton("BACK", callback_data="SI")
        button1 = InlineKeyboardButton("ANNULLA", callback_data="ANNULLA")
        keyboard = [[button, button1]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(reply, reply_markup=reply_markup)

        if party_id > 0:
            dm_id = data_party.getMaster(party_id)
            await context.bot.send_message(chat_id=dm_id, text=f"L'utente {name} è appena entrato nel tuo party.")


    return PARTY

async def invitePlayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.callback_query.message.chat_id
    logging.info(f"{chat_id}: dentro invitePlayer")

    await query.answer()
    result = query.data

    button1 = InlineKeyboardButton("BACK", callback_data="P INVITE")
    button2 = InlineKeyboardButton("ANNULLA", callback_data="ANNULLA")
    keyboard = [[button1, button2]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if result == "CODE":
        party_id = data_party.getPartyID(chat_id)
        invite_id = await data_invite.create(party_id, False)

        await query.edit_message_text(f"Ecco il codice invito: {invite_id}.\nÈ valido per un solo utente e può usarlo nella sezione 'CODICE' in '/party'", reply_markup=reply_markup)
        return PROCESS

    else:
        await query.edit_message_text("Scrivi il nickname della persona che vuoi invitare", reply_markup=reply_markup)
        return USERNAME

async def inviteUsername(update:Update, context:ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    username = update.message.text
    logging.info(f"{chat_id}: dentro inviteUsername")
    button1 = InlineKeyboardButton("BACK", callback_data="P INVITE")
    button2 = InlineKeyboardButton("ANNULLA", callback_data="ANNULLA")
    keyboard = [[button1, button2]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if username.startswith('@') is False:
        reply = "L'username non è valido.\nPerfavore inserisci un username valido del tipo <@username>"
        await update.message.reply_text(reply, reply_markup=reply_markup)
        return USERNAME

    username = username[1:]   #remove @
    party_id = data_party.getPartyID(chat_id)
    if await data_invite.checkInvite(username, party_id) is True:
        reply = f"l'utente @{username} è già stato invitato in questo party.\nL'invito può essere trovato nella sezione 'JOIN' del comando '/party'"
        await update.message.reply_text(reply, reply_markup=reply_markup)
        return USERNAME

    await data_invite.create(party_id, username)

    reply = f"L'utente @{username} è stato invitato correttamente.\nL'invito può essere trovato nella sezione 'JOIN' del comando '/party'"
    await update.message.reply_text(reply, reply_markup=reply_markup)
    return PROCESS

async def setCharacter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = update.callback_query.message.chat_id
    logging.info(f"{chat_id}: dentro setCharacter")

    await query.answer()
    result = query.data

    button1 = InlineKeyboardButton("BACK", callback_data="P SET")
    button2 = InlineKeyboardButton("ANNULLA", callback_data="ANNULLA")
    keyboard = [[button1, button2]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    reply = await data_party.setC(chat_id, int(result), data_character)

    await query.edit_message_text(reply, reply_markup=reply_markup)
    return PROCESS

if __name__ == '__main__':

    # application = ApplicationBuilder().token(TOKEN).arbitrary_callback_data(True).build()
    application = ApplicationBuilder().token(TOKEN).build()

    convRoll = ConversationHandler(
            entry_points=[CommandHandler("roll", roll)],
            states={
                DICE: [CallbackQueryHandler(diceStandard, pattern="^(\d+)$|^C$")],
                CUSTOMDICE: [MessageHandler(filters.Regex("(.+)"), diceCustom)]
            },
            fallbacks=[CallbackQueryHandler(cancelConversationQuery, pattern="^ANNULLA$")]
    )

    convCharacter = ConversationHandler(
            entry_points=[
                CommandHandler("character", startCharacter),
                ],
            states={
                LIST:[
                    CallbackQueryHandler(characterList, pattern="^SI$"),
                    CallbackQueryHandler(characterListMaster, pattern="^V$"),
                    ],
                SHEET:[
                    CallbackQueryHandler(sheetKeyboard, pattern="^SLOT(\d)$|^MEM(\d+)$"),
                    CallbackQueryHandler(characterList, pattern="^DEL(\d)$"),
                    ],
                CHOICE:[
                    CallbackQueryHandler(choiceSheet, pattern="^[RCBDFPSWIAH](\d)$|^[RCBDFPSWIAH]M(\d+)"),
                    CallbackQueryHandler(characterList, pattern="^I$"),
                    CallbackQueryHandler(characterListMaster, pattern="^M$"),
                    CallbackQueryHandler(editCharacter, pattern="^N(\d)$"),
                    ],
                EDIT:[
                    CallbackQueryHandler(editCharacter, pattern="^E[A-Z]\d|E[A-Z]M(\d+)$"),
                    CallbackQueryHandler(sheetKeyboard, pattern="^X(\d)$"),
                    CallbackQueryHandler(sheetKeyboard, pattern="^MEM(\d+)$"),
                    ],
                FINISHED:[
                    CallbackQueryHandler(choiceSheet, pattern="^[RCBDFPSWIAH](\d)$|^[RCBDFPSWIAH]M(\d+)"),
                    MessageHandler(filters.Regex("[\s\S]+"), settingEdit),
                    CallbackQueryHandler(sheetKeyboard, pattern="^SLOT(\d)$"),
                    ]
            },
            fallbacks=[CallbackQueryHandler(cancelConversationQuery, pattern="^ANNULLA$")]
    )

    convParty = ConversationHandler(
            entry_points=[
                CommandHandler('party', startParty),
                ],
            states={
                PARTY:[
                    CallbackQueryHandler(partyInfo, pattern="^SI$"),
                    ],
                PROCESS: [
                    CallbackQueryHandler(processParty, pattern="^P (\w)")
                    ],
                JOIN:[],
                KICK:[
                    CallbackQueryHandler(partyInfo, pattern="^BACK$"),
                    CallbackQueryHandler(kickButton, pattern="^.+!=!(\d+)$"),
                    ],
                EXIT:[
                    CallbackQueryHandler(partyInfo, pattern="^BACK$"),
                    CallbackQueryHandler(exitParty),
                    ],
                INVITED:[
                    CallbackQueryHandler(partyInfo, pattern="^BACK$"),
                    CallbackQueryHandler(inviteCheck)
                    ],
                INVITE:[
                    CallbackQueryHandler(partyInfo, pattern="^BACK$"),
                    CallbackQueryHandler(invitePlayer, pattern="^USERNAME$|^CODE$")
                    ],
                SEL: [
                    CallbackQueryHandler(processParty, pattern="^P JOIN$"),
                    CallbackQueryHandler(accepting_invite, "(\d+)-(\d+)$")
                    ],
                INSERISCI:[
                    CallbackQueryHandler(processParty, pattern="^P JOIN$"),
                    MessageHandler(filters.Regex("^(\d*)$"), generatedInvite),
                    ],
                USERNAME:[
                    CallbackQueryHandler(processParty, pattern="^P INVITE$"),
                    MessageHandler(filters.TEXT & (~filters.COMMAND), inviteUsername),
                    ],
                SET:[
                    CallbackQueryHandler(partyInfo, pattern="^BACK$"),
                    CallbackQueryHandler(processParty, pattern="^P SET$"),
                    CallbackQueryHandler(setCharacter, pattern="^0$|^1$|^2$")
                    ],
            },
            fallbacks=[CallbackQueryHandler(cancelConversationQuery, pattern="^ANNULLA$")],
    )

    application.add_handler(convCharacter)
    application.add_handler(convRoll)
    application.add_handler(convParty)

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', helpCommand))
    # Currency
    application.add_handler(CommandHandler('set_currency', setCurrency))
    application.add_handler(CommandHandler('pay', payCurrency))
    application.add_handler(CommandHandler('add_currency', addCurrency))
    application.add_handler(CommandHandler('show_currency', showCurrency))


    application.run_polling()
