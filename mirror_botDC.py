import discord
import os
from dotenv import load_dotenv
from discord.ext import commands

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if TOKEN is None:
    raise ValueError("TOKEN tidak ditemukan! Pastikan sudah diset di Railway.")

# Intents untuk membaca pesan
intents = discord.Intents.all()

# Buat objek bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Variabel untuk menyimpan status mirror
mirror_active = True  

# Event saat bot sudah online
@bot.event
async def on_ready():
    print(f"bot {bot.user} udah online bangsat!")

# Command untuk menyalakan mirroring
@bot.command()
async def on(ctx):
    global mirror_active
    mirror_active = True
    nickname = ctx.author.display_name  
    await ctx.send(f"✅ CIEEEE AKTIFIN AKU, KANGEN YAAA ? Halo, {nickname}! SEMOGA HARIMU BAIK BAIK AJA YA😊")

# Command untuk mematikan mirroring
@bot.command()
async def off(ctx):
    global mirror_active
    mirror_active = False
    await ctx.send(f"❌ PAYPAYYY {ctx.author.display_name} KALO KANGEN AKTIFIN AKU AJA YA !")

# Event untuk mirror pesan
@bot.event
async def on_message(message):
    global mirror_active

    if message.author == bot.user:
        return  # Hindari bot mirror pesan sendiri

    if message.content.startswith("!"):
        await bot.process_commands(message)  # Jangan mirror kalau pesan adalah command
        return  

    if mirror_active:  # Cek apakah mirroring aktif
        await message.channel.send(f"{message.author.name}: {message.content}")

    await bot.process_commands(message)  # Pastikan command tetap bisa dijalankan


    if mirror_active:  # Cek apakah mirroring aktif
        await message.channel.send(f"{message.author.name}: {message.content}")

# Jalankan bot
bot.run(TOKEN)
