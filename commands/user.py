import logging
import discord
from discord import ApplicationContext, Object
from discord.ext import commands

from scripts.bot import NationsBot, OPGUILD_ID
from scripts.nations import nation_list, new_nation, tiles, new_city, new_army, new_fleet, upgrade_types
from scripts.response import response, error
from scripts.errors import NationsException

logger = logging.getLogger(__name__)

class UserCog(commands.Cog):
    def __init__(self, bot: NationsBot):
        self.bot = bot

    @discord.slash_command(description="A simple latency test", guild_ids=[OPGUILD_ID])
    async def ping(self, ctx: ApplicationContext):
        latency_ms = round(self.bot.latency * 1000)
        await ctx.interaction.response.send_message(f"Pong! Latency: {latency_ms}ms")
        logger.info(f"{ctx.interaction.user.name} sent a ping.")

    @discord.slash_command(description="Make a new nation.", guild_ids=[OPGUILD_ID])
    @discord.option("name", input_type=str, description="The name of your new nation.")
    @discord.option("system_1", input_type=str, description="A system your government uses to gain power.", options=[
        "Authoritarian", "Democratic", "Militaristic", "Pacifist", "Federalist", "Centralist",
        "Isolationist", "Mercantilist", "Expansionist", "Territorialist", "Urbanist"
    ])
    @discord.option("system_2", input_type=str, description="A system your government uses to gain power.", options=[
        "Authoritarian", "Democratic", "Militaristic", "Pacifist", "Federalist", "Centralist",
        "Isolationist", "Mercantilist", "Expansionist", "Territorialist", "Urbanist"
    ])
    @discord.option("capital_name", input_type=str, description="The name of your new capital city.")
    @discord.option("capital_x", input_type=int, description="The x-coordinate (1st on the map) of your capital tile.")
    @discord.option("capital_y", input_type=int, description="The y-coordinate (2nd on the map) of your capital tile.")
    async def start(self, ctx: ApplicationContext, name: str, system_1: str, system_2: str, capital_name: str, capital_x: int, capital_y: int):
        try:
            try:
                new_nation(name, ctx.interaction.user.id, [system_1, system_2])
                new_city(capital_name, (capital_x, capital_y), ctx.interaction.user.id)
            except NationsException as e:
                await error(ctx.interaction, e.user_message)
            
        except Exception as e:
            logger.error(f"Failed to create new nation for {ctx.interaction.user.name}: {e}")
            await error(ctx.interaction)
            return 0
        
        await response(ctx.interaction, "Welcome!", "Welcome to Nations: New World! You can now get started whenever you want!")
        logger.info(f"{ctx.interaction.user.name} started a new nation, {name}")

    military = discord.SlashCommandGroup("military", description="Manage your military", guild_ids=[OPGUILD_ID])

    #TODO: Port these commands to using city names instead of coords
    @military.command(description="Trains a new army")
    @discord.option("name", input_type=str, description="The name of the new army.")
    @discord.option("location_x", input_type=str, description="The x-coordinate (1st on the map) of the city to train in.")
    @discord.option("location_y", input_type=str, description="The y-coordinate (2nd on the map) of the city to train in.")
    async def newarmy(self, ctx: ApplicationContext, name: str, location_x: int, location_y: int):
        location = (location_x, location_y)

        try:
            new_army(name, ctx.interaction.user.id, location)
        except NationsException as e:
            await error(ctx.interaction, e.user_message)
            return 0
        except Exception as e:
            logger.error(f"Failed to create new army for {ctx.interaction.user.name}: {e}")
            await error(ctx.interaction)
        
        await response(ctx.interaction, "Created!", f"New army {name} successfully started training in {tiles[location].name}")
        logger.info("Someone successfully made a new army!", )

    @military.command(description="Builds a new fleet")
    @discord.option("name", input_type=str, description="The name of the new fleet.")
    @discord.option("location_x", input_type=str, description="The x-coordinate (1st on the map) of the city to build in.")
    @discord.option("location_y", input_type=str, description="The y-coordinate (2nd on the map) of the city to build in.")
    async def fleet(self, ctx: ApplicationContext, name: str, location_x: int, location_y: int):
        location = (location_x, location_y)

        try:
            new_fleet(name, ctx.interaction.user.id, location)
        except NationsException as e:
            await error(ctx.interaction, e.user_message)
            return 0
        except Exception as e:
            logger.error(f"Failed to create new fleet for {ctx.interaction.user.name}: {e}")
            await error(ctx.interaction)
            return 0
        
        await response(ctx.interaction, "Created!", f"New fleet {name} successfully started training in {tiles[location].name}")
        logger.info("Someone successfully made a new fleet!")

    build = discord.SlashCommandGroup("build", description="Build structures", guild_ids=[OPGUILD_ID])

    @build.command(description="Builds a new upgrade in a city")
    @discord.option("cityname", input_type=str, description="The name of the city to build the upgrade in")
    @discord.option("upgrade", input_type=str, description="The upgrade you want to build", choices=[
        "Temple", "Grand Temple", "Station", "Central Station", "Workshop",
        "Charcoal pit", "Smeltery", "Port", "Foundry"
    ])
    async def upgrade(self, ctx: ApplicationContext, cityname: str, upgrade: str):
        try:
            nation = nation_list[ctx.interaction.user.id]
            city = nation.cities[cityname]

            upgrade_types[upgrade].build(city.location, city, nation.econ)
        except NationsException as e:
            await error(ctx.interaction, e.user_message)
            return 0
        except Exception as e:
            logger.error(f"Failed to build {upgrade}: {e}")
            await error(ctx.interaction)
            return 0
        
        await response(ctx.interaction, "Built!", f"Your {upgrade} has been built in {cityname}!")
        logger.info(f"Someone built a {upgrade.lower()}!")

    nation = discord.SlashCommandGroup("nation", description="Manage your nation", guild_ids=[OPGUILD_ID])

    @nation.command(description="Changes the summary of your nation that appears on your profile.")
    @discord.option("text", input_type=str, description="The text you want to appear on your profile.")
    async def dossier(self, ctx: ApplicationContext, text: str):
            try:
                nation_list[ctx.interaction.user.id].dossier = text
                logger.info(f"{ctx.interaction.user.name} changed their nation dossier to {text}")
                response(ctx.interaction, "Dossier changed!", f"Your dossier has been successfully changed to: \n'{text}'")
            except NationsException as e:
                error(ctx.interaction, e.user_message)
            except Exception as e:
                logger.error(f"Failed to change dossier for {ctx.interaction.user.name}: {e}")

async def setup(bot: commands.Bot):
    try:
        cog = UserCog(bot)
        await bot.add_cog(cog)
    except Exception as e:
        logger.critical(f"Failed to load user cog: {e}")
        await bot.close()
        return