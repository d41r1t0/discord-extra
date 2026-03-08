import discord
from discord.ext import commands
from discord import app_commands

import os
TOKEN = os.getenv("TOKEN")

PUBLIC_CHANNEL_ID = 1478764708830908590
TEST_GUILD_ID = 1244340511276400791
ROLE_ID = 1478149219947778250
NOTIFY_ROLE_ID = 1478149219947778250
COLLECTOR_ROLE_ID = 1479441246018736239
ADMIN_ROLE_ID = 1273664375865085974

# АЙДИ ДАЛБАЕБАВ
BARVAN_ID = 1145099819359154187
SAKAL_ID = 465874338638200843
NIKITA_ID = 645094081219002399
SASHA_ID = 1299736588871270482
SVINKA_ID = 914673555898265651

# Кастомные эмодзи
EMOJI_ATT = "<:att:1479275978596417789>"
EMOJI_DEF = "<:def:1479276966640353360>"

intents = discord.Intents.default()
intents.messages = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

role_tiers = {
    1479268082194317364: "<@&1479268082194317364>",  # t1
    1479268207196901501: "<@&1479268207196901501>",  # t2
    1479268212620267573: "<@&1479268212620267573>",  # t3
}

# приоритет сортировки
tier_priority = {
    1479268082194317364: 1,
    1479268207196901501: 2,
    1479268212620267573: 3,
}


