import re

from io import StringIO
from random import randint
from typing import Optional
from discord.ext import commands
from humanize import naturaltime
from collections import defaultdict
from .meta import BetterUserConverter
from textwrap import wrap as insert_spaces
from string import ascii_letters as alphabet_
from discord import Embed, AllowedMentions, utils, File

class Fun(commands.Cog):
    """Cog used for fun commands."""

    def __init__(self, bot):
        self.bot = bot

    ip_regex     = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
    binary_regex = re.compile(r'^[0-1]{8}$')

    async def _haste_helper(self, ctx, output):
        """Helper function that posts long outputs of conversion commands to a haste server."""
        if len(output) >= 200:
            async with self.bot.session.post('https://mystb.in/documents', data=output) as post:
                if url := (await post.json()).get('key'):
                    await ctx.reply(f'https://mystb.in/raw/{url}')
                else:
                    with StringIO() as f:
                        f.write(output)
                        f.seek(0)
                        await ctx.reply('Too long. Heres a file.', file=File(f, filename='binary.txt'))
        else:
            await ctx.reply(output, allowed_mentions=AllowedMentions(everyone=False, roles=False, users=[ctx.author]))

    @staticmethod
    async def _attachment_helper(ctx):
        output = ''

        for attachment in ctx.message.attachments:
            try:
                output += ''.join((await attachment.read()).decode('utf-8').replace(' ', '\n'))
            except UnicodeDecodeError:
                return await ctx.reply('use text files.')

        return output

    @commands.command()
    @commands.cooldown(1, 1.5, commands.BucketType.guild)
    async def binary(self, ctx, *, text=''):
        """Convert text to binary or vise versa."""
        text = await type(self)._attachment_helper(ctx) or text

        try:
            binary = insert_spaces(text.strip(), 8)
            input_is_binary = all(re.match(type(self).binary_regex, b) for b in binary)
            if len(text) % 8 and input_is_binary:
                output = ''.join([chr(int(byte, 2)) for byte in binary]).replace('\n', ' ')
            else:
                raise ValueError
        except ValueError:
            output = ' '.join([bin(ord(char))[2:].zfill(8) for char in text])

        await self._haste_helper(ctx, output)

    @commands.command(name='hex')
    @commands.cooldown(1, 1.5, commands.BucketType.guild)
    async def _hex(self, ctx, *, text=''):
        """Convert text to hexadecimal or vice versa."""
        text = await type(self)._attachment_helper(ctx) or text

        try:
            output = bytes.fromhex(text).decode('utf-8')
        except ValueError:
            output = ''.join([str(hex(ord(char)))[2:] for char in text])

        await self._haste_helper(ctx, output)

    @commands.command()
    @commands.cooldown(1, 1.5, commands.BucketType.guild)
    async def morse(self, ctx, *, text=''):
        """Convert text into morse code and vice versa."""
        text = await type(self)._attachment_helper(ctx) or text
        operator = 'decode' if {'.', '-', ' '}.issuperset(text) else 'encode'

        url = f'http://www.morsecode-api.de/{operator}?string={text}'
        async with self.bot.session.get(url) as get:
            key = 'morsecode' if operator == 'encode' else 'plaintext'
            output = (await get.json()).get(key)

        if len(output) <= 1:
            await ctx.reply('invalid morse code.')
        else:
            await self._haste_helper(ctx, output)

    @commands.command()
    @commands.cooldown(1, 1.5, commands.BucketType.guild)
    async def caesar(self, ctx, *, text):
        """Convert plain text into a caesar cipher. Default shift factor is 4."""
        table = str.maketrans(alphabet_, alphabet_[4:] + alphabet_[:4])
        await ctx.reply(text.translate(table))

    @commands.command()
    @commands.cooldown(1, 0.75, commands.BucketType.guild)
    async def catfact(self, ctx):
        """Random cat facts. UwU."""
        async with self.bot.session.get('https://catfact.ninja/fact?max_length=100') as g:
            fact  = (await g.json()).get('fact')
            embed = Embed(description=fact, colour=randint(0, 0xffffff))
            await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 1.5, commands.BucketType.guild)
    async def ip(self, ctx, *, ip=''):
        """Get information regarding a specific IP address."""
        ip = re.search(type(self).ip_regex, ip)

        if not ip:
            return await ctx.reply('invalid ip.')

        url = f'https://api.ipgeolocation.io/ipgeo?apiKey={self.bot.ip_key}&ip={ip.string}'
        async with self.bot.session.get(url) as g:
            info = defaultdict(lambda: 'None', await g.json())

        lat        = info['latitude']
        city       = info['city']
        flag       = info['country_flag']
        long       = info['longitude']
        country    = info['country']
        zipcode    = info['zipcode']
        calling    = info['calling_code']
        continent  = info['continent_name']
        state_prov = info['state_prov']

        embed = (
            Embed(title=ip.string, colour=randint(0, 0xffffff))
            .add_field(name='**Continent:**', value=continent, inline=True)
            .add_field(name='**Country:**', value=country, inline=True)
            .add_field(name='**State/Province:**', value=state_prov, inline=False)
            .add_field(name='**City:**', value=city, inline=True)
            .add_field(name='**Zip:**', value=zipcode, inline=False)
            .set_footer(text=f'Calling Code: {calling} | Lat: {lat} | Long: {long}')
            .set_thumbnail(url=flag)
        )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 1.5, commands.BucketType.guild)
    async def snipe(self, ctx, category='deleted'):
        """Snipe a deleted message."""
        if category not in ('edited', 'deleted'):
            category = 'deleted'

        try:
            guild  = str(ctx.guild.id)
            channl = str(ctx.channel.id)

            snipe  = self.bot.cache[guild][channl]['messages'][category][0]
            author = await BetterUserConverter().convert(ctx, snipe.author)
            avatar = author.avatar_url_as(static_format='png')

            embed = Embed(
                title=f'In #{snipe.channel} | Around {naturaltime(snipe.when)}.',
                colour=randint(0, 0xffffff)
            ).set_author(name=f'{author} ({author.id})', icon_url=avatar)

            if category == 'deleted':
                deleted_content   = snipe.content.replace('`', '')
                embed.description = f"```diff\n- {deleted_content}```"
            else:
                after_content     = snipe.content['a'].replace('`', '')
                before_content    = snipe.content['b'].replace('`', '')
                embed.description = f'```diff\n- {before_content}\n+ {after_content}```'

            if attachments := snipe.attachments:
                embed.add_field(name='**Attachments**', value='\n'.join(a.proxy_url for a in attachments))

            await ctx.send(embed=embed)
        except (KeyError, IndexError):
            await ctx.reply('there are no snipes for this channel.')


def setup(bot):
    bot.add_cog(Fun(bot))
