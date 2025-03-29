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

# Simpan deskripsi nama user
user_descriptions = {
    "fatih": "Fatih itu anaknya pendiam tapi aktif kok.",
    "rafi": "Rafi itu orangnya suka bercanda, tapi baik.",
    "budi": "Budi jago coding, sering bantu temen-temennya."
}

# Simpan riwayat chat untuk setiap user
chat_history = {}

# Simpan ID pesan terakhir dari bot
bot_last_messages = {}

# Fungsi untuk komunikasi dengan Gemini AI
def chat_gemini(prompt, user_id):
    if user_id not in chat_history:
        chat_history[user_id] = []
    
    full_context = "\n".join(chat_history[user_id] + [prompt])
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": full_context}]}]}
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        result = response.json()
        response_text = result["candidates"][0]["content"]["parts"][0]["text"]
        
        chat_history[user_id].append(prompt)
        chat_history[user_id].append(response_text)
        
        if len(chat_history[user_id]) > 10:
            chat_history[user_id] = chat_history[user_id][-10:]
            
        return response_text
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
        # Simpan ID pesan bot
        bot_last_messages[message.channel.id] = message.id
        return
    
    # Cek jika pesan adalah reply ke bot
    if message.reference:
        try:
            # Ambil pesan yang di-reply
            replied_msg = await message.channel.fetch_message(message.reference.message_id)
            # Cek apakah pesan yang di-reply adalah pesan dari bot
            if replied_msg.author == bot.user:
                # Generate respons dari AI
                jawaban = chat_gemini(message.content, str(message.author.id))
                sent_message = await message.channel.send(jawaban)
                # Update ID pesan terakhir bot
                bot_last_messages[message.channel.id] = sent_message.id
                return
        except discord.NotFound:
            pass  # Pesan yang di-reply tidak ditemukan
    
    # Cek apakah user bertanya nama bot
    if "nama kamu siapa" in message.content.lower():
        sent_message = await message.channel.send("Nama gue adalah Johny Sins, Sang aktor bintang Pornografi terkenal Diseluruh dunia, HAHAHAHAHA 😜!")
        bot_last_messages[message.channel.id] = sent_message.id
    
    # Cek apakah user bertanya tentang developer
    if any(phrase in message.content.lower() for phrase in ["siapa yang develop", "siapa yang buat", "siapa developermu", "siapa yang bikin"]):
        developer_id = "742535420461711481"
        sent_message = await message.channel.send(f"Yang develop aku namanya Fatih <@!{developer_id}>")
        bot_last_messages[message.channel.id] = sent_message.id

    # Lanjutkan ke command bot lainnya
    await bot.process_commands(message)

# Command untuk tanya AI (tetap ada untuk memulai percakapan)
@bot.command()
async def tanya(ctx, *, pertanyaan):
    jawaban = chat_gemini(pertanyaan, str(ctx.author.id))
    sent_message = await ctx.send(jawaban)
    bot_last_messages[ctx.channel.id] = sent_message.id

# Command untuk cek deskripsi user
@bot.command()
async def siapa(ctx, nama: str):
    nama = nama.lower()
    if nama in user_descriptions:
        await ctx.send(user_descriptions[nama])
    else:
        await ctx.send(f"Aku belum tahu tentang {nama}, kasih tahu aku dong!")

# Command untuk reset riwayat chat
@bot.command()
async def reset(ctx):
    user_id = str(ctx.author.id)
    if user_id in chat_history:
        chat_history[user_id] = []
        await ctx.send("Riwayat chat kamu sudah direset!")
    else:
        await ctx.send("Kamu belum memiliki riwayat chat.")

# Jalankan bot
bot.run(TOKEN)
