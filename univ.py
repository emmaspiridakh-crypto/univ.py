import os
import threading

from flask import Flask
import discord
from discord.ext import commands
import discord
from discord.ext import tasks

# ========
# CONFIG 
# ========

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

# Server logs 
MEMBER_JOIN_LOG = 1456762636040540183
MEMBER_LEAVE_LOG = 1456762636040540184
ROLE_LOG = 1456762636040540185
MESSAGE_LOG = 1456762636040540188
VOICE_LOG = 1456762636376215609
CHANNEL_LOG = 1456762636376215605

STATUS_CHANNEL_ID = 1483500984989913169  # ΒΑΛΕ ΤΟ VOICE CHANNEL ID
GUILD_ID = 1456762635075846420  # ΒΑΛΕ ΤΟ SERVER ID

# ============================================================
# LOG CHANNEL IDS (ΒΑΛΕ ΤΑ ΔΙΚΑ ΣΟΥ)
# ============================================================
BAN_LOG = 1456762636040540187
UNBAN_LOG = 1456762636040540187
KICK_LOG = 1483494737439621261
TIMEOUT_LOG = 1456762636040540186

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

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
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

def is_staff():
    async def predicate(ctx):
        user_roles = [role.id for role in ctx.author.roles]
        if any(r in user_roles for r in ALLOWED_ROLES):
            return True
        await ctx.send("❌ Δεν έχεις άδεια να χρησιμοποιήσεις αυτό το command.")
        return False
    return commands.check(predicate)

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

TICKET_CATEGORY_ID = 1456762638691467287

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
        category = guild.get_channel(TICKET_CATEGORY_ID)
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

# ============================================================
# SECTION — JOB PANEL & TICKET SYSTEM
# ============================================================

import discord
from discord.ext import commands
from discord.ui import View, Select, Button

# === PLACEHOLDERS (ΒΑΛΕ ΤΑ ΔΙΚΑ ΣΟΥ) ===
TICKET_CATEGORY_ID = 1456762638691467287  # Category όπου θα ανοίγουν τα tickets
JOB_MANAGER_ID = 1456762635256332289     # Job Manager role

ALLOWED_TICKET_ROLES = [JOB_MANAGER_ID, OWNER_ID, FOUNDER_ID]


# ============================================================
# DROPDOWN MENU
# ============================================================

class JobDropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Criminal Job", description="Άνοιγμα ticket για Criminal Job", emoji="🔫"),
            discord.SelectOption(label="Civilian Job", description="Άνοιγμα ticket για Civilian Job", emoji="👔"),
        ]

        super().__init__(
            placeholder="Επίλεξε κατηγορία job...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        job_type = self.values[0]

        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        # Roles που βλέπουν όλα τα tickets
        for role_id in ALLOWED_TICKET_ROLES:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        # Δημιουργία ticket channel
        channel = await guild.create_text_channel(
            name=f"{job_type.lower().replace(' ', '-')}-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        # Embed μέσα στο ticket
        embed = discord.Embed(
            title=f"🎫 Ticket Created — {job_type}",
            description=(
                f"👤 **User:** {interaction.user.mention}\n"
                f"📌 **Category:** {job_type}\n\n"
                "Παρακαλώ περιμένετε να σας εξυπηρετήσει το προσωπικό."
            ),
            color=discord.Color.blue()
        )

        # Close button
        view = CloseTicketView()

        await channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"Το ticket σου δημιουργήθηκε: {channel.mention}", ephemeral=True)


# ============================================================
# CLOSE BUTTON
# ============================================================

class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.channel.delete()


# ============================================================
# JOB PANEL COMMAND
# ============================================================

@bot.command()
async def jobpanel(ctx):
    embed = discord.Embed(
        title="💼 Job Panel",
        description="Επίλεξε κατηγορία job από το dropdown menu.",
        color=discord.Color.gold()
    )
    embed.set_image(url="https://i.imgur.com/ZLyLVjA.jpeg")  # ΒΑΛΕ ΤΗ ΔΙΚΗ ΣΟΥ ΕΙΚΟΝΑ

    view = View()
    view.add_item(JobDropdown())

    await ctx.send(embed=embed, view=view)

# ============================
# TEMP VOICE CHANNEL SYSTEM
# ============================

SUPPORT_VOICE_ID = 1456762640226451585  # ΒΑΛΕ ΤΟ ID ΤΟΥ SUPPORT VOICE LOBBY
STAFF_ID = 1456762635205873676  # ΒΑΛΕ ΤΟ STAFF ROLE ID

temp_voice_channels = {}  # user_id : channel_id


@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild

    # ========== USER JOINS SUPPORT LOBBY ==========
    if after.channel and after.channel.id == SUPPORT_VOICE_ID:

        # Αν έχει ήδη temp channel, μην ξαναφτιάξεις
        if member.id in temp_voice_channels:
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True),
        }

        # STAFF βλέπει όλα τα temp channels
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

        # Μεταφορά χρήστη
        try:
            await member.move_to(temp_channel)
        except:
            pass

        temp_voice_channels[member.id] = temp_channel.id

    # ========== USER LEAVES A TEMP CHANNEL ==========
    if before.channel and before.channel.id in temp_voice_channels.values():

        channel = before.channel

        if len(channel.members) == 0:
            await channel.delete()

            for user_id, chan_id in list(temp_voice_channels.items()):
                if chan_id == channel.id:
                    del temp_voice_channels[user_id]
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
        color=discord.Color.blue()
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

