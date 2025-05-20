import disnake
from disnake.ext import commands
import random
import asyncio

import config
import database

class InventoryMenu(disnake.ui.View):
    def __init__(self, bot_instance: commands.Bot):
        super().__init__(timeout=180)
        self.bot_instance = bot_instance

    async def on_timeout(self):
        for item in self.children:
            if isinstance(item, (disnake.ui.Button, disnake.ui.Select)):
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(content="Меню инвентаря истекло.", view=self)
            except disnake.NotFound:
                pass

    @disnake.ui.button(label="Мои Роли", style=disnake.ButtonStyle.blurple, custom_id="inventory_roles")
    async def roles_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self.send_roles_inventory(inter)

    @disnake.ui.button(label="Мои Кейсы", style=disnake.ButtonStyle.green, custom_id="inventory_cases")
    async def cases_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self.send_cases_inventory(inter)

    @disnake.ui.button(label="Мои Купоны", style=disnake.ButtonStyle.red, custom_id="inventory_coupons")
    async def coupons_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self.send_coupons_inventory(inter)

    async def send_roles_inventory(self, inter: disnake.MessageInteraction):
        items = database.get_inventory_items(inter.author.id)
        user_roles = [item for item in items if item[0] == "role"]

        embed = disnake.Embed(
            title="👑 Ваши Купленные Роли",
            description="Здесь отображаются купленные вами роли. Вы можете надеть или снять их.",
            color=disnake.Color.dark_purple()
        )
        embed.set_thumbnail(url=inter.author.avatar.url if inter.author.avatar else inter.author.default_avatar.url)

        options = []
        if not user_roles:
            embed.description += "\n\nУ вас пока нет купленных ролей."
        else:
            for item_type, role_id_str, quantity in user_roles:
                role_id = int(role_id_str)
                role = inter.guild.get_role(role_id)
                if role:
                    options.append(disnake.SelectOption(label=f"{role.name}", value=str(role.id)))
                else:
                    # Если роль удалена с сервера, предлагаем удалить из инвентаря
                    options.append(disnake.SelectOption(label=f"Неизвестная роль (ID: {role_id}) - Удалить из инвентаря", value=f"delete_missing_role_{role_id}"))


        view = disnake.ui.View()
        if options:
            select = disnake.ui.StringSelect(
                placeholder="Выберите роль для действия...",
                custom_id="select_role_action",
                options=options
            )
            view.add_item(select)
        view.add_item(disnake.ui.Button(label="⬅️ Назад в Инвентарь", style=disnake.ButtonStyle.secondary, custom_id="inventory_back_to_main"))

        await inter.response.edit_message(embed=embed, view=view)

    async def send_cases_inventory(self, inter: disnake.MessageInteraction):
        items = database.get_inventory_items(inter.author.id)
        user_cases = [item for item in items if item[0] == "case"]

        embed = disnake.Embed(
            title="🎁 Ваши Кейсы",
            description="Здесь отображаются ваши кейсы. Откройте их, чтобы получить призы!",
            color=disnake.Color.dark_gold()
        )
        embed.set_thumbnail(url=inter.author.avatar.url if inter.author.avatar else inter.author.default_avatar.url)

        options = []
        if not user_cases:
            embed.description += "\n\nУ вас пока нет кейсов."
        else:
            for item_type, case_type, quantity in user_cases:
                options.append(disnake.SelectOption(label=f"{case_type.replace('_', ' ').title()} ({quantity})", value=case_type))

        view = disnake.ui.View()
        if options:
            select = disnake.ui.StringSelect(
                placeholder="Выберите кейс для открытия...",
                custom_id="select_case_open",
                options=options
            )
            view.add_item(select)
        view.add_item(disnake.ui.Button(label="⬅️ Назад в Инвентарь", style=disnake.ButtonStyle.secondary, custom_id="inventory_back_to_main"))

        await inter.response.edit_message(embed=embed, view=view)

    async def send_coupons_inventory(self, inter: disnake.MessageInteraction):
        items = database.get_inventory_items(inter.author.id)
        user_coupons = [item for item in items if item[0] == "coupon"]

        embed = disnake.Embed(
            title="🎟️ Ваши Купоны",
            description="Здесь отображаются ваши купоны. Активируйте их, чтобы получить бонусы!",
            color=disnake.Color.dark_magenta()
        )
        embed.set_thumbnail(url=inter.author.avatar.url if inter.author.avatar else inter.author.default_avatar.url)

        options = []
        if not user_coupons:
            embed.description += "\n\nУ вас пока нет купонов."
        else:
            for item_type, coupon_type, quantity in user_coupons:
                options.append(disnake.SelectOption(label=f"{coupon_type.replace('_', ' ').title()} ({quantity})", value=coupon_type))

        view = disnake.ui.View()
        if options:
            select = disnake.ui.StringSelect(
                placeholder="Выберите купон для активации...",
                custom_id="select_coupon_activate",
                options=options
            )
            view.add_item(select)
        view.add_item(disnake.ui.Button(label="⬅️ Назад в Инвентарь", style=disnake.ButtonStyle.secondary, custom_id="inventory_back_to_main"))

        await inter.response.edit_message(embed=embed, view=view)


