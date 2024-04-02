from pymongo import MongoClient, timeout
from data.logging import *
import data.config as config
import requests

__all__ = ["steam_sync", "update_role", "get_stats"]

mongodb_client = MongoClient("mongodb://localhost:27017")
players = mongodb_client.players

main = players.main
syncroles = players.syncroles 
statistic = players.statistic


async def update_role(discord_id: int, discord_role_id: int):
    return

async def steam_sync(discord_id: int, steam: str):
    try:
        steam_id = int(steam)
    except ValueError:
        steam = steam[:-1] if steam[-1] == '/' else steam
        steam_usertag = steam.split('/')[-1]
        api_response = requests.get(f'http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={config.steam_api_key}&vanityurl={steam_usertag}')
        if api_response.status_code == 200:
            steam_id = int(api_response.json()['response']['steamid'])
        else:
            error(api_response.status_code, api_response.json()['response']['message'])

    if steam_id == 0:
        syncroles.delete_one(filter={"DiscordId": discord_id})
        #Соединение разорвано -> No Content
        return (204, None, steam_id)

    current_steam = syncroles.find_one({"_id": steam_id})
    current_discord = syncroles.find_one({"DiscordId": discord_id})

    #Коды ответа соответсвуют HTTP
    if not current_steam and not current_discord: 
        syncroles.insert_one(document={"_id": steam_id, "DiscordId": discord_id, "RoleId": None, 'Exception': False})
        #Ни стим, ни дискорд ещё не привязаны -> Created
        return (201, None, steam_id)
    elif not current_steam:
        syncroles.delete_one(filter={"DiscordId": discord_id})
        syncroles.insert_one(document={"_id": steam_id, "DiscordId": discord_id, "RoleId": None, 'Exception': False})
        #Привязаный стим был изменён -> OK
        return (200, None, steam_id)
    elif current_steam['DiscordId'] != discord_id:
        #Стим уже привязан к другому дискорду -> Conflict
        return (409, current_steam['DiscordId'],  steam_id)
    elif current_steam == current_discord:
        #Стим уже привязан к этому дискорд -> Not Modified
        return (304, None,  steam_id)
    else:
        #Пиздец -> Internal Server Error
        return (500, None, steam_id)

async def steam_sync_forced(discord_id: int, steam_id: int):
    syncroles.delete_one(filter={"_id": steam_id})
    if steam_id != 0:
        syncroles.insert_one(document={"_id": steam_id, "DiscordId": discord_id, "RoleId": None, 'Exception': False})
    return None

async def get_stats(discord_id: int):
    steam_id = syncroles.find_one(filter={"DiscordId": id})["_id"]
    stats = statistic.find_one(filter={"_id": steam_id})
    main = main.find_one(filter={"_id": steam_id}) 
    return stats, main