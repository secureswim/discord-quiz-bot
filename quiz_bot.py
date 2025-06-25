import discord
from discord.ext import commands, tasks
import pandas as pd
import os
import asyncio
import random
from dotenv import load_dotenv

# Load bot token
load_dotenv(dotenv_path=".env")
TOKEN = os.getenv('DISCORD_TOKEN')

# Load and process questions
df = pd.read_csv("quiz_bot_dataset.csv").dropna(subset=["question"])
df = df.sample(frac=1).reset_index(drop=True).head(20)
df["id"] = df.index + 1
questions = df.to_dict(orient="records")

# Log file setup
LOG_FILE = "quiz_log.txt"
def log_event(message):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# State
state = {
    "teams": {},
    "score": {},
    "current_index": -1,
    "current_question": None,
    "buzzed_team": None,
    "buzz_order": [],
    "question_active": False,
    "question_count": 0,
    "answer_timer": None,
    "no_buzz_timer": None
}

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user.name}")

@bot.command()
async def join(ctx, team_name):
    user = ctx.author.name
    # Remove from previous team if present
    for team in state["teams"]:
        if user in state["teams"][team]:
            state["teams"][team].remove(user)
    if team_name not in state["teams"]:
        existing = ', '.join(state["teams"].keys()) or "None yet"
        await ctx.send(
            f"🚨 Team **{team_name}** doesn't exist.\n"
            f"Existing teams: {existing}\n"
            f"Type `!confirm_create {team_name}` to create it, or join an existing one with `!join <team>`."
        )
        return
    if user not in state["teams"][team_name]:
        state["teams"][team_name].append(user)
        await ctx.send(f"✅ {user} joined **{team_name}**!")

@bot.command()
async def confirm_create(ctx, team_name):
    user = ctx.author.name
    if team_name in state["teams"]:
        await ctx.send(f"⚠️ Team **{team_name}** already exists. Use `!join {team_name}`.")
        return
    state["teams"][team_name] = [user]
    state["score"][team_name] = 0
    await ctx.send(f"🆕 Team **{team_name}** created and {user} joined it!")

@bot.command()
@commands.has_permissions(administrator=True)
async def start_quiz(ctx):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("📘 Quiz Log\n")
    state["current_index"] = -1
    state["question_count"] = 0
    await ctx.send("🎮 The quiz is starting! Get ready...")
    await asyncio.sleep(2)
    await ask_next(ctx)

async def ask_next(ctx):
    if state["question_count"] >= len(questions):
        await ctx.send("🏁 Quiz complete! Final scores:")
        await score(ctx)
        return

    state["current_index"] += 1
    if state["current_index"] >= len(questions):
        await ctx.send("🏁 No more questions available.")
        return

    state["current_question"] = questions[state["current_index"]]
    state["buzzed_team"] = None
    state["buzz_order"] = []
    state["question_active"] = True
    state["question_count"] += 1

    q = state["current_question"]
    await ctx.send(f"❓ **Q{state['question_count']}**:\n{q['question']}")
    log_event(f"Q{state['question_count']}: {q['question']}")

    if state.get("no_buzz_timer"):
        state["no_buzz_timer"].cancel()
    state["no_buzz_timer"] = asyncio.create_task(auto_skip_if_no_buzz(ctx))

async def auto_skip_if_no_buzz(ctx):
    await asyncio.sleep(60)
    if not state["buzzed_team"]:
        answer = state["current_question"].get("answer", "Not provided")
        await ctx.send(f"⏰ No one buzzed. Moving on! The correct answer was: **{answer}**")
        log_event(f"Q{state['question_count']}: No buzz | Answer: {answer}")
        state["question_active"] = False
        await asyncio.sleep(5)
        await ask_next(ctx)

@bot.command()
async def buzz(ctx):
    if not state["question_active"]:
        await ctx.send("⚠️ No active question right now.")
        return

    user = ctx.author.name
    for team, members in state["teams"].items():
        if user in members:
            if team in state["buzz_order"] or team == state["buzzed_team"]:
                await ctx.send("⚠️ Your team has already buzzed.")
                return

            if state.get("no_buzz_timer"):
                state["no_buzz_timer"].cancel()
                state["no_buzz_timer"] = None

            state["buzz_order"].append(team)
            if not state["buzzed_team"]:
                state["buzzed_team"] = team
                state["buzz_order"].remove(team)
                await ctx.send(f"🔔 **{team}** buzzed first! You have 30 seconds to answer.")
                state["answer_timer"] = asyncio.create_task(start_answer_timer(ctx, team))
            else:
                await ctx.send(f"🔔 **{team}** added to buzz queue.")
            return

    await ctx.send("⚠️ You're not part of any team.")