class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_button_click")
    async def on_inventory_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id == "open_inventory_menu":
            embed = disnake.Embed(
                title="🎒 Ваше Меню Инвентаря",
                description="Выберите категорию предметов:",
                color=disnake.Color.gold()
            )
            embed.set_footer(text=f"Ваш баланс: {database.get_user_data(inter.author.id)[1]:,} монет")
            view = InventoryMenu(self.bot)
            await inter.response.send_message(embed=embed, view=view, ephemeral=True)

        elif inter.component.custom_id == "inventory_back_to_main":
            embed = disnake.Embed(
                title="🎒 Ваше Меню Инвентаря",
                description="Выберите категорию предметов:",
                color=disnake.Color.gold()
            )
            embed.set_footer(text=f"Ваш баланс: {database.get_user_data(inter.author.id)[1]:,} монет")
            view = InventoryMenu(self.bot)
            await inter.response.edit_message(embed=embed, view=view)

        elif inter.component.custom_id.startswith("toggle_role_"):
            role_id = int(inter.component.custom_id.split("_")[2])
            role = inter.guild.get_role(role_id)
            if not role:
                await inter.response.send_message("Эта роль не найдена на сервере. Возможно, она была удалена.", ephemeral=True)
                await inter.message.edit(view=None) # Закрываем меню
                return

            member = inter.author
            if role in member.roles:
                try:
                    await member.remove_roles(role)
                    await inter.response.send_message(f"Вы сняли роль **{role.name}**.", ephemeral=True)
                except disnake.Forbidden:
                    await inter.response.send_message("У меня нет прав для снятия этой роли. Проверьте мои разрешения.", ephemeral=True)
                except Exception as e:
                    await inter.response.send_message(f"Произошла ошибка при снятии роли: {e}", ephemeral=True)
            else:
                try:
                    await member.add_roles(role)
                    await inter.response.send_message(f"Вы надели роль **{role.name}**.", ephemeral=True)
                except disnake.Forbidden:
                    await inter.response.send_message("У меня нет прав для выдачи этой роли. Проверьте мои разрешения.", ephemeral=True)
                except Exception as e:
                    await inter.response.send_message(f"Произошла ошибка при выдаче роли: {e}", ephemeral=True)
            
            # После действия с ролью, возвращаем пользователя к списку ролей в инвентаре
            inventory_menu_view = InventoryMenu(self.bot)
            await inventory_menu_view.send_roles_inventory(inter)


        elif inter.component.custom_id.startswith("confirm_delete_missing_role_"):
            role_id = int(inter.component.custom_id.split("_")[3])
            database.remove_inventory_item(inter.author.id, "role", str(role_id))
            await inter.response.edit_message(content=f"Несуществующая роль (ID: `{role_id}`) успешно удалена из вашего инвентаря.", embed=None, view=None)
            # Возвращаем пользователя к обновленному списку ролей
            inventory_menu_view = InventoryMenu(self.bot)
            await inventory_menu_view.send_roles_inventory(inter)

        elif inter.component.custom_id == "cancel_action":
            await inter.response.edit_message(content="Действие отменено.", embed=None, view=None)

        elif inter.component.custom_id.startswith("confirm_open_case_"):
            case_type = inter.component.custom_id.split("_")[3]
            quantity = database.get_inventory_item_quantity(inter.author.id, "case", case_type)

            if quantity < 1:
                await inter.response.edit_message(content="У вас больше нет этого кейса.", embed=None, view=None)
                return

            database.remove_inventory_item(inter.author.id, "case", case_type, 1)

            # Логика открытия кейса (пример)
            prizes = {
                "fire_case": {
                    "common": [500, 1000, 1500],
                    "uncommon": [2000, 2500],
                    "rare": [3000, 4000],
                    "epic": [5000, 7000]
                },
                "blazing_case": {
                    "common": [1000, 2000, 3000],
                    "uncommon": [4000, 5000],
                    "rare": [6000, 8000],
                    "epic": [10000, 15000]
                },
                "hell_case": {
                    "common": [2000, 4000, 6000],
                    "uncommon": [8000, 10000],
                    "rare": [12000, 15000],
                    "epic": [20000, 30000]
                }
            }
            
            # Процентное распределение (можно настроить)
            chances = {
                "common": 60,
                "uncommon": 25,
                "rare": 10,
                "epic": 5
            }

            rand = random.randint(1, 100)
            prize_rarity = ""
            current_chance = 0
            for rarity, chance in chances.items():
                current_chance += chance
                if rand <= current_chance:
                    prize_rarity = rarity
                    break
            
            reward_amount = random.choice(prizes[case_type][prize_rarity])
            database.update_user_balance(inter.author.id, reward_amount)

            embed = disnake.Embed(
                title=f"🎉 Вы Открыли {case_type.replace('_', ' ').title()}!",
                description=f"Вы получили `{reward_amount:,}` монет!",
                color=disnake.Color.orange()
            )
            embed.add_field(name="Редкость", value=prize_rarity.title(), inline=True)
            embed.set_footer(text=f"Осталось {quantity - 1} кейсов {case_type.replace('_', ' ').title()} | Ваш баланс: {database.get_user_data(inter.author.id)[1]:,} монет")
            await inter.response.edit_message(embed=embed, view=None)

            # Возвращаем пользователя к списку кейсов
            inventory_menu_view = InventoryMenu(self.bot)
            await inventory_menu_view.send_cases_inventory(inter)

        elif inter.component.custom_id.startswith("confirm_activate_coupon_"):
            coupon_type = inter.component.custom_id.split("_")[3]
            quantity = database.get_inventory_item_quantity(inter.author.id, "coupon", coupon_type)

            if quantity < 1:
                await inter.response.edit_message(content="У вас больше нет этого купона.", embed=None, view=None)
                return

            database.remove_inventory_item(inter.author.id, "coupon", coupon_type, 1)

            # Логика активации купона
            coupon_name = coupon_type.replace('_', ' ').title()
            embed = disnake.Embed(
                title=f"🎟️ Купон Активирован: {coupon_name}",
                color=disnake.Color.dark_magenta()
            )

            if coupon_type == "nitro_coupon":
                embed.description = "Вы успешно активировали купон на **Discord Nitro!**"
                embed.set_footer(text="Ожидайте, администрация свяжется с вами для выдачи.")
                # Возможно, отправка сообщения администраторам или в канал логов
                admin_channel = self.bot.get_channel(config.MOD_LOG_CHANNEL_ID) # Или специальный канал для запросов
                if admin_channel:
                    await admin_channel.send(f"Пользователь {inter.author.mention} (ID: {inter.author.id}) активировал купон на Discord Nitro. Пожалуйста, свяжитесь с ним для выдачи.")
            elif coupon_type == "decoration_coupon":
                embed.description = "Вы успешно активировали купон на **уникальное оформление профиля!**"
                embed.set_footer(text="Ожидайте, администрация свяжется с вами для обсуждения дизайна.")
                # Аналогично, уведомление администрации
                admin_channel = self.bot.get_channel(config.MOD_LOG_CHANNEL_ID)
                if admin_channel:
                    await admin_channel.send(f"Пользователь {inter.author.mention} (ID: {inter.author.id}) активировал купон на уникальное оформление профиля. Пожалуйста, свяжитесь с ним.")
            else:
                embed.description = f"Вы активировали неизвестный купон: **{coupon_name}**."

            await inter.response.edit_message(embed=embed, view=None)

            # Возвращаем пользователя к списку купонов
            inventory_menu_view = InventoryMenu(self.bot)
            await inventory_menu_view.send_coupons_inventory(inter)


    @commands.Cog.listener("on_dropdown")
    async def on_inventory_dropdown(self, inter: disnake.MessageInteraction):
        selected_item_id = inter.values[0]

        if inter.component.custom_id == "select_role_action":
            # Проверяем, если это "удалить несуществующую роль"
            if selected_item_id.startswith("delete_missing_role_"):
                role_id = int(selected_item_id.split("_")[3])
                embed = disnake.Embed(
                    title="Подтверждение удаления роли",
                    description=f"Роль с ID `{role_id}` не найдена на сервере. Вы уверены, что хотите удалить её из инвентаря?",
                    color=disnake.Color.orange()
                )
                view = disnake.ui.View(timeout=60)
                view.add_item(disnake.ui.Button(label="Да, удалить", style=disnake.ButtonStyle.red, custom_id=f"confirm_delete_missing_role_{role_id}"))
                view.add_item(disnake.ui.Button(label="Нет, отменить", style=disnake.ButtonStyle.secondary, custom_id="cancel_action"))
                await inter.response.edit_message(embed=embed, view=view)
            else:
                role_id = int(selected_item_id)
                role = inter.guild.get_role(role_id)
                if not role:
                    await inter.response.send_message("Эта роль не найдена на сервере. Возможно, она была удалена.", ephemeral=True)
                    return

                embed = disnake.Embed(
                    title=f"Действие с ролью: {role.name}",
                    description=f"Что вы хотите сделать с ролью **{role.name}**?",
                    color=disnake.Color.blue()
                )
                view = disnake.ui.View(timeout=60)
                view.add_item(disnake.ui.Button(label="Надеть/Снять Роль", style=disnake.ButtonStyle.primary, custom_id=f"toggle_role_{role_id}"))
                view.add_item(disnake.ui.Button(label="Назад", style=disnake.ButtonStyle.secondary, custom_id="inventory_roles_back")) # Кнопка назад в список ролей
                await inter.response.edit_message(embed=embed, view=view)

        elif inter.component.custom_id == "select_case_open":
            case_type = selected_item_id
            quantity = database.get_inventory_item_quantity(inter.author.id, "case", case_type)
            case_name = case_type.replace('_', ' ').title()

            embed = disnake.Embed(
                title=f"Открыть Кейс: {case_name}",
                description=f"У вас **{quantity}** кейсов **{case_name}**.\nВы хотите открыть один?",
                color=disnake.Color.orange()
            )
            view = disnake.ui.View(timeout=60)
            view.add_item(disnake.ui.Button(label="Открыть 1 кейс", style=disnake.ButtonStyle.green, custom_id=f"confirm_open_case_{case_type}"))
            view.add_item(disnake.ui.Button(label="Назад", style=disnake.ButtonStyle.secondary, custom_id="inventory_cases_back"))
            await inter.response.edit_message(embed=embed, view=view)

        elif inter.component.custom_id == "select_coupon_activate":
            coupon_type = selected_item_id
            quantity = database.get_inventory_item_quantity(inter.author.id, "coupon", coupon_type)
            coupon_name = coupon_type.replace('_', ' ').title()

            embed = disnake.Embed(
                title=f"Активировать Купон: {coupon_name}",
                description=f"У вас **{quantity}** купонов **{coupon_name}**.\nВы хотите активировать один?",
                color=disnake.Color.orange()
            )
            view = disnake.ui.View(timeout=60)
            view.add_item(disnake.ui.Button(label="Активировать 1 купон", style=disnake.ButtonStyle.green, custom_id=f"confirm_activate_coupon_{coupon_type}"))
            view.add_item(disnake.ui.Button(label="Назад", style=disnake.ButtonStyle.secondary, custom_id="inventory_coupons_back"))
            await inter.response.edit_message(embed=embed, view=view)

    # Добавляем обработчики для кнопок "Назад" внутри категорий инвентаря
    @commands.Cog.listener("on_button_click")
    async def on_inventory_category_back_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id == "inventory_roles_back":
            inventory_menu_view = InventoryMenu(self.bot)
            await inventory_menu_view.send_roles_inventory(inter) # Возвращаем к списку ролей

        elif inter.component.custom_id == "inventory_cases_back":
            inventory_menu_view = InventoryMenu(self.bot)
            await inventory_menu_view.send_cases_inventory(inter) # Возвращаем к списку кейсов

        elif inter.component.custom_id == "inventory_coupons_back":
            inventory_menu_view = InventoryMenu(self.bot)
            await inventory_menu_view.send_coupons_inventory(inter) # Возвращаем к списку купонов


def setup(bot):
    bot.add_cog(Inventory(bot))