import disnake
from disnake.ext import commands
import config
import database

class ShopCategoriesView(disnake.ui.View):
    def __init__(self, bot_instance: commands.Bot):
        super().__init__(timeout=180) # Тайм-аут 3 минуты
        self.bot_instance = bot_instance

    async def on_timeout(self):
        for item in self.children:
            if isinstance(item, (disnake.ui.Button, disnake.ui.Select)):
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(content="Меню магазина истекло.", view=self)
            except disnake.NotFound:
                pass

    @disnake.ui.button(label="Кейсы", style=disnake.ButtonStyle.blurple, custom_id="shop_category_cases")
    async def cases_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self.send_cases_shop(inter)

    @disnake.ui.button(label="Роли", style=disnake.ButtonStyle.green, custom_id="shop_category_roles")
    async def roles_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self.send_roles_shop(inter)

    @disnake.ui.button(label="Купоны", style=disnake.ButtonStyle.red, custom_id="shop_category_coupons")
    async def coupons_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await self.send_coupons_shop(inter)

    async def send_cases_shop(self, inter: disnake.MessageInteraction):
        embed = disnake.Embed(
            title="🎁 Магазин Кейсов",
            description="Откройте кейсы и получите ценные призы!",
            color=disnake.Color.dark_gold()
        )
        # embed.set_thumbnail(url="https://i.imgur.com/your_case_icon.png") # Замени на свою иконку

        options = []
        for case_type, price in config.CASE_PRICES.items():
            options.append(disnake.SelectOption(
                label=f"{case_type.replace('_', ' ').title()} - {price:,} монет",
                value=case_type
            ))

        view = disnake.ui.View()
        if options:
            select = disnake.ui.StringSelect(
                placeholder="Выберите кейс для покупки...",
                custom_id="select_buy_case",
                options=options
            )
            view.add_item(select)
        view.add_item(disnake.ui.Button(label="⬅️ Назад в меню", style=disnake.ButtonStyle.secondary, custom_id="shop_back_to_main"))

        await inter.response.edit_message(embed=embed, view=view)

    async def send_roles_shop(self, inter: disnake.MessageInteraction):
        embed = disnake.Embed(
            title="👑 Магазин Ролей",
            description="Купите уникальные роли и выделитесь среди других!",
            color=disnake.Color.dark_purple()
        )
        # embed.set_thumbnail(url="https://i.imgur.com/your_role_icon.png") # Замени на свою иконку

        shop_roles = database.get_shop_roles()
        options = []
        if shop_roles:
            for role_id, price in shop_roles:
                role = inter.guild.get_role(role_id)
                if role:
                    options.append(disnake.SelectOption(
                        label=f"{role.name} - {price:,} монет",
                        value=str(role.id)
                    ))
                else:
                    # Если роль не найдена на сервере, она не будет доступна для выбора
                    pass
        if not options:
            embed.description += "\n\nВ магазине пока нет ролей или они недействительны."

        view = disnake.ui.View()
        if options:
            select = disnake.ui.StringSelect(
                placeholder="Выберите роль для покупки...",
                custom_id="select_buy_role",
                options=options
            )
            view.add_item(select)
        view.add_item(disnake.ui.Button(label="⬅️ Назад в меню", style=disnake.ButtonStyle.secondary, custom_id="shop_back_to_main"))

        await inter.response.edit_message(embed=embed, view=view)

    async def send_coupons_shop(self, inter: disnake.MessageInteraction):
        embed = disnake.Embed(
            title="🎟️ Магазин Купонов",
            description="Приобретите купоны на особые бонусы!",
            color=disnake.Color.dark_magenta()
        )
        # embed.set_thumbnail(url="https://i.imgur.com/your_coupon_icon.png") # Замени на свою иконку

        options = []
        for coupon_type, price in config.COUPON_PRICES.items():
            options.append(disnake.SelectOption(
                label=f"{coupon_type.replace('_', ' ').title()} - {price:,} монет",
                value=coupon_type
            ))

        view = disnake.ui.View()
        if options:
            select = disnake.ui.StringSelect(
                placeholder="Выберите купон для покупки...",
                custom_id="select_buy_coupon",
                options=options
            )
            view.add_item(select)
        view.add_item(disnake.ui.Button(label="⬅️ Назад в меню", style=disnake.ButtonStyle.secondary, custom_id="shop_back_to_main"))

        await inter.response.edit_message(embed=embed, view=view)


