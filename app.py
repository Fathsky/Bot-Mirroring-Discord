import discord
from discord.ext import commands
import requests
import aiohttp
import json
import os
from dotenv import load_dotenv
import asyncio
import yt_dlp as youtube_dl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import discord.ui
import datetime
import random

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

user_descriptions = {}
chat_history = {}
mirror_configs = {}
tickets = {}
music_queues = {}

# ========== Gemini AI Bebas Command ==========
def chat_gemini(prompt, user_id):
    if not GEMINI_API_KEY:
        return "⚠️ API Key tidak ditemukan."

    if user_id not in chat_history:
        chat_history[user_id] = []

    prompt = prompt.replace(f'<@{bot.user.id}>', '').strip()
    full_context = "\n".join(chat_history[user_id] + [prompt])

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": full_context}]}]}

    try:
        r = requests.post(url, headers=headers, json=data)
        result = r.json()
        reply = result["candidates"][0]["content"]["parts"][0]["text"]
        chat_history[user_id].append(prompt)
        chat_history[user_id].append(reply)
        chat_history[user_id] = chat_history[user_id][-10:]
        return reply
    except:
        return "❌ Gagal menghubungi AI."

@bot.command()
async def tanyaai(ctx, *, prompt):
    response = chat_gemini(prompt, str(ctx.author.id))
    await ctx.send(response)

# ========== Musik + Queue ==========
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'noplaylist': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'force-ipv4': True,
    'cachedir': False,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'opus',
        'preferredquality': '192'
    }],
    'prefer_ffmpeg': True
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -af volume=1.0'
}

ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

async def get_tracks_from_spotify_url(url):
    try:
        tracks = []
        if "playlist" in url:
            playlist_id = url.split("/")[-1].split("?")[0]
            results = sp.playlist_tracks(playlist_id)
            for item in results["items"]:
                if item["track"]:  # Pastikan track tidak None
                    track = item["track"]
                    title = f"{track['name']} {track['artists'][0]['name']}"
                    tracks.append(title)
        elif "album" in url:
            album_id = url.split("/")[-1].split("?")[0]
            results = sp.album_tracks(album_id)
            for item in results["items"]:
                title = f"{item['name']} {item['artists'][0]['name']}"
                tracks.append(title)
        return tracks
    except Exception as e:
        print(f"Error getting Spotify tracks: {e}")
        return None

async def get_tracks_from_youtube_playlist(url):
    try:
        info = ytdl.extract_info(url, download=False)
        tracks = []
        if 'entries' in info:
            for entry in info['entries']:
                if entry:
                    tracks.append({
                        'url': entry['url'],
                        'title': entry['title']
                    })
        return tracks
    except Exception as e:
        print(f"Error getting YouTube playlist: {e}")
        return None

# Panel Kontrol Musik
class MusicControlView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx

    @discord.ui.button(label="▶ Play", style=discord.ButtonStyle.green, custom_id="music_play")
    async def play_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Hanya yang memutar musik yang bisa menggunakan tombol ini!", ephemeral=True)
            return
            
        voice = discord.utils.get(bot.voice_clients, guild=interaction.guild)
        if voice and voice.is_paused():
            async with self.ctx.channel.typing():
                await asyncio.sleep(1)
                voice.resume()
                await interaction.response.send_message("▶️ Melanjutkan pemutaran!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Tidak ada lagu yang di-pause!", ephemeral=True)

    @discord.ui.button(label="⏸ Pause", style=discord.ButtonStyle.blurple, custom_id="music_pause")
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Hanya yang memutar musik yang bisa menggunakan tombol ini!", ephemeral=True)
            return
            
        voice = discord.utils.get(bot.voice_clients, guild=interaction.guild)
        if voice and voice.is_playing():
            async with self.ctx.channel.typing():
                await asyncio.sleep(1)
                voice.pause()
                await interaction.response.send_message("⏸️ Musik di-pause!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Tidak ada lagu yang diputar!", ephemeral=True)

    @discord.ui.button(label="⏭ Skip", style=discord.ButtonStyle.blurple, custom_id="music_skip")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Hanya yang memutar musik yang bisa menggunakan tombol ini!", ephemeral=True)
            return
            
        voice = discord.utils.get(bot.voice_clients, guild=interaction.guild)
        if voice and voice.is_playing():
            async with self.ctx.channel.typing():
                await asyncio.sleep(1)
                voice.stop()
                await interaction.response.send_message("⏭️ Melewati lagu ini!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Tidak ada lagu yang bisa di-skip!", ephemeral=True)

    @discord.ui.button(label="⏹ Stop", style=discord.ButtonStyle.red, custom_id="music_stop")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Hanya yang memutar musik yang bisa menggunakan tombol ini!", ephemeral=True)
            return
            
        voice = discord.utils.get(bot.voice_clients, guild=interaction.guild)
        if voice:
            async with self.ctx.channel.typing():
                await asyncio.sleep(1)
                if voice.is_playing() or voice.is_paused():
                    voice.stop()
                    music_queues[interaction.guild.id] = []  # Clear queue
                await interaction.response.send_message("⏹️ Musik dihentikan dan antrian dibersihkan!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Bot tidak sedang di voice channel!", ephemeral=True)

