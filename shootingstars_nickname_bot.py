"""
슈팅스타즈 닉네임 관리 봇
"""

import logging
import sys
from datetime import datetime

import discord
from discord.ext import commands
from discord import app_commands

# =========================
# 설정
# =========================

BOT_TOKEN = "토큰 입력"

ROLE_NAME = "슈팅 스타즈 클랜 특전 : 닉네임 Ss 적용"
TAG_TEXTS = ["Ss_", "SS_"]

LOG_CHANNEL_ID = 1511415970210648266

ADMIN_ROLE_NAMES = [
    "🥺집에 가고싶은 공무원🥺",
    "😭노예나 다름없는 장관😭",
    "😕일 하기 싫어하는 총리😕",
    "👑데친 숙주나물 국왕👑",
    "💁무엇을  도와드릴까요?💁"
]

LOG_TITLE = "[🩷먹가 작고 귀여운 슈팅 스타즈🩷] 닉네임 로그"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
)
log = logging.getLogger("nickname_bot")

intents = discord.Intents.default()
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


def has_tag(member: discord.Member) -> bool:
    return member.nick is not None and any(tag in member.nick for tag in TAG_TEXTS)


def is_admin(member: discord.Member) -> bool:
    return any(role.name in ADMIN_ROLE_NAMES for role in member.roles)


async def send_log(guild: discord.Guild, embed: discord.Embed):
    channel = guild.get_channel(int(LOG_CHANNEL_ID))
    if channel:
        await channel.send(embed=embed)


def make_log_embed(member: discord.Member, result: str) -> discord.Embed:
    role = discord.utils.get(member.guild.roles, name=ROLE_NAME)
    role_mention = role.mention if role else f"@{ROLE_NAME}"
    current_tag = member.nick if member.nick else "없음"

    if result == "added":
        color = discord.Color.green()
        action_line = (
            f"**[역할 부여됨]** {member.mention}({member.name})님이 "
            f"닉네임 일치로 인해 {role_mention} 역할을 받았습니다."
        )
    else:
        color = discord.Color.red()
        action_line = (
            f"**[역할 제거됨]** {member.mention}({member.name})님이 "
            f"닉네임 불일치로 인해 {role_mention} 역할이 제거되었습니다. "
        )

    embed = discord.Embed(
        title=LOG_TITLE,
        description=action_line,
        color=color
    )
    embed.set_footer(text=f"Tag Manager 로그 • {datetime.now().strftime('%Y. %m. %d. %p %I:%M').replace('AM', '오전').replace('PM', '오후')}")
    return embed


async def sync_member(member: discord.Member):
    role = discord.utils.get(member.guild.roles, name=ROLE_NAME)

    if role is None:
        return "none"

    has_role = role in member.roles
    matched = has_tag(member)

    if matched and not has_role:
        await member.add_roles(role, reason="Ss_/SS_ 닉네임 감지")
        return "added"

    if not matched and has_role:
        await member.remove_roles(role, reason="Ss_/SS_ 닉네임 제거")
        return "removed"

    return "skip"


@bot.event
async def on_ready():
    await bot.tree.sync()
    log.info(f"로그인 완료: {bot.user}")

    for guild in bot.guilds:
        for member in guild.members:
            if not member.bot:
                try:
                    await sync_member(member)
                except Exception as e:
                    log.error(f"{member}: {e}")


@bot.event
async def on_member_update(before, after):
    if before.nick == after.nick:
        return

    result = await sync_member(after)

    if result in ("added", "removed"):
        embed = make_log_embed(after, result)
        await send_log(after.guild, embed)


@bot.event
async def on_member_join(member):
    if member.bot:
        return

    result = await sync_member(member)

    if result in ("added", "removed"):
        embed = make_log_embed(member, result)
        await send_log(member.guild, embed)


@bot.tree.command(name="전체검사", description="서버 전체 멤버를 재검사합니다.")
async def full_scan(interaction: discord.Interaction):

    if not is_admin(interaction.user):
        await interaction.response.send_message(
            "이 명령어를 사용할 권한이 없습니다.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    added = 0
    removed = 0
    checked = 0

    for member in interaction.guild.members:
        if member.bot:
            continue

        result = await sync_member(member)
        checked += 1

        if result in ("added", "removed"):
            embed = make_log_embed(member, result)
            await send_log(interaction.guild, embed)

        if result == "added":
            added += 1
        elif result == "removed":
            removed += 1

    await interaction.followup.send(
        f"전체 검사 완료\n\n"
        f"총 검사 인원 : {checked}명\n"
        f"역할 지급 : {added}명\n"
        f"역할 제거 : {removed}명",
        ephemeral=True
    )


if __name__ == "__main__":
    if BOT_TOKEN == "여기에_봇_토큰_입력":
        print("BOT_TOKEN을 입력하세요.")
        sys.exit(1)

    bot.run(BOT_TOKEN)