class CollectView(discord.ui.View):

    def __init__(self, limit, war_time, war_type):
        super().__init__(timeout=None)
        self.limit = limit
        self.war_time = war_time
        self.war_type = war_type
        self.users = {}

    def build_user_list(self):

        users_data = []

        for user_id, mention in self.users.items():

            member = None

            for g in bot.guilds:
                member = g.get_member(user_id)
                if member:
                    break

            tier = "ɴᴏ ᴛɪᴇʀ"
            priority = 999

            if member:
                for role_id, role_mention in role_tiers.items():
                    if discord.utils.get(member.roles, id=role_id):
                        tier = role_mention
                        priority = tier_priority.get(role_id, 999)
                        break

            users_data.append((priority, mention, tier))

        users_data.sort(key=lambda x: x[0])

        lines = [f"{i+1}. {mention}" for i, (_, mention, tier) in enumerate(users_data)]

        return "\n".join(lines)


    def build_embed(self):

        emoji = EMOJI_ATT if self.war_type == "ᴀᴛᴛ" else EMOJI_DEF
        color = discord.Color.from_str("#db58a4")

        embed = discord.Embed(
            title=f"{emoji} {self.war_type} {emoji}\n",
            color=color
        )

        embed.add_field(name="Формат", value=f"{self.limit}x{self.limit}", inline=True)
        embed.add_field(name="⏰ Время", value=self.war_time, inline=True)
        embed.add_field(name="\n━━━━━━━━━━━━━━━━\n", value="", inline=False)
        user_list = self.build_user_list() if self.users else ""
        embed.add_field(name="👥 Участники", value=user_list, inline=False)
        embed.set_footer(text=f"Записалось: {len(self.users)}/{self.limit}")
        return embed


    @discord.ui.button(label="Записаться", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not interaction.guild:
            await interaction.response.send_message("Команда только для сервера", ephemeral=True)
            return

        user = interaction.user

        if user.id in self.users:
            await interaction.response.send_message("Ты уже записан", ephemeral=True)
            return

        if len(self.users) >= self.limit:
            await interaction.response.send_message("Лимит уже достигнут", ephemeral=True)
            return

        self.users[user.id] = user.mention

        await interaction.response.edit_message(embed=self.build_embed(), view=self)


    @discord.ui.button(label="Выписаться", style=discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not interaction.guild:
            await interaction.response.send_message("Команда только для сервера", ephemeral=True)
            return

        user = interaction.user

        if user.id not in self.users:
            await interaction.response.send_message("Ты не записан", ephemeral=True)
            return

        del self.users[user.id]

        await interaction.response.edit_message(embed=self.build_embed(), view=self)


@bot.event
async def on_ready():

    await bot.tree.sync(guild=discord.Object(id=TEST_GUILD_ID))

    print("\nBot has been initialized!")

def build_dm_embed(limit, time, war_type):

    emoji = EMOJI_ATT if war_type == "ᴀᴛᴛ" else EMOJI_DEF
    color = discord.Color.from_str("#db58a4")
    embed = discord.Embed(
        title=f"{emoji} Сбор на {war_type}",
        color=color
    )

    embed.add_field(name="Формат", value=f"{limit}x{limit}", inline=True) 
    embed.add_field(name="⏰ Время", value=time, inline=True)

    embed.add_field(
        name="",
        value="Нажми кнопку **Записаться** --> <#1478764708830908590>",
        inline=False
    )

    return embed

async def send_collect(interaction, limit: int, time: str, war_type: str):

    if not interaction.guild:
        await interaction.response.send_message("Команда работает только на сервере", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    channel = bot.get_channel(PUBLIC_CHANNEL_ID)

    if not channel:
        await interaction.response.send_message("Канал не найден", ephemeral=True)
        return

    view = CollectView(limit, time, war_type)
    role_mention = f"<@&{ROLE_ID}>"

    await channel.send(
        content=role_mention,
        embed=view.build_embed(),
        view=view
    )

    role_members = [
        member for member in interaction.guild.members
        if any(role.id == NOTIFY_ROLE_ID for role in member.roles)
    ]

    notify_role = interaction.guild.get_role(ROLE_ID)

    # if notify_role:
    #     dm_embed = build_dm_embed(limit, time, war_type)
    #     for member in notify_role.members:
    #         try:
    #             await member.send(embed=dm_embed)
    #         except discord.Forbidden:
    #             pass

    try:
        user1 = await bot.fetch_user(BARVAN_ID)
        user2 = await bot.fetch_user(SAKAL_ID)
        user3 = await bot.fetch_user(NIKITA_ID)
        user4 = await bot.fetch_user(SASHA_ID)
        user5 = await bot.fetch_user(SVINKA_ID)
        await user1.send(f"https://media.discordapp.net/attachments/1026907701114052749/1244745339685175418/IMG_20240527_081413.gif?ex=69abde2f&is=69aa8caf&hm=b9ed697ae841dbaad4314f1312afa1093fecedc5c191f6664d469336bd897d55&=&width=739&height=986")
        await user2.send(f"https://media.discordapp.net/attachments/1026907701114052749/1244745339685175418/IMG_20240527_081413.gif?ex=69abde2f&is=69aa8caf&hm=b9ed697ae841dbaad4314f1312afa1093fecedc5c191f6664d469336bd897d55&=&width=739&height=986")
        await user3.send(f"https://media.discordapp.net/attachments/1026907701114052749/1244745339685175418/IMG_20240527_081413.gif?ex=69abde2f&is=69aa8caf&hm=b9ed697ae841dbaad4314f1312afa1093fecedc5c191f6664d469336bd897d55&=&width=739&height=986")
        await user4.send(f"https://media.discordapp.net/attachments/1026907701114052749/1244745339685175418/IMG_20240527_081413.gif?ex=69abde2f&is=6969aa8caf&hm=b9ed697ae841dbaad4314f1312afa1093fecedc5c191f6664d469336bd897d55&=&width=739&height=986")
        await user5.send(f"https://media.discordapp.net/attachments/1026907701114052749/1244745339685175418/IMG_20240527_081413.gif?ex=69abde2f&is=6969aa8caf&hm=b9ed697ae841dbaad4314f1312afa1093fecedc5c191f6664d469336bd897d55&=&width=739&height=986")
    except discord.Forbidden:
        pass

    await interaction.followup.send("Сбор опубликован", ephemeral=True)


@bot.tree.command(
    name="def",
    description="Сбор на защиту",
    guild=discord.Object(id=TEST_GUILD_ID)
)
async def defend(interaction: discord.Interaction, limit: int, time: str):

    if not any(role.id == COLLECTOR_ROLE_ID or role.id == ADMIN_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message(
            "Недостаточно прав!", ephemeral=True
        )
        return

    await send_collect(interaction, limit, time, "ᴅᴇꜰ")


@bot.tree.command(
    name="att",
    description="Сбор на атаку",
    guild=discord.Object(id=TEST_GUILD_ID)
)
async def attack(interaction: discord.Interaction, limit: int, time: str):

    if not any(role.id == COLLECTOR_ROLE_ID or role.id == ADMIN_ROLE_ID for role in interaction.user.roles):
        await interaction.response.send_message(
            "Недостаточно прав!", ephemeral=True
        )
        return

    await send_collect(interaction, limit, time, "ᴀᴛᴛ")


@bot.tree.command(
    name="clear",
    description="Очистить сообщения",
    guild=discord.Object(id=TEST_GUILD_ID)
)
async def clear(interaction: discord.Interaction, amount: int):

    if not interaction.guild:
        await interaction.response.send_message("Команда только для сервера", ephemeral=True)
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Недостаточно прав", ephemeral=True)
        return

    await interaction.response.send_message(f"Удаляю {amount} сообщений...", ephemeral=True)

    deleted = await interaction.channel.purge(limit=amount)

    await interaction.followup.send(f"Удалено {len(deleted)} сообщений", ephemeral=True)


bot.run(TOKEN)