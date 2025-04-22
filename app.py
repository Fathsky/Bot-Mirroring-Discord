import discord
from discord.ext import commands
import requests
import aiohttp
import json
import os
from dotenv import load_dotenv
import discord.ui
import datetime
import random
import asyncio

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

# Simpan konfigurasi mirror channel
mirror_configs = {}

# Simpan data tiket
tickets = {}

# Fungsi untuk komunikasi dengan Gemini AI
def chat_gemini(prompt, user_id):
    if not GEMINI_API_KEY:
        return "⚠️ API Key tidak ditemukan, periksa konfigurasi .env!"

    if user_id not in chat_history:
        chat_history[user_id] = []

    full_context = "\n".join(chat_history[user_id] + [prompt])

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": full_context}]}]}

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        result = response.json()
        try:
            response_text = result["candidates"][0]["content"]["parts"][0]["text"]

            chat_history[user_id].append(prompt)
            chat_history[user_id].append(response_text)

            if len(chat_history[user_id]) > 10:
                chat_history[user_id] = chat_history[user_id][-10:]

            return response_text
        except (KeyError, IndexError):
            return "⚠️ Terjadi kesalahan saat membaca respons dari AI."
    else:
        return f"⚠️ Error: {response.status_code} - {response.text}"

# Event ketika bot berhasil login
@bot.event
async def on_ready():
    print(f'✅ Bot {bot.user} sudah online!')

# Event untuk mirroring semua pesan dalam server
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.reference:
        try:
            replied_msg = await message.channel.fetch_message(message.reference.message_id)
            if replied_msg.author == bot.user:
                jawaban = chat_gemini(message.content, str(message.author.id))
                await message.channel.send(jawaban)
                return
        except discord.NotFound:
            pass

    if "nama kamu siapa" in message.content.lower():
        await message.channel.send("Nama gue adalah Johny Sins, Sang aktor bintang Pornografi terkenal Diseluruh dunia, HAHAHAHAHA 😜!")
        return

    if any(phrase in message.content.lower() for phrase in ["siapa yang develop", "siapa yang buat", "siapa developermu", "siapa yang bikin"]):
        developer_id = "742535420461711481"
        await message.channel.send(f"Yang develop aku namanya Fatih <@!{developer_id}>")
        return

    if message.channel.id in mirror_configs:
        config = mirror_configs[message.channel.id]
        print(f"🔄 Mirroring pesan dari {message.channel.name} ke webhook...")

        try:
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(config['webhook_url'], session=session)

                embed = discord.Embed(description=message.content, timestamp=message.created_at)
                embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url if message.author.avatar else None)
                files = [await a.to_file() for a in message.attachments] if message.attachments else []

                await webhook.send(
                    content=config['message'] or None,
                    embed=embed,
                    files=files,
                    username=message.author.display_name,
                    avatar_url=message.author.avatar.url if message.author.avatar else None
                )
        except Exception as e:
            print(f"⚠️ Error saat mengirim ke webhook: {e}")

    await bot.process_commands(message)

# View untuk rating dan tombol lainnya
class TicketClosedView(discord.ui.View):
    def __init__(self, thread_url="https://example.com/thread", transcript_url="https://example.com/transcript"):
        super().__init__(timeout=None)
        for i in range(1, 6):
            color = discord.ButtonStyle.green if i >= 4 else discord.ButtonStyle.red if i <= 2 else discord.ButtonStyle.blurple
            self.add_item(discord.ui.Button(label=f"{i} ⭐", style=color, custom_id=f"rating_{i}"))

# Button untuk buat tiket
class TicketOpenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(OpenTicketButton())

class OpenTicketButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🎫 Buka Tiket", style=discord.ButtonStyle.green, custom_id="open_ticket")

    async def callback(self, interaction: discord.Interaction):
        modal = TicketModal()
        await interaction.response.send_modal(modal)


