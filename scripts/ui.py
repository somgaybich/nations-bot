import discord
import asyncio

from scripts.constants import brand_color

class DirectionView(discord.ui.View):
    def __init__(self, future: asyncio.Future):
        super().__init__()
        self.future = future

    async def on_timeout(self):
        self.disable_all_items()
        await self.message.edit(content="You took too long to select a direction!", view=self)
        raise TimeoutError("User took too long to select a direction")

    @discord.ui.select(
        placeholder = "Choose a direction!",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(
                label="N",
                value="n"
            ),
            discord.SelectOption(
                label="NW",
                value="nw"
            ),
            discord.SelectOption(
                label="SW",
                value="sw"
            ),
            discord.SelectOption(
                label="S",
                value="s"
            ),
            discord.SelectOption(
                label="SE",
                value="se"
            ),
            discord.SelectOption(
                label="NE",
                value="ne"
            ),
            discord.SelectOption(
                label="Back"
            ),
            discord.SelectOption(
                label="Cancel"
            )
        ]
    )
    async def select_callback(self, select, interaction):
        self.future.set_result(select)

class ConfirmView(discord.ui.View):
    def __init__(self, future: asyncio.Future):
        super().__init__(timeout=10)
        self.future = future
        self.message: discord.Message | None = None
    
    async def on_timeout(self):
        self.disable_all_items()
        if self.message:
            await self.message.edit(view=self)
        if not self.future.done():
            self.future.set_result(None)
    
    @discord.ui.select(
        placeholder="Are you sure?",
        select_type=discord.ComponentType.string_select,
        options=[
            discord.SelectOption(label="Yes"),
            discord.SelectOption(label="No")
        ]
    )
    async def select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.response.edit_message(view=self)

        if not self.future.done():
            self.future.set_result(select.values[0])