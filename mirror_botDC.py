import discord
from discord.ext import commands
import requests
import json
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Inisialisasi bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Fungsi untuk komunikasi dengan Gemini AI
def chat_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        if response.status_code == 200:
            result = response.json()
            # Mengambil hasil dari API response
            return result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "Tidak ada jawaban")
        else:
            return f"Error: {response.status_code} - {response.text}"
    
    except requests.exceptions.RequestException as e:
        return f"Terjadi kesalahan saat menghubungi API: {str(e)}"


# Simpan deskripsi nama user
user_descriptions = {
    "fatih": "Fatih itu anaknya pendiam tapi aktif kok.",
    "rafi": "Rafi itu orangnya suka bercanda, tapi baik.",
    "budi": "Budi jago coding, sering bantu temen-temennya.",
    "muzan": "Muzan itu Si Agent Crypto, kerjaannya cuma Ngocok sama mikirin USDT sekarang lagi naik atau ngga ya HAHA"
}

# Fungsi untuk komunikasi dengan Gemini AI
def chat_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    else:
        return f"Error: {response.status_code} - {response.text}"

# Event ketika bot berhasil login
@bot.event
async def on_ready():
    print(f'Bot {bot.user} sudah online!')

# Event untuk mirroring semua pesan dalam server
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Cek apakah user bertanya nama bot
    if "nama kamu siapa" in message.content.lower():
        await message.channel.send("Namaku adalah Johny Sins!")

    # Lanjutkan ke command bot lainnya
    await bot.process_commands(message)

# Command untuk tanya AI
@bot.command()
async def tanya(ctx, *, pertanyaan):
    jawaban = chat_gemini(pertanyaan)
    await ctx.send(jawaban)

# Command untuk cek deskripsi user
@bot.command()
async def siapa(ctx, nama: str):
    nama = nama.lower()
    if nama in user_descriptions:
        await ctx.send(user_descriptions[nama])
    else:
        await ctx.send(f"Aku belum tahu tentang {nama}, kasih tahu aku dong!")

# Jalankan bot
bot.run(TOKEN)
