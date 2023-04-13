import json
from datetime import datetime, timedelta

with open("JSON/dnd_data.json", "r") as f:
    dnd_data = json.load(f)

def save_data():
    with open("JSON/dnd_data.json", "w") as f:
        json.dump(dnd_data, f, indent=2)

def get_last_id(key):

    if key == "parties":
        return dnd_data["parties"][-1]["id"]

    elif key == "invites":
        return dnd_data["invites"][-1]["invite_code"]

def getParty_isMaster(chat_id):

    for party in dnd_data["parties"]:
        for member in party["members"]:
            if member["chat_id"] == chat_id:
                return party["id"], member["master"]

    return None, False

def get_dm_id(party_id):
    for party in dnd_data["parties"]:
        if party_id == party["id"]:
            return party["members"][0]["chat_id"]

    return 0

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

def get_party(party_id):

    for party in dnd_data["parties"]:
        if party["id"] == party_id:
            return party["members"]

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