async def play_next(ctx):
    """Memutar lagu berikutnya dari antrian"""
    try:
        guild_id = ctx.guild.id
        if guild_id not in music_queues or not music_queues[guild_id]:
            return
            
        # Ambil lagu berikutnya
        next_track = music_queues[guild_id].pop(0)
        
        # Cari dan putar lagu
        if not ('youtube.com' in next_track or 'youtu.be' in next_track):
            info = ytdl.extract_info(f"ytsearch:{next_track}", download=False)['entries'][0]
        else:
            info = ytdl.extract_info(next_track, download=False)
            
        url = info['url']
        title = info['title']
        await play_song(ctx, url, title)
        
    except Exception as e:
        print(f"[MUSIC] Error dalam play_next: {e}")
        await ctx.send("❌ Gagal memutar lagu berikutnya.")
        if music_queues.get(guild_id):
            await play_next(ctx)

async def play_song(ctx, url, title):
    try:
        voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if not voice:
            return
            
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS))
        
        def after_callback(error):
            if error:
                print(f"[MUSIC] Error dalam callback: {error}")
                asyncio.run_coroutine_threadsafe(
                    ctx.send("❌ Terjadi error saat memutar musik!"),
                    bot.loop
                )
            else:
                # Putar lagu berikutnya setelah selesai
                asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        
        # Kirim pesan pemberitahuan sebelum memutar lagu
        await ctx.send(f"🎵 **INI KAN LAGU YANG KAMU MAU, SELAMAT MENDENGARKAN YA!**\n**{title}**")
        await asyncio.sleep(1)  # Tunggu sebentar agar pesan terlihat
        
        voice.play(source, after=after_callback)
        
        # Buat embed dengan info antrian
        guild_id = ctx.guild.id
        queue_info = ""
        if guild_id in music_queues and music_queues[guild_id]:
            next_songs = music_queues[guild_id][:3]  # Ambil 3 lagu berikutnya
            queue_info = "\n\n**📋 Berikutnya:**\n"
            for i, song in enumerate(next_songs, 1):
                queue_info += f"{i}. {song}\n"
            if len(music_queues[guild_id]) > 3:
                queue_info += f"\n...dan {len(music_queues[guild_id]) - 3} lagu lainnya"
        
        embed = discord.Embed(
            title="🎵 Panel Kontrol Musik",
            description=f"Sekarang memutar: **{title}**{queue_info}",
            color=discord.Color.blue()
        )
        view = MusicControlView(ctx)
        await ctx.send(embed=embed, view=view)
        
    except Exception as e:
        print(f"[MUSIC] Error saat memutar: {str(e)}")
        await ctx.send(f"❌ Gagal memutar lagu: {str(e)}")

@bot.command()
async def join(ctx):
    """Bot bergabung ke voice channel"""
    if ctx.author.voice:
        try:
            await ctx.author.voice.channel.connect()
            await ctx.send("✅ Ciluk Baa WKWKWKW, halo aku join ya!")
        except Exception as e:
            await ctx.send(f"❌ Gagal join: {str(e)}")
    else:
        await ctx.send("❌ Kamu harus join voice channel dulu!")

@bot.command()
async def panel(ctx):
    """Menampilkan panel kontrol musik"""
    embed = discord.Embed(
        title="🎵 Panel Kontrol Musik",
        description="Gunakan tombol di bawah untuk mengontrol musik",
        color=discord.Color.blue()
    )
    view = MusicControlView(ctx)
    await ctx.send(embed=embed, view=view)

@bot.command()
async def skip(ctx):
    """Skip lagu yang sedang diputar"""
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        voice.stop()
        await ctx.send("⏭️ Melewati lagu ini!")
    else:
        await ctx.send("❌ Tidak ada lagu yang bisa di-skip!")

