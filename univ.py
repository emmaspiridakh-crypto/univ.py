import os
import threading

from flask import Flask
import discord
from discord.ext import commands

# ============================
# CONFIG — ΒΑΖΕΙΣ ΕΣΥ ΤΑ IDs
# ============================

TOKEN = os.getenv("DISCORD_TOKEN")

# Ticket system roles
FOUNDER_ID = 1456762635302211722
OWNER_ID = 1456762635302211721
CO_OWNER_ID = 1456762635302211720
STAFF_ID = 1456762635205873676
DONATE_MANAGER_ID = 1456762635302211717

# Ticket logs
TICKET_LOG_CHANNEL_ID = 1456762636376215608

AUTOROLE_ID = 1456762635075846425 

# Server logs (6 channels όπως ζήτησες)
MEMBER_JOIN_LOG = 1456762636040540183
MEMBER_LEAVE_LOG = 1456762636040540184
ROLE_LOG = 1456762636040540185
MESSAGE_LOG = 1456762636040540188
VOICE_LOG = 1456762636376215609
CHANNEL_LOG = 1456762636376215605


# ============================
# FLASK KEEP-ALIVE (Render uptime)
# ============================

app = Flask(__name__)

@app.route("/")
def home():
    return "OK — bot is running."

def run_flask():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()


# ============================
# BOT SETUP
# ============================

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


# ============================
# HELPERS
# ============================

def is_founder(member: discord.Member) -> bool:
    return any(r.id == FOUNDER_ID for r in member.roles)

def is_panel_allowed(member: discord.Member) -> bool:
    allowed = {FOUNDER_ID, OWNER_ID, CO_OWNER_ID}
    return any(r.id in allowed for r in member.roles)

def get_ticket_log_channel(guild: discord.Guild):
    return guild.get_channel(TICKET_LOG_CHANNEL_ID)

# ============================
# CLOSE BUTTON
# ============================

class CloseTicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, emoji="🔒")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        guild = interaction.guild
        user = interaction.user

        log_ch = get_ticket_log_channel(guild)
        if log_ch:
            embed = discord.Embed(
                title="🔒 Ticket Closed",
                color=discord.Color.red()
            )
            embed.add_field(name="👤 Closed By", value=user.mention, inline=False)
            embed.add_field(name="📁 Channel", value=channel.mention, inline=False)
            embed.timestamp = discord.utils.utcnow()
            await log_ch.send(embed=embed)

        await channel.delete()

# ============================
# TICKET DROPDOWN
# ============================

