from discord.ext import commands


class FunCog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 2, commands.BucketType.guild)
    async def binary(self, ctx, *, text):
        """Convert text to binary or vise versa. Enter binary bytes separated by spaces to convert into utf-8."""
        try:
            output = ''.join([chr(int(byte, 2)) for byte in text.split()])
        except ValueError:
            output = ' '.join([bin(ord(char))[2:].zfill(8) for char in text])

        async with self.bot.session.post('https://hastebin.com/documents', data=output) as post:
            data = await post.json()

            url_code = data.get('key', None)
            if url_code:
                await ctx.send(
                    f'{ctx.author.mention}, **here is your converted text!\nhttps://hastebin.com/{url_code}**')
            else:
                raise RuntimeError(f'Failed to upload text to hastebin: {data.get("message", None)}')


def setup(bot):
    bot.add_cog(FunCog(bot))