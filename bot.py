import discord
from discord.ext import commands
from discord import app_commands

import os
TOKEN = os.environ.get("TOKEN")

PUBLIC_CHANNEL_ID = 1478764708830908590
TEST_GUILD_ID = 1244340511276400791
ROLE_ID = 1478149219947778250
NOTIFY_ROLE_ID = 1478149219947778250 # пока не используем (для авторассылки)
COLLECTOR_ROLE_ID = 1479441246018736239
ADMIN_ROLE_ID = 1273664375865085974

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
        self.players = {}
        self.substitutes = {}
        self._pending_remove = None

    def build_user_list(self, users_dict):

        users_data = []

        for user_id, mention in users_dict.items():

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

        return "\n".join(lines) if lines else ""


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

        players_list = self.build_user_list(self.players)
        subs_list = self.build_user_list(self.substitutes)

        embed.add_field(
            name=f"👥 Участники ({len(self.players)}/{self.limit})",
            value=f"{players_list}\n\u200b",
            inline=True
        )

        embed.add_field(
            name=f"🔁 Замена ({len(self.substitutes)})",
            value=subs_list,
            inline=False
        )

        embed.set_footer(text=f"Всего записано: {len(self.players)+len(self.substitutes)}")

        return embed


    @discord.ui.button(label="Записаться", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not interaction.guild:
            await interaction.response.send_message("Команда только для сервера", ephemeral=True)
            return

        user = interaction.user

        if user.id in self.players or user.id in self.substitutes:
            await interaction.response.send_message("Ты уже записан", ephemeral=True)
            return

        if len(self.players) < self.limit:
            self.players[user.id] = user.mention
        else:
            self.substitutes[user.id] = user.mention

        await interaction.response.edit_message(embed=self.build_embed(), view=self)


    @discord.ui.button(label="Выписаться", style=discord.ButtonStyle.red)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        promoted_user = None

        if not interaction.guild:
            await interaction.response.send_message("Команда только для сервера", ephemeral=True)
            return

        user = interaction.user

        if user.id not in self.players and user.id not in self.substitutes:
            await interaction.response.send_message("Ты не записан", ephemeral=True)
            return

        # если был в основном составе
        if user.id in self.players:

            del self.players[user.id]

            if self.substitutes:
                first_sub_id = next(iter(self.substitutes))
                first_sub_mention = self.substitutes[first_sub_id]

                self.players[first_sub_id] = first_sub_mention
                del self.substitutes[first_sub_id]

                promoted_user = first_sub_mention

        # если был в замене
        elif user.id in self.substitutes:
            del self.substitutes[user.id]

        await interaction.response.edit_message(embed=self.build_embed(), view=self)

        if promoted_user:
            await interaction.followup.send(
                f"[✈] {promoted_user} перешёл из замены в основной список!"
            )

    @discord.ui.button(label="Управление участниками", style=discord.ButtonStyle.blurple)
    async def manage_members(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Проверка прав
        if not any(role.id in [ADMIN_ROLE_ID, COLLECTOR_ROLE_ID] for role in interaction.user.roles):
            await interaction.response.send_message("❌ У тебя нет прав для управления участниками.", ephemeral=True)
            return

        if not self.players:
            await interaction.response.send_message("❌ В основном составе нет игроков для выписки.", ephemeral=True)
            return
        if not self.substitutes:
            await interaction.response.send_message("❌ В замене нет игроков для добавления.", ephemeral=True)
            return

        self._pending_remove = None

        view = discord.ui.View(timeout=None)

        # Цветные эмодзи для тир
        role_emojis = {
            1480010341843730698: "🔴 [T1]",  # T1
            1480010348756074537: "🔵 [T2]",  # T2
            1480010349141819492: "⚪ [T3]",  # T3
        }

        # --- Меню для удаления из основного состава ---
        remove_options = [
            discord.SelectOption(
                label=f"{interaction.guild.get_member(uid).name} - {role_emojis.get(next((r.id for r in interaction.guild.get_member(uid).roles if r.id in role_tiers), None), 'ɴᴏ ᴛɪᴇʀ')}",
                value=str(uid)
            )
            for uid in self.players
        ]
        remove_select = discord.ui.Select(
            placeholder="Выбери участника для выписки",
            options=remove_options,
            min_values=1,
            max_values=1
        )
        view.add_item(remove_select)

        # --- Меню для добавления из замены ---
        add_options = [
            discord.SelectOption(
                label=f"{interaction.guild.get_member(uid).name} - {role_emojis.get(next((r.id for r in interaction.guild.get_member(uid).roles if r.id in role_tiers), None), 'ɴᴏ ᴛɪᴇʀ')}",
                value=str(uid)
            )
            for uid in self.substitutes
        ]
        add_select = discord.ui.Select(
            placeholder="Выбери участника для добавления",
            options=add_options,
            min_values=1,
            max_values=1
        )
        view.add_item(add_select)

        # --- Коллбек для удаления ---
        async def remove_callback(interact: discord.Interaction):
            self._pending_remove = int(remove_select.values[0])
            await interact.response.send_message(
                f"✅ Выбран для выписки: {interaction.guild.get_member(self._pending_remove).mention}",
                ephemeral=True
            )

        # --- Коллбек для добавления ---
        async def add_callback(interact: discord.Interaction):
            if self._pending_remove is None:
                await interact.response.send_message("❌ Сначала выбери кого выписать.", ephemeral=True)
                return

            add_id = int(add_select.values[0])
            remove_id = self._pending_remove

            removed_member = interact.guild.get_member(remove_id)
            added_member = interact.guild.get_member(add_id)

            # Обмен участников
            self.players[add_id] = self.substitutes.pop(add_id)
            self.substitutes[remove_id] = self.players.pop(remove_id)

            self._pending_remove = None  # сброс

            # Обновляем embed (цвет роли останется в embed)
            await interaction.message.edit(embed=self.build_embed(), view=self)
            await interaction.followup.send(
                f"[❗] {added_member.mention} заменил {removed_member.mention}!",
            )

        remove_select.callback = remove_callback
        add_select.callback = add_callback

        await interaction.response.send_message(
            "Выбери участника для выписки и добавления (тир показан через эмодзи):",
            view=view,
            ephemeral=True
        )


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