class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="addrole", description="Добавить роль в магазин. Только для персонала.")
    @commands.has_role(config.ADMIN_ROLE_ID)
    async def addrole(self, inter: disnake.ApplicationCommandInteraction, role: disnake.Role, price: int):
        if price <= 0:
            await inter.response.send_message("Цена должна быть положительной.", ephemeral=True)
            return

        database.add_shop_role(role.id, price)
        embed = disnake.Embed(
            title="✅ Роль Добавлена в Магазин",
            description=f"Роль **{role.name}** (`{role.id}`) добавлена в магазин по цене `{price:,}` монет.",
            color=disnake.Color.green()
        )
        await inter.response.send_message(embed=embed)
        # Отправляем обновленное сообщение в магазин
        await self._update_shop_initial_message()

    @addrole.error
    async def addrole_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingRole):
            await inter.response.send_message("У вас нет прав для использования этой команды.", ephemeral=True)
        else:
            await inter.response.send_message(f"Произошла ошибка: {error}", ephemeral=True)

    @commands.slash_command(name="remrole", description="Удалить роль из магазина. Только для персонала.")
    @commands.has_role(config.ADMIN_ROLE_ID)
    async def remrole(self, inter: disnake.ApplicationCommandInteraction, role: disnake.Role):
        if not database.get_shop_role_price(role.id):
            await inter.response.send_message("Этой роли нет в магазине.", ephemeral=True)
            return

        database.remove_shop_role(role.id)
        embed = disnake.Embed(
            title="❌ Роль Удалена из Магазина",
            description=f"Роль **{role.name}** (`{role.id}`) удалена из магазина.",
            color=disnake.Color.red()
        )
        await inter.response.send_message(embed=embed)
        # Отправляем обновленное сообщение в магазин
        await self._update_shop_initial_message()

    @remrole.error
    async def remrole_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingRole):
            await inter.response.send_message("У вас нет прав для использования этой команды.", ephemeral=True)
        else:
            await inter.response.send_message(f"Произошла ошибка: {error}", ephemeral=True)

    async def _update_shop_initial_message(self):
        # Этот метод вызывается, чтобы обновить сообщение в канале магазина,
        # если оно было изменено (например, добавлена/удалена роль)
        shop_channel = self.bot.get_channel(config.SHOP_CHANNEL_ID)
        if shop_channel:
            async for msg in shop_channel.history(limit=5):
                if msg.author == self.bot.user and msg.embeds and "Добро пожаловать в магазин" in msg.embeds[0].title:
                    embed = disnake.Embed(
                        title="🛒 Добро пожаловать в магазин!",
                        description="Здесь вы можете приобрести различные предметы и улучшения за внутриигровую валюту.",
                        color=disnake.Color.blue()
                    )
                    embed.set_thumbnail(url="https://i.imgur.com/your_shop_icon.png") # Замени
                    embed.add_field(name="Как пользоваться?", value="Нажмите на кнопку ниже, чтобы открыть главное меню магазина.", inline=False)
                    view = disnake.ui.View()
                    view.add_item(disnake.ui.Button(style=disnake.ButtonStyle.green, label="Открыть Магазин", custom_id="open_shop_menu"))
                    await msg.edit(embed=embed, view=view)
                    return

    @commands.Cog.listener("on_button_click")
    async def on_shop_button_click(self, inter: disnake.MessageInteraction):
        # Отвечаем на interaction, чтобы не было ошибки "Interaction Failed"
        # Для начального меню магазина: отправляем новое эфемерное сообщение
        if inter.component.custom_id == "open_shop_menu":
            embed = disnake.Embed(
                title="🛍️ Главное Меню Магазина",
                description="Выберите категорию товаров:",
                color=disnake.Color.blue()
            )
            embed.set_footer(text=f"Ваш баланс: {database.get_user_data(inter.author.id)[1]:,} монет")
            view = ShopCategoriesView(self.bot)
            await inter.response.send_message(embed=embed, view=view, ephemeral=True)

        # Для кнопки "Назад в меню" внутри магазина: редактируем текущее эфемерное сообщение
        elif inter.component.custom_id == "shop_back_to_main":
            embed = disnake.Embed(
                title="🛍️ Главное Меню Магазина",
                description="Выберите категорию товаров:",
                color=disnake.Color.blue()
            )
            embed.set_footer(text=f"Ваш баланс: {database.get_user_data(inter.author.id)[1]:,} монет")
            view = ShopCategoriesView(self.bot)
            await inter.response.edit_message(embed=embed, view=view)

        elif inter.component.custom_id.startswith("confirm_buy_"):
            parts = inter.component.custom_id.split("_")
            item_type = parts[2]
            item_id = parts[3] # Для ролей это ID, для кейсов/купонов это название

            price = 0
            if item_type == "role":
                try:
                    price = database.get_shop_role_price(int(item_id))
                except ValueError:
                    await inter.response.send_message("Некорректный ID роли.", ephemeral=True)
                    await inter.message.edit(view=None)
                    return
            elif item_type == "case":
                price = config.CASE_PRICES.get(item_id)
            elif item_type == "coupon":
                price = config.COUPON_PRICES.get(item_id)

            if not price:
                await inter.response.send_message("Не удалось получить информацию о цене товара.", ephemeral=True)
                await inter.message.edit(view=None) # Удаляем кнопки
                return

            user_data = database.get_user_data(inter.author.id)
            current_balance = user_data[1]

            if current_balance < price:
                await inter.response.send_message(f"У вас недостаточно средств! Вам не хватает `{price - current_balance:,}` монет.", ephemeral=True)
                await inter.message.edit(view=None) # Удаляем кнопки
                return

            item_name = item_id.replace('_', ' ').title()
            if item_type == "role":
                role_to_buy = inter.guild.get_role(int(item_id))
                if not role_to_buy:
                    await inter.response.send_message("Эта роль не найдена на сервере. Возможно, она была удалена.", ephemeral=True)
                    await inter.message.edit(view=None)
                    return
                if role_to_buy in inter.author.roles:
                    await inter.response.send_message("У вас уже есть эта роль.", ephemeral=True)
                    await inter.message.edit(view=None)
                    return
                item_name = role_to_buy.name

            database.update_user_balance(inter.author.id, -price)
            database.add_inventory_item(inter.author.id, item_type, item_id)

            embed = disnake.Embed(
                title="✅ Покупка Успешна!",
                description=f"Вы успешно приобрели **{item_name}** за `{price:,}` монет.",
                color=disnake.Color.green()
            )
            embed.set_footer(text=f"Ваш новый баланс: {database.get_user_data(inter.author.id)[1]:,} монет")
            await inter.response.edit_message(embed=embed, view=None) # Удаляем кнопки после покупки

        elif inter.component.custom_id == "cancel_purchase":
            await inter.response.edit_message(content="Покупка отменена.", embed=None, view=None)

    @commands.Cog.listener("on_dropdown")
    async def on_shop_dropdown(self, inter: disnake.MessageInteraction):
        # Отвечаем на interaction, чтобы не было ошибки "Interaction Failed"
        selected_item_id = inter.values[0]
        item_type = ""
        price = 0
        item_name = ""

        if inter.component.custom_id == "select_buy_role":
            item_type = "role"
            role = inter.guild.get_role(int(selected_item_id))
            if not role:
                await inter.response.send_message("Выбранная роль не найдена на сервере.", ephemeral=True)
                return
            price = database.get_shop_role_price(int(selected_item_id))
            item_name = role.name
            if not price:
                await inter.response.send_message("Цена для этой роли не найдена в магазине.", ephemeral=True)
                return

        elif inter.component.custom_id == "select_buy_case":
            item_type = "case"
            price = config.CASE_PRICES.get(selected_item_id)
            item_name = selected_item_id.replace('_', ' ').title()
            if not price:
                await inter.response.send_message("Цена для этого кейса не найдена.", ephemeral=True)
                return

        elif inter.component.custom_id == "select_buy_coupon":
            item_type = "coupon"
            price = config.COUPON_PRICES.get(selected_item_id)
            item_name = selected_item_id.replace('_', ' ').title()
            if not price:
                await inter.response.send_message("Цена для этого купона не найдена.", ephemeral=True)
                return
        else:
            return # Не наш dropdown

        user_data = database.get_user_data(inter.author.id)
        current_balance = user_data[1]

        embed = disnake.Embed(
            title=f"Подтверждение покупки: {item_name}",
            description=f"Вы собираетесь приобрести **{item_name}** за `{price:,}` монет.",
            color=disnake.Color.orange()
        )
        embed.add_field(name="Ваш текущий баланс", value=f"`{current_balance:,}` монет", inline=False)
        embed.add_field(name="Остаток после покупки", value=f"`{current_balance - price:,}` монет", inline=False)

        view = disnake.ui.View(timeout=60) # Устанавливаем таймаут для подтверждения
        view.add_item(disnake.ui.Button(label="Подтвердить покупку", style=disnake.ButtonStyle.green, custom_id=f"confirm_buy_{item_type}_{selected_item_id}"))
        view.add_item(disnake.ui.Button(label="Отменить", style=disnake.ButtonStyle.red, custom_id="cancel_purchase"))

        await inter.response.edit_message(embed=embed, view=view)


def setup(bot):
    bot.add_cog(Shop(bot))