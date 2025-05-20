import disnake
from disnake.ext import commands, tasks
import datetime
import os
import asyncio

# Импортируем наши модули
import config
import database

# Инициализируем базу данных
database.init_db()

# Создаем папку data, если ее нет
if not os.path.exists('data'):
    os.makedirs('data')

# Инициализируем бота
bot = commands.Bot(command_prefix='!', intents=config.INTENTS, help_command=None)

# Событие, которое срабатывает, когда бот готов
@bot.event
async def on_ready():
    print(f'Бот {bot.user} вошел в систему!')
    print(f'ID бота: {bot.user.id}')
    print('--------------------')

    # Убедимся, что бот готов и кэши заполнены, прежде чем запускать задачи, которые зависят от этого.
    await bot.wait_until_ready()

    # Запускаем фоновые задачи, если они еще не запущены
    if not check_warn_expiry.is_running():
        check_warn_expiry.start()
    if not send_initial_shop_message.is_running():
        send_initial_shop_message.start()
    if not send_initial_inventory_message.is_running():
        send_initial_inventory_message.start()
    if not monthly_top_reset.is_running():
        monthly_top_reset.start()
    print("Фоновые задачи запущены.")


# Проверка истечения предупреждений
@tasks.loop(hours=1)
async def check_warn_expiry():
    await bot.wait_until_ready() # Убедимся, что бот готов
    now = datetime.datetime.now()
    with database.sqlite3.connect(database.DATABASE_NAME) as db:
        cursor = db.cursor()
        cursor.execute("""
            SELECT warn_id, user_id, reason FROM warnings
            WHERE is_active = 1 AND expire_date <= ?
        """, (now.isoformat(),))
        expired_warnings = cursor.fetchall()

        for warn_id, user_id, reason in expired_warnings:
            database.remove_warning(warn_id) # Помечаем как неактивное
            user = bot.get_user(user_id)
            if user:
                try:
                    await user.send(f"Ваше предупреждение **#{warn_id}** по причине: **'{reason}'** истекло.")
                except disnake.HTTPException:
                    print(f"Не удалось отправить ЛС пользователю {user.id} об истечении предупреждения.")

            # Логируем истечение предупреждения
            mod_log_channel = bot.get_channel(config.MOD_LOG_CHANNEL_ID)
            if mod_log_channel:
                embed = disnake.Embed(
                    title="Истечение Предупреждения",
                    description=f"Предупреждение для <@{user_id}> (ID: {user_id}) истекло.",
                    color=disnake.Color.orange(),
                    timestamp=now
                )
                embed.add_field(name="ID Предупреждения", value=warn_id, inline=True)
                embed.add_field(name="Причина", value=reason, inline=True)
                await mod_log_channel.send(embed=embed)
    print("Проверка истечения предупреждений завершена.")


# Отправка начального сообщения магазина
@tasks.loop(minutes=30) # Проверяем каждые 30 минут
async def send_initial_shop_message():
    await bot.wait_until_ready()
    shop_channel = bot.get_channel(config.SHOP_CHANNEL_ID)
    if shop_channel:
        # Проверяем, есть ли уже такое сообщение
        async for msg in shop_channel.history(limit=5): # Проверяем последние 5 сообщений
            if msg.author == bot.user and msg.embeds and "Добро пожаловать в магазин" in msg.embeds[0].title:
                return # Сообщение уже отправлено

        embed = disnake.Embed(
            title="🛒 Добро пожаловать в магазин!",
            description="Здесь вы можете приобрести различные предметы и улучшения за внутриигровую валюту.",
            color=disnake.Color.blue()
        )
        embed.set_thumbnail(url="https://i.imgur.com/your_shop_icon.png") # Замени на свою иконку магазина
        embed.add_field(name="Как пользоваться?", value="Нажмите на кнопку ниже, чтобы открыть главное меню магазина.", inline=False)

        view = disnake.ui.View()
        view.add_item(disnake.ui.Button(style=disnake.ButtonStyle.green, label="Открыть Магазин", custom_id="open_shop_menu"))

        await shop_channel.send(embed=embed, view=view)
        print(f"Инициализирующее сообщение магазина отправлено в канал {shop_channel.name}")

# Отправка начального сообщения инвентаря
@tasks.loop(minutes=30) # Проверяем каждые 30 минут
async def send_initial_inventory_message():
    await bot.wait_until_ready()
    inventory_channel = bot.get_channel(config.INVENTORY_CHANNEL_ID)
    if inventory_channel:
        async for msg in inventory_channel.history(limit=5):
            if msg.author == bot.user and msg.embeds and "🎒 Ваш Инвентарь" in msg.embeds[0].title:
                return

        embed = disnake.Embed(
            title="🎒 Ваш Инвентарь",
            description="Здесь хранятся все ваши купленные предметы: кейсы, купоны, роли.",
            color=disnake.Color.gold()
        )
        embed.set_thumbnail(url="https://i.imgur.com/your_inventory_icon.png") # Замени на свою иконку инвентаря
        embed.add_field(name="Как посмотреть?", value="Нажмите на кнопку ниже, чтобы открыть ваш инвентарь.", inline=False)

        view = disnake.ui.View()
        view.add_item(disnake.ui.Button(style=disnake.ButtonStyle.blurple, label="Открыть Инвентарь", custom_id="open_inventory_menu"))

        await inventory_channel.send(embed=embed, view=view)
        print(f"Инициализирующее сообщение инвентаря отправлено в канал {inventory_channel.name}")


# Ежемесячный сброс топа сообщений
_last_top_reset_month = None # Глобальная переменная для отслеживания последнего месяца сброса

@tasks.loop(hours=1) # Проверяем каждый час
async def monthly_top_reset():
    await bot.wait_until_ready()
    global _last_top_reset_month
    now = datetime.datetime.now()

    # Проверяем, если сегодня первое число месяца
    if now.day == config.TOP_MONTH_RESET_DAY:
        # Убеждаемся, что сброс был только один раз в текущем месяце
        if _last_top_reset_month != now.month:
            top_channel = bot.get_channel(config.TOP_MONTH_CHANNEL_ID)
            if top_channel:
                leaderboard = database.get_leaderboard_month_messages()
                if leaderboard:
                    embed = disnake.Embed(
                        title="🏆 Итоги Месячного Топа по Сообщениям!",
                        description="Поздравляем победителей прошлого месяца!",
                        color=disnake.Color.green(),
                        timestamp=now
                    )
                    for i, (user_id, count) in enumerate(leaderboard):
                        user = bot.get_user(user_id) # Получаем пользователя по ID
                        username = user.display_name if user else f"Неизвестный пользователь ({user_id})"
                        embed.add_field(name=f"#{i+1} {username}", value=f"Сообщений: `{count}`", inline=False)
                    await top_channel.send(embed=embed)
                database.reset_month_messages() # Сбрасываем счетчики
                _last_top_reset_month = now.month # Обновляем месяц последнего сброса
                print("Ежемесячный топ сообщений сброшен.")
            else:
                print(f"Канал для ежемесячного топа (ID: {config.TOP_MONTH_CHANNEL_ID}) не найден.")


# Загрузка когов
initial_extensions = [
    "cogs.economy",
    "cogs.moderation",
    "cogs.shop",
    "cogs.inventory",
    "cogs.events" # Этот ког будет обрабатывать сообщения для топа
]

for extension in initial_extensions:
    try:
        bot.load_extension(extension)
        print(f"Загружен ког: {extension}")
    except Exception as e:
        print(f"Не удалось загрузить ког {extension}: {e}")

# Запуск бота
bot.run(config.BOT_TOKEN)