import disnake
from disnake.ext import commands
import datetime
import asyncio

import config
import database

class StaffPanelButtons(disnake.ui.View):
    def __init__(self, target_user_id: int, mod_log_channel_id: int):
        super().__init__(timeout=180) # Тайм-аут 3 минуты
        self.target_user_id = target_user_id
        self.mod_log_channel_id = mod_log_channel_id # Передаем ID канала

    async def on_timeout(self):
        for item in self.children:
            if isinstance(item, disnake.ui.Button):
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(content="Меню панели персонала истекло.", view=self)
            except disnake.NotFound:
                pass # Сообщение могло быть удалено

    @disnake.ui.button(label="Предупреждение", style=disnake.ButtonStyle.red, custom_id="staffpanel_warn")
    async def warn_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_modal(
            title=f"Выдать предупреждение для ID: {self.target_user_id}",
            custom_id=f"warn_modal_{self.target_user_id}", # Передаем ID пользователя через custom_id
            components=[
                disnake.ui.TextInput(
                    label="Причина предупреждения",
                    placeholder="Например: Спам в чате, Ненормативная лексика",
                    custom_id="reason",
                    style=disnake.TextInputStyle.paragraph,
                    required=True,
                    max_length=500
                ),
                disnake.ui.TextInput(
                    label="Пункт правил",
                    placeholder="Какой пункт правил нарушил пользователь?",
                    custom_id="rule_point",
                    style=disnake.TextInputStyle.short,
                    required=True,
                    max_length=50
                )
            ]
        )
        # self.stop() # Не останавливаем, чтобы пользователь мог использовать другие кнопки, если это модальное окно не заменяет текущее сообщение

    @disnake.ui.button(label="Мут", style=disnake.ButtonStyle.red, custom_id="staffpanel_mute")
    async def mute_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_modal(
            title=f"Выдать мут для ID: {self.target_user_id}",
            custom_id=f"mute_modal_{self.target_user_id}", # Передаем ID пользователя через custom_id
            components=[
                disnake.ui.TextInput(
                    label="Причина мута",
                    placeholder="Например: Флуд, Оскорбления",
                    custom_id="reason",
                    style=disnake.TextInputStyle.paragraph,
                    required=True,
                    max_length=500
                ),
                disnake.ui.TextInput(
                    label="Длительность (минуты)",
                    placeholder="Введите количество минут (например, 60 для 1 часа)",
                    custom_id="duration_minutes",
                    style=disnake.TextInputStyle.short,
                    required=True,
                    max_length=5
                ),
                disnake.ui.TextInput(
                    label="Пункт правил",
                    placeholder="Какой пункт правил нарушил пользователь?",
                    custom_id="rule_point",
                    style=disnake.TextInputStyle.short,
                    required=True,
                    max_length=50
                )
            ]
        )
        # self.stop()

    @disnake.ui.button(label="Бан", style=disnake.ButtonStyle.red, custom_id="staffpanel_ban")
    async def ban_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.send_modal(
            title=f"Забанить для ID: {self.target_user_id}",
            custom_id=f"ban_modal_{self.target_user_id}", # Передаем ID пользователя через custom_id
            components=[
                disnake.ui.TextInput(
                    label="Причина бана",
                    placeholder="Например: Нарушение правил сервера",
                    custom_id="reason",
                    style=disnake.TextInputStyle.paragraph,
                    required=True,
                    max_length=500
                ),
                disnake.ui.TextInput(
                    label="Пункт правил",
                    placeholder="Какой пункт правил нарушил пользователь?",
                    custom_id="rule_point",
                    style=disnake.TextInputStyle.short,
                    required=True,
                    max_length=50
                )
            ]
        )
        # self.stop()

    @disnake.ui.button(label="Снять предупреждение", style=disnake.ButtonStyle.green, custom_id="staffpanel_unwarn")
    async def unwarn_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        warnings = database.get_active_warnings(self.target_user_id)
        if not warnings:
            await inter.response.send_message(f"У пользователя нет активных предупреждений.", ephemeral=True)
            return

        options = []
        for warn_id, reason, issue_date, expire_date in warnings:
            # Обрезаем причину для отображения в dropdown, чтобы не было слишком длинно
            reason_display = reason[:50] + "..." if len(reason) > 50 else reason
            options.append(disnake.SelectOption(label=f"ID: {warn_id} - {reason_display}", value=str(warn_id)))

        select = disnake.ui.StringSelect(
            placeholder="Выберите предупреждение для снятия...",
            custom_id=f"select_unwarn_{self.target_user_id}", # Передаем ID пользователя
            options=options
        )
        view = disnake.ui.View(timeout=60) # Короткий таймаут для этого меню
        view.add_item(select)
        await inter.response.send_message("Выберите предупреждение, которое хотите снять:", view=view, ephemeral=True)
        # self.stop() # Не останавливаем основное view, чтобы другие кнопки были доступны

    @disnake.ui.button(label="Снять мут", style=disnake.ButtonStyle.green, custom_id="staffpanel_unmute")
    async def unmute_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        target_user = inter.guild.get_member(self.target_user_id)
        if not target_user:
            await inter.response.send_message("Пользователь не найден на сервере.", ephemeral=True)
            return

        active_mute = database.get_active_mute(self.target_user_id)
        if not active_mute:
            await inter.response.send_message(f"У пользователя {target_user.display_name} нет активного мута.", ephemeral=True)
            return

        # Добавляем подтверждение снятия мута
        embed = disnake.Embed(
            title="Подтверждение снятия мута",
            description=f"Вы уверены, что хотите снять мут с **{target_user.display_name}**?",
            color=disnake.Color.orange()
        )
        view = disnake.ui.View(timeout=60)
        view.add_item(disnake.ui.Button(label="Да, снять мут", style=disnake.ButtonStyle.green, custom_id=f"confirm_unmute_{self.target_user_id}"))
        view.add_item(disnake.ui.Button(label="Нет, отменить", style=disnake.ButtonStyle.red, custom_id=f"cancel_action"))
        await inter.response.send_message(embed=embed, view=view, ephemeral=True)
        # self.stop() # Не останавливаем основное view

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="staffpanel", description="Открыть панель модерации для пользователя. Только для персонала.")
    @commands.has_role(config.ADMIN_ROLE_ID)
    async def staffpanel(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member):
        if user.bot:
            await inter.response.send_message("Вы не можете модерировать ботов.", ephemeral=True)
            return

        mod_log_channel = self.bot.get_channel(config.MOD_LOG_CHANNEL_ID)
        if not mod_log_channel:
            await inter.response.send_message("Канал для логов модерации не найден. Обратитесь к администратору бота.", ephemeral=True)
            return

        embed = disnake.Embed(
            title=f"🛠️ Панель Персонала для {user.display_name} (ID: {user.id})",
            description="Выберите действие, которое хотите применить к этому пользователю.",
            color=disnake.Color.dark_red()
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.set_footer(text=f"Открыл: {inter.author.display_name}")

        view = StaffPanelButtons(user.id, config.MOD_LOG_CHANNEL_ID) # Передаем ID пользователя и ID канала логов
        await inter.response.send_message(embed=embed, view=view, ephemeral=True)

    @staffpanel.error
    async def staffpanel_error(self, inter: disnake.ApplicationCommandInteraction, error):
        if isinstance(error, commands.MissingRole):
            await inter.response.send_message("У вас нет прав для использования этой команды.", ephemeral=True)
        else:
            await inter.response.send_message(f"Произошла ошибка: {error}", ephemeral=True)

    @commands.Cog.listener("on_modal_submit")
    async def on_modal_submit(self, inter: disnake.ModalInteraction):
        # Важно: Взаимодействие с модальным окном уже ответило,
        # поэтому здесь используем inter.followup.send_message
        # или inter.response.edit_message, если сообщение было создано с modal.

        if inter.custom_id.startswith("warn_modal_"):
            target_user_id = int(inter.custom_id.split("_")[2]) # Получаем ID из custom_id модала
            target_user = inter.guild.get_member(target_user_id) if inter.guild else self.bot.get_user(target_user_id)
            if not target_user:
                await inter.response.send_message("Не удалось найти пользователя.", ephemeral=True)
                return

            reason = inter.text_values["reason"]
            rule_point = inter.text_values["rule_point"]
            moderator = inter.author

            issue_date = datetime.datetime.now()
            expire_date = issue_date + datetime.timedelta(days=config.WARN_DURATION_DAYS)

            warn_id = database.add_warning(target_user.id, moderator.id, reason, issue_date, expire_date)

            embed = disnake.Embed(
                title="⚠️ Предупреждение Выдано",
                description=f"Пользователю **{target_user.display_name}** выдано предупреждение.",
                color=disnake.Color.orange(),
                timestamp=issue_date
            )
            embed.add_field(name="Модератор", value=moderator.display_name, inline=True)
            embed.add_field(name="Причина", value=reason, inline=True)
            embed.add_field(name="Пункт правил", value=rule_point, inline=True)
            embed.add_field(name="Истекает", value=disnake.utils.format_dt(expire_date, "R"), inline=False)
            embed.set_footer(text=f"ID пользователя: {target_user.id} | ID предупреждения: {warn_id}")
            await inter.response.send_message(embed=embed, ephemeral=True) # Отправляем сообщение в чат модератору

            # Отправка в ЛС
            try:
                dm_embed = disnake.Embed(
                    title="⚠️ Вы получили предупреждение!",
                    description=f"На сервере **{inter.guild.name}** вам было выдано предупреждение.",
                    color=disnake.Color.orange(),
                    timestamp=issue_date
                )
                dm_embed.add_field(name="Модератор", value=moderator.display_name, inline=True)
                dm_embed.add_field(name="Причина", value=reason, inline=True)
                dm_embed.add_field(name="Пункт правил", value=rule_point, inline=True)
                dm_embed.add_field(name="Истекает", value=disnake.utils.format_dt(expire_date, "R"), inline=False)
                dm_embed.set_footer(text=f"ID предупреждения: {warn_id}")
                await target_user.send(embed=dm_embed)
            except disnake.HTTPException:
                pass # Не удалось отправить ЛС

            # Логирование в канал модерации
            mod_log_channel = self.bot.get_channel(config.MOD_LOG_CHANNEL_ID)
            if mod_log_channel:
                await mod_log_channel.send(embed=embed)


        elif inter.custom_id.startswith("mute_modal_"):
            target_user_id = int(inter.custom_id.split("_")[2])
            target_user = inter.guild.get_member(target_user_id)
            if not target_user:
                await inter.response.send_message("Не удалось найти пользователя.", ephemeral=True)
                return

            reason = inter.text_values["reason"]
            duration_minutes_str = inter.text_values["duration_minutes"]
            rule_point = inter.text_values["rule_point"]
            moderator = inter.author

            try:
                duration_minutes = int(duration_minutes_str)
                if duration_minutes <= 0:
                    await inter.response.send_message("Длительность мута должна быть положительным числом.", ephemeral=True)
                    return
            except ValueError:
                await inter.response.send_message("Некорректная длительность мута. Введите число.", ephemeral=True)
                return

            issue_date = datetime.datetime.now()
            end_date = issue_date + datetime.timedelta(minutes=duration_minutes)

            mute_role = inter.guild.get_role(config.MUTED_ROLE_ID)
            if not mute_role: # Если роль не найдена по ID, пытаемся найти по имени или создать
                mute_role = disnake.utils.get(inter.guild.roles, name="Muted")
                if not mute_role:
                    try:
                        mute_role = await inter.guild.create_role(name="Muted", reason="Для системы мутов")
                        # Настраиваем разрешения для роли Muted во всех текстовых каналах
                        for channel in inter.guild.text_channels:
                            await channel.set_permissions(mute_role, send_messages=False, add_reactions=False, speak=False)
                        print(f"Роль 'Muted' создана и настроена.")
                    except disnake.Forbidden:
                        await inter.response.send_message("У меня нет прав для создания роли 'Muted' или настройки её разрешений.", ephemeral=True)
                        return

            try:
                if mute_role not in target_user.roles:
                    await target_user.add_roles(mute_role, reason=f"Мут выдан модератором {moderator.display_name} по причине: {reason}")
            except disnake.Forbidden:
                await inter.response.send_message("У меня нет прав для выдачи роли 'Muted'.", ephemeral=True)
                return

            database.add_mute(target_user.id, moderator.id, reason, issue_date, end_date)

            embed = disnake.Embed(
                title="🔇 Пользователь Замучен",
                description=f"Пользователь **{target_user.display_name}** был замучен.",
                color=disnake.Color.dark_orange(),
                timestamp=issue_date
            )
            embed.add_field(name="Модератор", value=moderator.display_name, inline=True)
            embed.add_field(name="Причина", value=reason, inline=True)
            embed.add_field(name="Пункт правил", value=rule_point, inline=True)
            embed.add_field(name="Длительность", value=f"`{duration_minutes}` минут", inline=True)
            embed.add_field(name="Заканчивается", value=disnake.utils.format_dt(end_date, "R"), inline=False)
            embed.set_footer(text=f"ID пользователя: {target_user.id}")
            await inter.response.send_message(embed=embed, ephemeral=True)

            # Отправка в ЛС
            try:
                dm_embed = disnake.Embed(
                    title="🔇 Вы были замучены!",
                    description=f"На сервере **{inter.guild.name}** вам был выдан мут.",
                    color=disnake.Color.dark_orange(),
                    timestamp=issue_date
                )
                dm_embed.add_field(name="Модератор", value=moderator.display_name, inline=True)
                dm_embed.add_field(name="Причина", value=reason, inline=True)
                dm_embed.add_field(name="Пункт правил", value=rule_point, inline=True)
                dm_embed.add_field(name="Длительность", value=f"`{duration_minutes}` минут", inline=True)
                dm_embed.add_field(name="Заканчивается", value=disnake.utils.format_dt(end_date, "R"), inline=False)
                await target_user.send(embed=dm_embed)
            except disnake.HTTPException:
                pass # Не удалось отправить ЛС

            # Логирование
            mod_log_channel = self.bot.get_channel(config.MOD_LOG_CHANNEL_ID)
            if mod_log_channel:
                await mod_log_channel.send(embed=embed)

            # Автоматическое снятие мута
            await asyncio.sleep(duration_minutes * 60)
            # Проверяем, не сняли ли мут вручную и пользователь еще на сервере
            if database.get_active_mute(target_user.id) and target_user in inter.guild.members:
                try:
                    if mute_role and mute_role in target_user.roles:
                        await target_user.remove_roles(mute_role, reason="Автоматическое снятие мута")
                    database.remove_mute(target_user.id)
                    unmute_embed = disnake.Embed(
                        title="🔊 Мут Снят Автоматически",
                        description=f"Мут с пользователя **{target_user.display_name}** был снят автоматически.",
                        color=disnake.Color.green(),
                        timestamp=datetime.datetime.now()
                    )
                    unmute_embed.set_footer(text=f"ID пользователя: {target_user.id}")
                    if mod_log_channel:
                        await mod_log_channel.send(embed=unmute_embed)
                    try:
                        await target_user.send(f"Ваш мут на сервере **{inter.guild.name}** был снят автоматически.")
                    except disnake.HTTPException:
                        pass
                except disnake.Forbidden:
                    print(f"Не удалось снять роль мута с {target_user.display_name} из-за отсутствия прав.")
                except Exception as e:
                    print(f"Ошибка при автоматическом снятии мута с {target_user.display_name}: {e}")


        elif inter.custom_id.startswith("ban_modal_"):
            target_user_id = int(inter.custom_id.split("_")[2])
            target_user = inter.guild.get_member(target_user_id)
            if not target_user:
                await inter.response.send_message("Не удалось найти пользователя.", ephemeral=True)
                return

            reason = inter.text_values["reason"]
            rule_point = inter.text_values["rule_point"]
            moderator = inter.author

            try:
                # Отправляем ЛС перед баном, т.к. после бана пользователь станет недоступен
                try:
                    dm_embed = disnake.Embed(
                        title="⛔ Вы были забанены!",
                        description=f"Вы были забанены на сервере **{inter.guild.name}**.",
                        color=disnake.Color.dark_red(),
                        timestamp=datetime.datetime.now()
                    )
                    dm_embed.add_field(name="Модератор", value=moderator.display_name, inline=True)
                    dm_embed.add_field(name="Причина", value=reason, inline=True)
                    dm_embed.add_field(name="Пункт правил", value=rule_point, inline=True)
                    await target_user.send(embed=dm_embed)
                    # Даем немного времени на доставку ЛС
                    await asyncio.sleep(0.5)
                except disnake.HTTPException:
                    pass # Не удалось отправить ЛС

                await target_user.ban(reason=f"Бан выдан модератором {moderator.display_name} по причине: {reason} (Пункт правил: {rule_point})")
                embed = disnake.Embed(
                    title="⛔ Пользователь Забанен",
                    description=f"Пользователь **{target_user.display_name}** был забанен.",
                    color=disnake.Color.dark_red(),
                    timestamp=datetime.datetime.now()
                )
                embed.add_field(name="Модератор", value=moderator.display_name, inline=True)
                embed.add_field(name="Причина", value=reason, inline=True)
                embed.add_field(name="Пункт правил", value=rule_point, inline=True)
                embed.set_footer(text=f"ID пользователя: {target_user.id}")
                await inter.response.send_message(embed=embed, ephemeral=True)

                # Логирование
                mod_log_channel = self.bot.get_channel(config.MOD_LOG_CHANNEL_ID)
                if mod_log_channel:
                    await mod_log_channel.send(embed=embed)

            except disnake.Forbidden:
                await inter.response.send_message("У меня нет прав для бана этого пользователя.", ephemeral=True)
            except Exception as e:
                await inter.response.send_message(f"Произошла ошибка при бане: {e}", ephemeral=True)


    @commands.Cog.listener("on_dropdown")
    async def on_moderation_dropdown(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id.startswith("select_unwarn_"):
            warn_id = int(inter.values[0])
            target_user_id = int(inter.component.custom_id.split("_")[2]) # Получаем ID пользователя из custom_id dropdown
            target_user = self.bot.get_user(target_user_id)

            if not target_user:
                 await inter.response.send_message("Не удалось найти пользователя для снятия предупреждения.", ephemeral=True)
                 return

            # Добавляем подтверждение снятия предупреждения
            embed = disnake.Embed(
                title=f"Подтверждение снятия предупреждения",
                description=f"Вы уверены, что хотите снять предупреждение **#{warn_id}** у **{target_user.display_name}**?",
                color=disnake.Color.orange()
            )
            view = disnake.ui.View(timeout=60)
            view.add_item(disnake.ui.Button(label="Да, снять", style=disnake.ButtonStyle.green, custom_id=f"confirm_unwarn_{warn_id}_{target_user_id}"))
            view.add_item(disnake.ui.Button(label="Нет, отменить", style=disnake.ButtonStyle.red, custom_id=f"cancel_action"))
            await inter.response.edit_message(embed=embed, view=view)


    @commands.Cog.listener("on_button_click")
    async def on_moderation_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id.startswith("confirm_unwarn_"):
            parts = inter.component.custom_id.split("_")
            warn_id = int(parts[2])
            target_user_id = int(parts[3])
            target_user = self.bot.get_user(target_user_id)

            if not target_user:
                 await inter.response.send_message("Не удалось найти пользователя для снятия предупреждения.", ephemeral=True)
                 return

            database.remove_warning(warn_id)
            embed = disnake.Embed(
                title="✅ Предупреждение Снято",
                description=f"Предупреждение **#{warn_id}** с пользователя **{target_user.display_name}** было снято модератором **{inter.author.display_name}**.",
                color=disnake.Color.green(),
                timestamp=datetime.datetime.now()
            )
            embed.set_footer(text=f"ID пользователя: {target_user.id}")
            await inter.response.edit_message(embed=embed, view=None) # Удаляем кнопки подтверждения

            # Отправка в ЛС
            try:
                await target_user.send(f"Ваше предупреждение **#{warn_id}** на сервере **{inter.guild.name}** было снято администратором **{inter.author.display_name}**.")
            except disnake.HTTPException:
                pass # Не удалось отправить ЛС

            # Логирование
            mod_log_channel = self.bot.get_channel(config.MOD_LOG_CHANNEL_ID)
            if mod_log_channel:
                await mod_log_channel.send(embed=embed)

        elif inter.component.custom_id.startswith("confirm_unmute_"):
            target_user_id = int(inter.component.custom_id.split("_")[2])
            target_user = inter.guild.get_member(target_user_id)
            moderator = inter.author

            if not target_user:
                await inter.response.edit_message(content="Пользователь не найден на сервере.", embed=None, view=None)
                return

            try:
                # Снимаем роль мута, если она есть
                mute_role = inter.guild.get_role(config.MUTED_ROLE_ID)
                if not mute_role: # Если роль не найдена по ID, пытаемся найти по имени
                    mute_role = disnake.utils.get(inter.guild.roles, name="Muted")

                if mute_role and mute_role in target_user.roles:
                    await target_user.remove_roles(mute_role, reason=f"Мут снят модератором {moderator.display_name}")

                database.remove_mute(self.target_user_id) # Используем target_user_id из View инициализации
                embed = disnake.Embed(
                    title="✅ Мут Снят",
                    description=f"Мут с пользователя **{target_user.display_name}** был снят модератором **{moderator.display_name}**.",
                    color=disnake.Color.green(),
                    timestamp=datetime.datetime.now()
                )
                embed.set_footer(text=f"ID пользователя: {target_user.id}")
                await inter.response.edit_message(embed=embed, view=None) # Редактируем сообщение с подтверждением

                # Отправка в ЛС
                try:
                    await target_user.send(f"Ваш мут на сервере **{inter.guild.name}** был снят администратором **{inter.author.display_name}**.")
                except disnake.HTTPException:
                    pass # Не удалось отправить ЛС

                # Логирование
                mod_log_channel = self.bot.get_channel(config.MOD_LOG_CHANNEL_ID)
                if mod_log_channel:
                    await mod_log_channel.send(embed=embed)

            except Exception as e:
                await inter.response.edit_message(content=f"Произошла ошибка при снятии мута: {e}", embed=None, view=None)

        elif inter.component.custom_id == "cancel_action":
            await inter.response.edit_message(content="Действие отменено.", embed=None, view=None)


def setup(bot):
    bot.add_cog(Moderation(bot))