@bot.command()
async def musichelp(ctx):
    """Menampilkan daftar command musik"""
    embed = discord.Embed(
        title="🎵 Daftar Command Musik",
        description="Berikut adalah command-command yang tersedia:",
        color=discord.Color.blue()
    )
    
    # Command Pemutaran
    embed.add_field(
        name="📱 Command Utama",
        value="""
        `!join` - Ciluk Baa WKWKWKW, halo aku join ya !
        `!play [nama/URL]` - Memutar lagu atau playlist
        `!skip` - Melewati lagu yang diputar
        `!stop` - Menghentikan lagu
        `!pause` - Menjeda lagu
        `!resume` - Melanjutkan lagu
        `!leave` - Aku keluar dari voice channel yaa, Bye bye !!
        """,
        inline=False
    )
    
    # Command Tambahan
    embed.add_field(
        name="🎛️ Command Tambahan",
        value="""
        `!panel` - Menampilkan tombol kontrol musik
        `!antrian` - Melihat daftar lagu dalam antrian
        `!playlist [URL]` - Melihat isi playlist Spotify/YouTube
        """,
        inline=False
    )
    
    # Contoh Penggunaan
    embed.add_field(
        name="💡 Contoh Penggunaan",
        value="""
        1. Join dan putar musik:
        • `!join`
        • `!play baik baik sayang`
        
        2. Putar playlist:
        • `!play https://open.spotify.com/playlist/...`
        • `!play https://www.youtube.com/playlist?list=...`
        
        3. Lihat isi playlist:
        • `!playlist https://open.spotify.com/playlist/...`
        """,
        inline=False
    )
    
    embed.set_footer(text="Gunakan !panel untuk menampilkan tombol kontrol musik")
    await ctx.send(embed=embed)

@bot.command()
async def play(ctx, *, query):
    try:
        # Pastikan user di voice channel
        if not ctx.author.voice:
            await ctx.send("❌ Kamu harus join voice channel dulu!")
            return

        async with ctx.channel.typing():
            # Join voice channel jika belum
            voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
            if not voice:
                try:
                    voice = await ctx.author.voice.channel.connect()
                    await asyncio.sleep(1)
                    await ctx.send("✅ Joined voice channel!")
                except Exception as e:
                    await ctx.send(f"❌ Gagal join voice channel: {str(e)}")
                    return

            # Inisialisasi queue jika belum ada
            guild_id = ctx.guild.id
            if guild_id not in music_queues:
                music_queues[guild_id] = []

            # Handle Spotify playlist/album
            if "spotify.com" in query:
                await ctx.send("🔍 Mencari lagu dari Spotify...")
                tracks = await get_tracks_from_spotify_url(query)
                if not tracks:
                    await ctx.send("❌ Gagal mendapatkan lagu dari Spotify!")
                    return
                    
                await asyncio.sleep(1)
                await ctx.send(f"📥 Menambahkan {len(tracks)} lagu dari Spotify ke antrian...")
                music_queues[guild_id].extend(tracks)
                
                if not voice.is_playing():
                    await play_next(ctx)
                return

            # Handle YouTube playlist
            if "playlist" in query and ("youtube.com" in query or "youtu.be" in query):
                await ctx.send("🔍 Mencari playlist YouTube...")
                tracks = await get_tracks_from_youtube_playlist(query)
                if not tracks:
                    await ctx.send("❌ Gagal mendapatkan playlist YouTube!")
                    return
                    
                await asyncio.sleep(1)
                await ctx.send(f"📥 Menambahkan {len(tracks)} lagu dari YouTube ke antrian...")
                for track in tracks:
                    music_queues[guild_id].append(track['url'])
                
                if not voice.is_playing():
                    await play_next(ctx)
                return

            # Handle single track
            try:
                await ctx.send("🔍 Mencari lagu...")
                await asyncio.sleep(1)
                
                # Tambahkan ke antrian
                music_queues[guild_id].append(query)
                position = len(music_queues[guild_id])
                
                if not voice.is_playing():
                    await play_next(ctx)
                else:
                    await ctx.send(f"➕ Ditambahkan ke antrian (#{position}): `{query}`")
                
            except Exception as e:
                await ctx.send(f"❌ Gagal mencari lagu: {str(e)}")
                return

    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command()