async def start_answer_timer(ctx, team):
    try:
        for t in [30, 25, 20, 15, 10, 5]:
            await ctx.send(f"⏳ **{team}** has {t} seconds left...")
            await asyncio.sleep(5)
        await ctx.send(f"⏰ **{team}** ran out of time! -10 points.")
        state["score"][team] -= 10
        log_event(f"{team} ran out of time. -10 points.")
        await pass_to_next_buzzer(ctx)
    except asyncio.CancelledError:
        pass

async def pass_to_next_buzzer(ctx):
    if state.get("answer_timer"):
        state["answer_timer"].cancel()
        state["answer_timer"] = None

    if state.get("no_buzz_timer"):
        state["no_buzz_timer"].cancel()
        state["no_buzz_timer"] = None

    state["buzzed_team"] = None

    while state["buzz_order"]:
        next_team = state["buzz_order"].pop(0)
        state["buzzed_team"] = next_team
        await ctx.send(f"🔔 Now **{next_team}** may answer. You have 30 seconds!")
        state["answer_timer"] = asyncio.create_task(start_answer_timer(ctx, next_team))
        return

    await ctx.send("❌ No more teams buzzed in. Moving to next question...")
    state["question_active"] = False
    await asyncio.sleep(10)
    await ask_next(ctx)

@bot.command()
async def answer(ctx, *, content=None):
    user = ctx.author.name
    for team, members in state["teams"].items():
        if user in members:
            if state["buzzed_team"] == team:
                if state["answer_timer"]:
                    state["answer_timer"].cancel()
                    state["answer_timer"] = None
                await ctx.send(f"🗣️ **{team}**'s answer: {content}")
                log_event(f"{team} answered: {content}")
            else:
                state["score"][team] -= 10
                await ctx.send(f"⛔ {team}, it's not your turn! Wait for the buzzer. -10 points.")
                log_event(f"{team} answered out of turn. -10 points.")
            return

@bot.command()
@commands.has_permissions(administrator=True)
async def correct(ctx):
    team = state["buzzed_team"]
    if team:
        if state.get("answer_timer"):
            state["answer_timer"].cancel()
            state["answer_timer"] = None
        state["score"][team] += 10
        await ctx.send(f"✅ Correct! **{team}** gets +10 points.")
        log_event(f"{team} answered correctly. +10 points.")
        state["question_active"] = False
        if state["question_count"] % 4 == 0:
            await score(ctx)
        await asyncio.sleep(10)
        await ask_next(ctx)
    else:
        await ctx.send("⚠️ No team is currently answering.")

@bot.command()
@commands.has_permissions(administrator=True)
async def wrong(ctx):
    team = state["buzzed_team"]
    if team:
        if state.get("answer_timer"):
            state["answer_timer"].cancel()
            state["answer_timer"] = None
        state["score"][team] -= 10
        await ctx.send(f"❌ Incorrect. **{team}** gets -10 points.")
        log_event(f"{team} answered incorrectly. -10 points.")
        await pass_to_next_buzzer(ctx)
    else:
        await ctx.send("⚠️ No team is currently answering.")

@bot.command()
async def score(ctx):
    msg = "**📊 Scoreboard:**\n"
    for team, pts in state["score"].items():
        msg += f"• {team}: {pts} points\n"
    await ctx.send(msg)

@bot.command()
@commands.has_permissions(administrator=True)
async def end(ctx):
    await ctx.send("🛑 Ending the quiz early.")
    await score(ctx)
    log_event("🔚 Quiz ended early.")
    if state.get("answer_timer"):
        state["answer_timer"].cancel()
        state["answer_timer"] = None
    if state.get("no_buzz_timer"):
        state["no_buzz_timer"].cancel()
        state["no_buzz_timer"] = None
    state["current_index"] = -1
    state["question_count"] = 0
    state["current_question"] = None
    state["buzzed_team"] = None
    state["buzz_order"] = []
    state["question_active"] = False
    state["score"] = {team: 0 for team in state["teams"]}

@bot.command()
async def teams(ctx):
    if not state["teams"]:
        await ctx.send("❌ No teams have been created yet.")
        return

    msg = "**👥 Current Teams:**\n"
    for team, members in state["teams"].items():
        msg += f"• **{team}** ({len(members)} members): {', '.join(members)}\n"
    await ctx.send(msg)

@bot.command()
async def leave(ctx):
    user = ctx.author.name
    for team, members in state["teams"].items():
        if user in members:
            members.remove(user)
            await ctx.send(f"👋 {user} left team **{team}**.")
            return
    await ctx.send("⚠️ You're not part of any team.")



bot.run(TOKEN)