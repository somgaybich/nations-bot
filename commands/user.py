import logging
import asyncio
import discord
from discord import ApplicationContext, Embed
from discord.ext import commands

from scripts.bot import NationsBot, OPGUILD_ID
from scripts.nations import City, Link, nation_list, new_nation, tiles, new_city, new_army, new_fleet, upgrade_types
from scripts.response import response, error
from scripts.errors import NationsException, CancelledException, InvalidLocation
from scripts.ui import DirectionView

logger = logging.getLogger(__name__)

def move_in_direction(current_tile, direction):
        last_tile = current_tile
        new_tile = getattr(current_tile, direction)()
        if new_tile.terrain in ["ocean", "lake", "high_mountain"]:
            raise InvalidLocation("Railroad building", new_tile.terrain)

        return new_tile, last_tile

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

    @build.command(description="Builds a new railroad")
    @discord.option("origin", input_type=str, description="The city the railroad starts in.")
    @discord.option("level", input_type=str, description="The level of railroad to build", choices=["simple", "quality"])
    async def rail(self, ctx: ApplicationContext, origin: str, level: str):
        ctx.defer()
        ctx.followup.send("")
        finished = False
        current_tile = nation_list[ctx.interaction.user.id].cities[origin]
        last_tile = None
        try:
            while not finished:
                # TODO: Add a map image showing current railroad progress
                direction_future = asyncio.Future()
                ctx.followup.edit_message(embed=Embed(
                    title="Choose a direction",
                    description="Select a direction for your railway to head next."
                ), view=DirectionView(direction_future, timeout=60))
                while not direction_future.done():
                    await asyncio.sleep(1)
                
                direction = direction_future.result()
                match direction:
                    case d if d in ("n", "nw", "sw", "s", "se", "ne"):
                        current_tile, last_tile = move_in_direction(current_tile, d)
                    case "Back":
                        if last_tile is not None:
                            current_tile, last_tile = last_tile, None
                        else:
                            await error(ctx.interaction, "You can't go back any further!")
                    case "Cancel":
                        raise CancelledException("Railroad building")
                
                if isinstance(current_tile, City):
                    finished = True

        except Exception as e:
            logger.error(f"Failed to build railroad for {ctx.interaction.user.name}: {e}")
            await error(ctx.interaction, e.user_message if isinstance(e, NationsException) else None)
            return 0

        #TODO: Add confirmation
        new_link = Link(origin=origin, destination=current_tile.name, owner=ctx.interaction.user.id, 
                        linktype=("simple railroad" if level=="simple" else "quality railroad"))
        new_link.build()
        await response(ctx.interaction, "Built!", f"Your railroad has been built to {current_tile.name}!")

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