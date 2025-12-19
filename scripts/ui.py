import discord
import asyncio

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