# Get Roblox user profile (to check display name)
def get_user_profile(user_id):
    response = requests.get(f"https://users.roblox.com/v1/users/{user_id}")
    if response.status_code == 200:
        return response.json()
    return None

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

    # Get user profile to check display name
    profile = get_user_profile(user_id)
    if not profile:
        embed = discord.Embed(
            title="Error",
            description="Could not fetch Roblox user profile. Please try again later.",
            color=discord.Color.red()
        )
        await ctx.respond(embed=embed, ephemeral=True)
        return

    display_name = profile.get("displayName", "").lower()
    if "fl13" not in display_name:
        embed = discord.Embed(
            title="Invalid Display Name",
            description="Your Roblox **display name** must contain **'fl13'** to apply.",
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