class TicketDropdown(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        options = [
            discord.SelectOption(label="Owner", emoji="👑"),
            discord.SelectOption(label="Support", emoji="💬"),
            discord.SelectOption(label="Ban Appeal", emoji="⚖️"),
            discord.SelectOption(label="Bug", emoji="🐞"),
            discord.SelectOption(label="Clip Permission", emoji="🎥"),
            discord.SelectOption(label="Staff Report", emoji="🚨"),
            discord.SelectOption(label="Donate", emoji="💸"),
            discord.SelectOption(label="Other", emoji="📁"),
        ]

        select = discord.ui.Select(
            placeholder="Διάλεξε κατηγορία ticket",
            options=options
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        category = interaction.data["values"][0]
        guild = interaction.guild
        user = interaction.user

        # Permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        if category == "Owner":
            roles = [FOUNDER_ID, OWNER_ID, CO_OWNER_ID]
        elif category == "Support":
            roles = [FOUNDER_ID, OWNER_ID, CO_OWNER_ID, STAFF_ID]
        elif category == "Ban Appeal":
            roles = [FOUNDER_ID, OWNER_ID, CO_OWNER_ID]
        elif category == "Bug":
            roles = [FOUNDER_ID, OWNER_ID, CO_OWNER_ID]
        elif category == "Clip Permission":
            roles = [FOUNDER_ID, OWNER_ID, CO_OWNER_ID]
        elif category == "Staff Report":
            roles = [FOUNDER_ID, OWNER_ID, CO_OWNER_ID]
        elif category == "Donate":
            roles = [FOUNDER_ID, OWNER_ID, CO_OWNER_ID, DONATE_MANAGER_ID]
        elif category == "Other":
            roles = [FOUNDER_ID, OWNER_ID, CO_OWNER_ID, STAFF_ID]
        else:
            roles = [FOUNDER_ID, OWNER_ID, CO_OWNER_ID, STAFF_ID]
               
        for role_id in roles:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True
                )

        # Create ticket channel
        channel = await guild.create_text_channel(
            name=f"{category}-{user.name}",
            overwrites=overwrites
        )

        # Ticket embed
        embed = discord.Embed(
            title=f"🎫 {category} Ticket",
            color=discord.Color.blue()
        )
        embed.add_field(name="👤 User", value=user.mention, inline=False)
        embed.add_field(name="📂 Category", value=category, inline=False)
        embed.add_field(
            name="📌 Info",
            value="Περίμενε λίγο και θα έρθουμε να σε εξυπηρετήσουμε σύντομα!",
            inline=False
        )
        embed.timestamp = discord.utils.utcnow()

        view = CloseTicketButton()
        await channel.send(embed=embed, view=view)

        # Log creation
        log_ch = get_ticket_log_channel(guild)
        if log_ch:
            log_embed = discord.Embed(
                title="🆕 Ticket Created",
                color=discord.Color.green()
            )
            log_embed.add_field(name="👤 User", value=user.mention, inline=False)
            log_embed.add_field(name="📂 Category", value=category, inline=False)
            log_embed.add_field(name="📁 Channel", value=channel.mention, inline=False)
            log_embed.timestamp = discord.utils.utcnow()
            await log_ch.send(embed=log_embed)

        await interaction.response.send_message(
            f"📨 Το ticket σου δημιουργήθηκε: {channel.mention}",
            ephemeral=True
        )

# ============================
# TEMP VOICE CHANNEL SYSTEM
# ============================

SUPPORT_VOICE_ID = 1456762640226451585  # ΒΑΛΕ ΤΟ ID ΤΟΥ SUPPORT VOICE LOBBY

temp_voice_channels = {}  # user_id : channel_id


@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild

    # ========== USER JOINS SUPPORT LOBBY ==========
    if after.channel and after.channel.id == SUPPORT_VOICE_ID:

        # Αν έχει ήδη temp channel, μην ξαναφτιάξεις
        if member.id in temp_voice_channels:
            return

        # Δημιουργία προσωρινού voice channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True),
        }

        # Προσθήκη STAFF
        staff_role = guild.get_role(STAFF_ID)
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True, connect=True, speak=True
            )

        # Δημιουργία channel
        temp_channel = await guild.create_voice_channel(
            name=f"Support - {member.name}",
            overwrites=overwrites,
            category=after.channel.category
        )

        # Μεταφορά χρήστη στο νέο κανάλι
        await member.move_to(temp_channel)

        # Αποθήκευση
        temp_voice_channels[member.id] = temp_channel.id

    # ========== USER LEAVES A TEMP CHANNEL ==========
    if before.channel and before.channel.id in temp_voice_channels.values():

        channel = before.channel

        # Αν το channel είναι άδειο → διαγραφή
        if len(channel.members) == 0:
            await channel.delete()

            # Αφαίρεση από το dict
            for user_id, chan_id in list(temp_voice_channels.items()):
                if chan_id == channel.id:
                    del temp_voice_channels[user_id]
