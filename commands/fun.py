from discord.ext import commands
import random


class Fun(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("🏓 Pong!")
    @commands.command()
    async def hola(self, ctx):
        await ctx.send(f"Hola, {ctx.author.mention}! 👋")
    @commands.command()
    async def hola2(self, ctx):
        await ctx.send(f"Hola, {ctx.author.name}! 👋")
    @commands.command()
    async def dau(self, ctx):
        numero = random.randint(1, 6)
        await ctx.send(f"🎲 Ha sortit un {numero}!")
    @commands.command()
    async def say(self, ctx, *, text):
        await ctx.send(text)




async def setup(bot):
    await bot.add_cog(Fun(bot))