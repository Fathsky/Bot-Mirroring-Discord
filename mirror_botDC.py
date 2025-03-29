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
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Tambahkan ini agar bot bisa membaca pesan

# Buat objek bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Variabel untuk menyimpan status mirror
mirror_active = True  

# Event saat bot sudah online
@bot.event
async def on_ready():
    print(f"Bot {bot.user} sudah online!")

# Command untuk menyalakan mirroring
@bot.command()
async def on(ctx):
    global mirror_active
    mirror_active = True
    nickname = ctx.author.display_name  
    await ctx.send(f"✅ CIEEEE AKTIFIN AKU, KANGEN YAAA? Halo, {nickname}! SEMOGA HARIMU BAIK BAIK AJA YA😊")
    
# Command untuk menanggapi panggilan "hai"
@bot.command()
async def hai(ctx):
    global mirror_active
    mirror_active = False 
    await ctx.send(f"Hai {ctx.author.display_name}, Ngapain manggil-manggil, urus sono pacar lo! Oh ya lupa, Lo kan gapunya pacar HAHAHAHAHA")

# Command untuk mematikan mirroring
@bot.command()
async def off(ctx):
    global mirror_active
    mirror_active = False
    await ctx.send(f"❌ PAYPAYYY {ctx.author.display_name}, KALO KANGEN AKTIFIN AKU AJA YA!")

# Event untuk mirror pesan
@bot.event
async def on_message(message):
    global mirror_active
    
    # Pastikan bot tetap bisa menjalankan command lainnya
    await bot.process_commands(message)

# Jalankan bot
bot.run(TOKEN)
