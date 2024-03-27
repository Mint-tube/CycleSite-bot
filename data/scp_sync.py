from pymongo import MongoClient, timeout
from data.logging import *

__all__ = ["steam_sync", "update_role", "get_statistic"]

mongodb_client = MongoClient("mongodb://localhost:27017")
players = mongodb_client.players

main = players.main
syncroles = players.syncroles 
statistic = players.statistic


async def update_role(discord_id: int, discord_role_id: int):
    return

async def steam_sync(discord_id: int, steam_id: int):
    if steam_id == 0:
        syncroles.delete_one(filter={"DiscordId": discord_id})
        #Соединение разорвано -> No Content
        return (204,)

    current_steam = syncroles.find_one({"_id": steam_id})
    current_discord = syncroles.find_one({"DiscordId": discord_id})

    #Коды ответа соответсвуют HTTP
    if not current_steam and not current_discord: 
        syncroles.insert_one(document={"_id": steam_id, "DiscordId": discord_id, "RoleId": None, 'Exception': False})
        #Ни стим, ни дискорд ещё не привязаны -> Created
        return (201,)
    elif not current_steam:
        syncroles.delete_one(filter={"DiscordId": discord_id})
        syncroles.insert_one(document={"_id": steam_id, "DiscordId": discord_id, "RoleId": None, 'Exception': False})
        #Привязаный стим был изменён -> OK
        return (200,)
    elif current_steam['DiscordId'] != discord_id:
        #Стим уже привязан к другому дискорду -> Conflict
        return (409, current_steam['DiscordId'])
    elif current_steam == current_discord:
        #Стим уже привязан к этому дискорд -> Not Modified
        return (304,)
    else:
        #Пиздец -> Internal Server Error
        return (500,)

async def steam_sync_forced(discord_id: int, steam_id: int):
    syncroles.delete_one(filter={"_id": steam_id})
    syncroles.insert_one(document={"_id": steam_id, "DiscordId": discord_id, "RoleId": None, 'Exception': False})
    return None

async def get_statistic(type: str, id: int):
    match type:
        case "steam":
            steam_id = id
        case "discord":
            steam_id = syncroles.find_one(filter={"DiscordId": id})["_id"]
    return statistic.find_one(filter={"_id": steam_id})