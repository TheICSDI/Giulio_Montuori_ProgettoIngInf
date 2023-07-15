from abc import ABC, abstractmethod
import json
import asyncio
import random
import copy
from datetime import datetime, timedelta

class DataManager(ABC):
    """
    Abstract class for managing all different type of JSON file
    """

    def __init__(self, filePwd):
        """
        Class constructor
        Open the json file and load its value in self.fileData
        """
        self.filePwd = filePwd
        with open(self.filePwd, "r") as f:
            self.fileData = json.load(f)

        self.lock = asyncio.Lock()

    async def saveData(self):
        """
        Save the current fileData in the JSON file
        """
        async with self.lock:
            with open(self.filePwd, "w") as f:
                json.dump(self.fileData, f, indent=2)

    async def getLastId(self):
        """
        Get the last current id
        """
        async with self.lock:
            return self.fileData[-1]["id"]

    @abstractmethod
    def create(self):
        """
        Create a new entry
        """
        pass

class PartyManager(DataManager):
    """
    Class for managing the party json data
    """

    async def create(self, chat_id, full_name):
        """
        Implement the father's method
        return the party_id
        """
        party_id = await self.getLastId() + 1
        new_party = {
            "id": party_id,
            "members": [
                {
                    "chat_id": chat_id,
                    "name": full_name,
                    "character": None,
                    "master": True,
                    "currency":
                    {
                        "copper": 0,
                        "silver": 0,
                        "electrum": 0,
                        "gold": 0,
                        "platinum": 0,
                    }
                }
            ]
        }
        self.fileData.append(new_party)
        await self.saveData()
        return party_id

    async def join(self, chat_id, party_id, full_name):
        """ Join an existing party """

        for party in self.fileData:
            if party["id"] == party_id:
                for member in party["members"]:
                    if member["chat_id"] == chat_id:
                        return 0, "Fai già parte di questo party"

                party["members"].append({
                    "chat_id": chat_id,
                    "name": full_name,
                    "character": None,
                    "master": False,
                    "currency":
                    {
                        "copper": 0,
                        "silver": 0,
                        "electrum": 0,
                        "gold": 0,
                        "platinum": 0,
                    }
                })
                await self.saveData()
                return party_id, f"Unito con successo al party {party_id}!"
        return 0, "Party ID non valido."

    async def removePlayer(self, chat_id, party_id, name):
        """ Remove a pleyer from an existing party """

        for party in self.fileData:
            if party_id is None or party["id"] == party_id:
                for member in party["members"]:

                    if name is None:

                        if (member["chat_id"] == chat_id and member["master"] is False):
                            party["members"].remove(member)
                            await self.saveData()
                            return "Rimosso con successo dal party!"

                        if (member["chat_id"] == chat_id and member["master"] is True):
                            # TODO dovrei notificare gli altrimemebri della chiusura del party
                            self.fileData.remove(party)
                            await self.saveData()
                            return "Rimosso dal party e party eliminato con successo."

                    else:
                        if member["name"] == name:
                            party["members"].remove(member)
                            await self.saveData()
                            return f"Player {name} rimosso con successo"

                if party_id is not None:
                    return "L'utente non è presente nel party"

        return "Non sei presente in nessun party"

    async def setC(self, chat_id, index, data_c):
        """ Set Character of a specific user in his party """

        c_list = data_c.getCharacters(chat_id)
        party_id = self.getPartyID(chat_id)

        character_name = c_list[index]["nickname"]
        for party in self.fileData:
            if party["id"] == party_id:
                for member in party["members"]:
                    if member["chat_id"] == chat_id:
                        member["character"] = character_name
                        await self.saveData()
                        return f"{character_name} impostato come personaggio per il party"

    async def operCurrency(self, chat_id, character, currency, ammount):
        """ Handle all the operations with Currency """

        currencies = ["copper", "silver", "electrum", "gold", "platinum"]

        if currency.lower() not in currencies:
            return "Monenta inserita non è valida.\nLe monente valide sono \"Copper\" \"Silver\" \"Electrum\" \"Gold\" \"Platinum\"."

        party_id = self.getPartyID(chat_id)
        members = self.getMembers(party_id)
        for member in members:
            if member["character"] == character:
                for c in member["currency"]:
                    if c == currency:
                        member["currency"][currency] += int(ammount)
                        await self.saveData()
                        return "Operazione completata con successso 😄"

        return "Operazione fallita ❌"

    async def setCurrency(self, chat_id, character, currency, ammount):
        """ Setter of a specific type of Currency """

        currencies = ["copper", "silver", "electrum", "gold", "platinum"]

        if currency not in currencies:
            return "Monenta inserita non è valida.\nLe monente valide sono \"Copper\" \"Silver\" \"Electrum\" \"Gold\" \"Platinum\"."

        party_id = self.getPartyID(chat_id)
        members = self.getMembers(party_id)
        for member in members:
            if member["character"] == character:
                for c in member["currency"]:
                    if c == currency:
                        member["currency"][currency] = int(ammount)
                        await self.saveData()
                        return "Operazione completata con successo 😄"

        return "Operazione fallita ❌"

    def getMembers(self, party_id):
        """
        Get members for an existing party
        return a list of members
        """

        for party in self.fileData:
            if party["id"] == party_id:
                return party["members"]

    def getPartyID(self, chat_id):
        """ Get the party id from a chat_id """

        for party in self.fileData:
            for member in party["members"]:
                if member["chat_id"] == chat_id:
                    return party["id"]

        return None

    def getPartyIsMaster(self, chat_id):
        """ Get the party id and check if that user is the master """

        for party in self.fileData:
            for member in party["members"]:
                if member["chat_id"] == chat_id:
                    return party["id"], member["master"]

        return None, False

    def getMaster(self, party_id):
        """ Get the chat id of the master form a specific party """

        for party in self.fileData:
            if party_id == party["id"]:
                return party["members"][0]["chat_id"]
                # the first member is the master