# Modal untuk input alasan tiket
class TicketModal(discord.ui.Modal, title="Buat Tiket"):
    alasan = discord.ui.TextInput(label="Alasan Membuat Tiket", placeholder="Contoh: mau ucapin happy birthday ke mantan WKWK", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        ticket_id = random.randint(100, 999)
        open_time = datetime.datetime.now()
        user = interaction.user

        tickets[ticket_id] = {
            "user": user,
            "reason": self.alasan.value,
            "open_time": open_time,
            "claimed_by": None,
            "closed_by": None
        }

        embed = discord.Embed(
            title="🎫 Tiket Dibuka",
            description=f"Tiket #{ticket_id} telah dibuat.",
            color=discord.Color.green(),
            timestamp=open_time
        )
        embed.add_field(name="Ticket ID", value=str(ticket_id), inline=True)
        embed.add_field(name="Opened By", value=user.mention, inline=True)
        embed.add_field(name="Reason", value=self.alasan.value, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
        await asyncio.sleep(0.5)
        await close_ticket(ticket_id, closed_by=user, channel=interaction.channel)

# Fungsi untuk tutup tiket
async def close_ticket(ticket_id, closed_by, channel):
    tiket = tickets.get(ticket_id)
    if not tiket:
        await channel.send("❌ Tiket tidak ditemukan.")
        return

    tiket["closed_by"] = closed_by
    closed_time = datetime.datetime.now()

    embed = discord.Embed(
        title="📪 Ticket Closed",
        description="Makasi Ya Udah Open Tiket, Nanti Pasti Mimin Respon Ko!\n\nTicket Closed",
        color=discord.Color.dark_gray(),
        timestamp=closed_time
    )
    embed.add_field(name="🎟️ Ticket ID", value=str(ticket_id), inline=True)
    embed.add_field(name="✅ Opened By", value=tiket['user'].mention, inline=True)
    embed.add_field(name="🔴 Closed By", value=closed_by.mention, inline=True)
    embed.add_field(name="🕒 Open Time", value=tiket['open_time'].strftime('%B %d, %Y %I:%M %p'), inline=True)
    embed.add_field(name="🧍 Claimed By", value=tiket['claimed_by'] or "Not claimed", inline=True)
    embed.add_field(name="🌀 Reason", value=tiket['reason'], inline=False)

    view = TicketClosedView()
    await channel.send(embed=embed, view=view)

# Command buat munculin tombol buka tiket
@bot.command()
async def tiket(ctx):
    view = TicketOpenView()
    await ctx.send("Klik tombol di bawah untuk membuka tiket:", view=view)

# Command untuk ngobrol dengan AI
@bot.command()
async def tanya(ctx, *, pertanyaan):
    jawaban = chat_gemini(pertanyaan, str(ctx.author.id))
    await ctx.send(jawaban)

# Command untuk cek deskripsi user
@bot.command()
async def siapa(ctx, nama: str):
    nama = nama.lower()
    if nama in user_descriptions:
        await ctx.send(user_descriptions[nama])
    else:
        await ctx.send(f"Aku belum kenal sama {nama}, kasih tau aku dong biar aku kenal dia!")

# Command untuk reset riwayat chat
@bot.command()
async def reset(ctx):
    user_id = str(ctx.author.id)
    if user_id in chat_history:
        chat_history[user_id] = []
        await ctx.send("Riwayat chat kamu sudah direset!")
    else:
        await ctx.send("Kamu belum memiliki riwayat chat.")

# Modal untuk input mirror settings
class MirrorModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Setup Mirror Channel")
        self.add_item(discord.ui.TextInput(label="Channel ID Sumber", placeholder="Masukkan Channel ID...", required=True, style=discord.TextStyle.short))
        self.add_item(discord.ui.TextInput(label="Webhook URL Tujuan", placeholder="Masukkan Webhook URL...", required=True, style=discord.TextStyle.short))
        self.add_item(discord.ui.TextInput(label="Pesan (Opsional)", placeholder="Pesan yang ingin ditampilkan...", required=False, style=discord.TextStyle.paragraph))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            channel_id = int(self.children[0].value)
            webhook_url = self.children[1].value
            message = self.children[2].value
            mirror_configs[channel_id] = {'webhook_url': webhook_url, 'message': message}
            await interaction.response.send_message("✅ Mirror setup berhasil dikonfigurasi!", ephemeral=True)
            print(f"✅ Mirror Channel {channel_id} -> {webhook_url} (Pesan: {message})")
        except ValueError:
            await interaction.response.send_message("❌ Channel ID harus berupa angka!", ephemeral=True)

# View dengan satu button untuk setup mirror
class MirrorView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Buat Pesan Mirror", style=discord.ButtonStyle.green, emoji="📑", custom_id="mirror_setup"))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.data["custom_id"] == "mirror_setup":
            await interaction.response.send_modal(MirrorModal())
        return True

# Command untuk memunculkan button mirror
@bot.command()
async def mirror(ctx):
    view = MirrorView()
    await ctx.send("Klik button di bawah untuk buat Mirror Messages:", view=view)

# Jalankan bot
bot.run(TOKEN)