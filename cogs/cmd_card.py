from PIL import Image, ImageDraw, ImageFont
import discord
from discord.ext import commands
import io
import os

def make_rectangle_pos(x, y, size):
    return [(x, y), (x+size, y), (x+size,y+size), (x, y+size), (x, y)]

def make_Japanese_syllabary_table(char_flg, char_list, current_name, print_current_name = True):
    #   背景の作成
    width  = 880
    height = 300
    fsize  = 24
    im = Image.new("RGB", (width, height), (255, 255, 255))
    
    # フォント設定（Docker内のパスを指定）
    font_path = "/app/fonts/NotoSansJP-Regular.ttf"
    
    try:
        font = ImageFont.truetype(font_path, 20)
    except OSError:
        print(f"[ERROR] Font not found at {font_path}. Using default.")
        font = ImageFont.load_default()
        
    draw = ImageDraw.Draw(im)

    str_color = (0, 0, 0)
    # bg_color  = (236,239,241) # 初期値として定義されていなかったのでコメントアウトまたは適宜設定

    if (print_current_name):
        length = len(current_name)
        pos_x = width / 2 - length*fsize/2
        pos_y = 25
        draw.text((pos_x,pos_y),current_name.replace('？', '●'),font=font,fill=str_color)
    
    pos_x = 30
    # pos_y = 0
    next_space  = 40
    str_posx = 6
    str_posy = 1
    rectangle_size = 30
    
    for charf, chars in zip(char_flg, char_list):
        pos_y = 75
        for flg, char in zip(charf, chars):
            if (char == '2'):
                char = '２'
            elif (char == 'Z'):
                char = 'Ｚ'
            if (char == ''):
                pos_y += next_space
                continue
            if (flg == 1):
                bg_color = (117, 117, 117)
                str_color = (255, 255, 255)
            elif (flg == 2):
                bg_color = (201, 180, 88)
                str_color = (255, 255, 255)
            elif (flg == 3):
                bg_color = (76, 175, 80)
                str_color = (255, 255, 255)
            else:
                bg_color = (236,239,241)
                str_color = (0, 0, 0)
            
            draw.line(xy = make_rectangle_pos(pos_x, pos_y, rectangle_size), fill = bg_color, width = 3)
            draw.rectangle([(pos_x + 2, pos_y + 2), (pos_x + rectangle_size - 2, pos_y + rectangle_size - 2)], fill = bg_color, width = 0, outline = bg_color)
            draw.text((pos_x + str_posx,pos_y + str_posy),char,font=font,fill=str_color)
            pos_y += next_space
        pos_x += next_space

    buffer = io.BytesIO()
    im.save(buffer, format='JPEG', quality=95)
    buffer.seek(0)
    return buffer

class CmdCard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def create_card(self, ctx):
        """日本語音節表の画像を生成する"""
        char_flg = [[1, 2, 3], [0, 1, 2]]
        char_list = [['あ', 'い', 'う'], ['え', 'お', 'か']]
        current_name = ctx.author.display_name

        image_buffer = make_Japanese_syllabary_table(char_flg, char_list, current_name)
        
        # 生成した画像を送信
        await ctx.send(file=discord.File(image_buffer, filename='table.jpg'))

async def setup(bot):
    await bot.add_cog(CmdCard(bot))