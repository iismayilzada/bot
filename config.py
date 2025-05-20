import disnake

# Токен бота Discord. НЕ ПОКАЗЫВАЙ ЕГО НИКОМУ!
BOT_TOKEN = "MTM3NDM5MTQ4MzE3NTY2NTc0NQ.GmqnXl.czKM09bKwNUa7fMW6nvinuf1sRA-7WzBzW_ngE"

# ID каналов
SHOP_CHANNEL_ID = 1374391945962455090  # Канал магазина
INVENTORY_CHANNEL_ID = 1374392217925320745 # Канал инвентаря
MOD_LOG_CHANNEL_ID = 1374393333333333333 # Канал для логов модерации (замени на реальный ID)
TICKET_CATEGORY_ID = 1374395514438553680 # Категория для тикетов купонов

# ID ролей
ADMIN_ROLE_ID = 1358080308917961017 # Роль администратора/модератора для доступа к админским командам

# Цены кейсов
CASE_PRICES = {
    "fire_case": 6000,
    "blazing_case": 9000,
    "hell_case": 15000,
}

# Цены купонов
COUPON_PRICES = {
    "nitro_coupon": 120000,
    "decoration_coupon": 120000,
}

# Разрешенные интенты для бота
INTENTS = disnake.Intents.default()
INTENTS.message_content = True
INTENTS.members = True # Важно для модерации и балансов пользователей
INTENTS.presences = True # Для некоторых функций, если понадобится

# Настройки экономики
DAILY_AMOUNT = 150
WEEKLY_AMOUNT = 800
TIMELY_AMOUNT = 50
WORK_AMOUNT = 100

ROB_CHANCE = 20 # Шанс успеха ограбления в %
ROB_FAIL_CHANCE = 60 # Шанс быть пойманным в %
ROB_COOLDOWN_HOURS = 15
ROB_SUCCESS_PERCENT = 0.10 # 10% от баланса
ROB_FINE_AMOUNT = 50000 # Штраф за неудачное ограбление

BANK_COMMISSION_PERCENT = 0.04 # 4% комиссия

WARN_DURATION_DAYS = 14 # Длительность предупреждения в днях

# Настройки топов (для топ месяца)
TOP_MONTH_RESET_DAY = 1 # День месяца для сброса топа (например, 1 число каждого месяца)
TOP_MONTH_CHANNEL_ID = 1374394444444444444 # Канал для отчета о победителях топа месяца (замени на реальный ID)