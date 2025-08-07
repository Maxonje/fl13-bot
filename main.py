import discord
from discord.ext import commands
import os
import requests

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Load environment variables (from Railway secrets)
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
ALLOWED_ROLE_ID = int(os.getenv("ALLOWED_ROLE_ID"))
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
GROUP_ID = int(os.getenv("GROUP_ID"))
RANK_ID = int(os.getenv("RANK_1"))

# Temporary in-memory data
applied_users = set()
user_links = {}

# Roblox API headers
roblox_headers = {
    'Content-Type': 'application/json',
    'Cookie': f'.ROBLOSECURITY={ROBLOX_COOKIE}'
}

# Get Roblox user ID from username
def get_user_id(username):
    response = requests.post("https://users.roblox.com/v1/usernames/users", json={
        "usernames": [username],
        "excludeBannedUsers": True
    })
    if response.status_code == 200 and response.json()["data"]:
        return response.json()["data"][0]["id"]
    return None

# Check if user is in the group
def is_in_group(user_id):
    response = requests.get(f"https://groups.roblox.com/v2/users/{user_id}/groups/roles")
    if response.status_code == 200:
        for group in response.json()["data"]:
            if group["group"]["id"] == GROUP_ID:
                return True
    return False

# Set rank
def set_rank(user_id):
    response = requests.patch(
        f"https://groups.roblox.com/v1/groups/{GROUP_ID}/users/{user_id}",
        headers=roblox_headers,
        json={"roleId": RANK_ID}
    )
    return response.status_code == 200

# Demote to rank 1
def rank_down(user_id):
    response = requests.patch(
        f"https://groups.roblox.com/v1/groups/{GROUP_ID}/users/{user_id}",
        headers=roblox_headers,
        json={"roleId": 1}
    )
    return response.status_code == 200

# Slash command: /turfapply
@bot.slash_command(name="turfapply", description="Apply for Turf by verifying your Roblox username.")
async def turfapply(ctx: discord.ApplicationContext, username: str):
    member = ctx.author

    # Role check
    if ALLOWED_ROLE_ID not in [role.id for role in member.roles]:
        embed = discord.Embed(
            title="Access Denied",
            description="You must have the required role to use this command.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, ephemeral=True)
        return

    # Already applied check
    if member.id in applied_users:
        embed = discord.Embed(
            title="Already Applied",
            description="You have already submitted your Turf application.",
            color=discord.Color.orange()
        )
        await ctx.respond(embed=embed, ephemeral=True)
        return

    # Username format check
    if "fl13" not in username.lower():
        embed = discord.Embed(
            title="Invalid Username",
            description="Your Roblox username must contain **'fl13'** to apply.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, ephemeral=True)
        return

    # Get Roblox user ID
    user_id = get_user_id(username)
    if not user_id:
        embed = discord.Embed(
            title="User Not Found",
            description=f"Could not find a Roblox user with the username `{username}`.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, ephemeral=True)
        return

    # Check if in group
    if not is_in_group(user_id):
        embed = discord.Embed(
            title="Not in Group",
            description="You must already be a member of the Roblox group to apply.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, ephemeral=True)
        return

    # Set rank
    if set_rank(user_id):
        applied_users.add(member.id)
        user_links[member.id] = user_id

        embed = discord.Embed(
            title="Application Approved ✅",
            description=f"You have been ranked in the Roblox group to **Rank {RANK_ID}**.",
            color=discord.Color.green()
        )
        embed.set_footer(text="Welcome to Turf.")
        await ctx.respond(embed=embed, ephemeral=False)
    else:
        embed = discord.Embed(
            title="Error",
            description="Something went wrong while trying to rank you. Please try again later.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, ephemeral=True)

# Role removal = auto demotion
@bot.event
async def on_member_update(before, after):
    lost_role = ALLOWED_ROLE_ID in [r.id for r in before.roles] and ALLOWED_ROLE_ID not in [r.id for r in after.roles]
    if lost_role:
        discord_id = after.id
        if discord_id in user_links:
            roblox_id = user_links[discord_id]
            if rank_down(roblox_id):
                print(f"[INFO] {after} was auto-demoted in Roblox due to lost role.")

# Bot ready event
@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")

# Run the bot
bot.run(DISCORD_TOKEN)
