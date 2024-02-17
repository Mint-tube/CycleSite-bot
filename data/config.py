from enum import Enum

token = 'MTE4ODAyNDA1Nzg3OTMzNDk3NA.GnOFjw.a56IrzEUjsRxOIRCVMndz2ntIZIfycmq4eD1q4' #Токен бота 
guild = '1122085072577757275' #Сервер на котором работает бот
naga_api_key = 'ng-IqawEKgW5IEZABcbQTns4nYCbCsaB'

bot_engineers = [554281270260006914, 949708119334854658] #Банхаммеры, 05 и прочие диктаторы
admin_role = 1138744407135354970 #Роль Администратора
secretary_role = 1194921855690219570 #Роль Администратора заявок
nitro_booster_id = 1122867829662814279
muted_role = 1134749599307939903

#Цвета
info = 0x5c5eff
danger = 0xda4957
warning = 0xf9c327
success = 0x44d936

auto_cancel_time = 15 #Время автоматической отмены подтверждения в секундах
very_serious_categories = [1123186876724035624, 1132586162356244480, 1132614501200568452, 1133666070390132776] #Категории без рандомных реакций
very_secret_categories = [1189653594845220884, 1195776115613126738, 1123186876724035624, 1195776029973819533] #Категории с логами в отельный канал
tickets_log_channel = 1174675122976735353 #Канал для логов закрытых тикетов
warns_log_channel = 1133679118882459675 #Канал для логов предупреждений
ai_channels = [1195776115613126738, 1172161486630686751] #Каналы для чата с ботом


class webhooks():
    main_logs = 'https://discord.com/api/webhooks/1172796781562703932/md7f5TJhqwlSB_zwxEvLiIPvmifUVUHkJHvg0hWvpeK0qU6CgQVrtgO5ybswKD6NLydB'
    private_logs = 'https://discord.com/api/webhooks/1203371359745609840/IBgMhj0iC07U6UizACoydbGjRser2L-VEeqtbqjH8UC-H2W63B1ebX5UZuzei-_4Pndy'
    voice_logs = 'https://discord.com/api/webhooks/1204502508752470106/7MJT-4YE0IpK5aGdfVoFy_wTuPnOKnzWmkf1M2Jp1uiX9Te_NjEAE7E2kp7p0yDNMnFK'
