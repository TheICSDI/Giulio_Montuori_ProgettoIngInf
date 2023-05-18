import json
import asyncio
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

class DataManager(ABC):
    """
    Abstract class for maneging all different type of JSON file
    """

    # dict fileData
    # String filePwd


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

    async def create(self, chat_id, full_name):
        """
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
                }
            ]
        }
        self.fileData.append(new_party)
        await self.saveData()

    async def join(self, chat_id, party_id, full_name):
        """
        """
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
                })
                await self.saveData()
                return party_id, f"Unito con successo al party {party_id}!"
        return 0, "Party ID non valido. Per favore controlla l'ID e riprova."

    async def removePlayer(self, chat_id, party_id, name):
        """
        """
        for party in self.fileData:
            if party_id is None or party_id == party_id["id"]:
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

    def getMembers(self, party_id):
        """
        """
        for party in self.fileData:
            if party["id"] == party_id:
                return party["members"]

    def getPartyID(self, chat_id):
        """
        """
        for party in self.fileData:
            for member in party["members"]:
                if member["chat_id"] == chat_id:
                    return party["id"]

    def getPartyIsMaster(self, chat_id):
        """
        """
        for party in self.fileData:
            for member in party["members"]:
                if member["chat_id"] == chat_id:
                    return party["id"], member["master"]

        return None, False

    def getMaster(self, party_id):
        """
        """
        for party in self.fileData:
            if party_id == party["id"]:
                return party["members"][0]["chat_id"]
                # the first member is the master

class InviteManager(DataManager):
    """
    """

    async def create(self, party_id, username):
        """
        """
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


    async def joinParty(self, pM, invite_id, chat_id, username, full_name):
        """
        """
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

    def checkInvite(self, username, party_id):
        """
        """
        for invite in self.fileData:
            if (username == invite["username"] and party_id == invite["party_id"]):
                return True

        return False

    def getInvites(self, username):
        """
        """
        usr_invites = []
        for invite in self.fileData:
            if invite["username"] == username:
                usr_invites.append(invite)

        return usr_invites
