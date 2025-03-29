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

# Simpan deskripsi nama user
user_descriptions = {
    "fatih": "Fatih itu anaknya pendiam tapi aktif kok.",
    "rafi": "Rafi itu orangnya suka bercanda, tapi baik.",
    "budi": "Budi jago coding, sering bantu temen-temennya.",
}

# Fungsi komunikasi dengan Gemini AI yang lebih fleksibel
def chat_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}

    # Tambahkan ke history biar percakapan nyambung
    conversation_history.append({"role": "user", "content": prompt})

    data = {
        "inputs": [{"text": prompt}],  # Use 'text' for input content
        "history": conversation_history
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # Check for errors in response

        # Debug response
        print("Response:", response.json())  # This will print the entire API response
        
        result = response.json()

        # Get the response from the API
        bot_response = result.get("candidates", [{}])[0].get("content", "No response found")

        # Save bot's response to history for continuity
        conversation_history.append({"role": "bot", "content": bot_response})

        return bot_response

    except requests.exceptions.RequestException as e:
        return f"⚠️ Error: {str(e)}"



# Event untuk mirroring semua pesan dalam server
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Cek apakah user bertanya nama bot
    if "nama kamu siapa" in message.content.lower():
        await message.channel.send("Namaku adalah Johny Sins!, Sang artis bintang Pornografi yang sangat Lincah dan juga Tampan")
    
    # Jangan lupa untuk memproses command bot setelah mirroring
    await bot.process_commands(message)  

# Event ketika bot berhasil login
@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} sudah online!')

# Command untuk ngobrol dengan AI
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

# Command untuk user nambahin deskripsi sendiri
@bot.command()
async def tambahin(ctx, nama: str, *, deskripsi: str):
    nama = nama.lower()
    user_descriptions[nama] = deskripsi
    await ctx.send(f"✅ Oke! Sekarang aku tahu bahwa {nama} itu {deskripsi}")

# Jalankan bot
bot.run(TOKEN)
