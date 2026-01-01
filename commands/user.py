import logging
import asyncio
import discord
from discord import ApplicationContext, Embed

from scripts.nations import City, Tile, Link, nation_list, upgrade_types, units, new_nation, new_city, new_army, new_fleet
from scripts.response import response, error
from scripts.errors import NationsException, CancelledException, InvalidLocation
from scripts.ui import DirectionView

logger = logging.getLogger(__name__)

# TODO: Implement database saves here

def move_in_direction(current_tile: Tile, direction: str):
        last_tile = current_tile
        new_tile = getattr(current_tile, direction)()
        if new_tile.terrain in ["ocean", "lake", "high_mountains"]:
            raise InvalidLocation("Movement", f"in {new_tile.terrain}")
        for unit in units:
            if unit.location == current_tile.location:
                # do battle stuff?
                pass

        return new_tile, last_tile

class UserCog(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.slash_command(description="A simple latency test")
    async def ping(self, ctx: ApplicationContext):
        latency_ms = round(self.bot.latency * 1000)
        await ctx.interaction.response.send_message(f"Pong! Latency: {latency_ms}ms")
        logger.info(f"{ctx.interaction.user.name} sent a ping.")

    @discord.slash_command(description="Make a new nation.")
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
                raise
            
        except Exception as e:
            logger.error(f"Failed to create new nation for {ctx.interaction.user.name}: {e}")
            await error(ctx.interaction)
            raise
        
        await response(ctx.interaction, "Welcome!", "Welcome to Nations: New World! You can now get started whenever you want!")
        logger.info(f"{ctx.interaction.user.name} started a new nation, {name}")

    # ----- MILITARY COMMANDS ----- #

    military = discord.SlashCommandGroup("military", description="Manage your military")

    @military.command(description="Trains a new army")
    @discord.option("name", input_type=str, description="The name of the new army.")
    @discord.option("city", input_type=str, description="The city to train in.")
    async def newarmy(self, ctx: ApplicationContext, name: str, city: str):
        try:
            new_army(name, ctx.interaction.user.id, city)
        except NationsException as e:
            await error(ctx.interaction, e.user_message)
            raise
        except Exception as e:
            logger.error(f"Failed to create new army for {ctx.interaction.user.name}: {e}")
            await error(ctx.interaction)
            raise
        
        await response(ctx.interaction, "Created!", f"New army {name} started training in {city}")

    @military.command(description="Builds a new fleet")
    @discord.option("name", input_type=str, description="The name of the new fleet.")
    @discord.option("city", input_type=str, description="The city to train in.")
    async def fleet(self, ctx: ApplicationContext, name: str, city: str):
        try:
            new_fleet(name, ctx.interaction.user.id, city)
        except NationsException as e:
            await error(ctx.interaction, e.user_message)
            raise
        except Exception as e:
            logger.error(f"Failed to create new fleet for {ctx.interaction.user.name}: {e}")
            await error(ctx.interaction)
            raise
        
        await response(ctx.interaction, "Created!", f"New fleet {name} started training in {city}")

    # ----- BUILD COMMANDS ----- #

    build = discord.SlashCommandGroup("build", description="Build structures")

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
            raise
        except Exception as e:
            logger.error(f"Failed to build {upgrade}: {e}")
            await error(ctx.interaction)
            raise
        
        await response(ctx.interaction, "Built!", f"Your {upgrade} has been built in {cityname}!")
        logger.info(f"Someone built a {upgrade.lower()}!")

    @build.command(description="Builds a new railroad")
    @discord.option("origin", input_type=str, description="The city the railroad starts in.")
    @discord.option("level", input_type=str, description="The level of railroad to build", choices=["simple", "quality"])
    async def rail(self, ctx: ApplicationContext, origin: str, level: str):
        ctx.interaction.response.defer()
        ctx.interaction.followup.send("")
        finished = False
        current_tile = nation_list[ctx.interaction.user.id].cities[origin]
        last_tile = None
        try:
            while not finished:
                # TODO: Add a map image showing current railroad progress
                direction_future = asyncio.Future()
                ctx.interaction.followup.edit_message(embed=Embed(
                    title="Choose a direction",
                    description="Select a direction for your railway to head next."
                ), view=DirectionView(direction_future, timeout=60))
                while not direction_future.done():
                    await asyncio.sleep(1)
                
                direction = direction_future.result()
                match direction:
                    case direction if direction in ("n", "nw", "sw", "s", "se", "ne"):
                        current_tile, last_tile = move_in_direction(current_tile, direction)
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
            raise

        #TODO: Add confirmation
        new_link = Link(origin=origin, destination=current_tile.name, owner=ctx.interaction.user.id, 
                        linktype=("simple railroad" if level=="simple" else "quality railroad"))
        new_link.build()
        await response(ctx.interaction, "Built!", f"Your railroad has been built to {current_tile.name}!")

    # ----- MILITARY COMMANDS ----- #

    nation = discord.SlashCommandGroup("nation", description="Manage your nation")

    @nation.command(description="Changes the summary of your nation that appears on your profile.")
    @discord.option("text", input_type=str, description="The text you want to appear on your profile.")
    async def dossier(self, ctx: ApplicationContext, text: str):
            try:
                nation_list[ctx.interaction.user.id].dossier = text
                logger.info(f"{ctx.interaction.user.name} changed their nation dossier to {text}")
                response(ctx.interaction, "Dossier changed!", f"Your dossier has been successfully changed to: \n'{text}'")
            except NationsException as e:
                error(ctx.interaction, e.user_message)
                raise
            except Exception as e:
                logger.error(f"Failed to change dossier for {ctx.interaction.user.name}: {e}")
                raise

def setup(bot: discord.Bot):
    try:
        logger.debug("Registering user cog")
        bot.add_cog(UserCog(bot))
        logger.debug("Registered user cog")
    except Exception as e:
        logger.critical(f"Failed to load user cog: {e}")
        bot.close()
        raise