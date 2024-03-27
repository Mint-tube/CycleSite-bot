from pymongo import MongoClient, timeout

__all__ = ["steam_sync", "update_role", "statistic"]

mongodb_client = MongoClient("mongodb://localhost:27017")
players = mongodb_client.players

syncroles = players.syncroles 
syncroles = players.syncroles 
statistic = players.statistic


async def steam_sync(discord_id: int, steam_id: int):
    current_steam = syncroles.find_one({"_id": steam_id})
    current_discord = syncroles.find_one({"DiscordId": discord_id})

    #Коды ответа соответсвуют HTTP
    if current_steam == None and current_discord == None: 
        syncroles.insert_one(document={"_id": steam_id, "DiscordId": discord, "RoleId": None, 'Exception': False})
        #Ни стим, ни дискорд ещё не привязаны -> Created
        return (201,)
    elif current_steam['DiscordId'] != None and current_steam['DiscordId'] != discord_id:
        #Стим уже привязан к другому дискорду -> Conflict
        return (409, current_steam['DiscordId'])
    elif current_steam['DiscordId'] == discord_id and current_discord['_id'] == steam_id:
        #Стим уже привязан к этому дискорд -> Not Modified
        return (304,)
    else:
        syncroles.update_one(filter={"_id": steam_id}, update={"DiscordId": discord_id})
        #Привязаный стим был изменён -> OK
        return (200,)
