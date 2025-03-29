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

# Simpan riwayat percakapan
conversation_history = []

# Simpan deskripsi user
user_descriptions = {
    "fatih": "Fatih itu anaknya pendiam tapi aktif kok.",
    "rafi": "Rafi itu orangnya suka bercanda, tapi baik.",
    "budi": "Budi jago coding, sering bantu temen-temennya.",
}

# 🔥 Fungsi komunikasi dengan Gemini AI (Versi Fix)
def chat_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}

    # Simpan percakapan sebelumnya (biar nyambung)
    conversation_history.append({"role": "user", "content": prompt})

    data = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # Cek kalau ada error HTTP

        result = response.json()

        # Ambil jawaban AI
        bot_response = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "Maaf, aku nggak ngerti 😅")

        # Simpan ke riwayat percakapan
        conversation_history.append({"role": "bot", "content": bot_response})

        return bot_response

    except requests.exceptions.RequestException as e:
        return f"⚠️ Error: {str(e)}"

# ✅ Event ketika bot berhasil online
@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} sudah online!')

# ✅ Event untuk mirroring pesan dalam server
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Cek kalau ada yang nanya nama bot
    if "nama kamu siapa" in message.content.lower():
        await message.channel.send("Namaku adalah Johny Sins!, Sang artis bintang terkenal yang lincah dan tampan 😎")

    await bot.process_commands(message)  # Pastikan command lain tetap jalan

# ✅ Command ngobrol dengan AI
@bot.command()
async def tanya(ctx, *, pertanyaan):
    jawaban = chat_gemini(pertanyaan)
    await ctx.send(jawaban)

# ✅ Command cek deskripsi user
@bot.command()
async def siapa(ctx, nama: str):
    nama = nama.lower()
    if nama in user_descriptions:
        await ctx.send(user_descriptions[nama])
    else:
        await ctx.send(f"Aku belum tahu tentang {nama}, kasih tahu aku dong!")

# ✅ Command user bisa nambahin deskripsi sendiri
@bot.command()
async def tambahin(ctx, nama: str, *, deskripsi: str):
    nama = nama.lower()
    user_descriptions[nama] = deskripsi
    await ctx.send(f"✅ Oke! Sekarang aku tahu bahwa {nama} itu {deskripsi}")

# ✅ Command buat hapus data user
@bot.command()
async def hapusdata(ctx, nama: str):
    nama = nama.lower()
    if nama in user_descriptions:
        del user_descriptions[nama]
        await ctx.send(f"✅ Data tentang {nama} sudah dihapus!")
    else:
        await ctx.send(f"⚠️ Gak ada data tentang {nama}.")

# ✅ Command buat lihat semua user yang dikenal bot
@bot.command()
async def listuser(ctx):
    if user_descriptions:
        daftar = "\n".join([f"🔹 {nama}: {desc}" for nama, desc in user_descriptions.items()])
        await ctx.send(f"📜 **Daftar User yang Aku Tahu:**\n{daftar}")
    else:
        await ctx.send("⚠️ Aku belum kenal siapa pun!")

# ✅ Jalankan bot
bot.run(TOKEN)