class InviteManager(DataManager):
    """
    Class for managing the invite json data
    """

    async def create(self, party_id, username):
        """ Implement the father's method """

        invite_id = await self.getLastId() + 1

        expiration_time = datetime.now() + timedelta(hours=48)
        expiration_time = expiration_time.strftime("%d/%m/%Y %H:%M:%S") # converto in stringa

        new_invite = {
            "id": invite_id,
            "expiration": expiration_time,
            "party_id": party_id,
            "username": username,
        }
        self.fileData.append(new_invite)
        await self.saveData()

        if username is False:
            return invite_id


    async def joinParty(self, pM, invite_id, chat_id, username, full_name):
        """ Joining a party through an invite """

        for invite in self.fileData:
            if (invite["id"] == invite_id and invite["username"] == username):
                expiration_time = datetime.strptime(invite["expiration"], "%d/%m/%Y %H:%M:%S")
                if datetime.now() > expiration_time:
                    self.fileData.remove(invite)
                    await self.saveData()
                    return 0, "Il codice di invito è scaduto. Chiedi al Master del party di generare un nuovo invito."

                party_id = invite["party_id"]
                self.fileData.remove(invite)
                await self.saveData()
                p, r = await pM.join(chat_id, party_id, full_name)
                return p, r

            if invite["id"] > invite_id:
                break

        return 0, "Codice di invito non valido"

    async def checkInvite(self, username, party_id):
        """ Check if the user as a valid pending invite for that specific party """

        for invite in self.fileData:
            if username == invite["username"] and party_id == invite["id"]:
                expiration_time = datetime.strptime(invite["expiration"], "%d/%m/%Y %H:%M:%S")
                if datetime.now() > expiration_time:
                    return True

                self.fileData.remove(invite)
                await self.saveData()
                return False

        return False

    def getInvites(self, username):
        """ Get a list of a valid invite form a specific user """

        usr_invites = []
        for invite in self.fileData:
            if invite["username"] == username:
                usr_invites.append(invite)

        return usr_invites

class CharacterManager(DataManager):
    """
    Class for managing the character json data
    """

    async def create(self, chat_id):
        """ Implement the father method and create an entry of a player in the json """

        base = copy.deepcopy(self.fileData["100000"])
        self.fileData[str(chat_id)] = base
        await self.saveData()

    async def createCharacter(self, chat_id, index):
        """ Create an empty templete of a character"""

        base = copy.deepcopy(self.fileData["100000"][0])
        self.fileData[str(chat_id)][int(index)] = base
        await self.saveData()

    async def removeCharacter(self, party, chat_id, index):
        """ Remove an entry of a character"""
        self.fileData[str(chat_id)][int(index)] = 0

        party_id = party.getPartyID(chat_id)
        if party_id is not None:
            members = party.getMembers(party_id)
            for m in members:
                if m["character"] is not None:
                    m["character"] = None
                    await party.saveData()

        await self.saveData()

    async def setValue(self, chat_id, slot, key, value):
        """ Set a value of a attribute in the character dict """

        try:
            data = copy.deepcopy(self.fileData[str(chat_id)][int(slot)])  # make a deep copy of the data
            words = key.split('->')

            current = data

            for word in words[:-1]:
                if isinstance(current, list):
                    current = current[int(word)]
                else:
                    current = current[word]

            last_key = words[-1]
            # Handle boolean values
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            if isinstance(current, list):
                current[int(last_key)] = value
            else:
                current[last_key] = value

            self.fileData[str(chat_id)][int(slot)] = data  # assign the modified data back
            await self.saveData()
            return f"✅ Setting updated successfully to {value}"

        except KeyError:
            return None

    def getCharacters(self, chat_id):
        """ Getter of all the character from a specific player """

        if str(chat_id) in self.fileData:
            c = self.fileData[str(chat_id)]

        else:
            raise KeyError(f"No characters found for chat_id: {chat_id}")
        return c

    def fullKey(self, Key):
        """ Convert the short key to a full size key """

        section_keys = {
            "A": "attribute",
            "H": "healt",
            "R": "race",
            "C": "class",
            "B": "background",
            "D": "details",
            "F": "feats",
            "P": "proficiencies",  # using proficiencies for both case weapon and armor
            "S": "spells",
            "W": "weapons",
            "I": "indietro",
        }

        try:
            Key = section_keys[Key]

        except KeyError:
            return None

        return Key