# ============================================================
# STAFF COMMANDS
# ============================================================

@bot.command()
@is_staff()
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)

    log = bot.get_channel(BAN_LOG)
    if log:
        embed = discord.Embed(
            title="🔨 Member Banned",
            description=f"**User:** {member}\n**By:** {ctx.author}\n**Reason:** {reason}",
            color=discord.Color.red()
        )
        await log.send(embed=embed)

    await ctx.send(f"🔨 {member} banned.")

@bot.command()
@is_staff()
async def unban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)

    log = bot.get_channel(UNBAN_LOG)
    if log:
        embed = discord.Embed(
            title="🔄 Member Unbanned",
            description=f"**User:** {user}\n**By:** {ctx.author}",
            color=discord.Color.green()
        )
        await log.send(embed=embed)

    await ctx.send(f"🔄 {user} unbanned.")

@bot.command()
@is_staff()
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)

    log = bot.get_channel(KICK_LOG)
    if log:
        embed = discord.Embed(
            title="🦶 Member Kicked",
            description=f"**User:** {member}\n**By:** {ctx.author}\n**Reason:** {reason}",
            color=discord.Color.orange()
        )
        await log.send(embed=embed)

    await ctx.send(f"🦶 {member} kicked.")

@bot.command()
@is_staff()
async def timeout(ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
    duration = timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)

    log = bot.get_channel(TIMEOUT_LOG)
    if log:
        embed = discord.Embed(
            title="⏳ Member Timed Out",
            description=f"**User:** {member}\n**By:** {ctx.author}\n**Duration:** {minutes} minutes\n**Reason:** {reason}",
            color=discord.Color.blue()
        )
        await log.send(embed=embed)

    await ctx.send(f"⏳ {member} timed out for {minutes} minutes.")

@bot.command()
async def panel(ctx):
    if not is_staff(ctx.author):
        return await ctx.send("❌ Δεν έχεις άδεια.")

    embed = discord.Embed(
        title="⚙️ Staff Commands Panel",
        description=(
            "**🔨 !ban <member> <reason>**\n"
            "**🆙 !unban <user_id>**\n"
            "**✏️ !kick <member> <reason>**\n"
            "**⏳ !timeout <member> <minutes> <reason>**\n"
        ),
        color=discord.Color.green()
    )
    embed.set_footer(text="Μόνο staff μπορούν να τα χρησιμοποιήσουν.")
    await ctx.send(embed=embed)
# ================================================
# SECTION — SERVER STATUS VOICE CHANNEL
# ================================================
@tasks.loop(seconds=30)
async def update_server_status():
    guild = bot.get_guild(GUILD_ID)
    if guild is None:
        return

    # Μετρήσεις
    total_members = len([m for m in guild.members if not m.bot])
    total_bots = len([m for m in guild.members if m.bot])
    online_members = len([m for m in guild.members if m.status != discord.Status.offline and not m.bot])

    # Voice channel
    channel = guild.get_channel(STATUS_CHANNEL_ID)
    if channel:
        try:
            await channel.edit(
                name=f"👥{total_members} | 🤖{total_bots} | 🟢{online_members}"
            )
    
        except:
            pass

async def start_status_task():
    await bot.wait_until_ready()
    update_server_status.start()

# ============================
# BOT READY EVENT
# ============================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")
    print("Bot is fully online and operational.")
    await start_status_task()


# ============================
# START BOT
# ============================

if __name__ == "__main__":
    keep_alive()  
    bot.run(TOKEN)
