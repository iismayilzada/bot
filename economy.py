import disnake
from disnake.ext import commands
import datetime
import random

import config
import database

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="balance", description="Показать баланс свой или другого пользователя.")
    async def balance(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member = None):
        target_user = user if user else inter.author
        user_data = database.get_user_data(target_user.id)
        balance = user_data[1] # balance is the second column
        bank = user_data[2] # bank is the third column

        embed = disnake.Embed(
            title=f"💰 Баланс {target_user.display_name}",
            color=disnake.Color.green()
        )
        embed.add_field(name="Наличные", value=f"`{balance:,}` монет", inline=True)
        embed.add_field(name="В банке", value=f"`{bank:,}` монет", inline=True)
        embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else target_user.default_avatar.url)
        embed.set_footer(text=f"Запросил: {inter.author.display_name}")
        await inter.response.send_message(embed=embed, ephemeral=False)

    async def _check_cooldown(self, inter: disnake.ApplicationCommandInteraction, user_id: int, command_type: str, cooldown_hours: int):
        last_claim_str = database.get_last_claim_time(user_id, command_type)
        if last_claim_str:
            last_claim_time = datetime.datetime.fromisoformat(last_claim_str)
            time_since_last_claim = datetime.datetime.now() - last_claim_time
            if time_since_last_claim.total_seconds() < cooldown_hours * 3600:
                remaining_time = datetime.timedelta(hours=cooldown_hours) - time_since_last_claim
                hours, remainder = divmod(int(remaining_time.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                await inter.response.send_message(
                    f"Вы уже использовали эту команду. Пожалуйста, подождите `{hours}ч {minutes}м {seconds}с`.",
                    ephemeral=True
                )
                return False
        return True

    @commands.slash_command(name="daily", description="Получите ежедневные монеты.")
    async def daily(self, inter: disnake.ApplicationCommandInteraction):
        if not await self._check_cooldown(inter, inter.author.id, "daily", 24):
            return

        database.update_user_balance(inter.author.id, config.DAILY_AMOUNT)
        database.update_last_claim_time(inter.author.id, "daily", datetime.datetime.now().isoformat())

        embed = disnake.Embed(
            title="🎁 Ежедневный Бонус!",
            description=f"Вы получили `{config.DAILY_AMOUNT}` монет!",
            color=disnake.Color.purple()
        )
        embed.set_thumbnail(url=inter.author.avatar.url if inter.author.avatar else inter.author.default_avatar.url)
        embed.set_footer(text=f"Следующий бонус через 24 часа.")
        await inter.response.send_message(embed=embed, ephemeral=False)

    @commands.slash_command(name="weekly", description="Получите еженедельные монеты.")
    async def weekly(self, inter: disnake.ApplicationCommandInteraction):
        if not await self._check_cooldown(inter, inter.author.id, "weekly", 7 * 24):
            return

        database.update_user_balance(inter.author.id, config.WEEKLY_AMOUNT)
        database.update_last_claim_time(inter.author.id, "weekly", datetime.datetime.now().isoformat())

        embed = disnake.Embed(
            title="🎉 Еженедельный Бонус!",
            description=f"Вы получили `{config.WEEKLY_AMOUNT}` монет!",
            color=disnake.Color.blue()
        )
        embed.set_thumbnail(url=inter.author.avatar.url if inter.author.avatar else inter.author.default_avatar.url)
        embed.set_footer(text=f"Следующий бонус через 7 дней.")
        await inter.response.send_message(embed=embed, ephemeral=False)

    @commands.slash_command(name="timely", description="Получите своевременные монеты.")
    async def timely(self, inter: disnake.ApplicationCommandInteraction):
        if not await self._check_cooldown(inter, inter.author.id, "timely", 2):
            return

        database.update_user_balance(inter.author.id, config.TIMELY_AMOUNT)
        database.update_last_claim_time(inter.author.id, "timely", datetime.datetime.now().isoformat())

        embed = disnake.Embed(
            title="⏱️ Своевременный Бонус!",
            description=f"Вы получили `{config.TIMELY_AMOUNT}` монет!",
            color=disnake.Color.orange()
        )
        embed.set_thumbnail(url=inter.author.avatar.url if inter.author.avatar else inter.author.default_avatar.url)
        embed.set_footer(text=f"Следующий бонус через 2 часа.")
        await inter.response.send_message(embed=embed, ephemeral=False)

    @commands.slash_command(name="work", description="Выполните работу, чтобы заработать монеты.")
    async def work(self, inter: disnake.ApplicationCommandInteraction):
        if not await self._check_cooldown(inter, inter.author.id, "work", 4):
            return

        database.update_user_balance(inter.author.id, config.WORK_AMOUNT)
        database.update_last_claim_time(inter.author.id, "work", datetime.datetime.now().isoformat())

        embed = disnake.Embed(
            title="👷 Работа!",
            description=f"Вы усердно поработали и заработали `{config.WORK_AMOUNT}` монет!",
            color=disnake.Color.brand_green()
        )
        embed.set_thumbnail(url=inter.author.avatar.url if inter.author.avatar else inter.author.default_avatar.url)
        embed.set_footer(text=f"Следующая работа доступна через 4 часа.")
        await inter.response.send_message(embed=embed, ephemeral=False)

    @commands.slash_command(name="addcoin", description="Добавить монеты пользователю. Только для персонала.")
    @commands.has_role(config.ADMIN_ROLE_ID) # Проверка роли администратора
    async def addcoin(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member, amount: int):
        if amount <= 0:
            await inter.response.send_message("Количество монет должно быть положительным.", ephemeral=True)
            return

        database.update_user_balance(user.id, amount)
        embed = disnake.Embed(
            title="✅ Монеты Добавлены",
            description=f"На баланс **{user.display_name}** добавлено `{amount:,}` монет.",
            color=disnake.Color.green()
        )
        embed.set_footer(text=f"Выполнил: {inter.author.display_name}")
        await inter.response.send_message(embed=embed)
        try:
            await user.send(f"На ваш баланс было добавлено `{amount:,}` монет администратором {inter.author.display_name}.")
        except disnake.HTTPException:
            pass # Не удалось отправить ЛС

    @addcoin.error
    async def addcoin_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingRole):
            await inter.response.send_message("У вас нет прав для использования этой команды.", ephemeral=True)
        else:
            await inter.response.send_message(f"Произошла ошибка: {error}", ephemeral=True)

    @commands.slash_command(name="deposit", description="Внести монеты в банк.")
    async def deposit(self, inter: disnake.ApplicationCommandInteraction, amount: int):
        user_data = database.get_user_data(inter.author.id)
        current_balance = user_data[1]

        if amount <= 0:
            await inter.response.send_message("Количество монет для внесения должно быть положительным.", ephemeral=True)
            return
        if amount > current_balance:
            await inter.response.send_message("У вас недостаточно монет на балансе.", ephemeral=True)
            return

        commission = int(amount * config.BANK_COMMISSION_PERCENT)
        net_amount = amount - commission

        database.update_user_balance(inter.author.id, -amount)
        database.update_user_bank(inter.author.id, net_amount)

        embed = disnake.Embed(
            title="🏦 Внесение в Банк",
            description=f"Вы успешно внесли `{amount:,}` монет в банк.",
            color=disnake.Color.blue()
        )
        embed.add_field(name="Комиссия", value=f"`{commission:,}` монет ({config.BANK_COMMISSION_PERCENT*100}%)", inline=False)
        embed.add_field(name="Внесено (чисто)", value=f"`{net_amount:,}` монет", inline=False)
        embed.set_footer(text=f"Ваш текущий баланс в банке: {database.get_user_data(inter.author.id)[2]:,}")
        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="withdraw", description="Снять монеты из банка.")
    async def withdraw(self, inter: disnake.ApplicationCommandInteraction, amount: int):
        user_data = database.get_user_data(inter.author.id)
        current_bank = user_data[2]

        if amount <= 0:
            await inter.response.send_message("Количество монет для снятия должно быть положительным.", ephemeral=True)
            return
        if amount > current_bank:
            await inter.response.send_message("У вас недостаточно монет в банке.", ephemeral=True)
            return

        commission = int(amount * config.BANK_COMMISSION_PERCENT)
        net_amount = amount - commission

        database.update_user_bank(inter.author.id, -amount)
        database.update_user_balance(inter.author.id, net_amount)

        embed = disnake.Embed(
            title="💸 Снятие из Банка",
            description=f"Вы успешно сняли `{amount:,}` монет из банка.",
            color=disnake.Color.dark_blue()
        )
        embed.add_field(name="Комиссия", value=f"`{commission:,}` монет ({config.BANK_COMMISSION_PERCENT*100}%)", inline=False)
        embed.add_field(name="Получено (чисто)", value=f"`{net_amount:,}` монет", inline=False)
        embed.set_footer(text=f"Ваш текущий баланс на руках: {database.get_user_data(inter.author.id)[1]:,}")
        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="rob", description="Попробуйте ограбить другого пользователя.")
    async def rob(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member):
        if user.bot:
            await inter.response.send_message("Вы не можете грабить ботов!", ephemeral=True)
            return
        if user.id == inter.author.id:
            await inter.response.send_message("Вы не можете ограбить самого себя!", ephemeral=True)
            return

        # Проверка кулдауна
        if not await self._check_cooldown(inter, inter.author.id, "rob", config.ROB_COOLDOWN_HOURS):
            return

        target_data = database.get_user_data(user.id)
        target_balance = target_data[1]

        if target_balance < 1000: # Минимальный баланс для ограбления
            await inter.response.send_message(f"{user.display_name} слишком беден, чтобы его грабить.", ephemeral=True)
            return

        result = random.randint(1, 100)
        await inter.response.defer(ephemeral=False) # Откладываем ответ, так как может быть задержка

        embed = disnake.Embed()
        embed.set_thumbnail(url=inter.author.avatar.url if inter.author.avatar else inter.author.default_avatar.url)
        embed.set_author(name=inter.author.display_name, icon_url=inter.author.avatar.url if inter.author.avatar else inter.author.default_avatar.url)

        if result <= config.ROB_CHANCE: # Успех
            stolen_amount = int(target_balance * config.ROB_SUCCESS_PERCENT)
            database.update_user_balance(user.id, -stolen_amount)
            database.update_user_balance(inter.author.id, stolen_amount)
            embed.title = "🎉 Ограбление Успешно!"
            embed.description = f"Вы успешно ограбили **{user.display_name}** и получили `{stolen_amount:,}` монет!"
            embed.color = disnake.Color.green()
            await inter.edit_original_response(embed=embed)
        elif result <= config.ROB_CHANCE + config.ROB_FAIL_CHANCE: # Поймали
            database.update_user_balance(inter.author.id, -config.ROB_FINE_AMOUNT) # Может уйти в минус
            embed.title = "🚨 Ограбление Неудачно!"
            embed.description = (
                f"Вас поймали при попытке ограбления **{user.display_name}**! "
                f"Вы оштрафованы на `{config.ROB_FINE_AMOUNT:,}` монет."
            )
            embed.color = disnake.Color.red()
            await inter.edit_original_response(embed=embed)
        else: # Неудача, без штрафа
            embed.title = "😅 Ограбление Не удалось"
            embed.description = f"Вы попытались ограбить **{user.display_name}**, но ничего не вышло. Вы не были пойманы."
            embed.color = disnake.Color.orange()
            await inter.edit_original_response(embed=embed)

        database.update_last_claim_time(inter.author.id, "rob", datetime.datetime.now().isoformat())

    @commands.slash_command(name="leaderboard", description="Посмотреть таблицу лидеров.")
    async def leaderboard(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=False)
        await self._send_leaderboard_embed(inter)

    async def _send_leaderboard_embed(self, inter: disnake.ApplicationCommandInteraction):
        embed = disnake.Embed(
            title="🏆 Таблица Лидеров",
            description="Выберите категорию топа:",
            color=disnake.Color.dark_teal()
        )
        embed.set_footer(text="Обновляется регулярно.")

        view = disnake.ui.View()
        view.add_item(disnake.ui.Button(style=disnake.ButtonStyle.blurple, label="Топ по Балансу", custom_id="leaderboard_balance"))
        view.add_item(disnake.ui.Button(style=disnake.ButtonStyle.green, label="Топ Месяца (Сообщения)", custom_id="leaderboard_month_messages"))
        view.add_item(disnake.ui.Button(style=disnake.ButtonStyle.red, label="Топ по Сообщениям (Всего)", custom_id="leaderboard_total_messages"))

        await inter.edit_original_response(embed=embed, view=view)

    @commands.Cog.listener("on_button_click")
    async def on_leaderboard_button_click(self, inter: disnake.MessageInteraction):
        if not inter.component.custom_id.startswith("leaderboard_"):
            return
        await inter.response.defer(ephemeral=False) # Откладываем ответ, чтобы успеть обновить сообщение

        leaderboard_type = inter.component.custom_id.split("_")[1]
        embed = disnake.Embed(color=disnake.Color.dark_teal())

        if leaderboard_type == "balance":
            leaderboard_data = database.get_leaderboard_balance()
            embed.title = "💰 Топ по Балансу"
            if leaderboard_data:
                description = ""
                for i, (user_id, balance) in enumerate(leaderboard_data):
                    user = self.bot.get_user(user_id)
                    username = user.display_name if user else f"Неизвестный пользователь ({user_id})"
                    description += f"**#{i+1}** {username}: `{balance:,}` монет\n"
                embed.description = description
            else:
                embed.description = "Пока нет данных для топа по балансу."
        elif leaderboard_type == "month_messages":
            leaderboard_data = database.get_leaderboard_month_messages()
            embed.title = "🗓️ Топ Месяца (Сообщения)"
            if leaderboard_data:
                description = ""
                for i, (user_id, count) in enumerate(leaderboard_data):
                    user = self.bot.get_user(user_id)
                    username = user.display_name if user else f"Неизвестный пользователь ({user_id})"
                    description += f"**#{i+1}** {username}: `{count:,}` сообщений\n"
                embed.description = description
            else:
                embed.description = "Пока нет данных для топа месяца."
        elif leaderboard_type == "total_messages":
            leaderboard_data = database.get_leaderboard_messages()
            embed.title = "💬 Топ по Сообщениям (Всего)"
            if leaderboard_data:
                description = ""
                for i, (user_id, count) in enumerate(leaderboard_data):
                    user = self.bot.get_user(user_id)
                    username = user.display_name if user else f"Неизвестный пользователь ({user_id})"
                    description += f"**#{i+1}** {username}: `{count:,}` сообщений\n"
                embed.description = description
            else:
                embed.description = "Пока нет данных для топа по сообщениям."
        else:
            await inter.followup.send("Неизвестный тип топа.", ephemeral=True)
            return

        embed.set_footer(text=f"Запросил: {inter.author.display_name}")

        view = disnake.ui.View()
        view.add_item(disnake.ui.Button(style=disnake.ButtonStyle.blurple, label="Топ по Балансу", custom_id="leaderboard_balance"))
        view.add_item(disnake.ui.Button(style=disnake.ButtonStyle.green, label="Топ Месяца (Сообщения)", custom_id="leaderboard_month_messages"))
        view.add_item(disnake.ui.Button(style=disnake.ButtonStyle.red, label="Топ по Сообщениям (Всего)", custom_id="leaderboard_total_messages"))

        await inter.edit_original_response(embed=embed, view=view)


def setup(bot):
    bot.add_cog(Economy(bot))