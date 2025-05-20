import disnake
from disnake.ext import commands
import database

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Игнорируем сообщения от ботов
        if message.author.bot:
            return

        # Обновляем счетчики сообщений
        database.update_messages_count(message.author.id)

        # Важно: Не обрабатывайте здесь команды, иначе они будут дублироваться
        # Если вы хотите, чтобы префиксные команды работали, не добавляйте `await self.bot.process_commands(message)`
        # Здесь мы только обновляем статистику.


def setup(bot):
    bot.add_cog(Events(bot))