@bot.event
async def on_member_join(member):
    channel = member.guild.get_channel(MEMBER_JOIN_LOG)
    if channel:
        embed = discord.Embed(
            title="📥 **Member Joined**",
            color=discord.Color.green()
        )
        embed.add_field(name="👤 User", value=f"{member.mention} (`{member.id}`)", inline=False)
        embed.add_field(name="📅 Account Created", value=str(member.created_at)[:19], inline=False)
        embed.timestamp = discord.utils.utcnow()
        embed.set_thumbnail(url=member.avatar)
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = member.guild.get_channel(MEMBER_LEAVE_LOG)
    if channel:
        embed = discord.Embed(
            title="📤 **Member Left**",
            color=discord.Color.red()
        )
        embed.add_field(name="👤 User", value=f"{member.mention} (`{member.id}`)", inline=False)
        embed.add_field(name="📅 Joined Server", value=str(member.joined_at)[:19], inline=False)
        embed.timestamp = discord.utils.utcnow()
        embed.set_thumbnail(url=member.avatar)
        await channel.send(embed=embed)

# ============================
# AUTOROLE SYSTEM
# ============================

@bot.event
async def on_member_join(member):
    # === AUTOROLE ===
    role = member.guild.get_role(AUTOROLE_ID)
    if role:
        try:
            await member.add_roles(role)
        except:
            pass

@bot.event
async def on_member_update(before, after):
    channel = after.guild.get_channel(ROLE_LOG)
    if not channel:
        return

    before_roles = set(before.roles)
    after_roles = set(after.roles)

    added = after_roles - before_roles
    removed = before_roles - after_roles

    # ROLE ADDED
    if added:
        for role in added:
            embed = discord.Embed(
                title="🟩 **Role Added**",
                color=discord.Color.green()
            )
            embed.add_field(name="👤 User", value=after.mention, inline=False)
            embed.add_field(name="➕ Role Added", value=role.mention, inline=False)
            embed.timestamp = discord.utils.utcnow()
            await channel.send(embed=embed)

    # ROLE REMOVED
    if removed:
        for role in removed:
            embed = discord.Embed(
                title="🟥 **Role Removed**",
                color=discord.Color.red()
            )
            embed.add_field(name="👤 User", value=after.mention, inline=False)
            embed.add_field(name="➖ Role Removed", value=role.mention, inline=False)
            embed.timestamp = discord.utils.utcnow()
            await channel.send(embed=embed)

@bot.event
async def on_guild_role_create(role):
    channel = role.guild.get_channel(ROLE_LOG)
    if channel:
        embed = discord.Embed(
            title="🆕 **Role Created**",
            color=discord.Color.blue()
        )
        embed.add_field(name="📛 Role", value=role.mention, inline=False)
        embed.timestamp = discord.utils.utcnow()
        await channel.send(embed=embed)

@bot.event
async def on_guild_role_delete(role):
    channel = role.guild.get_channel(ROLE_LOG)
    if channel:
        embed = discord.Embed(
            title="❌ **Role Deleted**",
            color=discord.Color.dark_red()
        )
        embed.add_field(name="📛 Role", value=role.name, inline=False)
        embed.timestamp = discord.utils.utcnow()
        await channel.send(embed=embed)

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    channel = message.guild.get_channel(MESSAGE_LOG)
    if channel:
        embed = discord.Embed(
            title="🗑️ **Message Deleted**",
            color=discord.Color.red()
        )
        embed.add_field(name="👤 User", value=message.author.mention, inline=False)
        embed.add_field(name="📍 Channel", value=message.channel.mention, inline=False)
        embed.add_field(name="💬 Content", value=message.content or "*No content*", inline=False)
        embed.timestamp = discord.utils.utcnow()
        await channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return
    if before.content == after.content:
        return

    channel = before.guild.get_channel(MESSAGE_LOG)
    if channel:
        embed = discord.Embed(
            title="✏️ **Message Edited**",
            color=discord.Color.orange()
        )
        embed.add_field(name="👤 User", value=before.author.mention, inline=False)
        embed.add_field(name="📍 Channel", value=before.channel.mention, inline=False)
        embed.add_field(name="📝 Before", value=before.content or "*Empty*", inline=False)
        embed.add_field(name="📝 After", value=after.content or "*Empty*", inline=False)
        embed.timestamp = discord.utils.utcnow()
        await channel.send(embed=embed)

