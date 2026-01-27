import os
import logging
import asyncio
import discord
import random
from discord import ApplicationContext, Embed
from PIL import ImageColor

from scripts.response import interaction_response, interacton_error, followup_error
from scripts.errors import NationsException, CancelledException
import scripts.rendering as rendering
from scripts.ui import DirectionView, ConfirmView

from game.constants import brand_color
from game.actions import new_nation, new_city, new_army, new_fleet

from world.map import move_in_direction
from world.cities import City
from world.structures import Link, structure_types
from world.world import nation_list

logger = logging.getLogger(__name__)

class UserCog(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.slash_command(description="A simple latency test.")
    async def ping(self, ctx: ApplicationContext):
        latency_ms = round(self.bot.latency * 1000)

        if random.randint(0, 1000) == 0:
            await ctx.interaction.response.send_message(embed=Embed(
                color=brand_color,
                title="Oops!",
                description="I missed! You win."
            ))
        else:
            await ctx.interaction.response.send_message(embed=Embed(
                color=brand_color,
                title="Pong!",
                description=f"Latency: {latency_ms}ms"
            ))
        
        logger.info(f"{ctx.interaction.user.name} sent a ping.")

    @discord.slash_command(description="Make a new nation.")
    @discord.default_permissions(administrator=True)
    @discord.option("name", input_type=str, description="The name of your new nation.")
    @discord.option("capital_name", input_type=str, description="The name of your new capital city.")
    @discord.option("capital_x", input_type=int, description="The x-coordinate (1st on the map) of your capital tile.")
    @discord.option("capital_y", input_type=int, description="The y-coordinate (2nd on the map) of your capital tile.")
    async def start(self, ctx: ApplicationContext, name: str, capital_name: str, capital_x: int, capital_y: int):
        try:
            await ctx.interaction.response.defer()

            virtual_snapshot = rendering.snapshot_center(capital_x, capital_y, {(capital_x, capital_y): "metropolis"})
            map_filepath = "data/snapshot" + str(ctx.interaction.user.id) + ".png"
            virtual_snapshot.save(map_filepath)
            with open(map_filepath, "rb") as f:
                snapshot_file = discord.File(map_filepath, filename="snapshot.png")
                
                confirm_future = asyncio.Future()
                confirm_view = ConfirmView(confirm_future)
                followup_msg = await ctx.followup.send(
                    embed=Embed(
                        color=brand_color,
                        title="Confirm placement",
                        description="Your capital will go here. Are you sure?"
                    ).set_image(
                        url="attachment://snapshot.png"
                    ),
                    file=snapshot_file,
                    view=confirm_view,
                    wait=True
                )
            await asyncio.wait([confirm_future])
            confirmation = confirm_future.result()
            if confirmation in ["No", None]:
                raise CancelledException("Nation creation")

            logger.debug(f"Making new nation for {ctx.interaction.user.name}...")
            await new_nation(name, ctx.interaction.user.id)
            logger.debug(f"Made new nation, making new city for {ctx.interaction.user.name}...")
            await new_city(capital_name, (capital_x, capital_y), ctx.interaction.user.id, capital=True)
            logger.debug(f"Finished making nation & city for {ctx.interaction.user.name}")
        except NationsException as e:
            await followup_msg.delete()
            await followup_error(ctx.followup, e.user_message)
            raise
        except Exception as e:
            await followup_msg.delete()
            logger.error(f"Failed to create new nation for {ctx.interaction.user.name}: {e}")
            await followup_error(ctx.followup)
            raise
        await followup_msg.delete()
        
        await ctx.interaction.followup.send(
            embed=Embed(
                color=brand_color,
                title="Welcome!",
                description="Welcome to Nations: New World! You now have access to all game commands. Check out the #manual for help!"
            ),
            ephemeral=True
        )
        logger.info(f"{ctx.interaction.user.name} started a new nation, {name}")

    @discord.slash_command(description="Show a user's profile")
    @discord.default_permissions(administrator=True)
    @discord.option("target", input_type=discord.User, description="The user to show the profile of.", default=None)
    async def profile(self, ctx: ApplicationContext, target: discord.User):
        if target is None:
            target = ctx.user()

        try:
            nation = nation_list[target.id]
            await ctx.interaction.response.send_message(embed=nation.profile())
        except NationsException as e:
            await interacton_error(ctx.interaction, e.user_message)
            raise
        except Exception as e:
            logger.error(f"Error getting nation profile for {target.name}: {e}")
            await interacton_error(ctx.interaction)
            raise

    @discord.slash_command(description="Get a map of a location's surroundings!")
    @discord.option("location_x", input_type=int, description="The x-coordinate (1st on the map) of the hex to show.")
    @discord.option("location_y", input_type=int, description="The y-coordinate (2nd on the map) of the hex to show.")
    async def map(self, ctx: ApplicationContext, location_x: int, location_y: int):
        try:
            map_image = rendering.snapshot_center((location_x, location_y))
            map_filepath = "data/snapshot" + str(ctx.interaction.user.id) + ".png"
            map_image.save(map_filepath)

            await ctx.interaction.response.send_message(file=discord.File(map_filepath), ephemeral=True)
            os.remove(map_filepath)
        except NationsException as e:
            await interacton_error(ctx.interaction, e.user_message)
            raise
        except Exception as e:
            logger.error(f"Failed to render map snapshot for {ctx.interaction.user.name} at location {(location_x, location_y)}: {e}")
            await interacton_error(ctx.interaction)
            raise

    # ----- MILITARY COMMANDS ----- #

    military = discord.SlashCommandGroup("military", description="Manage your military")

    @military.command(description="Trains a new army")
    @discord.default_permissions(administrator=True)
    @discord.option("name", input_type=str, description="The name of the new army.")
    @discord.option("city", input_type=str, description="The city to train in.")
    async def newarmy(self, ctx: ApplicationContext, name: str, city: str):
        try:
            await new_army(name, ctx.interaction.user.id, city)
        except NationsException as e:
            await interacton_error(ctx.interaction, e.user_message)
            raise
        except Exception as e:
            logger.error(f"Failed to create new army for {ctx.interaction.user.name}: {e}")
            await interacton_error(ctx.interaction)
            raise
        
        await interaction_response(ctx.interaction, "Created!", f"New army {name} started training in {city}")

    @military.command(description="Builds a new fleet")
    @discord.default_permissions(administrator=True)
    @discord.option("name", input_type=str, description="The name of the new fleet.")
    @discord.option("city", input_type=str, description="The city to train in.")
    async def fleet(self, ctx: ApplicationContext, name: str, city: str):
        try:
            await new_fleet(name, ctx.interaction.user.id, city)
        except NationsException as e:
            await interacton_error(ctx.interaction, e.user_message)
            raise
        except Exception as e:
            logger.error(f"Failed to create new fleet for {ctx.interaction.user.name}: {e}")
            await interacton_error(ctx.interaction)
            raise
        
        await interaction_response(ctx.interaction, "Created!", f"New fleet {name} started training in {city}")

    # ----- BUILD COMMANDS ----- #

    build = discord.SlashCommandGroup("build", description="Build structures")

    @build.command(description="Builds a new city")
    @discord.default_permissions(administrator=True)
    @discord.option("name", input_type=str, description="The name of your new city")
    @discord.option("x", input_type=int, description="The x-coordinate (1st on the map) of your new city")
    @discord.option("y", input_type=int, description="The y-coordinate (2nd on the map) of your new city")
    async def city(self, ctx: ApplicationContext, name: str, x: int, y: int):
        await ctx.interaction.response.defer()
        followup_msg: discord.WebhookMessage = None
        
        try:
            virtual_snapshot = rendering.snapshot_center(x, y, {(x, y): "metropolis"})
            map_filepath = "data/snapshot" + str(ctx.interaction.user.id) + ".png"
            virtual_snapshot.save(map_filepath)

            with open(map_filepath, "rb") as f:
                snapshot_file = discord.File(map_filepath, filename="snapshot.png")
                
                confirm_future = asyncio.Future()
                confirm_view = ConfirmView(confirm_future)
                followup_msg = await ctx.followup.send(
                    embed=Embed(
                        color=brand_color,
                        title="Confirm placement",
                        description="Your new city will go here. Are you sure?"
                    ).set_image(
                        url="attachment://snapshot.png"
                    ),
                    file=snapshot_file,
                    view=confirm_view,
                    wait=True
                )
            await asyncio.wait([confirm_future])
            confirmation = confirm_future.result()
            if confirmation in ["No", None]:
                raise CancelledException("Nation creation")
            
            logger.debug(f"Making new city for {ctx.interaction.user.name}...")
            await new_city(name, (x, y), ctx.interaction.user.id)
        except NationsException as e:
            await followup_error(ctx.followup, e.user_message)
            raise
        except Exception as e:
            logger.error(f"Failed to build new city '{name}' at {(x, y)}: {e}")
            await followup_error(ctx.followup)
            raise
        
        await followup_msg.delete()
        await followup_response(ctx.followup, title="Built!", message=f"Your city '{name}' was built at {(x, y)}")


    @build.command(description="Builds a new upgrade in a city")
    @discord.default_permissions(administrator=True)
    @discord.option("cityname", input_type=str, description="The name of the city to build the upgrade in")
    @discord.option("upgrade", input_type=str, description="The upgrade you want to build", choices=[
        "Temple", "Grand Temple", "Station", "Central Station", "Workshop",
        "Charcoal pit", "Smeltery", "Port", "Foundry"
    ])
    async def upgrade(self, ctx: ApplicationContext, cityname: str, upgrade: str):
        try:
            nation = nation_list[ctx.interaction.user.id]
            city = nation.cities[cityname]

            structure_types[upgrade].build(city.location, city, nation.econ)
        except NationsException as e:
            await interacton_error(ctx.interaction, e.user_message)
            raise
        except Exception as e:
            logger.error(f"Failed to build {upgrade}: {e}")
            await interacton_error(ctx.interaction)
            raise
        
        await interaction_response(ctx.interaction, "Built!", f"Your {upgrade} has been built in {cityname}!")
        logger.info(f"Someone built a {upgrade.lower()}!")

    @build.command(description="Builds a new railroad")
    @discord.default_permissions(administrator=True)
    @discord.option("origin", input_type=str, description="The city the railroad starts in.")
    @discord.option("level", input_type=str, description="The level of railroad to build", choices=["simple", "quality"])
    async def rail(self, ctx: ApplicationContext, origin: str, level: str):
        await ctx.interaction.response.defer()
        followup_msg: discord.WebhookMessage = await ctx.followup.send(content="Thinking...")
        finished = False
        current_tile = nation_list[ctx.interaction.user.id].cities[origin]
        last_tile = None
        try:
            while not finished:
                # TODO: Add a map image showing current railroad progress
                direction_future = asyncio.Future()
                await ctx.interaction.followup.edit_message(embed=Embed(
                    message_id=followup_msg.id,
                    color=brand_color,
                    title="Choose a direction",
                    description="Select a direction for your railway to head next."
                ), view=DirectionView(direction_future, timeout=60))
                await asyncio.wait([direction_future])
                
                direction = direction_future.result()
                match direction:
                    case direction if direction in ("n", "nw", "sw", "s", "se", "ne"):
                        current_tile, last_tile = move_in_direction(current_tile, direction)
                    case "Back":
                        if last_tile is not None:
                            current_tile, last_tile = last_tile, None
                        else:
                            await interacton_error(ctx.interaction, "You can't go back any further!")
                    case "Cancel":
                        raise CancelledException("Railroad building")
                
                if isinstance(current_tile, City):
                    finished = True
        except Exception as e:
            logger.error(f"Failed to build railroad for {ctx.interaction.user.name}: {e}")
            await followup_msg.delete()
            await followup_error(ctx.followup, e.user_message if isinstance(e, NationsException) else "")
            raise

        #TODO: Add confirmation
        new_link = Link(origin=origin, destination=current_tile.name, owner=ctx.interaction.user.id, 
                        linktype=("simple railroad" if level=="simple" else "quality railroad"))
        await interaction_response(ctx.interaction, "Built!", f"Your railroad has been built to {current_tile.name}!")

    # ----- MILITARY COMMANDS ----- #

    nation = discord.SlashCommandGroup("nation", description="Manage your nation")

    @nation.command(description="Changes the summary of your nation that appears on your profile.")
    @discord.default_permissions(administrator=True)
    @discord.option("text", input_type=str, description="The text you want to appear on your profile.")
    @discord.option("title", input_type=str, description="The title of this dossier block", default="Dossier")
    async def dossier(self, ctx: ApplicationContext, text: str, title: str):
        try:
            nation_list[ctx.interaction.user.id].dossier[title] = text
            await nation_list[ctx.interaction.user.id].save()
            logger.info(f"{ctx.interaction.user.name} changed their profile's {title} block to {text}")
            await interaction_response(ctx.interaction, f"{title} block changed!", f"Your profile's {title} block has been changed to: \n'{text}'")
        except NationsException as e:
            await interacton_error(ctx.interaction, e.user_message)
            raise
        except Exception as e:
            logger.warning(f"Failed to change dossier for {ctx.interaction.user.name}: {e}")
            raise

    @nation.command(description="Changes the color associated with your nation.")
    @discord.default_permissions(administrator=True)
    @discord.option("hex", input_type=str, description="The hex value of the new color")
    async def color(self, ctx: ApplicationContext, hex: str):
        try:
            nation_list[ctx.interaction.user.id].color = discord.Colour.from_rgb(ImageColor.getrgb(hex))
            await nation_list[ctx.interaction.user.id].save()
            logger.info(f"{ctx.interaction.user.name} changed their nation color to '{hex}'")
            await interaction_response(ctx.interaction, f"Color changed!", f"Your nation color has been changed to '{hex}'")
        except NationsException as e:
            interacton_error(ctx.interaction, e.user_message)
            raise
        except Exception as e:
            logger.warning(f"Failed to change color for {ctx.interaction.user.name}: {e}")
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