async def stop(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice and (voice.is_playing() or voice.is_paused()):
        voice.stop()
        await ctx.send("⏹️ Musik dihentikan!")
    else:
        await ctx.send("❌ Tidak ada musik yang diputar!")

@bot.command()
async def pause(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_playing():
        voice.pause()
        await ctx.send("⏸️ Musik di-pause!")
    else:
        await ctx.send("❌ Tidak ada musik yang diputar!")

@bot.command()
async def resume(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_paused():
        voice.resume()
        await ctx.send("▶️ Melanjutkan pemutaran!")
    else:
        await ctx.send("❌ Tidak ada musik yang di-pause!")

@bot.command()
async def leave(ctx):
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice:
        await voice.disconnect()
        await ctx.send("👋 Aku keluar dari voice channel yaa, Bye bye!")

# ========== Mirror Setup (Tombol + Modal) ==========
class MirrorModal(discord.ui.Modal, title="Setup Mirror"):
    source_id = discord.ui.TextInput(label="Channel ID Sumber")
    target_id = discord.ui.TextInput(label="Channel ID Tujuan")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            source = int(self.source_id.value)
            target = int(self.target_id.value)
            mirror_configs[interaction.guild.id] = {"source": source, "target": target}
            await interaction.response.send_message("✅ Mirror diset!", ephemeral=True)
        except:
            await interaction.response.send_message("❌ Gagal parsing ID!", ephemeral=True)

class MirrorButton(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(label="Buat Pesan Mirror", style=discord.ButtonStyle.green, custom_id="mirror_button"))

@bot.command()
async def mirror(ctx):
    view = MirrorButton()
    await ctx.send("Klik tombol untuk setup Mirror:", view=view)

@bot.event
async def on_interaction(interaction):
    if interaction.data.get("custom_id") == "mirror_button":
        await interaction.response.send_modal(MirrorModal())

# ========== Tiket System ==========
class TicketModal(discord.ui.Modal, title="Tiket"):
    alasan = discord.ui.TextInput(label="Kenapa buka tiket?", required=True)
    
    async def on_submit(self, interaction: discord.Interaction):
        ticket_id = random.randint(100, 999)
        open_time = datetime.datetime.now()
        
        # Buat embed untuk tiket dibuka
        embed_open = discord.Embed(
            title="🎫 Tiket Dibuka",
            description=f"Tiket #{ticket_id} telah dibuat.",
            color=discord.Color.green(),
            timestamp=open_time
        )
        embed_open.add_field(name="Ticket ID", value=ticket_id, inline=True)
        embed_open.add_field(name="Opened By", value=interaction.user.mention, inline=True)
        embed_open.add_field(name="Reason", value=self.alasan.value, inline=False)
        embed_open.set_footer(text=f"Today at {open_time.strftime('%I:%M %p')}")

        # Simpan data tiket
        tickets[ticket_id] = {
            "user": interaction.user,
            "reason": self.alasan.value,
            "open_time": open_time,
            "claimed_by": None,
            "closed_by": None
        }

        await interaction.response.send_message(embed=embed_open, ephemeral=True)
        await asyncio.sleep(0.5)

        # Buat embed untuk tiket ditutup
        embed_closed = discord.Embed(
            title="📪 Ticket Closed",
            description="Makasi Ya Udah Open Tiket, Nanti Pasti Mimin Respon Ko!\n\nTicket Closed",
            color=discord.Color.dark_gray(),
            timestamp=open_time
        )
        embed_closed.add_field(name="🎟️ Ticket ID", value=ticket_id, inline=True)
        embed_closed.add_field(name="✅ Opened By", value=interaction.user.mention, inline=True)
        embed_closed.add_field(name="🔴 Closed By", value=interaction.user.mention, inline=True)
        embed_closed.add_field(name="🕒 Open Time", value=open_time.strftime('%B %d, %Y %I:%M %p'), inline=True)
        embed_closed.add_field(name="🧍 Claimed By", value="Not claimed", inline=True)
        embed_closed.add_field(name="🌀 Reason", value=self.alasan.value, inline=False)
        embed_closed.set_footer(text=f"Today at {open_time.strftime('%I:%M %p')}")

        # Buat view dengan rating buttons
        view = discord.ui.View()
        for i in range(1, 6):
            style = discord.ButtonStyle.green if i >= 4 else discord.ButtonStyle.red if i <= 2 else discord.ButtonStyle.blurple
            button = discord.ui.Button(label=f"{i} ⭐", style=style, custom_id=f"rating_{i}")
            view.add_item(button)

        await interaction.channel.send(embed=embed_closed, view=view)

class TicketView(discord.ui.View):
    @discord.ui.button(label="Buka Tiket", style=discord.ButtonStyle.green)
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketModal())

@bot.command()
async def tiket(ctx):
    await ctx.send("Klik untuk buka tiket:", view=TicketView())

# ========== Auto Respond AI + Mirror ==========
@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author.bot:
        return

    print(f"\n[Message] New message from {message.author}: {message.content}")
    print(f"[Message] Has reference: {bool(message.reference)}")
    if message.reference:
        print(f"[Message] Reference message ID: {message.reference.message_id}")

    # Cek mirror
    config = mirror_configs.get(message.guild.id)
    if config and message.channel.id == config["source"]:
        target = bot.get_channel(config["target"])
        if target:
            await target.send(f"{message.author.display_name}: {message.content}")

    # Cek reply ke bot dengan pengecekan yang lebih aman
    is_reply_to_bot = False
    if message.reference and message.reference.message_id:
        try:
            print(f"[Reply Check] Mencoba mengambil pesan yang di-reply...")
            replied = await message.channel.fetch_message(message.reference.message_id)
            print(f"[Reply Check] Pesan yang di-reply ditemukan. Author: {replied.author.id}, Bot ID: {bot.user.id}")
            
            if replied and replied.author.id == bot.user.id:
                is_reply_to_bot = True
                print(f"[Reply Check] ✅ Reply terdeteksi dari {message.author} ke pesan bot")
            else:
                print(f"[Reply Check] ❌ Reply bukan ke bot")
        except Exception as e:
            print(f"[Reply Check Error] {e}")

    is_ai_channel = message.channel.name.lower() == "chat-ai"
    is_mention = bot.user.mentioned_in(message)

    # Debug prints
    print(f"[Debug] AI Channel: {is_ai_channel}")
    print(f"[Debug] Is Mention: {is_mention}")
    print(f"[Debug] Is Reply: {is_reply_to_bot}")

    should_respond = is_reply_to_bot or is_ai_channel or is_mention
    print(f"[Decision] Should respond: {should_respond}")

    if should_respond:
        print(f"[AI Response] Bot akan merespon pesan dari {message.author}")
        try:
            async with message.channel.typing():
                prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
                response = chat_gemini(prompt, str(message.author.id))
                await message.channel.send(response)
            print(f"[AI Response] ✅ Berhasil mengirim respons")
        except Exception as e:
            print(f"[AI Response Error] {e}")
    else:
        print("[Decision] Bot tidak akan merespon")

@bot.event
async def on_ready():
    print(f"✅ Bot aktif sebagai {bot.user}")

@bot.command()
async def playlist(ctx, *, url):
    """Menampilkan daftar lagu dari playlist Spotify atau YouTube"""
    try:
        if "spotify.com" in url:
            tracks = await get_tracks_from_spotify_url(url)
            if not tracks:
                await ctx.send("❌ Gagal mendapatkan playlist Spotify!")
                return
                
            embed = discord.Embed(
                title="📋 Daftar Lagu Spotify",
                description="Gunakan command !play untuk memutar lagu",
                color=discord.Color.green()
            )
            
            for i, track in enumerate(tracks[:10], 1):
                embed.add_field(
                    name=f"#{i}",
                    value=track,
                    inline=False
                )
                
            if len(tracks) > 10:
                embed.set_footer(text=f"Dan {len(tracks) - 10} lagu lainnya...")
            
            await ctx.send(embed=embed)
            
        elif "youtube.com" in url or "youtu.be" in url:
            tracks = await get_tracks_from_youtube_playlist(url)
            if not tracks:
                await ctx.send("❌ Gagal mendapatkan playlist YouTube!")
                return
                
            embed = discord.Embed(
                title="📋 Daftar Lagu YouTube",
                description="Gunakan command !play untuk memutar lagu",
                color=discord.Color.red()
            )
            
            for i, track in enumerate(tracks[:10], 1):
                embed.add_field(
                    name=f"#{i}",
                    value=track['title'],
                    inline=False
                )
                
            if len(tracks) > 10:
                embed.set_footer(text=f"Dan {len(tracks) - 10} lagu lainnya...")
            
            await ctx.send(embed=embed)
            
        else:
            await ctx.send("❌ URL tidak valid! Gunakan URL playlist Spotify atau YouTube.")
            
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command()
async def antrian(ctx):
    """Menampilkan daftar antrian musik"""
    async with ctx.channel.typing():
        await asyncio.sleep(1)
        guild_id = ctx.guild.id
        if guild_id not in music_queues or not music_queues[guild_id]:
            await ctx.send("📭 Antrian kosong!")
            return
            
        embed = discord.Embed(
            title="📋 Daftar Antrian Musik",
            color=discord.Color.blue()
        )
        
        # Tampilkan maksimal 10 lagu
        for i, track in enumerate(music_queues[guild_id][:10], 1):
            embed.add_field(
                name=f"#{i}",
                value=track,
                inline=False
            )
        
        if len(music_queues[guild_id]) > 10:
            embed.set_footer(text=f"Dan {len(music_queues[guild_id]) - 10} lagu lainnya...")
        
        await ctx.send(embed=embed)

bot.run(TOKEN)