@bot.event
async def on_voice_state_update(member, before, after):
    channel = member.guild.get_channel(VOICE_LOG)
    if not channel:
        return

    # JOIN
    if before.channel is None and after.channel is not None:
        embed = discord.Embed(
            title="🔊 **Voice Join**",
            color=discord.Color.green()
        )
        embed.add_field(name="👤 User", value=member.mention, inline=False)
        embed.add_field(name="📍 Channel", value=after.channel.mention, inline=False)
        embed.timestamp = discord.utils.utcnow()
        await channel.send(embed=embed)

    # LEAVE
    elif before.channel is not None and after.channel is None:
        embed = discord.Embed(
            title="🔇 **Voice Leave**",
            color=discord.Color.red()
        )
        embed.add_field(name="👤 User", value=member.mention, inline=False)
        embed.add_field(name="📍 Channel", value=before.channel.mention, inline=False)
        embed.timestamp = discord.utils.utcnow()
        await channel.send(embed=embed)

    # MOVE
    elif before.channel != after.channel:
        embed = discord.Embed(
            title="🔁 **Voice Move**",
            color=discord.Color.orange()
        )
        embed.add_field(name="👤 User", value=member.mention, inline=False)
        embed.add_field(name="➡️ From", value=before.channel.mention, inline=True)
        embed.add_field(name="➡️ To", value=after.channel.mention, inline=True)
        embed.timestamp = discord.utils.utcnow()
        await channel.send(embed=embed)

@bot.event
async def on_guild_channel_create(channel_obj):
    channel = channel_obj.guild.get_channel(CHANNEL_LOG)
    if channel:
        embed = discord.Embed(
            title="📁 **Channel Created**",
            color=discord.Color.green()
        )
        embed.add_field(name="📛 Name", value=channel_obj.name, inline=False)
        embed.add_field(name="📂 Type", value=str(channel_obj.type), inline=False)
        embed.timestamp = discord.utils.utcnow()
        await channel.send(embed=embed)

@bot.event
async def on_guild_channel_delete(channel_obj):
    channel = channel_obj.guild.get_channel(CHANNEL_LOG)
    if channel:
        embed = discord.Embed(
            title="🗑️ **Channel Deleted**",
            color=discord.Color.red()
        )
        embed.add_field(name="📛 Name", value=channel_obj.name, inline=False)
        embed.add_field(name="📂 Type", value=str(channel_obj.type), inline=False)
        embed.timestamp = discord.utils.utcnow()
        await channel.send(embed=embed)

# ============================
# COMMANDS
# ============================

@bot.command()
async def ticketpanel(ctx):
    if not is_panel_allowed(ctx.author):
        return await ctx.send("❌ Δεν έχεις άδεια να χρησιμοποιήσεις αυτή την εντολή.")

    embed = discord.Embed(
        title="🎟️ Universe Roleplay Roblox Tickets",
        description=(
            "💠 Για άμεση επικοινωνία με το κατάλληλο άτομο,\n"
            "διάλεξε σωστά την κατηγορία του ticket.\n\n"
            "📎 Το Support είναι εδώ για να βοηθήσει.\n"
        
        ),
        color=discord.Color.()
    )

    embed.set_image(url="https://i.imgur.com/GP0vv0W.jpeg")

    view = TicketDropdown()
    await ctx.send(embed=embed, view=view)


@bot.command()
async def say(ctx, *, message):
    if not is_founder(ctx.author):
        return await ctx.send("❌ Δεν έχεις άδεια.")
    await ctx.send(message)


@bot.command()
async def dmall(ctx, *, message):
    if not is_founder(ctx.author):
        return await ctx.send("❌ Δεν έχεις άδεια.")

    sent = 0
    for member in ctx.guild.members:
        if member.bot:
            continue
        try:
            await member.send(message)
            sent += 1
        except:
            pass

    await ctx.send(f"📨 DM στάλθηκαν σε {sent} μέλη.")

# ============================
# BOT READY EVENT
# ============================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")
    print("Bot is fully online and operational.")


# ============================
# START BOT
# ============================

if __name__ == "__main__":
    keep_alive()  # Flask uptime
    bot.run(TOKEN)
